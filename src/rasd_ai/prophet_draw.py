import pandas as pd
import matplotlib.pyplot as plt
from predictor import ProphetForecaster

df = pd.read_csv("outputs/mock_hebron.csv")

tank_id = df["tank_id"].iloc[0]
df_tank = df[df["tank_id"] == tank_id]

#  Prophet
forecaster = ProphetForecaster(threshold=100.0, horizon_hours=72)
pred = forecaster.fit_predict_tto(df_tank)

plt.figure(figsize=(8,4))
plt.plot(df_tank["timestamp"], df_tank["level_pct"], label="Sensor Data")
plt.axhline(100, color="red", linestyle="--", label="Overflow Threshold")

plt.title("Tank Fill Level Forecast")
plt.xlabel("Time")
plt.ylabel("Level (%)")
plt.legend()
plt.tight_layout()

plt.savefig("outputs/prophet_forecast.png", dpi=200)
plt.show()
