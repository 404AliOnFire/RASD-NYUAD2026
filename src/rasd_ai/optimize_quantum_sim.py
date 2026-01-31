import json
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd

import dimod

def _read_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))

def _write_json(p: Path, obj: Any) -> None:
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def _tier_weights(tier: str) -> Tuple[float, float]:
    # returns (unserved_penalty, serve_reward_multiplier)
    t = str(tier).upper()
    if t == "HIGH":
        return 4000.0, 1.4
    if t == "MEDIUM":
        return 1200.0, 1.0
    return 300.0, 0.7

def main():
    import sys
    print("PYTHON EXE:", sys.executable)
    print("PYTHON VER:", sys.version)

    out = Path("outputs")
    priorities_path = out / "priorities.csv"
    if not priorities_path.exists():
        raise FileNotFoundError("missing outputs/priorities.csv run run_pipeline first")

    df = pd.read_csv(priorities_path)

    # toy quantum demo size
    TOP_N = 10
    MAX_TRUCKS = 2

    # take the most critical first
    tier_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    df["tier_rank"] = df["tier"].map(lambda x: tier_rank.get(str(x).upper(), 2))
    dfq = df.sort_values(["tier_rank", "priority"], ascending=[True, False]).head(TOP_N).copy()

    # load trucks if available else make simple ones
    trucks_path = out / "trucks.json"
    if trucks_path.exists():
        trucks = _read_json(trucks_path)
    else:
        trucks = [
            {"truck_id": 1, "capacity": 999, "shift_min": 480, "type": "small"},
            {"truck_id": 2, "capacity": 999, "shift_min": 480, "type": "small"},
        ]

    trucks = trucks[:MAX_TRUCKS]

    # optional travel matrix
    T_path = out / "travel_time_matrix.npy"
    T = None
    if T_path.exists():
        T = np.load(T_path)

    # build BQM for assignment x[t,p]
    bqm = dimod.BinaryQuadraticModel({}, {}, 0.0, dimod.BINARY)

    W_PRIORITY = 60.0
    W_ONCE = 250.0
    W_CAP = 6.0
    W_TRAVEL = 1.0
    W_LATE = 2.0

    # create decision variables
    pits = dfq["tank_id"].astype(int).tolist()
    Tn = len(trucks)
    Pn = len(pits)

    def var(ti: int, pj: int) -> str:
        return f"x_{ti}_{pj}"

    # objective reward for serving high priority
    for ti in range(Tn):
        for pj in range(Pn):
            pr = float(dfq.iloc[pj]["priority"])
            tier = str(dfq.iloc[pj]["tier"]).upper()
            unserved_pen, serve_mult = _tier_weights(tier)
            # reward = negative energy
            bqm.add_variable(var(ti, pj), -W_PRIORITY * serve_mult * pr)

            # estimated lateness penalty using tto_hours as soft deadline
            # if tto is small we want serve sooner
            tto = float(dfq.iloc[pj]["tto_hours"])
            # map tto to a "deadline minutes" proxy
            deadline_min = max(30.0, min(12 * 60.0, tto * 60.0))
            # if we have travel matrix we can use depot->pit approx else small constant
            travel_min = 20.0
            if T is not None:
                # assumes generate_routing_inputs made a node index with depot at 0 and tanks mapped somehow
                # if mapping differs this still stays a soft proxy
                travel_min = 25.0
            late_est = max(0.0, travel_min - deadline_min)
            bqm.add_linear(var(ti, pj), W_LATE * late_est)

            # travel proxy penalty
            bqm.add_linear(var(ti, pj), W_TRAVEL * travel_min)

    # constraint each pit at most once
    for pj in range(Pn):
        s = sum(dimod.Binary(var(ti, pj)) for ti in range(Tn))
        # penalty for s >= 2
        bqm += W_ONCE * (s * (s - 1))

        # also add unserved penalty to encourage serving important pits
        tier = str(dfq.iloc[pj]["tier"]).upper()
        unserved_pen, _ = _tier_weights(tier)
        # penalize (1 - s)^2 encourages s close to 1
        bqm += unserved_pen * (1 - s) * (1 - s)

    # capacity per truck using profile as demand proxy
    # A small B medium C large
    profile_to_demand = {"A": 1.0, "B": 1.5, "C": 2.5}
    for ti in range(Tn):
        cap = float(trucks[ti].get("capacity", 999))
        load = 0
        for pj in range(Pn):
            prof = str(dfq.iloc[pj]["profile"]).upper()
            d = float(profile_to_demand.get(prof, 1.0))
            load += d * dimod.Binary(var(ti, pj))
        # soft capacity penalty square
        bqm += W_CAP * (load - cap) * (load - cap)

    # solve using simulated annealing
    try:
        from neal import SimulatedAnnealingSampler
    except Exception as e:
        raise RuntimeError("neal not installed install dwave-ocean-sdk") from e

    sampler = SimulatedAnnealingSampler()
    sampleset = sampler.sample(bqm, num_reads=3000)
    best = sampleset.first.sample

    # decode assignment
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
        "note": "cqm is reference model for dwave hybrid qpu when available demo uses annealing simulation",
    }

    _write_json(out / "quantum_routes.json", routes)
    _write_json(out / "quantum_metrics.json", metrics)

    print(" saved outputs/quantum_routes.json")
    print(" saved outputs/quantum_metrics.json")
    print(metrics)

if __name__ == "__main__":
    main()
