import numpy as np
import pandas as pd
from dataclasses import dataclass
from prophet import Prophet

# ------------------------
# Utilities
# ------------------------

def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))

def robust_z(x_now: float, history: np.ndarray, eps: float = 1e-6) -> float:
    h = np.asarray(history, dtype=float)
    med = np.median(h)
    mad = np.median(np.abs(h - med)) + eps
    return (x_now - med) / mad

def clamp01(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))

# ------------------------
# Sensor Simulation (for hackathon)
# ------------------------

@dataclass
class SimConfig:
    n_tanks: int = 12
    days: int = 30
    freq_min: int = 15
    seed: int = 7

class SensorSimulator:
    def __init__(self, cfg: SimConfig):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)

    def generate(self) -> pd.DataFrame:
        # timeline
        periods = int((self.cfg.days * 24 * 60) / self.cfg.freq_min)
        ts = pd.date_range("2026-01-01", periods=periods, freq=f"{self.cfg.freq_min}min")

        rows = []
        for tank_id in range(self.cfg.n_tanks):
            # tank-specific behavior
            base_rate = self.rng.uniform(0.02, 0.12)  # % per 15min (≈ 2% to 12% per day)
            level = self.rng.uniform(5, 40)

            # gas baseline relates to level + random
            gas_base = self.rng.uniform(20, 60)
            temp_base = self.rng.uniform(15, 28)
            hum_base  = self.rng.uniform(30, 60)

            # occasional hazard events
            hazard_days = self.rng.choice(np.arange(3, self.cfg.days-2), size=2, replace=False)
            hazard_idx = set()
            for d in hazard_days:
                start = int((d * 24 * 60) / self.cfg.freq_min)
                hazard_idx.update(range(start, start + int((6 * 60) / self.cfg.freq_min)))  # 6 hours

            for i, t in enumerate(ts):
                # seasonality: higher usage morning/evening
                hour = t.hour
                daily_factor = 1.0 + (0.35 if hour in [6,7,8,19,20,21] else 0.0)

                noise = self.rng.normal(0, 0.25)
                level += (base_rate * daily_factor * 100) + noise

                # clamp and allow "pumping" reset sometimes
                if level > 100:
                    level = 100

                # gas rises with level, plus hazard spikes
                gas = gas_base + 0.6 * level + self.rng.normal(0, 5)
                if i in hazard_idx:
                    gas += self.rng.uniform(80, 180)  # spike

                # environment with mild drift
                temp = temp_base + 3*np.sin(2*np.pi*(hour/24)) + self.rng.normal(0, 0.8)
                hum  = hum_base  + 5*np.cos(2*np.pi*(hour/24)) + self.rng.normal(0, 2.0)

                rows.append({
                    "timestamp": t,
                    "tank_id": tank_id,
                    "level_pct": float(np.clip(level, 0, 100)),
                    "gas": float(max(gas, 0)),
                    "temp_c": float(temp),
                    "hum_pct": float(np.clip(hum, 0, 100))
                })

        return pd.DataFrame(rows)

# ------------------------
# Prophet Forecaster (per tank)
# ------------------------

class ProphetForecaster:
    def __init__(self, threshold: float = 100.0, horizon_hours: int = 72):
        self.threshold = threshold
        self.horizon_hours = horizon_hours

    def fit_predict_tto(self, df_tank: pd.DataFrame) -> dict:
        df = df_tank.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp").sort_index()

        df_hour = df["level_pct"].resample("1h").median().reset_index()
        df_hour.columns = ["ds", "y"]

        m = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05
        )
        m.fit(df_hour)

        future = m.make_future_dataframe(periods=self.horizon_hours, freq="h")
        fc = m.predict(future)

        now_ts = df_hour["ds"].max()
        current_level = float(df_hour.loc[df_hour["ds"] == now_ts, "y"].iloc[0])

        future_fc = fc[fc["ds"] > now_ts]
        hit = future_fc[future_fc["yhat"] >= self.threshold].head(1)

        if len(hit) == 0:
            tto_hours = 999.0
            hit_ts = None
        else:
            hit_ts = hit["ds"].iloc[0]
            tto_hours = (hit_ts - now_ts).total_seconds() / 3600.0

        last = future_fc.iloc[-1]
        unc = float(max(last["yhat_upper"] - last["yhat_lower"], 0.0))

        return {
            "tto_hours": float(tto_hours),
            "current_level": current_level,
            "hit_ts": hit_ts,
            "uncertainty": unc,
        }


# ------------------------
# Risk Fusion Engine
# ------------------------

class RiskFusionEngine:
    def __init__(self,
                 w_gas: float = 0.20,
                 w_env: float = 0.10,
                 z_start: float = 2.0,
                 z_scale: float = 1.0,
                 anom_window_hours: int = 48):
        self.w_gas = w_gas
        self.w_env = w_env
        self.z_start = z_start
        self.z_scale = z_scale
        self.anom_window_hours = anom_window_hours

    def compute(self, df_tank: pd.DataFrame, tto_hours: float, current_level: float) -> dict:
        # base risk
        r_tto = np.exp(-min(tto_hours, 999.0) / 24.0)
        r_fill = np.clip(current_level / 100.0, 0, 1)
        base = 0.65 * r_tto + 0.35 * r_fill

        # last window for anomalies
        df = df_tank.sort_values("timestamp")
        cutoff = df["timestamp"].max() - pd.Timedelta(hours=self.anom_window_hours)
        win = df[df["timestamp"] >= cutoff]

        gas_hist = win["gas"].to_numpy()
        temp_hist = win["temp_c"].to_numpy()
        hum_hist  = win["hum_pct"].to_numpy()

        gas_now  = float(df.iloc[-1]["gas"])
        temp_now = float(df.iloc[-1]["temp_c"])
        hum_now  = float(df.iloc[-1]["hum_pct"])

        z_gas  = robust_z(gas_now, gas_hist)
        z_temp = robust_z(temp_now, temp_hist)
        z_hum  = robust_z(hum_now, hum_hist)

        gas_anom = sigmoid((z_gas - self.z_start) / self.z_scale)
        temp_anom = sigmoid((z_temp - self.z_start) / self.z_scale)
        hum_anom  = sigmoid((z_hum  - self.z_start) / self.z_scale)
        env_anom = 0.5 * temp_anom + 0.5 * hum_anom

        priority = clamp01(base + self.w_gas * gas_anom + self.w_env * env_anom)

        # tier
        if tto_hours <= 24.0 or priority >= 0.75:
            tier = "HIGH"
        elif priority >= 0.45:
            tier = "MEDIUM"
        else:
            tier = "LOW"

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

# ------------------------
# End-to-End Demo
# ------------------------

def run_demo():
    # 1) simulate
    sim = SensorSimulator(SimConfig(n_tanks=10, days=30, freq_min=15))
    df = sim.generate()

    # 2) components
    forecaster = ProphetForecaster(threshold=100.0, horizon_hours=72)
    fusion = RiskFusionEngine(w_gas=0.20, w_env=0.10, anom_window_hours=48)

    # 3) compute per tank
    out_rows = []
    for tank_id, df_tank in df.groupby("tank_id"):
        pred = forecaster.fit_predict_tto(df_tank)
        risk = fusion.compute(df_tank, pred["tto_hours"], pred["current_level"])

        out_rows.append({
            "tank_id": int(tank_id),
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

    out = pd.DataFrame(out_rows).sort_values(["tier", "priority"], ascending=[True, False])
    print(out.to_string(index=False))

    # ready-to-send weights for optimization
    weights = out[["tank_id", "priority", "tier", "tto_hours", "level_pct"]].to_dict(orient="records")
    return weights

if __name__ == "__main__":
    print('module ok')
    # weights is your dispatch input to CQM/OR-Tools
