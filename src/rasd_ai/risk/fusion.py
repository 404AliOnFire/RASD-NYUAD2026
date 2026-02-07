"""
Risk fusion engine for computing priority scores and tiers.
"""

import numpy as np
import pandas as pd

from rasd_ai.config.settings import SETTINGS
from rasd_ai.risk.anomalies import robust_z, sigmoid, clamp01


class RiskFusionEngine:
    """
    Computes risk scores by fusing base risk (TTO + level)
    with anomaly signals from gas and environment sensors.
    """

    def __init__(
        self,
        w_gas: float = SETTINGS.RISK_WEIGHT_GAS,
        w_env: float = SETTINGS.RISK_WEIGHT_ENV,
        z_start: float = SETTINGS.RISK_Z_START,
        z_scale: float = SETTINGS.RISK_Z_SCALE,
        anom_window_hours: int = SETTINGS.ANOMALY_WINDOW_HOURS,
    ):
        self.w_gas = w_gas
        self.w_env = w_env
        self.z_start = z_start
        self.z_scale = z_scale
        self.anom_window_hours = anom_window_hours

    def compute(self, df_tank: pd.DataFrame, tto_hours: float, current_level: float) -> dict:
        """
        Compute risk score and tier for a tank.

        Args:
            df_tank: DataFrame with sensor data for this tank
            tto_hours: Time to overflow in hours
            current_level: Current fill level percentage

        Returns:
            dict with priority, tier, and component scores
        """
        # Base risk from TTO and fill level
        r_tto = np.exp(-min(tto_hours, 999.0) / 24.0)
        r_fill = np.clip(current_level / 100.0, 0, 1)
        base = 0.65 * r_tto + 0.35 * r_fill

        # Get recent window for anomaly detection
        df = df_tank.sort_values("timestamp")
        cutoff = df["timestamp"].max() - pd.Timedelta(hours=self.anom_window_hours)
        win = df[df["timestamp"] >= cutoff]

        # Extract sensor histories
        gas_hist = win["gas"].to_numpy()
        temp_hist = win["temp_c"].to_numpy()
        hum_hist = win["hum_pct"].to_numpy()

        # Current sensor values
        gas_now = float(df.iloc[-1]["gas"])
        temp_now = float(df.iloc[-1]["temp_c"])
        hum_now = float(df.iloc[-1]["hum_pct"])

        # Compute robust Z-scores
        z_gas = robust_z(gas_now, gas_hist)
        z_temp = robust_z(temp_now, temp_hist)
        z_hum = robust_z(hum_now, hum_hist)

        # Convert to anomaly scores via sigmoid
        gas_anom = sigmoid((z_gas - self.z_start) / self.z_scale)
        temp_anom = sigmoid((z_temp - self.z_start) / self.z_scale)
        hum_anom = sigmoid((z_hum - self.z_start) / self.z_scale)
        env_anom = 0.5 * temp_anom + 0.5 * hum_anom

        # Final priority score
        priority = clamp01(base + self.w_gas * gas_anom + self.w_env * env_anom)

        # Determine tier
        tier = SETTINGS.compute_tier(priority, tto_hours)

        return {
            "priority": float(priority),
            "tier": tier,
            "base": float(base),
            "gas_anom": float(gas_anom),
            "env_anom": float(env_anom),
            "z_gas": float(z_gas),
            "z_temp": float(z_temp),
            "z_hum": float(z_hum),
            "gas_now": gas_now,
            "temp_now": temp_now,
            "hum_now": hum_now,
        }
