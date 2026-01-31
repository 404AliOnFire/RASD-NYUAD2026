import os
import pandas as pd

from simulator_hebron import HebronCitySimulator, HebronSimConfig
from predictor import ProphetForecaster, RiskFusionEngine

def main():
    os.makedirs("outputs", exist_ok=True)

    # 1) Generate Mock Data
    sim = HebronCitySimulator(HebronSimConfig(n_tanks=20, days=30, freq_min=15))
    df = sim.generate()
    df.to_csv("outputs/mock_hebron.csv", index=False)
    print("✅ saved outputs/mock_hebron.csv")

    # 2) Run Prediction + Risk Fusion per tank
    forecaster = ProphetForecaster(threshold=100.0, horizon_hours=72)
    fusion = RiskFusionEngine(w_gas=0.20, w_env=0.10, anom_window_hours=48)

    results = []
    for tank_id, df_tank in df.groupby("tank_id"):
        pred = forecaster.fit_predict_tto(df_tank)
        risk = fusion.compute(df_tank, pred["tto_hours"], pred["current_level"])
        profile = df_tank.iloc[-1]["profile"]

        results.append({
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
        })

    out = pd.DataFrame(results).sort_values(["tier", "priority"], ascending=[True, False])
    out.to_csv("outputs/priorities.csv", index=False)

    print("✅ saved outputs/priorities.csv")
    print("\n--- TOP PRIORITIES ---")
    print(out.head(10).to_string(index=False))

    # 3) Build routing inputs + baseline + quantum simulation
    print("\n✅ building routing inputs")
    from generate_routing_inputs import main as gen_inputs_main
    gen_inputs_main()

    print("\n✅ building baseline routes")
    from build_baseline_routes import main as baseline_main
    baseline_main()

    print("\n✅ running quantum annealing simulation")
    from optimize_quantum_sim import main as quantum_sim_main
    quantum_sim_main()

if __name__ == "__main__":
    main()
