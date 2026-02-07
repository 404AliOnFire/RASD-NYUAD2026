"""
Frontend data export utilities.
"""

import shutil
from typing import List, Any

from rasd_ai.config.paths import PATHS, FRONTEND_DATA_DIR, FRONTEND_LOGO_DIR
from rasd_ai.data.loaders import load_json, load_csv, save_json
from rasd_ai.optimization.metrics import build_coord_map, nearest_neighbor_sequence


def build_routes_for_frontend() -> dict:
    """
    Build routes_for_frontend.json with polylines for visualization.

    Returns:
        Dict with depot, pits, and routes data
    """
    print("\n📦 Building routes for frontend...")

    # Load data
    nodes = load_json(PATHS.nodes_json)
    priorities = load_csv(PATHS.priorities_csv)
    baseline_routes = load_json(PATHS.baseline_routes_json)
    quantum_routes = load_json(PATHS.quantum_routes_json)

    # Build coordinate map
    coords = build_coord_map(nodes)

    # Find depot
    depot = None
    for n in nodes:
        if n["node_id"] == "depot":
            depot = {"id": "depot", "lat": n["lat"], "lon": n["lon"]}
            break
    if depot is None:
        depot = {"id": "depot", "lat": 31.53, "lon": 35.095}

    # Build pits list
    tier_map = dict(zip(priorities["tank_id"].astype(int), priorities["tier"]))
    priority_map = dict(zip(priorities["tank_id"].astype(int), priorities["priority"]))

    pits = []
    for n in nodes:
        if n["node_id"] != "depot":
            nid = int(n["node_id"])
            pits.append(
                {
                    "id": nid,
                    "lat": n["lat"],
                    "lon": n["lon"],
                    "tier": tier_map.get(nid, "LOW"),
                    "priority": priority_map.get(nid, 0.0),
                }
            )

    def build_polyline(seq: List[Any]) -> List[List[float]]:
        """Build polyline coordinates from sequence."""
        polyline = []
        for node_id in seq:
            if node_id in coords:
                lat, lon = coords[node_id]
                polyline.append([lat, lon])
        return polyline

    # Process baseline routes
    baseline_data = []
    for truck_id, info in baseline_routes.items():
        seq = info.get("sequence", [])
        if len(seq) < 2:
            continue
        stops = seq
        polyline = build_polyline(seq)
        baseline_data.append({"truck_id": truck_id, "stops": stops, "polyline": polyline})

    # Process quantum routes
    quantum_data = []
    for truck_id, info in quantum_routes.items():
        assigned_pits = info.get("assigned_pits", [])
        if not assigned_pits:
            continue
        # Build sequence using nearest neighbor
        seq = nearest_neighbor_sequence(assigned_pits, coords, start="depot")
        polyline = build_polyline(seq)
        quantum_data.append({"truck_id": truck_id, "stops": seq, "polyline": polyline})

    result = {
        "depot": depot,
        "pits": pits,
        "routes": {"baseline": baseline_data, "quantum": quantum_data},
    }

    save_json(PATHS.routes_for_frontend_json, result)
    print(f"✅ saved {PATHS.routes_for_frontend_json}")

    return result


def copy_to_frontend():
    """Copy all output files to frontend public/data directory."""
    print("\n📁 Copying files to frontend...")

    # Ensure directories exist
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_LOGO_DIR.mkdir(parents=True, exist_ok=True)

    # Files to copy
    files_to_copy = [
        PATHS.nodes_json,
        PATHS.priorities_csv,
        PATHS.baseline_routes_json,
        PATHS.baseline_metrics_json,
        PATHS.baseline_metrics_enriched_json,
        PATHS.quantum_routes_json,
        PATHS.quantum_metrics_json,
        PATHS.quantum_metrics_enriched_json,
        PATHS.routes_for_frontend_json,
        PATHS.closures_json,
        PATHS.trucks_json,
        # Figures
        PATHS.fig_routes_compare,
        PATHS.fig_tier_coverage,
        PATHS.fig_workload_balance,
        PATHS.fig_workload,
        PATHS.fig_distance_and_served,
        PATHS.fig_efficiency_vs_safety,
        PATHS.fig_kpi_summary,
    ]

    copied = 0
    for src in files_to_copy:
        if src.exists():
            dst = FRONTEND_DATA_DIR / src.name
            shutil.copy2(src, dst)
            copied += 1

    # Copy logo
    if PATHS.logo_png.exists():
        shutil.copy2(PATHS.logo_png, FRONTEND_LOGO_DIR / "RASD.png")
        copied += 1

    print(f"✅ Copied {copied} files to frontend")


if __name__ == "__main__":
    build_routes_for_frontend()
    copy_to_frontend()
