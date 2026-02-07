"""
Generate routing inputs from priorities data.
"""

import math
import random
from typing import Dict

import numpy as np

from rasd_ai.config.paths import PATHS
from rasd_ai.config.settings import SETTINGS
from rasd_ai.data.loaders import load_csv, save_json, save_numpy

# Zone configurations
ZONES = ["center", "ring", "outer"]
CONGESTION = {"center": 1.5, "ring": 1.2, "outer": 1.0}
ZONE_SHARE = {"center": 0.45, "ring": 0.40, "outer": 0.15}
NARROW_PROB = {"center": 0.40, "ring": 0.15, "outer": 0.05}


def weighted_choice(rng: random.Random, weights_dict: Dict[str, float]) -> str:
    """Choose randomly based on weights."""
    r = rng.random()
    cum = 0.0
    for k, w in weights_dict.items():
        cum += w
        if r <= cum:
            return k
    return list(weights_dict.keys())[-1]


def uniform_in_bbox(rng: random.Random) -> tuple:
    """Generate random coordinates within Hebron bounding box."""
    lat = rng.uniform(SETTINGS.HEBRON_LAT_MIN, SETTINGS.HEBRON_LAT_MAX)
    lon = rng.uniform(SETTINGS.HEBRON_LON_MIN, SETTINGS.HEBRON_LON_MAX)
    return lat, lon


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance in km."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def compute_demand_and_service(tier: str) -> tuple:
    """Get demand units and service time for a tier."""
    if tier == "HIGH":
        return 3, 18
    if tier == "MEDIUM":
        return 2, 12
    return 1, 7


def tto_to_deadline_min(tto_hours: float) -> int:
    """Convert TTO hours to deadline minutes."""
    if tto_hours is None or tto_hours >= 900:
        return 24 * 60

    raw = int(max(60, min(24 * 60, tto_hours * 60)))
    deadline = max(60, raw - SETTINGS.SAFETY_MARGIN_MIN)
    return int(deadline)


def generate_routing_inputs():
    """Generate all routing input files."""
    PATHS.outputs.mkdir(parents=True, exist_ok=True)

    # Load priorities
    df = load_csv(PATHS.priorities_csv)
    if "priority" not in df.columns:
        raise ValueError("priorities.csv missing 'priority' column")

    # Select Top-N
    df_top = df.sort_values("priority", ascending=False).head(SETTINGS.TOP_N_PITS).copy()

    # Generate depot location
    depot_lat = (SETTINGS.HEBRON_LAT_MIN + SETTINGS.HEBRON_LAT_MAX) / 2
    depot_lon = (SETTINGS.HEBRON_LON_MIN + SETTINGS.HEBRON_LON_MAX) / 2

    rng = random.Random(SETTINGS.DEFAULT_SEED)

    # Add routing fields
    zones = []
    narrow_flags = []
    lats = []
    lons = []
    demands = []
    service_mins = []
    deadline_mins = []

    for _, row in df_top.iterrows():
        z = weighted_choice(rng, ZONE_SHARE)
        is_narrow = 1 if rng.random() < NARROW_PROB[z] else 0

        lat, lon = uniform_in_bbox(rng)
        demand, service_min = compute_demand_and_service(str(row.get("tier", "LOW")))
        deadline_min = tto_to_deadline_min(float(row.get("tto_hours", 999)))

        zones.append(z)
        narrow_flags.append(is_narrow)
        lats.append(lat)
        lons.append(lon)
        demands.append(demand)
        service_mins.append(service_min)
        deadline_mins.append(deadline_min)

    df_top["lat"] = lats
    df_top["lon"] = lons
    df_top["zone"] = zones
    df_top["is_narrow"] = narrow_flags
    df_top["demand"] = demands
    df_top["service_min"] = service_mins
    df_top["deadline_min"] = deadline_mins

    # Save routing pits
    df_top.to_csv(PATHS.routing_pits_csv, index=False)

    # Define trucks
    trucks = [
        {
            "truck_id": 1,
            "capacity": 18,
            "shift_min": SETTINGS.SHIFT_DURATION_MIN,
            "type": "small",
        },
        {
            "truck_id": 2,
            "capacity": 22,
            "shift_min": SETTINGS.SHIFT_DURATION_MIN,
            "type": "medium",
        },
        {
            "truck_id": 3,
            "capacity": 26,
            "shift_min": SETTINGS.SHIFT_DURATION_MIN,
            "type": "large",
        },
        {
            "truck_id": 4,
            "capacity": 22,
            "shift_min": SETTINGS.SHIFT_DURATION_MIN,
            "type": "medium",
        },
    ]
    save_json(PATHS.trucks_json, trucks)

    # Build nodes list
    nodes = [{"node_id": "depot", "lat": depot_lat, "lon": depot_lon, "zone": "center"}]
    for _, r in df_top.iterrows():
        nodes.append(
            {
                "node_id": int(r["tank_id"]),
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "zone": str(r["zone"]),
            }
        )

    # Build travel time matrix
    n = len(nodes)
    T = np.zeros((n, n), dtype=np.float32)

    for i in range(n):
        for j in range(n):
            if i == j:
                T[i, j] = 0.0
                continue
            d_km = haversine_km(nodes[i]["lat"], nodes[i]["lon"], nodes[j]["lat"], nodes[j]["lon"])
            base_min = (d_km / SETTINGS.BASE_SPEED_KMH) * 60.0
            mult = CONGESTION.get(nodes[j]["zone"], 1.0)
            T[i, j] = float(base_min * mult)

    # Inject road closures
    closed_edges = []
    total_edges = n * (n - 1)
    k_close = max(1, int(total_edges * SETTINGS.CLOSURE_FRACTION))
    candidates = [(i, j) for i in range(n) for j in range(n) if i != j]
    rng.shuffle(candidates)

    for i, j in candidates[:k_close]:
        T[i, j] = 1e6
        closed_edges.append({"from": nodes[i]["node_id"], "to": nodes[j]["node_id"]})

    save_numpy(PATHS.travel_time_matrix_npy, T)
    save_json(PATHS.closures_json, closed_edges)
    save_json(PATHS.nodes_json, nodes)

    print("✅ Generated routing inputs:")
    print(f"   - {PATHS.routing_pits_csv}")
    print(f"   - {PATHS.trucks_json}")
    print(f"   - {PATHS.nodes_json}")
    print(f"   - {PATHS.travel_time_matrix_npy}")
    print(f"   - {PATHS.closures_json}")


def main():
    """Entry point for routing input generation."""
    generate_routing_inputs()


if __name__ == "__main__":
    main()
