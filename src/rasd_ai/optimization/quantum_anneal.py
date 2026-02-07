"""
Quantum annealing solver using D-Wave Ocean SDK (simulation mode).
"""

import sys
from typing import Tuple

import numpy as np
import pandas as pd
import dimod

from rasd_ai.config.paths import PATHS
from rasd_ai.config.settings import SETTINGS
from rasd_ai.data.loaders import load_json, load_csv, load_numpy, save_json


def _tier_weights(tier: str) -> Tuple[float, float]:
    """Get penalty and reward weights for a tier."""
    t = str(tier).upper()
    if t == "HIGH":
        return 4000.0, 1.4
    if t == "MEDIUM":
        return 1200.0, 1.0
    return 300.0, 0.7


def solve_quantum_annealing(
    df_priorities: pd.DataFrame,
    trucks: list,
    T: np.ndarray = None,
    top_n: int = SETTINGS.QUANTUM_TOP_N,
    max_trucks: int = SETTINGS.QUANTUM_MAX_TRUCKS,
    num_reads: int = SETTINGS.QUANTUM_NUM_READS,
) -> Tuple[dict, dict]:
    """
    Solve VRP assignment using simulated quantum annealing.

    Args:
        df_priorities: DataFrame with priority data
        trucks: List of truck configurations
        T: Optional travel time matrix
        top_n: Number of top priority pits to consider
        max_trucks: Maximum trucks to use
        num_reads: Number of annealing samples

    Returns:
        Tuple of (routes dict, metrics dict)
    """
    # Sort and select top pits
    tier_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    df = df_priorities.copy()
    df["tier_rank"] = df["tier"].map(lambda x: tier_rank.get(str(x).upper(), 2))
    dfq = df.sort_values(["tier_rank", "priority"], ascending=[True, False]).head(top_n).copy()

    trucks = trucks[:max_trucks]

    # Build BQM
    bqm = dimod.BinaryQuadraticModel({}, {}, 0.0, dimod.BINARY)

    W_PRIORITY = 60.0
    W_ONCE = 250.0
    W_CAP = 6.0
    W_TRAVEL = 1.0
    W_LATE = 2.0

    pits = dfq["tank_id"].astype(int).tolist()
    Tn = len(trucks)
    Pn = len(pits)

    def var(ti: int, pj: int) -> str:
        return f"x_{ti}_{pj}"

    # Objective: reward for serving high priority pits
    for ti in range(Tn):
        for pj in range(Pn):
            pr = float(dfq.iloc[pj]["priority"])
            tier = str(dfq.iloc[pj]["tier"]).upper()
            unserved_pen, serve_mult = _tier_weights(tier)

            bqm.add_variable(var(ti, pj), -W_PRIORITY * serve_mult * pr)

            tto = float(dfq.iloc[pj]["tto_hours"])
            deadline_min = max(30.0, min(12 * 60.0, tto * 60.0))
            travel_min = 25.0 if T is not None else 20.0
            late_est = max(0.0, travel_min - deadline_min)

            bqm.add_linear(var(ti, pj), W_LATE * late_est)
            bqm.add_linear(var(ti, pj), W_TRAVEL * travel_min)

    # Constraint: each pit at most once
    for pj in range(Pn):
        s = sum(dimod.Binary(var(ti, pj)) for ti in range(Tn))
        bqm += W_ONCE * (s * (s - 1))

        tier = str(dfq.iloc[pj]["tier"]).upper()
        unserved_pen, _ = _tier_weights(tier)
        bqm += unserved_pen * (1 - s) * (1 - s)

    # Capacity constraints
    profile_to_demand = {"A": 1.0, "B": 1.5, "C": 2.5}
    for ti in range(Tn):
        cap = float(trucks[ti].get("capacity", 999))
        load = 0
        for pj in range(Pn):
            prof = str(dfq.iloc[pj]["profile"]).upper()
            d = float(profile_to_demand.get(prof, 1.0))
            load += d * dimod.Binary(var(ti, pj))
        bqm += W_CAP * (load - cap) * (load - cap)

    # Solve using simulated annealing
    try:
        from neal import SimulatedAnnealingSampler  # pylint: disable=import-outside-toplevel
    except ImportError as e:
        raise RuntimeError("neal not installed - install dwave-ocean-sdk") from e

    sampler = SimulatedAnnealingSampler()
    sampleset = sampler.sample(bqm, num_reads=num_reads)
    best = sampleset.first.sample

    # Decode solution
    routes = {}
    for ti in range(Tn):
        assigned = []
        for pj in range(Pn):
            if best.get(var(ti, pj), 0) == 1:
                assigned.append(int(pits[pj]))
        routes[f"truck_{int(trucks[ti].get('truck_id', ti+1))}"] = {
            "assigned_pits": assigned,
            "solver": "ocean_simulated_annealing",
        }

    metrics = {
        "solver_used": "ocean_simulated_annealing",
        "problem_size": f"toy {Pn} pits {Tn} trucks",
        "note": "CQM is reference model for D-Wave hybrid QPU when available; demo uses annealing simulation",
    }

    return routes, metrics


def main():
    """Run quantum annealing solver on priorities data."""
    print("PYTHON EXE:", sys.executable)
    print("PYTHON VER:", sys.version)

    df = load_csv(PATHS.priorities_csv)

    # Load or create trucks
    try:
        trucks = load_json(PATHS.trucks_json)
    except FileNotFoundError:
        trucks = [
            {"truck_id": 1, "capacity": 999, "shift_min": 480, "type": "small"},
            {"truck_id": 2, "capacity": 999, "shift_min": 480, "type": "small"},
        ]

    # Load travel matrix if available
    T = None
    if PATHS.travel_time_matrix_npy.exists():
        T = load_numpy(PATHS.travel_time_matrix_npy)

    routes, metrics = solve_quantum_annealing(df, trucks, T)

    save_json(PATHS.quantum_routes_json, routes)
    save_json(PATHS.quantum_metrics_json, metrics)

    print("✅ Quantum routes created")
    print(f"   - {PATHS.quantum_routes_json}")
    print(f"   - {PATHS.quantum_metrics_json}")
    print(f"\nMetrics: {metrics}")


if __name__ == "__main__":
    main()
