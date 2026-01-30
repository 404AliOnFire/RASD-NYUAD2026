# FIXED VERSION: optimize_quantum.py
# Hackathon-safe Quantum/Hybrid Optimizer (Assignment via CQM + Greedy Routing)

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd

import dimod
from dimod import ConstrainedQuadraticModel, Binary

# -----------------------------
# Pack A settings (Demo)
# -----------------------------
W_PRIORITY = 350.0
W_TRAVEL = 1.0
W_LATE = {"HIGH": 90, "MEDIUM": 30, "LOW": 10}
W_UNSERVED = {"HIGH": 9000, "MEDIUM": 2000, "LOW": 400}

FORBIDDEN_TIME = 1e5

# -----------------------------
# Helpers
# -----------------------------

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Any):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def ensure_outputs_dir() -> Path:
    outdir = Path("outputs")
    outdir.mkdir(exist_ok=True)
    return outdir


def build_node_index(nodes: List[Dict]) -> Dict[Any, int]:
    return {n["node_id"]: i for i, n in enumerate(nodes)}


def is_forbidden(tmin: float) -> bool:
    return tmin >= FORBIDDEN_TIME


def truck_can_serve(truck: Dict, pit_row: pd.Series) -> bool:
    if truck.get("type") == "large" and int(pit_row.get("is_narrow", 0)) == 1:
        return False
    return True

# -----------------------------
# Build CQM (Assignment only)
# -----------------------------

def build_cqm(pits: pd.DataFrame, trucks: List[Dict], nodes: List[Dict], T: np.ndarray):
    cqm = ConstrainedQuadraticModel()
    node_to_idx = build_node_index(nodes)
    depot_idx = node_to_idx["depot"]

    x = {}

    # Variables
    for truck in trucks:
        tid = int(truck["truck_id"])
        for _, r in pits.iterrows():
            pid = int(r["tank_id"])
            if not truck_can_serve(truck, r):
                continue
            x[(tid, pid)] = Binary(f"x_t{tid}_p{pid}")

    # Each pit served at most once
    for _, r in pits.iterrows():
        pid = int(r["tank_id"])
        expr = 0
        for truck in trucks:
            tid = int(truck["truck_id"])
            if (tid, pid) in x:
                expr += x[(tid, pid)]
        cqm.add_constraint(expr <= 1, label=f"serve_once_{pid}")

    # Capacity constraint
    for truck in trucks:
        tid = int(truck["truck_id"])
        cap = float(truck["capacity"])
        expr = 0
        for _, r in pits.iterrows():
            pid = int(r["tank_id"])
            if (tid, pid) in x:
                expr += float(r.get("demand", 1)) * x[(tid, pid)]
        cqm.add_constraint(expr <= cap, label=f"capacity_t{tid}")

    # Shift constraint (approx depot -> pit -> depot)
    for truck in trucks:
        tid = int(truck["truck_id"])
        shift = float(truck["shift_min"])
        expr = 0
        for _, r in pits.iterrows():
            pid = int(r["tank_id"])
            if (tid, pid) not in x:
                continue
            p_idx = node_to_idx[pid]
            t_out = T[depot_idx, p_idx]
            t_back = T[p_idx, depot_idx]
            approx_travel = (t_out + t_back) if not (is_forbidden(t_out) or is_forbidden(t_back)) else 1e6
            expr += (approx_travel + float(r.get("service_min", 0))) * x[(tid, pid)]
        cqm.add_constraint(expr <= shift, label=f"shift_t{tid}")

    # Objective
    obj = 0
    for _, r in pits.iterrows():
        pid = int(r["tank_id"])
        tier = str(r.get("tier", "LOW"))
        pr = float(r.get("priority", 0))

        served_expr = 0
        for truck in trucks:
            tid = int(truck["truck_id"])
            if (tid, pid) in x:
                served_expr += x[(tid, pid)]

        # penalty if unserved
        obj += W_UNSERVED[tier] * (1 - served_expr)
        # reward for serving priority
        obj += -W_PRIORITY * pr * served_expr

    for truck in trucks:
        tid = int(truck["truck_id"])
        for _, r in pits.iterrows():
            pid = int(r["tank_id"])
            if (tid, pid) not in x:
                continue
            p_idx = node_to_idx[pid]
            t_out = T[depot_idx, p_idx]
            t_back = T[p_idx, depot_idx]
            approx_travel = (t_out + t_back) if not (is_forbidden(t_out) or is_forbidden(t_back)) else 1e6
            deadline = float(r.get("deadline_min", 1440))
            late_est = max(0.0, t_out - deadline)

            obj += W_TRAVEL * approx_travel * x[(tid, pid)]
            obj += W_LATE[r.get("tier", "LOW")] * late_est * x[(tid, pid)]

    cqm.set_objective(obj)
    return cqm, x

# -----------------------------
# Solve
# -----------------------------

def solve_cqm(cqm):
    try:
        from dwave.system import LeapHybridCQMSampler
        sampler = LeapHybridCQMSampler()
        return sampler.sample_cqm(cqm, time_limit=5), "dwave_hybrid"
    except Exception:
        sampler = dimod.ExactCQMSolver()
        return sampler.sample_cqm(cqm), "exact_fallback"

# -----------------------------
# Main
# -----------------------------

def main():
    out = ensure_outputs_dir()

    pits = pd.read_csv(out / "routing_pits.csv")
    nodes = load_json(out / "nodes.json")
    trucks = load_json(out / "trucks.json")
    T = np.load(out / "travel_time_matrix.npy")

    cqm, x = build_cqm(pits, trucks, nodes, T)
    sampleset, solver_used = solve_cqm(cqm)

    feasible = sampleset.filter(lambda d: d.is_feasible)
    best = feasible.first if len(feasible) else sampleset.first
    sample = best.sample

    routes = {}
    served = set()

    for truck in trucks:
        tid = int(truck["truck_id"])
        assigned = []
        for (t, p), var in x.items():
            if t == tid and sample[str(var)] > 0.5:
                assigned.append(int(p))
                served.add(int(p))
        routes[f"truck_{tid}"] = {
            "assigned_pits": assigned,
            "capacity": truck["capacity"],
            "shift_min": truck["shift_min"],
            "type": truck.get("type")
        }

    metrics = {
        "solver_used": solver_used,
        "served_total": len(served),
        "missed_total": len(pits) - len(served)
    }

    save_json(out / "quantum_routes.json", routes)
    save_json(out / "quantum_metrics.json", metrics)

    print("✅ Quantum optimization finished")
    print(metrics)


if __name__ == "__main__":
    main()
