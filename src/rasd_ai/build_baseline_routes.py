import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd


# -----------------------------
# Penalty settings (tweakable)
# -----------------------------
PENALTY_PER_MIN = {
    "HIGH": 80,     # lateness penalty per minute
    "MEDIUM": 25,
    "LOW": 8,
}

UNSERVED_PENALTY = {
    "HIGH": 6000,   # if not served at all
    "MEDIUM": 1500,
    "LOW": 300,
}

# Baseline scoring weights (naive heuristic)
# higher priority wins, but travel time matters a bit
ALPHA_PRIORITY = 1.0
BETA_TRAVEL = 0.015  # subtract travel_min * BETA


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
    """
    nodes.json contains:
      index 0: depot with node_id="depot"
      index 1..N: pits with node_id = tank_id (int)
    """
    idx = {}
    for i, n in enumerate(nodes):
        idx[n["node_id"]] = i
    return idx


def truck_can_serve(truck: Dict, pit_row: pd.Series) -> bool:
    # simple narrow streets rule:
    # large trucks cannot go into narrow pits
    ttype = str(truck.get("type", "")).lower()
    is_narrow = int(pit_row.get("is_narrow", 0))
    if ttype == "large" and is_narrow == 1:
        return False
    return True


def travel_time(T: np.ndarray, i: int, j: int) -> float:
    return float(T[i, j])


def is_forbidden_time(tmin: float) -> bool:
    return tmin >= 1e5  # closures are ~1e6


# -----------------------------
# Baseline Greedy Router
# -----------------------------
def build_baseline_routes(
    df_pits: pd.DataFrame,
    nodes: List[Dict],
    trucks: List[Dict],
    T: np.ndarray,
) -> Tuple[Dict, Dict]:
    node_to_idx = build_node_index(nodes)

    # Prepare pit lookup
    pits = df_pits.copy()
    pits["tank_id"] = pits["tank_id"].astype(int)
    pits["tier"] = pits["tier"].astype(str)

    # Served flags
    served = {int(tid): False for tid in pits["tank_id"].tolist()}

    # For penalty calculation
    arrival_time_min: Dict[int, float] = {}  # tank_id -> arrival_min
    served_by_truck: Dict[int, List[int]] = {}

    # Metrics accumulators
    total_travel_min = 0.0
    total_service_min = 0.0

    # Build routes
    routes = {}

    for truck in trucks:
        truck_id = int(truck["truck_id"])
        cap = float(truck["capacity"])
        shift_min = float(truck["shift_min"])

        remaining_cap = cap
        elapsed = 0.0  # minutes since shift start
        curr_node = "depot"
        curr_idx = node_to_idx[curr_node]

        route_list = ["depot"]
        served_by_truck[truck_id] = []

        while True:
            # Find feasible candidates not served yet
            best_tid = None
            best_score = -1e18
            best_next_idx = None
            best_travel = None

            for _, r in pits.iterrows():
                tid = int(r["tank_id"])
                if served[tid]:
                    continue

                # capacity feasibility
                demand = float(r.get("demand", 1))
                if demand > remaining_cap:
                    continue

                # truck access feasibility
                if not truck_can_serve(truck, r):
                    continue

                # travel feasibility (closures)
                next_idx = node_to_idx.get(tid, None)
                if next_idx is None:
                    continue

                tmin = travel_time(T, curr_idx, next_idx)
                if is_forbidden_time(tmin):
                    continue

                # time feasibility: must fit travel + service + return-to-depot within shift
                service = float(r.get("service_min", 0))
                back_to_depot = travel_time(T, next_idx, node_to_idx["depot"])
                if is_forbidden_time(back_to_depot):
                    back_to_depot = 1e6

                new_elapsed_if_take = elapsed + tmin + service + back_to_depot
                if new_elapsed_if_take > shift_min:
                    continue

                # naive score: priority minus a small travel penalty
                pr = float(r.get("priority", 0.0))
                score = (ALPHA_PRIORITY * pr) - (BETA_TRAVEL * tmin)

                if score > best_score:
                    best_score = score
                    best_tid = tid
                    best_next_idx = next_idx
                    best_travel = tmin

            if best_tid is None:
                break  # no more feasible jobs for this truck

            # Commit the move
            # travel to pit
            elapsed += float(best_travel)
            total_travel_min += float(best_travel)

            # record arrival time (before service)
            arrival_time_min[best_tid] = elapsed

            # service
            pit_row = pits.loc[pits["tank_id"] == best_tid].iloc[0]
            service = float(pit_row.get("service_min", 0))
            elapsed += service
            total_service_min += service

            # update capacity / served
            demand = float(pit_row.get("demand", 1))
            remaining_cap -= demand
            served[best_tid] = True

            # update route
            route_list.append(best_tid)
            served_by_truck[truck_id].append(best_tid)
            curr_idx = best_next_idx
            curr_node = best_tid

        # Return to depot
        back = travel_time(T, curr_idx, node_to_idx["depot"])
        if not is_forbidden_time(back):
            elapsed += back
            total_travel_min += back
        route_list.append("depot")

        routes[f"truck_{truck_id}"] = route_list

    # -----------------------------
    # Compute penalties + coverage
    # -----------------------------
    total_penalty = 0.0
    high_total = int((pits["tier"] == "HIGH").sum())
    med_total = int((pits["tier"] == "MEDIUM").sum())
    low_total = int((pits["tier"] == "LOW").sum())

    high_served = 0
    med_served = 0
    low_served = 0

    for _, r in pits.iterrows():
        tid = int(r["tank_id"])
        tier = str(r["tier"])
        deadline = float(r.get("deadline_min", 24 * 60))
        if served[tid]:
            if tier == "HIGH":
                high_served += 1
            elif tier == "MEDIUM":
                med_served += 1
            else:
                low_served += 1

            arr = float(arrival_time_min.get(tid, 0.0))
            late = max(0.0, arr - deadline)
            total_penalty += late * PENALTY_PER_MIN.get(tier, 10)
        else:
            total_penalty += UNSERVED_PENALTY.get(tier, 500)

    served_total = sum(1 for v in served.values() if v)
    missed_total = len(served) - served_total

    metrics = {
        "served_total": served_total,
        "missed_total": missed_total,
        "high_total": high_total,
        "high_served": high_served,
        "high_missed": high_total - high_served,
        "medium_total": med_total,
        "medium_served": med_served,
        "low_total": low_total,
        "low_served": low_served,
        "total_travel_min": round(total_travel_min, 2),
        "total_service_min": round(total_service_min, 2),
        "total_penalty": round(total_penalty, 2),
    }

    # Optional: include per-truck route details for frontend
    route_details = {}
    for truck in trucks:
        tid = int(truck["truck_id"])
        key = f"truck_{tid}"
        seq = routes[key]
        route_details[key] = {
            "sequence": seq,
            "served_pits": served_by_truck.get(tid, []),
            "capacity": truck["capacity"],
            "shift_min": truck["shift_min"],
            "type": truck.get("type", ""),
        }

    return route_details, metrics


def main():
    outdir = ensure_outputs_dir()

    pits_path = outdir / "routing_pits.csv"
    nodes_path = outdir / "nodes.json"
    trucks_path = outdir / "trucks.json"
    matrix_path = outdir / "travel_time_matrix.npy"

    if not pits_path.exists():
        raise FileNotFoundError("missing outputs/routing_pits.csv run generate_routing_inputs.py first")
    if not nodes_path.exists():
        raise FileNotFoundError("missing outputs/nodes.json run generate_routing_inputs.py first")
    if not trucks_path.exists():
        raise FileNotFoundError("missing outputs/trucks.json run generate_routing_inputs.py first")
    if not matrix_path.exists():
        raise FileNotFoundError("missing outputs/travel_time_matrix.npy run generate_routing_inputs.py first")

    df_pits = pd.read_csv(pits_path)
    nodes = load_json(nodes_path)
    trucks = load_json(trucks_path)
    T = np.load(matrix_path)

    routes, metrics = build_baseline_routes(df_pits, nodes, trucks, T)

    routes_path = outdir / "baseline_routes.json"
    metrics_path = outdir / "baseline_metrics.json"

    save_json(routes_path, routes)
    save_json(metrics_path, metrics)

    print("✅ baseline created")
    print(f" - {routes_path}")
    print(f" - {metrics_path}")
    print("\nmetrics summary:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
