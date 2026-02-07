#!/usr/bin/env python
"""
Quick smoke test for the refactored RASD modules.

This script tests all module imports to verify the package structure is correct.
"""

# pylint: disable=broad-exception-caught,unused-import,import-outside-toplevel

import sys
from pathlib import Path

# Add src directory to path for IDE compatibility
# This file is at: src/rasd_ai/test_imports.py
# We need to add: src/ to sys.path
_this_file = Path(__file__).resolve()
_rasd_ai_dir = _this_file.parent  # src/rasd_ai
_src_dir = _rasd_ai_dir.parent  # src

if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))


def run_import_tests() -> None:
    """Run all import tests and report results."""
    print("Python:", sys.executable)
    print("Version:", sys.version)
    print("Added to path:", _src_dir)

    print("\n--- Testing imports ---")

    try:
        from rasd_ai.config.paths import PATHS, PROJECT_ROOT, OUTPUTS_DIR

        print("✅ config.paths imported")
        print(f"   PROJECT_ROOT: {PROJECT_ROOT}")
        print(f"   OUTPUTS_DIR: {OUTPUTS_DIR}")
    except ImportError as err:
        print(f"❌ config.paths failed: {err}")

    try:
        from rasd_ai.config.settings import SETTINGS

        print("✅ config.settings imported")
        print(f"   DEFAULT_N_TANKS: {SETTINGS.DEFAULT_N_TANKS}")
    except ImportError as err:
        print(f"❌ config.settings failed: {err}")

    try:
        from rasd_ai.data.loaders import load_json, save_json, load_csv

        print("✅ data.loaders imported")
    except ImportError as err:
        print(f"❌ data.loaders failed: {err}")

    try:
        from rasd_ai.simulation.hebron import HebronCitySimulator, HebronSimConfig

        print("✅ simulation.hebron imported")
    except ImportError as err:
        print(f"❌ simulation.hebron failed: {err}")

    try:
        from rasd_ai.forecasting.prophet_model import ProphetForecaster

        print("✅ forecasting.prophet_model imported")
    except ImportError as err:
        print(f"❌ forecasting.prophet_model failed: {err}")

    try:
        from rasd_ai.risk.fusion import RiskFusionEngine

        print("✅ risk.fusion imported")
    except ImportError as err:
        print(f"❌ risk.fusion failed: {err}")

    try:
        from rasd_ai.optimization.routing_inputs import generate_routing_inputs

        print("✅ optimization.routing_inputs imported")
    except ImportError as err:
        print(f"❌ optimization.routing_inputs failed: {err}")

    try:
        from rasd_ai.optimization.baseline_greedy import build_baseline_routes

        print("✅ optimization.baseline_greedy imported")
    except ImportError as err:
        print(f"❌ optimization.baseline_greedy failed: {err}")

    try:
        from rasd_ai.optimization.quantum_anneal import solve_quantum_annealing

        print("✅ optimization.quantum_anneal imported")
    except ImportError as err:
        print(f"❌ optimization.quantum_anneal failed: {err}")

    try:
        from rasd_ai.viz.plots import generate_all_visualizations

        print("✅ viz.plots imported")
    except ImportError as err:
        print(f"❌ viz.plots failed: {err}")

    try:
        from rasd_ai.exporters.frontend import build_routes_for_frontend

        print("✅ exporters.frontend imported")
    except ImportError as err:
        print(f"❌ exporters.frontend failed: {err}")

    print("\n--- Import test complete ---")


if __name__ == "__main__":
    run_import_tests()
