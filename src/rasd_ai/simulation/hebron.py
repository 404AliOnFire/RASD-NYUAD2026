"""
Hebron city sensor data simulator for RASD demo.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from rasd_ai.config.settings import SETTINGS
from rasd_ai.data.schemas import PROFILES


@dataclass
class HebronSimConfig:
    """Configuration for Hebron city simulation."""

    n_tanks: int = SETTINGS.DEFAULT_N_TANKS
    days: int = SETTINGS.DEFAULT_DAYS
    freq_min: int = SETTINGS.DEFAULT_FREQ_MIN
    seed: int = SETTINGS.DEFAULT_SEED
    share_A: float = SETTINGS.SHARE_PROFILE_A
    share_B: float = SETTINGS.SHARE_PROFILE_B
    share_C: float = SETTINGS.SHARE_PROFILE_C


class HebronCitySimulator:
    """
    Urban Hebron-like mock data generator for 3 sensors.

    Generates columns: timestamp, tank_id, profile, level_pct, gas, temp_c, hum_pct
    """

    def __init__(self, cfg: HebronSimConfig):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)

    def _assign_profiles(self):
        """Assign tank profiles based on configured shares."""
        n = self.cfg.n_tanks
        a = int(round(n * self.cfg.share_A))
        b = int(round(n * self.cfg.share_B))
        c = max(n - a - b, 0)
        tags = ["A"] * a + ["B"] * b + ["C"] * c
        self.rng.shuffle(tags)
        return tags

    def generate(self) -> pd.DataFrame:
        """
        Generate simulated sensor data for all tanks.

        Returns:
            DataFrame with sensor readings for all tanks over the simulation period
        """
        periods = int((self.cfg.days * 24 * 60) / self.cfg.freq_min)
        ts = pd.date_range("2026-01-01", periods=periods, freq=f"{self.cfg.freq_min}min")
        tags = self._assign_profiles()

        rows = []
        for tank_id in range(self.cfg.n_tanks):
            tag = tags[tank_id]
            p = PROFILES[tag]

            # Effective daily accumulation
            acc_l_day = p.people * p.liters_per_person_day * p.accumulation_ratio
            pct_per_day = (acc_l_day / p.capacity_liters) * 100.0
            steps_per_day = int((24 * 60) / self.cfg.freq_min)
            pct_per_step = pct_per_day / steps_per_day

            level = float(self.rng.uniform(5, 55))

            gas_base = float(self.rng.uniform(20, 60))
            k_gas = float(self.rng.uniform(0.35, 0.75))

            temp_base = float(self.rng.uniform(12, 26))
            hum_base = float(self.rng.uniform(35, 65))

            # Two hazard events per tank
            hazard_days = self.rng.choice(np.arange(3, self.cfg.days - 2), size=2, replace=False)
            hazard_idx = set()
            for d in hazard_days:
                start = int(d * steps_per_day)
                hazard_idx.update(range(start, start + int((6 * 60) / self.cfg.freq_min)))

            for i, t in enumerate(ts):
                hour = t.hour
                dow = t.dayofweek

                # City pattern: morning + evening peaks
                peak = 0.0
                if hour in [6, 7, 8]:
                    peak += 0.45
                if hour in [19, 20, 21, 22]:
                    peak += 0.55

                # Weekend effect (Fri/Sat)
                weekend = 0.20 if dow in [4, 5] else 0.0
                mult = 1.0 + peak + weekend

                # Level increases slowly + noise
                level += pct_per_step * mult + self.rng.normal(0, 0.08)
                level = float(np.clip(level, 0, 100))

                # Gas correlated with level + noise
                gas = gas_base + (k_gas * level * 10) + self.rng.normal(0, 6)
                if i in hazard_idx:
                    gas += float(self.rng.uniform(80, 220))

                # DHT22 sensor cycles
                temp = temp_base + 4.0 * np.sin(2 * np.pi * (hour / 24.0)) + self.rng.normal(0, 0.7)
                hum = hum_base + 7.0 * np.cos(2 * np.pi * (hour / 24.0)) + self.rng.normal(0, 2.0)
                hum = float(np.clip(hum, 0, 100))

                rows.append(
                    {
                        "timestamp": t,
                        "tank_id": tank_id,
                        "profile": tag,
                        "level_pct": level,
                        "gas": float(max(gas, 0)),
                        "temp_c": float(temp),
                        "hum_pct": hum,
                    }
                )

        return pd.DataFrame(rows)
