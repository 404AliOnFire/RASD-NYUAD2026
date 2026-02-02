# python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

CSV_PATH = "outputs/priorities.csv"


MODE = "STRATIFIED"
TOP_HIGH = 8
TOP_MED  = 4
TOP_LOW  = 4

HIGH_THR = 0.75
MED_THR  = 0.45

def compute_tier(p):
    if p >= HIGH_THR:
        return "HIGH"
    elif p >= MED_THR:
        return "MEDIUM"
    else:
        return "LOW"

def main():
    df = pd.read_csv(CSV_PATH)

    df["tier_calc"] = df["priority"].apply(compute_tier)

    df["tto_label"] = df["tto_hours"].apply(lambda x: "∞" if x >= 900 else f"{int(round(x))}h")

    if MODE == "ALL":
        plot_df = df.copy()
    else:
        # Stratified: خذ أفضل من كل Tier عشان دايمًا يظهروا الثلاثة
        high_df = df[df["tier_calc"] == "HIGH"].sort_values("priority", ascending=False).head(TOP_HIGH)
        med_df  = df[df["tier_calc"] == "MEDIUM"].sort_values("priority", ascending=False).head(TOP_MED)
        low_df  = df[df["tier_calc"] == "LOW"].sort_values("priority", ascending=False).head(TOP_LOW)
        plot_df = pd.concat([high_df, med_df, low_df], ignore_index=True)

    plot_df = plot_df.sort_values("priority", ascending=True).copy()
    plot_df["tank_id"] = plot_df["tank_id"].astype(str)

    colors = {"HIGH": "#ff3b3b", "MEDIUM": "#ffd43b", "LOW": "#2bff88"}
    plot_df["color"] = plot_df["tier_calc"].map(colors)

    # ---  (white background) ---
    fig = plt.figure(figsize=(14, 6), dpi=160)
    ax = plt.gca()
    fig.patch.set_facecolor("#ffffff")  # white figure background
    ax.set_facecolor("#ffffff")         # white axes background

    bars = ax.barh(plot_df["tank_id"], plot_df["priority"], color=plot_df["color"], alpha=0.92)

    # thresholds
    ax.axvline(MED_THR, linestyle="--", linewidth=1.6, alpha=0.7, color="black")
    ax.axvline(HIGH_THR, linestyle="--", linewidth=1.6, alpha=0.7, color="black")

    ax.text(MED_THR + 0.01, 0.2, "MEDIUM", fontsize=10, alpha=0.85, color="black")
    ax.text(HIGH_THR + 0.01, 0.2, "HIGH", fontsize=10, alpha=0.85, color="black")

    # labels: Priority + TTO + gas_now
    for b, pr, tto, gas in zip(bars, plot_df["priority"], plot_df["tto_label"], plot_df["gas_now"]):
        ax.text(
            pr + 0.012,
            b.get_y() + b.get_height()/2,
            f"{pr:.2f}  |  TTO: {tto}  |  Gas: {gas:.0f}",
            va="center",
            fontsize=9.5,
            alpha=0.95,
            color="black"
        )

    ax.set_xlim(0, 1.05)
    ax.set_title("Risk-Based Priority (AI + Sensor Fusion)", fontsize=18, pad=14, color="black")
    ax.set_xlabel("Priority Score (0 → 1)", fontsize=12, color="black")
    ax.grid(axis="x", linestyle=":", alpha=0.18, color="black")
    ax.tick_params(axis="y", labelsize=11, colors="black")
    ax.tick_params(axis="x", labelsize=10, colors="black")

    for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_alpha(0.15)

    # legend
    legend_handles = [
        Patch(facecolor=colors["HIGH"], label="HIGH"),
        Patch(facecolor=colors["MEDIUM"], label="MEDIUM"),
        Patch(facecolor=colors["LOW"], label="LOW"),
    ]
    leg = ax.legend(handles=legend_handles, loc="lower right", frameon=False)
    for t in leg.get_texts():
        t.set_color("black")

    plt.tight_layout()

    #  white background PNG and optional transparent version
    out_white = "outputs/priority_scores_WOW_whitebg.png"
    out_trans = "outputs/priority_scores_WOW_transparent.png"
    plt.savefig(out_white, dpi=220, transparent=False)
    plt.savefig(out_trans, dpi=220, transparent=True)

    print(f"✅ saved {out_white}")
    print(f"✅ saved {out_trans}")
    plt.show()

if __name__ == "__main__":
    main()
