"""
Priority visualization module for RASD.

Generates bar charts showing tank priority scores with tier coloring.
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from rasd_ai.config.paths import PATHS

# Configuration constants
MODE = "STRATIFIED"
TOP_HIGH = 8
TOP_MED = 4
TOP_LOW = 4

HIGH_THR = 0.75
MED_THR = 0.45


def compute_tier(priority: float) -> str:
    """
    Compute tier based on priority score.

    Args:
        priority: Priority score between 0 and 1.

    Returns:
        str: Tier classification (HIGH, MEDIUM, or LOW).
    """
    if priority >= HIGH_THR:
        return "HIGH"
    if priority >= MED_THR:
        return "MEDIUM"
    return "LOW"


def main() -> None:
    """Generate priority visualization chart."""
    data_frame = pd.read_csv(PATHS.priorities_csv)

    data_frame["tier_calc"] = data_frame["priority"].apply(compute_tier)

    data_frame["tto_label"] = data_frame["tto_hours"].apply(
        lambda x: "∞" if x >= 900 else f"{int(round(x))}h"
    )

    if MODE == "ALL":
        plot_df = data_frame.copy()
    else:
        # Stratified: take best from each tier
        high_df = (
            data_frame[data_frame["tier_calc"] == "HIGH"]
            .sort_values("priority", ascending=False)
            .head(TOP_HIGH)
        )
        med_df = (
            data_frame[data_frame["tier_calc"] == "MEDIUM"]
            .sort_values("priority", ascending=False)
            .head(TOP_MED)
        )
        low_df = (
            data_frame[data_frame["tier_calc"] == "LOW"]
            .sort_values("priority", ascending=False)
            .head(TOP_LOW)
        )
        plot_df = pd.concat([high_df, med_df, low_df], ignore_index=True)

    plot_df = plot_df.sort_values("priority", ascending=True).copy()
    plot_df["tank_id"] = plot_df["tank_id"].astype(str)

    colors = {"HIGH": "#ff3b3b", "MEDIUM": "#ffd43b", "LOW": "#2bff88"}
    plot_df["color"] = plot_df["tier_calc"].map(colors)

    # Create figure with white background
    fig = plt.figure(figsize=(14, 6), dpi=160)
    axes = plt.gca()
    fig.patch.set_facecolor("#ffffff")
    axes.set_facecolor("#ffffff")

    bars = axes.barh(plot_df["tank_id"], plot_df["priority"], color=plot_df["color"], alpha=0.92)

    # Add threshold lines
    axes.axvline(MED_THR, linestyle="--", linewidth=1.6, alpha=0.7, color="black")
    axes.axvline(HIGH_THR, linestyle="--", linewidth=1.6, alpha=0.7, color="black")

    axes.text(MED_THR + 0.01, 0.2, "MEDIUM", fontsize=10, alpha=0.85, color="black")
    axes.text(HIGH_THR + 0.01, 0.2, "HIGH", fontsize=10, alpha=0.85, color="black")

    # Add labels: Priority + TTO + gas_now
    for bar, priority, tto, gas in zip(
        bars, plot_df["priority"], plot_df["tto_label"], plot_df["gas_now"]
    ):
        axes.text(
            priority + 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"{priority:.2f}  |  TTO: {tto}  |  Gas: {gas:.0f}",
            va="center",
            fontsize=9.5,
            alpha=0.95,
            color="black",
        )

    axes.set_xlim(0, 1.05)
    axes.set_title("Risk-Based Priority (AI + Sensor Fusion)", fontsize=18, pad=14, color="black")
    axes.set_xlabel("Priority Score (0 → 1)", fontsize=12, color="black")
    axes.grid(axis="x", linestyle=":", alpha=0.18, color="black")
    axes.tick_params(axis="y", labelsize=11, colors="black")
    axes.tick_params(axis="x", labelsize=10, colors="black")

    for spine in axes.spines.values():
        spine.set_color("black")
        spine.set_alpha(0.15)

    # Add legend
    legend_handles = [
        Patch(facecolor=colors["HIGH"], label="HIGH"),
        Patch(facecolor=colors["MEDIUM"], label="MEDIUM"),
        Patch(facecolor=colors["LOW"], label="LOW"),
    ]
    leg = axes.legend(handles=legend_handles, loc="lower right", frameon=False)
    for text in leg.get_texts():
        text.set_color("black")

    plt.tight_layout()

    # Save outputs
    out_white = PATHS.outputs / "priority_scores_WOW_whitebg.png"
    out_trans = PATHS.outputs / "priority_scores_WOW_transparent.png"
    plt.savefig(out_white, dpi=220, transparent=False)
    plt.savefig(out_trans, dpi=220, transparent=True)

    print(f"✅ saved {out_white}")
    print(f"✅ saved {out_trans}")
    plt.show()


if __name__ == "__main__":
    main()
