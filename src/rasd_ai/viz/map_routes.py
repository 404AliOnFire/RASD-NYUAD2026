"""
Route comparison map visualization.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional

import matplotlib.pyplot as plt

from rasd_ai.config.paths import PATHS
from rasd_ai.data.loaders import load_json, load_csv, save_json
from rasd_ai.optimization.metrics import (
    nearest_neighbor_sequence,
    build_coord_map,
    compute_route_metrics,
)


def tier_color(tier: str) -> str:
    """Get color for tier."""
    t = str(tier).upper()
    if t == "HIGH":
        return "#e74c3c"
    if t == "MEDIUM":
        return "#f1c40f"
    return "#2ecc71"


def clean_save(fig, outpath: Path):
    """Save figure with white background."""
    fig.patch.set_facecolor("white")
    plt.tight_layout()
    fig.savefig(outpath, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"✅ saved {outpath}")


def build_baseline_sequences(baseline_routes: dict) -> Dict[str, List[Any]]:
    """Extract sequences from baseline routes."""
    seqs = {}
    for tid, info in baseline_routes.items():
        if "sequence" in info:
            seqs[tid] = info["sequence"]
    return seqs


def build_quantum_sequences(quantum_routes: dict, coords: Dict[Any, tuple]) -> Dict[str, List[Any]]:
    """Build sequences for quantum routes using nearest neighbor."""
    seqs = {}
    for tid, info in quantum_routes.items():
        pits = info.get("assigned_pits", [])
        if pits:
            seqs[tid] = nearest_neighbor_sequence(pits, coords, start="depot")
    return seqs


def plot_routes_compare(
    baseline_seqs: Dict[str, List[Any]],
    quantum_seqs: Dict[str, List[Any]],
    coords: Dict[Any, tuple],
    tier_map: Dict[int, str],
    output_path: Optional[Path] = None,
    label_count: int = 10,
):
    """
    Plot side-by-side comparison of baseline and quantum routes.

    Args:
        baseline_seqs: Dict of truck_id to route sequence for baseline
        quantum_seqs: Dict of truck_id to route sequence for quantum
        coords: Dict mapping node_id to (lat, lon)
        tier_map: Dict mapping pit_id to tier
        output_path: Output file path
        label_count: Number of pit labels to show
    """
    if output_path is None:
        output_path = PATHS.fig_routes_compare

    fig = plt.figure(figsize=(14, 6))
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2)

    def plot_on_ax(ax, seqs, title):
        # Plot routes
        for _tid, seq in seqs.items():
            xs, ys = [], []
            for n in seq:
                if n not in coords:
                    continue
                lat, lon = coords[n]
                xs.append(lon)
                ys.append(lat)
            if xs:
                ax.plot(xs, ys, linewidth=2)

        # Plot nodes
        for nid, (lat, lon) in coords.items():
            if nid == "depot":
                ax.scatter([lon], [lat], s=90, c="purple", marker="s", zorder=10)
                ax.annotate(
                    "depot",
                    (lon, lat),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=10,
                )
            else:
                color = tier_color(
                    tier_map.get(int(nid) if isinstance(nid, (int, str)) else nid, "LOW")
                )
                ax.scatter([lon], [lat], s=35, c=color)

        # Add labels for top pits
        pit_ids = list(tier_map.keys())[:label_count]
        for pid in pit_ids:
            if pid in coords:
                lat, lon = coords[pid]
                ax.annotate(
                    str(pid),
                    (lon, lat),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=9,
                )

        ax.set_title(title, fontsize=13, weight="bold")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True, alpha=0.25)

    plot_on_ax(ax1, baseline_seqs, "Baseline (Classical)")
    plot_on_ax(ax2, quantum_seqs, "Quantum (Annealing Simulation)")
    fig.suptitle("Routes Comparison", fontsize=16, weight="bold")

    clean_save(fig, output_path)


def generate_route_comparison():
    """Generate route comparison visualization from saved data."""
    print("\n🗺️ Generating route comparison...")

    # Load data
    nodes = load_json(PATHS.nodes_json)
    priorities = load_csv(PATHS.priorities_csv)
    baseline_routes = load_json(PATHS.baseline_routes_json)
    quantum_routes = load_json(PATHS.quantum_routes_json)

    # Build mappings
    coords = build_coord_map(nodes)
    tier_map = dict(zip(priorities["tank_id"].astype(int), priorities["tier"]))

    # Build sequences
    baseline_seqs = build_baseline_sequences(baseline_routes)
    quantum_seqs = build_quantum_sequences(quantum_routes, coords)

    # Generate plot
    plot_routes_compare(baseline_seqs, quantum_seqs, coords, tier_map)

    # Compute and save enriched metrics
    baseline_metrics = compute_route_metrics(baseline_seqs, tier_map, coords)
    quantum_metrics = compute_route_metrics(quantum_seqs, tier_map, coords)

    save_json(PATHS.baseline_metrics_enriched_json, baseline_metrics)
    save_json(PATHS.quantum_metrics_enriched_json, quantum_metrics)

    print(f"✅ saved {PATHS.baseline_metrics_enriched_json}")
    print(f"✅ saved {PATHS.quantum_metrics_enriched_json}")


if __name__ == "__main__":
    generate_route_comparison()
