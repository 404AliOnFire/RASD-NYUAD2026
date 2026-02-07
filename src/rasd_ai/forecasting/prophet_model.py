"""
Prophet-based forecasting for tank fill levels and time-to-overflow.
"""

import pandas as pd
from prophet import Prophet

from rasd_ai.config.settings import SETTINGS


class ProphetForecaster:
    """Forecasts tank fill level and time-to-overflow using Prophet."""

    def __init__(
        self,
        threshold: float = SETTINGS.OVERFLOW_THRESHOLD_PCT,
        horizon_hours: int = SETTINGS.FORECAST_HORIZON_HOURS,
    ):
        self.threshold = threshold
        self.horizon_hours = horizon_hours

    def fit_predict_tto(self, df_tank: pd.DataFrame) -> dict:
        """
        Fit Prophet on tank data and predict time-to-overflow.

        Args:
            df_tank: DataFrame with 'timestamp' and 'level_pct' columns

        Returns:
            dict with 'tto_hours', 'current_level', 'hit_ts', 'uncertainty'
        """
        df = df_tank.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp").sort_index()

        # Resample to hourly median
        df_hour = df["level_pct"].resample("1h").median().reset_index()
        df_hour.columns = ["ds", "y"]

        # Fit Prophet
        m = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        m.fit(df_hour)

        # Make future predictions
        future = m.make_future_dataframe(periods=self.horizon_hours, freq="h")
        fc = m.predict(future)

        # Get current values
        now_ts = df_hour["ds"].max()
        current_level = float(df_hour.loc[df_hour["ds"] == now_ts, "y"].iloc[0])

        # Find time to overflow
        future_fc = fc[fc["ds"] > now_ts]
        hit = future_fc[future_fc["yhat"] >= self.threshold].head(1)

        if len(hit) == 0:
            tto_hours = 999.0
            hit_ts = None
        else:
            hit_ts = hit["ds"].iloc[0]
            tto_hours = (hit_ts - now_ts).total_seconds() / 3600.0

        # Uncertainty from last forecast point
        last = future_fc.iloc[-1]
        unc = float(max(last["yhat_upper"] - last["yhat_lower"], 0.0))

        return {
            "tto_hours": float(tto_hours),
            "current_level": current_level,
            "hit_ts": hit_ts,
            "uncertainty": unc,
        }
