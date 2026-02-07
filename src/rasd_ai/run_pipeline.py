"""
RASD Main Pipeline

Run the complete pipeline:
1. Generate mock sensor data
2. Run Prophet forecasting + risk fusion
3. Generate routing inputs
4. Build baseline routes
5. Solve with quantum annealing simulation
6. Generate visualizations
7. Export for frontend

Usage:
    python -m rasd_ai.run_pipeline
    python -m rasd_ai.run_pipeline --demo
"""

import argparse
import pandas as pd

from rasd_ai.config.paths import PATHS
from rasd_ai.config.settings import SETTINGS
from rasd_ai.simulation.hebron import HebronCitySimulator, HebronSimConfig
from rasd_ai.forecasting.prophet_model import ProphetForecaster
from rasd_ai.risk.fusion import RiskFusionEngine
from rasd_ai.optimization.routing_inputs import generate_routing_inputs
from rasd_ai.optimization.baseline_greedy import main as baseline_main
from rasd_ai.optimization.quantum_anneal import main as quantum_main
from rasd_ai.viz.map_routes import generate_route_comparison
from rasd_ai.viz.plots import generate_all_visualizations
from rasd_ai.exporters.frontend import build_routes_for_frontend, copy_to_frontend


def run_simulation():
    """Step 1: Generate mock sensor data."""
    print("\n" + "=" * 60)
    print("📊 STEP 1: Generating mock sensor data...")
    print("=" * 60)

    sim = HebronCitySimulator(
        HebronSimConfig(
            n_tanks=SETTINGS.DEFAULT_N_TANKS,
            days=SETTINGS.DEFAULT_DAYS,
            freq_min=SETTINGS.DEFAULT_FREQ_MIN,
        )
    )
    df = sim.generate()
    df.to_csv(PATHS.mock_data_csv, index=False)
    print(f"✅ Saved {PATHS.mock_data_csv}")
    return df


def run_forecasting_and_risk(df: pd.DataFrame):
    """Step 2: Run Prophet forecasting and risk fusion."""
    print("\n" + "=" * 60)
    print("🔮 STEP 2: Running Prophet forecasting + risk fusion...")
    print("=" * 60)

    forecaster = ProphetForecaster(
        threshold=SETTINGS.OVERFLOW_THRESHOLD_PCT,
        horizon_hours=SETTINGS.FORECAST_HORIZON_HOURS,
    )
    fusion = RiskFusionEngine(
        w_gas=SETTINGS.RISK_WEIGHT_GAS,
        w_env=SETTINGS.RISK_WEIGHT_ENV,
        anom_window_hours=SETTINGS.ANOMALY_WINDOW_HOURS,
    )

    results = []
    for tank_id, df_tank in df.groupby("tank_id"):
        pred = forecaster.fit_predict_tto(df_tank)
        risk = fusion.compute(df_tank, pred["tto_hours"], pred["current_level"])
        profile = df_tank.iloc[-1]["profile"]

        results.append(
            {
                "tank_id": int(tank_id),
                "profile": profile,
                "level_pct": round(pred["current_level"], 2),
                "tto_hours": round(pred["tto_hours"], 2),
                "priority": round(risk["priority"], 4),
                "tier": risk["tier"],
                "gas_now": round(risk["gas_now"], 1),
                "temp_c": round(risk["temp_now"], 1),
                "hum_pct": round(risk["hum_now"], 1),
                "base": round(risk["base"], 4),
                "gas_anom": round(risk["gas_anom"], 4),
                "env_anom": round(risk["env_anom"], 4),
            }
        )

    out = pd.DataFrame(results).sort_values(["tier", "priority"], ascending=[True, False])
    out.to_csv(PATHS.priorities_csv, index=False)

    print(f"✅ Saved {PATHS.priorities_csv}")
    print("\n--- TOP PRIORITIES ---")
    print(out.head(10).to_string(index=False))


def run_routing():
    """Step 3-5: Generate routing inputs, baseline, and quantum routes."""
    print("\n" + "=" * 60)
    print("🚛 STEP 3: Generating routing inputs...")
    print("=" * 60)
    generate_routing_inputs()

    print("\n" + "=" * 60)
    print("📍 STEP 4: Building baseline routes...")
    print("=" * 60)
    baseline_main()

    print("\n" + "=" * 60)
    print("⚛️  STEP 5: Running quantum annealing simulation...")
    print("=" * 60)
    quantum_main()


def run_visualizations():
    """Step 6: Generate visualizations."""
    print("\n" + "=" * 60)
    print("📈 STEP 6: Generating visualizations...")
    print("=" * 60)
    generate_route_comparison()
    generate_all_visualizations()


def run_export():
    """Step 7: Export for frontend."""
    print("\n" + "=" * 60)
    print("📦 STEP 7: Exporting for frontend...")
    print("=" * 60)
    build_routes_for_frontend()
    copy_to_frontend()


def main(demo: bool = False):  # pylint: disable=unused-argument
    """
    Run the complete RASD pipeline.

    Args:
        demo: If True, run with demo settings (reserved for future use)
    """
    # Note: demo parameter reserved for future configuration options
    print("\n" + "=" * 60)
    print("🚀 RASD PIPELINE STARTING...")
    print("=" * 60)
    print(f"   Outputs directory: {PATHS.outputs}")

    # Ensure outputs directory exists
    PATHS.outputs.mkdir(parents=True, exist_ok=True)

    # Run all steps
    df = run_simulation()
    run_forecasting_and_risk(df)
    run_routing()
    run_visualizations()
    run_export()

    print("\n" + "=" * 60)
    print("✅ RASD PIPELINE COMPLETE!")
    print("=" * 60)
    print(f"\n📁 All outputs saved to: {PATHS.outputs}")
    print(f"🌐 Frontend data copied to: {PATHS.frontend_data}")
    print("\nTo run the frontend:")
    print("   cd src/rasd_ai/frontend")
    print("   npm install")
    print("   npm run dev")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RASD Pipeline")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode")
    args = parser.parse_args()

    main(demo=args.demo)
