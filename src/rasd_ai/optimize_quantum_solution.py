"""
Legacy quantum solution evaluator.

This module is deprecated. Use rasd_ai.optimization.quantum_anneal instead.
"""

import json

import numpy as np
import pandas as pd

from rasd_ai.config.paths import PATHS


def evaluate_quantum_solution() -> dict:
    """
    Evaluate quantum solution metrics.

    Returns:
        dict: Metrics including travel time, coverage, and priority stats.
    """
    routes = json.loads(PATHS.quantum_routes_json.read_text(encoding="utf-8"))

    priorities_df = pd.read_csv(PATHS.priorities_csv)
    high_pits = set(priorities_df[priorities_df["tier"] == "HIGH"]["tank_id"])

    travel_matrix = np.load(PATHS.travel_time_matrix_npy)

    total_travel = 0.0
    served = set()

    for _truck_id, info in routes.items():
        pits = info.get("assigned_pits", [])
        for i in range(len(pits) - 1):
            total_travel += travel_matrix[pits[i]][pits[i + 1]]
        served.update(pits)

    high_served = len(served & high_pits)

    metrics = {
        "total_travel_min": round(float(total_travel), 2),
        "served_total": len(served),
        "high_total": len(high_pits),
        "high_served": high_served,
        "high_missed": len(high_pits) - high_served,
    }

    PATHS.quantum_metrics_json.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("quantum_metrics.json updated with operational KPIs")
    return metrics


if __name__ == "__main__":
    evaluate_quantum_solution()
