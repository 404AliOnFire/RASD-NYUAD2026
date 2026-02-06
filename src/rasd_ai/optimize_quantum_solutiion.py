import json
import numpy as np

def evaluate_quantum_solution():
    with open("outputs/quantum_routes.json") as f:
        routes = json.load(f)

    with open("outputs/priorities.csv") as f:
        import pandas as pd
        pr = pd.read_csv(f)
        high_pits = set(pr[pr["tier"] == "HIGH"]["tank_id"])

    travel_matrix = np.load("outputs/travel_time_matrix.npy")

    total_travel = 0.0
    served = set()

    for truck_id, info in routes.items():
        pits = info.get("assigned_pits", [])
        for i in range(len(pits) - 1):
            total_travel += travel_matrix[pits[i]][pits[i+1]]
        served.update(pits)

    high_served = len(served & high_pits)

    metrics = {
        "total_travel_min": round(float(total_travel), 2),
        "served_total": len(served),
        "high_total": len(high_pits),
        "high_served": high_served,
        "high_missed": len(high_pits) - high_served
    }

    with open("outputs/quantum_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("quantum_metrics.json updated with operational KPIs")

if __name__ == "__main__":
    evaluate_quantum_solution()
