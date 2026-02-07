"""
Settings and constants for RASD project.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RasdSettings:
    """Immutable configuration settings for RASD pipeline."""

    # ─────────────────────────────────────────────
    # Fuel and emissions
    # ─────────────────────────────────────────────
    FUEL_L_PER_KM: float = 0.35
    CO2_KG_PER_L: float = 2.68
    FUEL_COST_USD_PER_L: float = 1.80

    # ─────────────────────────────────────────────
    # Speed and travel
    # ─────────────────────────────────────────────
    BASE_SPEED_KMH: float = 25.0
    SERVICE_TIME_MIN_PER_STOP: float = 10.0

    # ─────────────────────────────────────────────
    # Thresholds
    # ─────────────────────────────────────────────
    OVERFLOW_THRESHOLD_PCT: float = 100.0
    HIGH_PRIORITY_THRESHOLD: float = 0.75
    MEDIUM_PRIORITY_THRESHOLD: float = 0.45
    TTO_CRITICAL_HOURS: float = 24.0

    # ─────────────────────────────────────────────
    # Simulation defaults
    # ─────────────────────────────────────────────
    DEFAULT_N_TANKS: int = 20
    DEFAULT_DAYS: int = 30
    DEFAULT_FREQ_MIN: int = 15
    DEFAULT_SEED: int = 7

    # ─────────────────────────────────────────────
    # Forecasting
    # ─────────────────────────────────────────────
    FORECAST_HORIZON_HOURS: int = 72
    ANOMALY_WINDOW_HOURS: int = 48

    # ─────────────────────────────────────────────
    # Risk fusion weights
    # ─────────────────────────────────────────────
    RISK_WEIGHT_GAS: float = 0.20
    RISK_WEIGHT_ENV: float = 0.10
    RISK_Z_START: float = 2.0
    RISK_Z_SCALE: float = 1.0

    # ─────────────────────────────────────────────
    # Routing
    # ─────────────────────────────────────────────
    TOP_N_PITS: int = 30
    N_TRUCKS: int = 4
    SHIFT_DURATION_MIN: int = 480
    CLOSURE_FRACTION: float = 0.03
    SAFETY_MARGIN_MIN: int = 90

    # ─────────────────────────────────────────────
    # Quantum solver
    # ─────────────────────────────────────────────
    QUANTUM_TOP_N: int = 10
    QUANTUM_MAX_TRUCKS: int = 2
    QUANTUM_NUM_READS: int = 3000

    # ─────────────────────────────────────────────
    # Hebron bounding box
    # ─────────────────────────────────────────────
    HEBRON_LAT_MIN: float = 31.505
    HEBRON_LAT_MAX: float = 31.555
    HEBRON_LON_MIN: float = 35.070
    HEBRON_LON_MAX: float = 35.120

    # ─────────────────────────────────────────────
    # Penalty settings (for baseline optimizer)
    # ─────────────────────────────────────────────
    PENALTY_PER_MIN_HIGH: int = 80
    PENALTY_PER_MIN_MEDIUM: int = 25
    PENALTY_PER_MIN_LOW: int = 8
    UNSERVED_PENALTY_HIGH: int = 6000
    UNSERVED_PENALTY_MEDIUM: int = 1500
    UNSERVED_PENALTY_LOW: int = 300

    # ─────────────────────────────────────────────
    # Profile configurations
    # ─────────────────────────────────────────────
    SHARE_PROFILE_A: float = 0.45
    SHARE_PROFILE_B: float = 0.45
    SHARE_PROFILE_C: float = 0.10

    def get_penalty_per_min(self, tier: str) -> int:
        """Get penalty per minute for a given tier."""
        tier = str(tier).upper()
        if tier == "HIGH":
            return self.PENALTY_PER_MIN_HIGH
        if tier == "MEDIUM":
            return self.PENALTY_PER_MIN_MEDIUM
        return self.PENALTY_PER_MIN_LOW

    def get_unserved_penalty(self, tier: str) -> int:
        """Get unserved penalty for a given tier."""
        tier = str(tier).upper()
        if tier == "HIGH":
            return self.UNSERVED_PENALTY_HIGH
        if tier == "MEDIUM":
            return self.UNSERVED_PENALTY_MEDIUM
        return self.UNSERVED_PENALTY_LOW

    def compute_tier(self, priority: float, tto_hours: float = 999.0) -> str:
        """Compute tier from priority score and TTO."""
        if tto_hours <= self.TTO_CRITICAL_HOURS or priority >= self.HIGH_PRIORITY_THRESHOLD:
            return "HIGH"
        if priority >= self.MEDIUM_PRIORITY_THRESHOLD:
            return "MEDIUM"
        return "LOW"


# Default settings instance
SETTINGS = RasdSettings()
