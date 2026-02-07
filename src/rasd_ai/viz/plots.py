"""
Visualization plots for RASD dashboard.
"""

from pathlib import Path
from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from rasd_ai.config.paths import PATHS
from rasd_ai.config.settings import SETTINGS
from rasd_ai.data.loaders import load_json_safe

# Configure matplotlib
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "font.size": 11,
        "axes.titlesize": 18,
        "axes.labelsize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 11,
    }
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


def viz_forecast(df: Optional[pd.DataFrame] = None, output_path: Optional[Path] = None):
    """Create forecast visualization."""
    if df is None:
        if not PATHS.mock_data_csv.exists():
            print("⚠️ Missing mock_hebron.csv -> skip forecast plot")
            return
        df = pd.read_csv(PATHS.mock_data_csv)

    if output_path is None:
        output_path = PATHS.viz_file(1, "forecast")

    # Find time column
    time_col = None
    for c in ["timestamp", "ds", "time"]:
        if c in df.columns:
            time_col = c
            break
    if time_col is None:
        print("⚠️ No timestamp column found -> skip forecast plot")
        return

    df["level_pct"] = pd.to_numeric(df["level_pct"], errors="coerce")
    df = df.dropna(subset=["level_pct"])

    # Find best tank to visualize
    candidates = []
    for tid, g in df.groupby("tank_id"):
        g = g.copy()
        g[time_col] = pd.to_datetime(g[time_col], errors="coerce")
        g = g.dropna(subset=[time_col]).sort_values(time_col)
        if len(g) < 30:
            continue
        last = float(g["level_pct"].iloc[-1])
        first = float(g["level_pct"].iloc[0])
        if first + 15 < last < 99.2:
            candidates.append((tid, last))

    if candidates:
        tank_id = sorted(candidates, key=lambda x: x[1], reverse=True)[0][0]
    else:
        last_levels = (
            df.sort_values(time_col)
            .groupby("tank_id")["level_pct"]
            .last()
            .sort_values(ascending=False)
        )
        tank_id = last_levels.index[0]

    d = df[df["tank_id"] == tank_id].copy()
    d[time_col] = pd.to_datetime(d[time_col], errors="coerce")
    d = d.dropna(subset=[time_col]).sort_values(time_col)

    y = d["level_pct"].values
    if len(y) < 15:
        print("⚠️ Not enough points -> skip forecast plot")
        return

    # Compute recent slope
    k = max(8, int(len(y) * 0.2))
    slope = (y[-1] - y[-k]) / max(1, k)
    slope = max(slope, 0.02)

    diffs = pd.Series(d[time_col]).diff().dropna()
    step = diffs.median()
    horizon_pts = 40

    future_times = [pd.Timestamp(d[time_col].iloc[-1]) + step * (i + 1) for i in range(horizon_pts)]
    yhat = [min(100.0, y[-1] + slope * (i + 1)) for i in range(horizon_pts)]

    fig = plt.figure(figsize=(12, 4.5), dpi=200)
    ax = plt.gca()

    ax.plot(d[time_col], d["level_pct"], linewidth=2.0, alpha=0.8, label="Sensor Data")
    ax.plot(
        future_times,
        yhat,
        linestyle="--",
        linewidth=3.0,
        color="orange",
        label="Forecast (AI)",
    )
    ax.axhline(
        100,
        linestyle="--",
        linewidth=1.6,
        color="steelblue",
        label="Overflow Threshold (100%)",
    )

    ax.set_title(f"Tank Fill Level Forecast (Tank #{tank_id})")
    ax.set_xlabel("Time")
    ax.set_ylabel("Level (%)")
    ax.set_ylim(0, 103)
    ax.grid(True, linestyle=":", alpha=0.25)
    ax.legend(loc="lower right")

    clean_save(fig, output_path)


def viz_priority_wow(df: Optional[pd.DataFrame] = None, output_path: Optional[Path] = None):
    """Create priority visualization by tier."""
    if df is None:
        if not PATHS.priorities_csv.exists():
            print("⚠️ Missing priorities.csv -> skip priority plot")
            return
        df = pd.read_csv(PATHS.priorities_csv)

    if output_path is None:
        output_path = PATHS.viz_file(2, "priority_wow")

    # Sort by priority
    df = df.sort_values("priority", ascending=False).head(16)

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = [tier_color(t) for t in df["tier"]]
    _bars = ax.barh(range(len(df)), df["priority"], color=colors, edgecolor="white", linewidth=0.5)

    ax.set_yticks(range(len(df)))
    ax.set_yticklabels([f"Tank #{int(t)}" for t in df["tank_id"]])
    ax.invert_yaxis()
    ax.set_xlabel("Priority Score")
    ax.set_title("Tank Priority Ranking")
    ax.set_xlim(0, 1.05)
    ax.grid(axis="x", alpha=0.3)

    # Legend
    legend_elements = [
        Patch(facecolor=tier_color("HIGH"), label="HIGH"),
        Patch(facecolor=tier_color("MEDIUM"), label="MEDIUM"),
        Patch(facecolor=tier_color("LOW"), label="LOW"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    clean_save(fig, output_path)


def viz_priority_breakdown(
    df: Optional[pd.DataFrame] = None,
    tank_id: Optional[int] = None,
    output_path: Optional[Path] = None,
):
    """Create priority breakdown visualization for a single tank."""
    if df is None:
        if not PATHS.priorities_csv.exists():
            print("⚠️ Missing priorities.csv -> skip breakdown plot")
            return
        df = pd.read_csv(PATHS.priorities_csv)

    if output_path is None:
        output_path = PATHS.viz_file(3, "priority_breakdown")

    # Choose best tank for explainability
    if tank_id is None:
        for c in ["base", "gas_anom", "env_anom", "priority"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0).clip(0, 1.2)
        df["explain_score"] = df["priority"] * (df["gas_anom"] + df["env_anom"] + 1e-6)
        tank_id = int(df.sort_values("explain_score", ascending=False).iloc[0]["tank_id"])

    row = df[df["tank_id"] == tank_id].iloc[0]

    components = {
        "Base Risk": float(row["base"]),
        "Gas Anomaly": float(row["gas_anom"]) * SETTINGS.RISK_WEIGHT_GAS,
        "Env Anomaly": float(row["env_anom"]) * SETTINGS.RISK_WEIGHT_ENV,
    }

    fig, ax = plt.subplots(figsize=(8, 5))

    names = list(components.keys())
    values = list(components.values())
    colors = ["#3498db", "#e74c3c", "#f39c12"]

    bars = ax.bar(names, values, color=colors, edgecolor="white", linewidth=2)

    ax.set_ylabel("Contribution to Priority")
    ax.set_title(f"Priority Breakdown - Tank #{tank_id}")
    ax.set_ylim(0, max(values) * 1.2)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{val:.3f}",
            ha="center",
            va="bottom",
            fontsize=11,
        )

    clean_save(fig, output_path)


def viz_kpis(metrics: Optional[dict] = None, output_path: Optional[Path] = None):
    """Create KPI summary visualization."""
    if metrics is None:

        metrics = load_json_safe(PATHS.quantum_metrics_enriched_json, {})
        if not metrics:
            metrics = load_json_safe(PATHS.quantum_metrics_json, {})

    if output_path is None:
        output_path = PATHS.viz_file(5, "kpis")

    if not metrics:
        print("⚠️ No metrics available -> skip KPI plot")
        return

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    # Distance
    ax = axes[0]
    dist = metrics.get("total_distance_km", 0)
    ax.bar(["Distance"], [dist], color="#3498db", width=0.5)
    ax.set_ylabel("km")
    ax.set_title("Total Distance")
    ax.text(0, dist + 0.5, f"{dist:.1f} km", ha="center", va="bottom", fontsize=12)

    # Coverage
    ax = axes[1]
    served = metrics.get("served_total", 0)
    missed = metrics.get("missed_total", 0)
    ax.bar(["Served", "Missed"], [served, missed], color=["#2ecc71", "#e74c3c"], width=0.5)
    ax.set_ylabel("Tanks")
    ax.set_title("Coverage")

    # Fuel & CO2
    ax = axes[2]
    fuel = metrics.get("fuel_l_est", 0)
    co2 = metrics.get("co2_kg_est", 0)
    ax.bar(["Fuel (L)", "CO₂ (kg)"], [fuel, co2], color=["#f39c12", "#9b59b6"], width=0.5)
    ax.set_title("Environmental Impact")

    fig.suptitle("Route Optimization KPIs", fontsize=14, fontweight="bold")
    clean_save(fig, output_path)


def generate_all_visualizations():
    """Generate all visualization plots."""
    print("\n📊 Generating visualizations...")
    viz_forecast()
    viz_priority_wow()
    viz_priority_breakdown()
    viz_kpis()
    print("✅ All visualizations complete")


if __name__ == "__main__":
    generate_all_visualizations()
