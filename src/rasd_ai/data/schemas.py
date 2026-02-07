"""
Data schemas and types for RASD project.
"""

from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class NodeRecord:
    """A node in the routing network (pit or depot)."""

    node_id: Union[int, str]
    lat: float
    lon: float
    zone: str = "center"


@dataclass
class PriorityRecord:
    """Priority and risk data for a tank."""

    tank_id: int
    profile: str
    level_pct: float
    tto_hours: float
    priority: float
    tier: str
    gas_now: float
    temp_c: float
    hum_pct: float
    base: float
    gas_anom: float
    env_anom: float


@dataclass
class TruckConfig:
    """Truck configuration for routing."""

    truck_id: int
    capacity: float
    shift_min: float
    type: str = "medium"


@dataclass
class RouteData:
    """Route data for a truck."""

    truck_id: str
    sequence: List[Union[int, str]]
    served_pits: List[int]
    capacity: float
    shift_min: float
    truck_type: str = ""


@dataclass
class RouteSummary:
    """Summary metrics for a route."""

    truck_id: str
    stops_count: int
    distance_km: float
    fuel_l: float
    co2_kg: float
    fuel_cost_usd: float
    eta_min: float


@dataclass
class MetricsRecord:
    """Metrics for a solution (baseline or quantum)."""

    served_total: int
    missed_total: int
    high_total: int
    high_served: int
    high_missed: int
    medium_total: int
    medium_served: int
    medium_missed: int = 0
    low_total: int = 0
    low_served: int = 0
    low_missed: int = 0
    total_travel_min: float = 0.0
    total_service_min: float = 0.0
    total_penalty: float = 0.0
    total_distance_km: float = 0.0
    fuel_l_est: float = 0.0
    co2_kg_est: float = 0.0
    solver_used: Optional[str] = None


@dataclass
class TankProfile:
    """Tank profile configuration."""

    name: str
    people: int
    liters_per_person_day: float
    accumulation_ratio: float
    capacity_liters: int


# Profile definitions
PROFILES = {
    "A": TankProfile("House-Conservative", 5, 25, 0.30, 2500),
    "B": TankProfile("House-Moderate", 6, 35, 0.35, 2500),
    "C": TankProfile("Building", 20, 35, 0.45, 8000),
}
