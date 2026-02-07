"""
Optimization Module for RASD.

Provides route optimization algorithms including baseline greedy and quantum annealing.
"""

from rasd_ai.optimization.baseline_greedy import build_baseline_routes
from rasd_ai.optimization.quantum_anneal import solve_quantum_annealing
from rasd_ai.optimization.routing_inputs import generate_routing_inputs
from rasd_ai.optimization.metrics import compute_route_metrics

__all__ = [
    "build_baseline_routes",
    "solve_quantum_annealing",
    "generate_routing_inputs",
    "compute_route_metrics",
]
