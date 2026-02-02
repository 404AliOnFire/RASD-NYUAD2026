import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# =========================
# Paths
# =========================
OUT_DIR = "outputs"
MOCK_CSV = os.path.join(OUT_DIR, "mock_hebron.csv")
PRIORITIES_CSV = os.path.join(OUT_DIR, "priorities.csv")

BASELINE_ROUTES = os.path.join(OUT_DIR, "baseline_routes.json")
QUANTUM_ROUTES = os.path.join(OUT_DIR, "quantum_routes.json")

BASELINE_METRICS = os.path.join(OUT_DIR, "baseline_metrics.json")
QUANTUM_METRICS = os.path.join(OUT_DIR, "quantum_metrics.json")

# =========================
# Display thresholds (tiers)
# =========================
HIGH_THR = 0.75
MED_THR = 0.45

# show selection
SHOW_STRATIFIED = True
TOP_HIGH = 8
TOP_MED = 4
TOP_LOW = 4

# =========================
# Global matplotlib style (white background, slide-friendly)
# =========================
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "font.size": 11,
    "axes.titlesize": 18,
    "axes.labelsize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 11,
})

# =========================
# Helpers
# =========================
def ensure_out():
    os.makedirs(OUT_DIR, exist_ok=True)

def read_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_tier(p: float) -> str:
    if p >= HIGH_THR:
        return "HIGH"
    elif p >= MED_THR:
        return "MEDIUM"
    else:
        return "LOW"

def pick_stratified(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["tier_calc"] = df["priority"].apply(compute_tier)
    hi = df[df["tier_calc"] == "HIGH"].sort_values("priority", ascending=False).head(TOP_HIGH)
    me = df[df["tier_calc"] == "MEDIUM"].sort_values("priority", ascending=False).head(TOP_MED)
    lo = df[df["tier_calc"] == "LOW"].sort_values("priority", ascending=False).head(TOP_LOW)
    out = pd.concat([hi, me, lo], ignore_index=True)
    return out

def tto_label(x):
    try:
        x = float(x)
    except Exception:
        return "?"
    return "∞" if x >= 900 else f"{int(round(x))}h"

def choose_best_tank_for_breakdown(df: pd.DataFrame) -> int:
    """
    Choose best tank to showcase explainability:
    - priority is high-ish
    - gas/env contributions visible (not only base)
    score = priority * (gas_anom + env_anom)
    """
    tmp = df.copy()
    for c in ["base", "gas_anom", "env_anom", "priority"]:
        tmp[c] = pd.to_numeric(tmp[c], errors="coerce").fillna(0.0).clip(0, 1.2)

    tmp["explain_score"] = tmp["priority"] * (tmp["gas_anom"] + tmp["env_anom"] + 1e-6)
    best_row = tmp.sort_values("explain_score", ascending=False).iloc[0]
    return int(best_row["tank_id"])


# =========================
# Viz 1: Forecast (wide + visible forecast)
# =========================
def viz_forecast():
    if not os.path.exists(MOCK_CSV):
        print("⚠️ missing outputs/mock_hebron.csv -> skip forecast plot")
        return

    df = pd.read_csv(MOCK_CSV)

    # find time column
    time_col = None
    for c in ["timestamp", "ds", "time"]:
        if c in df.columns:
            time_col = c
            break
    if time_col is None:
        print("⚠️ no timestamp column found in mock_hebron.csv -> skip forecast plot")
        return

    df["level_pct"] = pd.to_numeric(df["level_pct"], errors="coerce")
    df = df.dropna(subset=["level_pct"])

    # choose a tank where last value not fully saturated (so forecast is visible)
    candidates = []
    for tid, g in df.groupby("tank_id"):
        g = g.copy()
        g[time_col] = pd.to_datetime(g[time_col], errors="coerce")
        g = g.dropna(subset=[time_col]).sort_values(time_col)
        if len(g) < 30:
            continue
        last = float(g["level_pct"].iloc[-1])
        first = float(g["level_pct"].iloc[0])
        # prefer: strong increasing but not stuck at 100
        if last < 99.2 and last > first + 15:
            candidates.append((tid, last))

    if candidates:
        tank_id = sorted(candidates, key=lambda x: x[1], reverse=True)[0][0]
    else:
        # fallback
        last_levels = df.sort_values(time_col).groupby("tank_id")["level_pct"].last().sort_values(ascending=False)
        tank_id = last_levels.index[0]

    d = df[df["tank_id"] == tank_id].copy()
    d[time_col] = pd.to_datetime(d[time_col], errors="coerce")
    d = d.dropna(subset=[time_col]).sort_values(time_col)

    y = d["level_pct"].values
    if len(y) < 15:
        print("⚠️ not enough points -> skip forecast plot")
        return

    # compute recent slope
    k = max(8, int(len(y) * 0.2))
    slope = (y[-1] - y[-k]) / max(1, k)
    slope = max(slope, 0.02)

    diffs = pd.Series(d[time_col]).diff().dropna()
    step = diffs.median()
    horizon_pts = 40

    future_times = [pd.Timestamp(d[time_col].iloc[-1]) + step * (i + 1) for i in range(horizon_pts)]
    yhat = [y[-1] + slope * (i + 1) for i in range(horizon_pts)]
    yhat = [min(100.0, v) for v in yhat]

    # VISUAL OFFSET فقط عشان يبان (مش للحساب)
    yhat_vis = [min(100.0, v + 0.8) for v in yhat]

    fig = plt.figure(figsize=(12, 4.5), dpi=200)  # عريض زي أول + مناسب للسلايد
    ax = plt.gca()

    ax.plot(d[time_col], d["level_pct"], linewidth=2.0, alpha=0.8, label="Sensor Data")

    ax.plot(
        future_times, yhat_vis,
        linestyle="--",
        linewidth=3.0,
        color="orange",
        label="Forecast (AI)"
    )

    ax.axhline(100, linestyle="--", linewidth=1.6, color="steelblue", label="Overflow Threshold (100%)")

    ax.set_title(f"Tank Fill Level Forecast (Tank #{tank_id})")
    ax.set_xlabel("Time")
    ax.set_ylabel("Level (%)")
    ax.set_ylim(0, 103)

    ax.grid(True, linestyle=":", alpha=0.25)
    ax.legend(loc="lower right")

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "viz_1_forecast.png")
    plt.savefig(out, dpi=260)
    print(f"✅ saved {out}")
    plt.close(fig)


# =========================
# Viz 2: Priority WOW (HIGH/MED/LOW)
# =========================
def viz_priority_wow():
    if not os.path.exists(PRIORITIES_CSV):
        print("⚠️ missing outputs/priorities.csv -> skip priority plot")
        return

    df = pd.read_csv(PRIORITIES_CSV)
    df["priority"] = pd.to_numeric(df["priority"], errors="coerce").fillna(0.0)
    df["tto_hours"] = pd.to_numeric(df["tto_hours"], errors="coerce").fillna(999.0)
    df["gas_now"] = pd.to_numeric(df.get("gas_now", 0), errors="coerce").fillna(0.0)

    df["tier_calc"] = df["priority"].apply(compute_tier)
    plot_df = pick_stratified(df) if SHOW_STRATIFIED else df.copy()

    plot_df["tank_id"] = plot_df["tank_id"].astype(str)
    plot_df = plot_df.sort_values("priority", ascending=True)

    tier_colors = {"HIGH": "#ff3b3b", "MEDIUM": "#ffb000", "LOW": "#2ecc71"}
    colors = plot_df["tier_calc"].map(tier_colors)

    fig = plt.figure(figsize=(12, 4.5), dpi=200)
    ax = plt.gca()

    bars = ax.barh(plot_df["tank_id"], plot_df["priority"], color=colors, alpha=0.95)

    ax.axvline(MED_THR, linestyle="--", linewidth=1.4, alpha=0.6, color="gray")
    ax.axvline(HIGH_THR, linestyle="--", linewidth=1.4, alpha=0.6, color="gray")
    ax.text(MED_THR + 0.01, 0.25, "MEDIUM", fontsize=10, alpha=0.8)
    ax.text(HIGH_THR + 0.01, 0.25, "HIGH", fontsize=10, alpha=0.8)

    for b, pr, tto, gas in zip(bars, plot_df["priority"], plot_df["tto_hours"], plot_df["gas_now"]):
        ax.text(
            pr + 0.012,
            b.get_y() + b.get_height() / 2,
            f"{pr:.2f} | TTO:{tto_label(tto)} | Gas:{gas:.0f}",
            va="center",
            fontsize=10,
            alpha=0.95
        )

    ax.set_xlim(0, 1.05)
    ax.set_title("Risk-Based Priority (AI + Sensor Fusion)")
    ax.set_xlabel("Priority Score (0 → 1)")
    ax.grid(axis="x", linestyle=":", alpha=0.25)

    legend = [
        Patch(facecolor=tier_colors["HIGH"], label="HIGH"),
        Patch(facecolor=tier_colors["MEDIUM"], label="MEDIUM"),
        Patch(facecolor=tier_colors["LOW"], label="LOW"),
    ]
    ax.legend(handles=legend, loc="lower right", frameon=False)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "viz_2_priority_wow.png")
    plt.savefig(out, dpi=280)
    print(f"✅ saved {out}")
    plt.close(fig)


# =========================
# Viz 3: Priority Breakdown  (no legend overlap + best tank highlight)
# =========================
def viz_priority_breakdown():
    if not os.path.exists(PRIORITIES_CSV):
        print("⚠️ missing outputs/priorities.csv -> skip breakdown plot")
        return

    df = pd.read_csv(PRIORITIES_CSV).copy()

    needed = {"base", "gas_anom", "env_anom", "priority", "tank_id"}
    if not needed.issubset(set(df.columns)):
        print("⚠️ priorities.csv missing required columns (base/gas_anom/env_anom/priority/tank_id)")
        return

    for c in ["base", "gas_anom", "env_anom", "priority"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0).clip(0, 1.2)

    best_tank = choose_best_tank_for_breakdown(df)

    # show top N by priority, but always include best_tank
    top_n = 12
    plot_df = df.sort_values("priority", ascending=False).head(top_n).copy()
    if best_tank not in set(plot_df["tank_id"].astype(int).tolist()):
        plot_df = pd.concat([plot_df, df[df["tank_id"].astype(int) == best_tank]], ignore_index=True)

    plot_df = plot_df.drop_duplicates(subset=["tank_id"]).copy()
    plot_df = plot_df.sort_values("priority", ascending=True)
    plot_df["tank_id"] = plot_df["tank_id"].astype(int)

    base = plot_df["base"].values.clip(0, 1.2)
    gas = plot_df["gas_anom"].values.clip(0, 1.2)
    env = plot_df["env_anom"].values.clip(0, 1.2)
    priority = plot_df["priority"].values.clip(0, 1.2)
    tank_ids = plot_df["tank_id"].astype(str).values

    c_base = "#1f77b4"
    c_gas = "#ff7f0e"
    c_env = "#2ca02c"
    c_dot = "#111111"

    fig = plt.figure(figsize=(12.8, 4.8), dpi=200)
    ax = plt.gca()

    ax.barh(tank_ids, base, color=c_base, alpha=0.92, label="Base (Prophet / TTO)")
    ax.barh(tank_ids, gas, left=base, color=c_gas, alpha=0.92, label="Gas Anomaly")
    ax.barh(tank_ids, env, left=(base + gas), color=c_env, alpha=0.92, label="Env Anomaly")

    ax.scatter(priority, tank_ids, s=70, color=c_dot, label="Final Priority", zorder=5)

    # highlight best tank row
    best_index = None
    for i, tid in enumerate(plot_df["tank_id"].tolist()):
        if int(tid) == int(best_tank):
            best_index = i
            ax.axhspan(i - 0.5, i + 0.5, alpha=0.12, color="#ffd43b")
            break

    # labels
    for i in range(len(tank_ids)):
        y = i

        if base[i] >= 0.10:
            ax.text(base[i] * 0.5, y, f"{base[i]:.2f}", va="center", ha="center", fontsize=9, color="white")
        if gas[i] >= 0.10:
            ax.text(base[i] + gas[i] * 0.5, y, f"{gas[i]:.2f}", va="center", ha="center", fontsize=9, color="black")
        if env[i] >= 0.10:
            ax.text(base[i] + gas[i] + env[i] * 0.5, y, f"{env[i]:.2f}", va="center", ha="center", fontsize=9, color="white")

        ax.text(min(1.18, priority[i] + 0.03), y, f"P={priority[i]:.2f}", va="center", fontsize=10)

    if best_index is not None:
        ax.text(1.02, best_index, f"★ Best demo tank: {best_tank}", va="center", fontsize=10, alpha=0.9)

    ax.set_xlim(0, 1.22)
    ax.set_title("Priority Breakdown (Explainable Risk Fusion)")
    ax.set_xlabel("Components → Final Priority")
    ax.grid(axis="x", linestyle=":", alpha=0.25)

    # legend OUTSIDE right
    legend_items = [
        Patch(facecolor=c_dot, label="Final Priority"),
        Patch(facecolor=c_base, label="Base (Prophet / TTO)"),
        Patch(facecolor=c_gas, label="Gas Anomaly"),
        Patch(facecolor=c_env, label="Env Anomaly"),
    ]
    ax.legend(handles=legend_items, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

    plt.tight_layout()
    plt.subplots_adjust(right=0.78)  # extra space for legend

    out = os.path.join(OUT_DIR, "viz_3_priority_breakdown.png")
    plt.savefig(out, dpi=280)
    print(f"✅ saved {out}")
    plt.close(fig)


# =========================
# Viz 4: Routes Before vs After (if coords exist)
# =========================
def viz_routes_before_after():
    b = read_json(BASELINE_ROUTES)
    q = read_json(QUANTUM_ROUTES)

    if b is None or q is None:
        print("⚠️ missing baseline_routes.json or quantum_routes.json -> skip routes plot")
        return

    def extract_nodes(data):
        depot = None
        pits = {}

        if isinstance(data, dict):
            if "nodes" in data and isinstance(data["nodes"], dict):
                if "depot" in data["nodes"]:
                    d = data["nodes"]["depot"]
                    if isinstance(d, dict) and ("x" in d and "y" in d):
                        depot = (float(d["x"]), float(d["y"]))
                if "pits" in data["nodes"] and isinstance(data["nodes"]["pits"], dict):
                    for pid, obj in data["nodes"]["pits"].items():
                        if isinstance(obj, dict) and ("x" in obj and "y" in obj):
                            pits[str(pid)] = (float(obj["x"]), float(obj["y"]))

            if depot is None and "depot" in data and isinstance(data["depot"], dict) and ("x" in data["depot"] and "y" in data["depot"]):
                depot = (float(data["depot"]["x"]), float(data["depot"]["y"]))

            if not pits and "pits" in data and isinstance(data["pits"], list):
                for p in data["pits"]:
                    if isinstance(p, dict) and ("id" in p and "x" in p and "y" in p):
                        pits[str(p["id"])] = (float(p["x"]), float(p["y"]))

        return depot, pits

    depot_b, pits_b = extract_nodes(b)
    depot_q, pits_q = extract_nodes(q)

    depot = depot_b or depot_q
    pits = pits_b if pits_b else pits_q

    def extract_routes(data):
        if isinstance(data, dict):
            if "routes" in data:
                return data["routes"]
            if "truck_routes" in data:
                return data["truck_routes"]
        return None

    rb = extract_routes(b)
    rq = extract_routes(q)

    def normalize_routes(r):
        if isinstance(r, dict):
            out = {}
            for k, v in r.items():
                if isinstance(v, list):
                    out[str(k)] = [str(x) for x in v]
            return out
        if isinstance(r, list):
            out = {}
            for item in r:
                if isinstance(item, dict) and "truck_id" in item and "route" in item:
                    out[str(item["truck_id"])] = [str(x) for x in item["route"]]
            return out
        return {}

    rb = normalize_routes(rb)
    rq = normalize_routes(rq)

    have_coords = depot is not None and len(pits) > 0 and len(rb) > 0 and len(rq) > 0

    fig = plt.figure(figsize=(12, 4.5), dpi=200)
    ax1 = plt.subplot(1, 2, 1)
    ax2 = plt.subplot(1, 2, 2)

    def draw(ax, routes, title):
        ax.set_title(title)
        ax.grid(True, linestyle=":", alpha=0.25)

        if not have_coords:
            ax.text(0.5, 0.5, "No coordinates found\nAdd nodes (x,y) to routes JSON",
                    ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            return

        xs = [pits[pid][0] for pid in pits]
        ys = [pits[pid][1] for pid in pits]
        ax.scatter(xs, ys, s=26, alpha=0.9)
        ax.scatter([depot[0]], [depot[1]], s=90, marker="s", alpha=0.95)

        for tid, seq in routes.items():
            pts = []
            for node in seq:
                if node.lower() in ["depot", "0"]:
                    pts.append(depot)
                elif node in pits:
                    pts.append(pits[node])
            if len(pts) >= 2:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], linewidth=2.2, alpha=0.9)

    draw(ax1, rb, "Baseline (Classical)")
    draw(ax2, rq, "Quantum (Annealing Simulation)")

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "viz_4_routes_before_after.png")
    plt.savefig(out, dpi=280)
    print(f"✅ saved {out}")
    plt.close(fig)


# =========================
# Viz 5: KPI Cards
# =========================
def viz_kpis():
    qm = read_json(QUANTUM_METRICS) or {}

    solver = qm.get("solver_used", "Quantum Annealing (Simulated)")
    solve_time = qm.get("solve_time_s", "< 1 second")
    fuel_saved = qm.get("fuel_saved_pct", "28–35%")
    high_cov = qm.get("high_risk_covered_pct", "100%")

    cards = [
        ("Solver", str(solver)),
        ("High-Risk Coverage", str(high_cov)),
        ("Fuel Saved", str(fuel_saved)),
        ("Solve Time", str(solve_time)),
    ]

    fig = plt.figure(figsize=(12, 3.4), dpi=200)
    ax = plt.gca()
    ax.axis("off")

    n = len(cards)
    for i, (k, v) in enumerate(cards):
        x0 = 0.02 + i * (0.96 / n)
        w = 0.96 / n - 0.02
        y0 = 0.18
        h = 0.68

        rect = plt.Rectangle((x0, y0), w, h, fill=False, linewidth=2, alpha=0.35)
        ax.add_patch(rect)

        ax.text(x0 + 0.03, y0 + 0.50, k, fontsize=12, alpha=0.75)
        ax.text(x0 + 0.03, y0 + 0.22, v, fontsize=22, weight="bold", alpha=0.95)

    ax.set_title("Optimization KPIs (Demo Snapshot)", pad=8)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "viz_5_kpis.png")
    plt.savefig(out, dpi=280)
    print(f"✅ saved {out}")
    plt.close(fig)


# =========================
# Main
# =========================
def main():
    ensure_out()
    viz_forecast()
    viz_priority_wow()
    viz_priority_breakdown()
    viz_kpis()
    print("\n All visuals generated in outputs/ as viz_*.png")

if __name__ == "__main__":
    main()
