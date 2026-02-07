"""
Prophet forecast visualization module.

Generates forecast charts for tank fill levels using Prophet model.
"""

import pandas as pd
import matplotlib.pyplot as plt

from rasd_ai.config.paths import PATHS
from rasd_ai.forecasting.prophet_model import ProphetForecaster


def main() -> None:
    """Generate Prophet forecast visualization."""
    data_frame = pd.read_csv(PATHS.mock_data_csv)

    tank_id = data_frame["tank_id"].iloc[0]
    df_tank = data_frame[data_frame["tank_id"] == tank_id]

    # Run Prophet forecast
    forecaster = ProphetForecaster(threshold=100.0, horizon_hours=72)
    _pred = forecaster.fit_predict_tto(df_tank)

    plt.figure(figsize=(8, 4))
    plt.plot(df_tank["timestamp"], df_tank["level_pct"], label="Sensor Data")
    plt.axhline(100, color="red", linestyle="--", label="Overflow Threshold")

    plt.title("Tank Fill Level Forecast")
    plt.xlabel("Time")
    plt.ylabel("Level (%)")
    plt.legend()
    plt.tight_layout()

    output_path = PATHS.outputs / "prophet_forecast.png"
    plt.savefig(output_path, dpi=200)
    print(f"✅ saved {output_path}")
    plt.show()


if __name__ == "__main__":
    main()
