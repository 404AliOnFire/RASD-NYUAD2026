"""
Baseline greedy routing algorithm.
"""

from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd

from rasd_ai.config.paths import PATHS
from rasd_ai.config.settings import SETTINGS
from rasd_ai.data.loaders import load_json, load_csv, load_numpy, save_json


def build_node_index(nodes: List[Dict]) -> Dict[Any, int]:
    """Build index mapping node_id to array position."""
    idx = {}
    for i, n in enumerate(nodes):
        idx[n["node_id"]] = i
    return idx


def truck_can_serve(truck: Dict, pit_row: pd.Series) -> bool:
    """Check if truck can serve this pit (narrow street constraint)."""
    ttype = str(truck.get("type", "")).lower()
    is_narrow = int(pit_row.get("is_narrow", 0))
    if ttype == "large" and is_narrow == 1:
        return False
    return True


def travel_time(T: np.ndarray, i: int, j: int) -> float:
    """Get travel time between two nodes."""
    return float(T[i, j])


def is_forbidden_time(tmin: float) -> bool:
    """Check if route is blocked (closures marked as 1e6)."""
    return tmin >= 1e5


def build_baseline_routes(
    df_pits: pd.DataFrame,
    nodes: List[Dict],
    trucks: List[Dict],
    T: np.ndarray,
) -> Tuple[Dict, Dict]:
    """
    Build routes using greedy priority-based heuristic.

    Args:
        df_pits: DataFrame with pit data
        nodes: List of node dicts with node_id, lat, lon
        trucks: List of truck configuration dicts
        T: Travel time matrix

    Returns:
        Tuple of (route_details dict, metrics dict)
    """
    node_to_idx = build_node_index(nodes)

    # Prepare pit lookup
    pits = df_pits.copy()
    pits["tank_id"] = pits["tank_id"].astype(int)
    pits["tier"] = pits["tier"].astype(str)

    # Served flags
    served = {int(tid): False for tid in pits["tank_id"].tolist()}
    arrival_time_min: Dict[int, float] = {}
    served_by_truck: Dict[int, List[int]] = {}

    # Metrics accumulators
    total_travel_min = 0.0
    total_service_min = 0.0

    routes = {}

    for truck in trucks:
        truck_id = int(truck["truck_id"])
        cap = float(truck["capacity"])
        shift_min = float(truck["shift_min"])

        remaining_cap = cap
        elapsed = 0.0
        curr_node = "depot"
        curr_idx = node_to_idx[curr_node]

        route_list = ["depot"]
        served_by_truck[truck_id] = []

        while True:
            best_tid = None
            best_score = -1e18
            best_next_idx = None
            best_travel = None

            for _, r in pits.iterrows():
                tid = int(r["tank_id"])
                if served[tid]:
                    continue

                demand = float(r.get("demand", 1))
                if demand > remaining_cap:
                    continue

                if not truck_can_serve(truck, r):
                    continue

                next_idx = node_to_idx.get(tid, None)
                if next_idx is None:
                    continue

                tmin = travel_time(T, curr_idx, next_idx)
                if is_forbidden_time(tmin):
                    continue

                service = float(r.get("service_min", 0))
                back_to_depot = travel_time(T, next_idx, node_to_idx["depot"])
                if is_forbidden_time(back_to_depot):
                    back_to_depot = 1e6

                new_elapsed_if_take = elapsed + tmin + service + back_to_depot
                if new_elapsed_if_take > shift_min:
                    continue

                pr = float(r.get("priority", 0.0))
                score = pr - (0.015 * tmin)

                if score > best_score:
                    best_score = score
                    best_tid = tid
                    best_next_idx = next_idx
                    best_travel = tmin

            if best_tid is None:
                break

            elapsed += float(best_travel)
            total_travel_min += float(best_travel)
            arrival_time_min[best_tid] = elapsed

            pit_row = pits.loc[pits["tank_id"] == best_tid].iloc[0]
            service = float(pit_row.get("service_min", 0))
            elapsed += service
            total_service_min += service

            demand = float(pit_row.get("demand", 1))
            remaining_cap -= demand
            served[best_tid] = True

            route_list.append(best_tid)
            served_by_truck[truck_id].append(best_tid)
            curr_idx = best_next_idx
            curr_node = best_tid

        back = travel_time(T, curr_idx, node_to_idx["depot"])
        if not is_forbidden_time(back):
            elapsed += back
            total_travel_min += back
        route_list.append("depot")

        routes[f"truck_{truck_id}"] = route_list

    # Compute coverage metrics
    total_penalty = 0.0
    high_total = int((pits["tier"] == "HIGH").sum())
    med_total = int((pits["tier"] == "MEDIUM").sum())
    low_total = int((pits["tier"] == "LOW").sum())

    high_served = med_served = low_served = 0

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
            total_penalty += late * SETTINGS.get_penalty_per_min(tier)
        else:
            total_penalty += SETTINGS.get_unserved_penalty(tier)

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
    """Build baseline routes from generated routing inputs."""
    df_pits = load_csv(PATHS.routing_pits_csv)
    nodes = load_json(PATHS.nodes_json)
    trucks = load_json(PATHS.trucks_json)
    T = load_numpy(PATHS.travel_time_matrix_npy)

    routes, metrics = build_baseline_routes(df_pits, nodes, trucks, T)

    save_json(PATHS.baseline_routes_json, routes)
    save_json(PATHS.baseline_metrics_json, metrics)

    print("✅ Baseline routes created")
    print(f"   - {PATHS.baseline_routes_json}")
    print(f"   - {PATHS.baseline_metrics_json}")
    print("\nMetrics summary:")
    for k, v in metrics.items():
        print(f"   {k}: {v}")


if __name__ == "__main__":
    main()
