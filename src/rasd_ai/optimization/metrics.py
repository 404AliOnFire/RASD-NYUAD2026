"""
Metrics computation for route solutions.
"""

import math
from typing import Dict, List, Any, Set

from rasd_ai.config.settings import SETTINGS


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance in km."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def nearest_neighbor_sequence(
    pits: List[int], coords: Dict[Any, tuple], start: str = "depot"
) -> List[Any]:
    """Build sequence using nearest neighbor heuristic."""
    remaining = set(pits)
    seq = [start]
    cur = start

    while remaining:
        clat, clon = coords[cur]
        best, best_d = None, 1e18
        for p in remaining:
            if p not in coords:
                continue
            lat, lon = coords[p]
            d = haversine_km(clat, clon, lat, lon)
            if d < best_d:
                best, best_d = p, d
        if best is None:
            break
        seq.append(best)
        remaining.remove(best)
        cur = best

    seq.append(start)
    return seq


def route_distance_km(seq: List[Any], coords: Dict[Any, tuple]) -> float:
    """Calculate total route distance in km."""
    total = 0.0
    for a, b in zip(seq, seq[1:]):
        if a not in coords or b not in coords:
            continue
        lat1, lon1 = coords[a]
        lat2, lon2 = coords[b]
        total += haversine_km(lat1, lon1, lat2, lon2)
    return total


def build_coord_map(nodes: List[Dict]) -> Dict[Any, tuple]:
    """Build coordinate map from nodes list."""
    coords = {}
    for r in nodes:
        nid = r["node_id"]
        coords[nid] = (float(r["lat"]), float(r["lon"]))
    return coords


def compute_route_metrics(
    sequences: Dict[str, List[Any]], tier_map: Dict[int, str], coords: Dict[Any, tuple]
) -> Dict[str, Any]:
    """
    Compute comprehensive metrics for routes.

    Args:
        sequences: Dict mapping truck_id to route sequence
        tier_map: Dict mapping pit_id to tier (HIGH/MEDIUM/LOW)
        coords: Dict mapping node_id to (lat, lon)

    Returns:
        Dict with computed metrics
    """
    served: Set[int] = set()
    dist_by_truck: Dict[str, float] = {}
    stops_by_truck: Dict[str, int] = {}

    for tid, seq in sequences.items():
        pits = [n for n in seq if n != "depot"]
        served.update(pits)
        stops_by_truck[tid] = len(pits)
        dist_by_truck[tid] = route_distance_km(seq, coords)

    all_pits = set(tier_map.keys())
    served_total = len(served)
    missed_total = len(all_pits - served)

    def tier_counts(label: str) -> tuple:
        ids = {pid for pid, t in tier_map.items() if t == label}
        return len(ids), len(ids & served), len(ids - served)

    high_total, high_served, high_missed = tier_counts("HIGH")
    med_total, med_served, med_missed = tier_counts("MEDIUM")
    low_total, low_served, low_missed = tier_counts("LOW")

    total_km = float(sum(dist_by_truck.values()))
    fuel_l = total_km * SETTINGS.FUEL_L_PER_KM
    co2_kg = fuel_l * SETTINGS.CO2_KG_PER_L

    return {
        "served_total": served_total,
        "missed_total": missed_total,
        "high_total": high_total,
        "high_served": high_served,
        "high_missed": high_missed,
        "medium_total": med_total,
        "medium_served": med_served,
        "medium_missed": med_missed,
        "low_total": low_total,
        "low_served": low_served,
        "low_missed": low_missed,
        "total_distance_km": round(total_km, 2),
        "fuel_l_est": round(fuel_l, 2),
        "co2_kg_est": round(co2_kg, 2),
        "distance_by_truck_km": {k: round(float(v), 2) for k, v in dist_by_truck.items()},
        "stops_by_truck": stops_by_truck,
    }
