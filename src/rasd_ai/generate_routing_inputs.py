import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


TOP_N = 30
N_TRUCKS = 4
SHIFT_MIN = 480

HEBRON_BBOX = {
    "lat_min": 31.505,  # south
    "lat_max": 31.555,  # north
    "lon_min": 35.070,  # west
    "lon_max": 35.120,  # east
}

# Zone definitions (simple demo)
# - center: more congestion + more narrow streets
# - ring: medium congestion
# - outer: low congestion
ZONES = ["center", "ring", "outer"]

# Congestion multipliers by zone
CONGESTION = {
    "center": 1.5,
    "ring": 1.2,
    "outer": 1.0,
}

# Share of points by zone (sum ~ 1)
ZONE_SHARE = {
    "center": 0.45,
    "ring": 0.40,
    "outer": 0.15,
}

# Narrow streets probability by zone
NARROW_PROB = {
    "center": 0.40,
    "ring": 0.15,
    "outer": 0.05,
}

# Road closures: fraction of edges to mark as "closed"
CLOSURE_FRACTION = 0.03

# Speed km/h used for base travel time estimation
BASE_SPEED_KMH = 25.0

# Deadline safety margin (minutes) subtracted from TTO-derived deadline
SAFETY_MARGIN_MIN = 90


# -----------------------------
# Helpers
# -----------------------------
def weighted_choice(rng: random.Random, weights_dict):
    r = rng.random()
    cum = 0.0
    for k, w in weights_dict.items():
        cum += w
        if r <= cum:
            return k
    # fallback
    return list(weights_dict.keys())[-1]


def uniform_in_bbox(rng: random.Random, bbox):
    lat = rng.uniform(bbox["lat_min"], bbox["lat_max"])
    lon = rng.uniform(bbox["lon_min"], bbox["lon_max"])
    return lat, lon


def haversine_km(lat1, lon1, lat2, lon2):
    # Earth radius (km)
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def compute_demand_and_service(tier: str):
    # simple, hackathon-friendly
    # demand units can be "volume units" (not liters) for capacity constraint
    if tier == "HIGH":
        return 3, 18
    if tier == "MEDIUM":
        return 2, 12
    return 1, 7  # LOW


def tto_to_deadline_min(tto_hours: float):
    # Soft-deadline: clamp within [60, 24h] and subtract safety margin
    if tto_hours is None or tto_hours >= 900:
        # far away; give loose deadline
        return 24 * 60

    raw = int(max(60, min(24 * 60, tto_hours * 60)))
    deadline = max(60, raw - SAFETY_MARGIN_MIN)
    return int(deadline)


def ensure_outputs_dir():
    outdir = Path("outputs")
    outdir.mkdir(exist_ok=True)
    return outdir


# -----------------------------
# Main generator
# -----------------------------
def main():
    outdir = ensure_outputs_dir()

    # 1) Load priorities
    priorities_path = outdir / "priorities.csv"
    if not priorities_path.exists():
        raise FileNotFoundError(f"Missing {priorities_path}. Run run_pipeline.py first.")

    df = pd.read_csv(priorities_path)
    if "priority" not in df.columns:
        raise ValueError("priorities.csv missing 'priority' column")

    # 2) Select Top-N
    df_top = df.sort_values("priority", ascending=False).head(TOP_N).copy()

    # 3) Generate demo depot (truck base) near center of bbox
    depot_lat = (HEBRON_BBOX["lat_min"] + HEBRON_BBOX["lat_max"]) / 2
    depot_lon = (HEBRON_BBOX["lon_min"] + HEBRON_BBOX["lon_max"]) / 2

    rng = random.Random(7)

    # 4) Add routing fields
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

        lat, lon = uniform_in_bbox(rng, HEBRON_BBOX)
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

    # 5) Save routing pits
    routing_path = outdir / "routing_pits.csv"
    df_top.to_csv(routing_path, index=False)

    # 6) Define trucks (capacities in same units as demand)
    # Keep it realistic: small/medium/large mix
    trucks = [
        {"truck_id": 1, "capacity": 18, "shift_min": SHIFT_MIN, "type": "small"},
        {"truck_id": 2, "capacity": 22, "shift_min": SHIFT_MIN, "type": "medium"},
        {"truck_id": 3, "capacity": 26, "shift_min": SHIFT_MIN, "type": "large"},
        {"truck_id": 4, "capacity": 22, "shift_min": SHIFT_MIN, "type": "medium"},
    ]
    trucks_path = outdir / "trucks.json"
    trucks_path.write_text(json.dumps(trucks, indent=2), encoding="utf-8")

    # 7) Build travel time matrix (minutes)
    # Nodes = depot + TOP_N pits
    nodes = [{"node_id": "depot", "lat": depot_lat, "lon": depot_lon, "zone": "center"}]
    for _, r in df_top.iterrows():
        nodes.append({"node_id": int(r["tank_id"]), "lat": float(r["lat"]), "lon": float(r["lon"]), "zone": str(r["zone"])})

    n = len(nodes)
    T = np.zeros((n, n), dtype=np.float32)

    # Base travel time with zone congestion multiplier (destination zone)
    for i in range(n):
        for j in range(n):
            if i == j:
                T[i, j] = 0.0
                continue
            d_km = haversine_km(nodes[i]["lat"], nodes[i]["lon"], nodes[j]["lat"], nodes[j]["lon"])
            base_min = (d_km / BASE_SPEED_KMH) * 60.0
            mult = CONGESTION.get(nodes[j]["zone"], 1.0)
            T[i, j] = float(base_min * mult)

    # 8) Inject road closures (random edges)
    # Mark a small fraction of edges as "closed" by setting huge time
    closed_edges = []
    total_edges = n * (n - 1)
    k_close = max(1, int(total_edges * CLOSURE_FRACTION))
    candidates = [(i, j) for i in range(n) for j in range(n) if i != j]
    rng.shuffle(candidates)

    for (i, j) in candidates[:k_close]:
        T[i, j] = 1e6  # effectively forbidden
        closed_edges.append({"from": nodes[i]["node_id"], "to": nodes[j]["node_id"]})

    matrix_path = outdir / "travel_time_matrix.npy"
    np.save(matrix_path, T)

    closures_path = outdir / "closures.json"
    closures_path.write_text(json.dumps(closed_edges, indent=2), encoding="utf-8")

    # 9) Save nodes list for frontend
    nodes_path = outdir / "nodes.json"
    nodes_path.write_text(json.dumps(nodes, indent=2), encoding="utf-8")

    print(" Generated routing inputs:")
    print(f" - {routing_path}")
    print(f" - {trucks_path}")
    print(f" - {nodes_path}")
    print(f" - {matrix_path}")
    print(f" - {closures_path}")
    print("\nNext: baseline routes + quantum optimizer can consume these files.")


if __name__ == "__main__":
    main()
