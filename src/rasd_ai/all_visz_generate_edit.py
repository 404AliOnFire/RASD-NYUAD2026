import os, json, math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =========================
# SETTINGS (demo-friendly)
# =========================
OUTDIR = "outputs"
LABEL_PITS_ON_MAP = 10      # keep map clean
FUEL_L_PER_KM = 0.35        # demo estimate
CO2_KG_PER_L = 2.68         # demo estimate


# =========================
# IO Helpers
# =========================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# =========================
# Geo Helpers
# =========================
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def build_coord_map(nodes_list):
    # nodes.json should be list of dicts: {node_id, lat, lon, zone?}
    coords = {}
    for r in nodes_list:
        nid = r["node_id"]
        coords[nid] = (float(r["lat"]), float(r["lon"]))
    return coords


# =========================
# Routing Helpers
# =========================
def nearest_neighbor_sequence(pits, coords, start="depot"):
    remaining = set(pits)
    seq = [start]
    cur = start
    while remaining:
        clat, clon = coords[cur]
        best, best_d = None, 1e18
        for p in remaining:
            lat, lon = coords[p]
            d = haversine_km(clat, clon, lat, lon)
            if d < best_d:
                best, best_d = p, d
        seq.append(best)
        remaining.remove(best)
        cur = best
    seq.append(start)
    return seq

def route_distance_km(seq, coords):
    total = 0.0
    for a, b in zip(seq, seq[1:]):
        lat1, lon1 = coords[a]
        lat2, lon2 = coords[b]
        total += haversine_km(lat1, lon1, lat2, lon2)
    return total


# =========================
# Tier + styling
# =========================
def tier_color(t):
    t = str(t).upper()
    if t == "HIGH": return "#e74c3c"
    if t == "MEDIUM": return "#f1c40f"
    return "#2ecc71"

def clean_save(fig, outpath):
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    fig.savefig(outpath, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("✅ saved", outpath)


# =========================
# Build sequences
# =========================
def build_baseline_sequences(baseline_routes):
    # expects: {truck_id: {"sequence": ["depot", 1,2,...,"depot"]}}
    seqs = {}
    for tid, info in baseline_routes.items():
        seqs[tid] = info["sequence"]
    return seqs

def build_quantum_sequences(quantum_routes, coords):
    # expects assignment only: {truck_id: {"assigned_pits":[...]}}
    seqs = {}
    for tid, info in quantum_routes.items():
        pits = info.get("assigned_pits", [])
        if pits:
            seqs[tid] = nearest_neighbor_sequence(pits, coords, start="depot")
    return seqs


# =========================
# Metrics (distance + tier coverage + workload)
# =========================
def compute_metrics(seqs, tier_map, coords):
    served = set()
    dist_by_truck = {}
    stops_by_truck = {}

    for tid, seq in seqs.items():
        pits = [n for n in seq if n != "depot"]
        served.update(pits)
        stops_by_truck[tid] = len(pits)
        dist_by_truck[tid] = route_distance_km(seq, coords)

    # tier totals are from tier_map keys
    all_pits = set(tier_map.keys())
    served_total = len(served)
    missed_total = len(all_pits - served)

    def tier_counts(label):
        ids = {pid for pid, t in tier_map.items() if t == label}
        return len(ids), len(ids & served), len(ids - served)

    high_total, high_served, high_missed = tier_counts("HIGH")
    med_total, med_served, med_missed = tier_counts("MEDIUM")
    low_total, low_served, low_missed = tier_counts("LOW")

    total_km = float(sum(dist_by_truck.values()))
    fuel_l = total_km * FUEL_L_PER_KM
    co2_kg = fuel_l * CO2_KG_PER_L

    return {
        "served_total": served_total,
        "missed_total": missed_total,
        "high_total": high_total, "high_served": high_served, "high_missed": high_missed,
        "medium_total": med_total, "medium_served": med_served, "medium_missed": med_missed,
        "low_total": low_total, "low_served": low_served, "low_missed": low_missed,
        "total_distance_km": round(total_km, 2),
        "fuel_l_est": round(fuel_l, 2),
        "co2_kg_est": round(co2_kg, 2),
        "distance_by_truck_km": {k: round(float(v), 2) for k, v in dist_by_truck.items()},
        "stops_by_truck": stops_by_truck
    }


# =========================
# FIG 1: Map routes compare
# =========================
def fig_routes_compare(baseline_seqs, quantum_seqs, coords, tier_map):
    fig = plt.figure(figsize=(14, 6))
    ax1 = fig.add_subplot(1,2,1)
    ax2 = fig.add_subplot(1,2,2)

    def plot(ax, seqs, title):
        # routes lines
        for tid, seq in seqs.items():
            xs, ys = [], []
            for n in seq:
                lat, lon = coords[n]
                xs.append(lon); ys.append(lat)
            ax.plot(xs, ys, linewidth=2)

        # nodes scatter
        for nid, (lat, lon) in coords.items():
            if nid == "depot":
                ax.scatter([lon], [lat], s=90)
                ax.annotate("depot", (lon, lat), xytext=(5,5),
                            textcoords="offset points", fontsize=10)
            else:
                ax.scatter([lon], [lat], s=35, c=tier_color(tier_map.get(int(nid), "LOW")))

        # labels (limited)
        pit_ids = list(tier_map.keys())[:LABEL_PITS_ON_MAP]
        for pid in pit_ids:
            lat, lon = coords[pid]
            ax.annotate(str(pid), (lon, lat), xytext=(4,4),
                        textcoords="offset points", fontsize=9)

        ax.set_title(title, fontsize=13, weight="bold")
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        ax.grid(True, alpha=0.25)

    plot(ax1, baseline_seqs, "Baseline (Classical)")
    plot(ax2, quantum_seqs, "Quantum (Annealing Simulation)")
    fig.suptitle("Routes Comparison", fontsize=16, weight="bold")
    return fig


# =========================
# FIG 2: Distance + Served (more interesting than High-only 100%)
# =========================
def fig_distance_and_served(base_m, q_m):
    fig = plt.figure(figsize=(12, 5))
    ax1 = fig.add_subplot(1,2,1)
    ax2 = fig.add_subplot(1,2,2)

    labels = ["Baseline", "Quantum"]

    # distance
    dist = [base_m["total_distance_km"], q_m["total_distance_km"]]
    ax1.bar(labels, dist)
    ax1.set_title("Operational Efficiency\n(Total Distance)", weight="bold")
    ax1.set_ylabel("Distance (km)")
    ax1.grid(axis="y", alpha=0.3)
    for i, v in enumerate(dist):
        ax1.text(i, v*1.03, f"{v:.1f} km", ha="center", fontsize=10)

    # served count
    served = [base_m["served_total"], q_m["served_total"]]
    ax2.bar(labels, served)
    ax2.set_title("Dispatch Output\n(Served Pits)", weight="bold")
    ax2.set_ylabel("Count")
    ax2.grid(axis="y", alpha=0.3)
    for i, v in enumerate(served):
        ax2.text(i, v + 0.3, f"{int(v)} served", ha="center", fontsize=10)

    fig.suptitle("Classical vs Quantum-Inspired Optimization", fontsize=16, weight="bold")
    return fig


# =========================
# FIG 3: Tier Coverage (THIS is the exciting one)
# shows Safety-first behavior (Quantum serves HIGH, baseline may spread)
# =========================
def fig_tier_coverage(base_m, q_m):
    tiers = ["HIGH", "MEDIUM", "LOW"]

    def cov(m, t):
        tot = m[f"{t.lower()}_total"]
        srv = m[f"{t.lower()}_served"]
        return 0 if tot == 0 else srv / tot * 100

    base_cov = [cov(base_m, t) for t in tiers]
    q_cov    = [cov(q_m, t) for t in tiers]

    fig = plt.figure(figsize=(12, 4.2))
    ax = fig.add_subplot(1,1,1)

    x = np.arange(len(tiers))
    w = 0.35
    ax.bar(x - w/2, base_cov, w, label="Baseline")
    ax.bar(x + w/2, q_cov, w, label="Quantum")

    ax.set_xticks(x); ax.set_xticklabels(tiers)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Coverage (%)")
    ax.set_title("Coverage by Risk Tier (Safety-First vs General)", weight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.legend()

    for i, v in enumerate(base_cov):
        ax.text(i - w/2, v + 2, f"{v:.0f}%", ha="center", fontsize=10)
    for i, v in enumerate(q_cov):
        ax.text(i + w/2, v + 2, f"{v:.0f}%", ha="center", fontsize=10)

    return fig


# =========================
# FIG 4: Workload distribution (filter empty trucks!)
# =========================
def fig_workload(base_m, q_m):
    b = dict(base_m["stops_by_truck"])
    q = dict(q_m["stops_by_truck"])

    # FILTER trucks with 0 stops (fix your truck_4 issue)
    b = {k:v for k,v in b.items() if v > 0}
    q = {k:v for k,v in q.items() if v > 0}

    fig = plt.figure(figsize=(12, 4.5))
    ax1 = fig.add_subplot(1,2,1)
    ax2 = fig.add_subplot(1,2,2)

    ax1.bar(list(b.keys()), list(b.values()))
    ax1.set_title("Baseline Workload\n(Stops per Truck)", weight="bold")
    ax1.set_ylabel("Stops")
    ax1.grid(axis="y", alpha=0.3)
    ax1.tick_params(axis="x", rotation=25)

    ax2.bar(list(q.keys()), list(q.values()))
    ax2.set_title("Quantum Workload\n(Stops per Truck)", weight="bold")
    ax2.set_ylabel("Stops")
    ax2.grid(axis="y", alpha=0.3)
    ax2.tick_params(axis="x", rotation=25)

    fig.suptitle("Workload Distribution (Empty Trucks Hidden)", fontsize=16, weight="bold")
    return fig


# =========================
# MAIN
# =========================
def main():
    os.makedirs(OUTDIR, exist_ok=True)

    nodes = load_json(os.path.join(OUTDIR, "nodes.json"))
    coords = build_coord_map(nodes)

    priorities = pd.read_csv(os.path.join(OUTDIR, "priorities.csv"))
    tier_map = {int(r["tank_id"]): str(r["tier"]).upper() for _, r in priorities.iterrows()}

    baseline_routes = load_json(os.path.join(OUTDIR, "baseline_routes.json"))
    quantum_routes  = load_json(os.path.join(OUTDIR, "quantum_routes.json"))

    baseline_seqs = build_baseline_sequences(baseline_routes)
    quantum_seqs  = build_quantum_sequences(quantum_routes, coords)

    base_m = compute_metrics(baseline_seqs, tier_map, coords)
    q_m    = compute_metrics(quantum_seqs, tier_map, coords)

    save_json(os.path.join(OUTDIR, "baseline_metrics_enriched.json"), base_m)
    save_json(os.path.join(OUTDIR, "quantum_metrics_enriched.json"), q_m)
    print("✅ saved baseline_metrics_enriched.json")
    print("✅ saved quantum_metrics_enriched.json")

    # figures
    f1 = fig_routes_compare(baseline_seqs, quantum_seqs, coords, tier_map)
    clean_save(f1, os.path.join(OUTDIR, "fig_routes_compare.png"))

    f2 = fig_distance_and_served(base_m, q_m)
    clean_save(f2, os.path.join(OUTDIR, "fig_distance_and_served.png"))

    f3 = fig_tier_coverage(base_m, q_m)
    clean_save(f3, os.path.join(OUTDIR, "fig_tier_coverage.png"))

    f4 = fig_workload(base_m, q_m)
    clean_save(f4, os.path.join(OUTDIR, "fig_workload.png"))

    print("\n✅ DONE. Use these in slides:")
    print(" - outputs/fig_routes_compare.png")
    print(" - outputs/fig_distance_and_served.png")
    print(" - outputs/fig_tier_coverage.png")
    print(" - outputs/fig_workload.png")


if __name__ == "__main__":
    main()
