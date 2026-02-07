"""
Centralized path configuration for RASD project.
All paths use pathlib.Path and are resolved relative to project root.
"""

from pathlib import Path

# Project root is 3 levels up from this file:
# src/rasd_ai/config/paths.py -> src/rasd_ai/config -> src/rasd_ai -> src -> PROJECT_ROOT
# But we want outputs to be under src/rasd_ai/outputs for consistency
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # RASD_NYUAD/
RASD_AI_ROOT = Path(__file__).resolve().parents[1]  # src/rasd_ai/

# Main output directory - all generated files go here
OUTPUTS_DIR = RASD_AI_ROOT / "outputs"

# Frontend public data directory (for copying outputs)
FRONTEND_DATA_DIR = RASD_AI_ROOT / "frontend" / "public" / "data"
FRONTEND_LOGO_DIR = RASD_AI_ROOT / "frontend" / "public" / "logo"

# Logo directory
LOGO_DIR = RASD_AI_ROOT / "logo"


class PathConfig:
    """Centralized path configuration for all RASD modules."""

    def __init__(self, outputs_dir: Path = OUTPUTS_DIR):
        """
        Initialize path configuration.

        Args:
            outputs_dir: Base directory for output files.
        """
        self.outputs = outputs_dir
        self.outputs.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────
    # Data files (inputs/outputs)
    # ─────────────────────────────────────────────
    @property
    def mock_data_csv(self) -> Path:
        """Path to mock sensor data CSV."""
        return self.outputs / "mock_hebron.csv"

    @property
    def priorities_csv(self) -> Path:
        """Path to priorities CSV."""
        return self.outputs / "priorities.csv"

    @property
    def routing_pits_csv(self) -> Path:
        """Path to routing pits CSV."""
        return self.outputs / "routing_pits.csv"

    # ─────────────────────────────────────────────
    # JSON files
    # ─────────────────────────────────────────────
    @property
    def nodes_json(self) -> Path:
        """Path to nodes JSON."""
        return self.outputs / "nodes.json"

    @property
    def trucks_json(self) -> Path:
        """Path to trucks configuration JSON."""
        return self.outputs / "trucks.json"

    @property
    def closures_json(self) -> Path:
        """Path to road closures JSON."""
        return self.outputs / "closures.json"

    @property
    def baseline_routes_json(self) -> Path:
        """Path to baseline routes JSON."""
        return self.outputs / "baseline_routes.json"

    @property
    def baseline_metrics_json(self) -> Path:
        """Path to baseline metrics JSON."""
        return self.outputs / "baseline_metrics.json"

    @property
    def quantum_routes_json(self) -> Path:
        """Path to quantum routes JSON."""
        return self.outputs / "quantum_routes.json"

    @property
    def quantum_metrics_json(self) -> Path:
        """Path to quantum metrics JSON."""
        return self.outputs / "quantum_metrics.json"

    @property
    def baseline_metrics_enriched_json(self) -> Path:
        """Path to enriched baseline metrics JSON."""
        return self.outputs / "baseline_metrics_enriched.json"

    @property
    def quantum_metrics_enriched_json(self) -> Path:
        """Path to enriched quantum metrics JSON."""
        return self.outputs / "quantum_metrics_enriched.json"

    @property
    def routes_for_frontend_json(self) -> Path:
        """Path to frontend routes JSON."""
        return self.outputs / "routes_for_frontend.json"

    # ─────────────────────────────────────────────
    # Numpy files
    # ─────────────────────────────────────────────
    @property
    def travel_time_matrix_npy(self) -> Path:
        """Path to travel time matrix numpy file."""
        return self.outputs / "travel_time_matrix.npy"

    # ─────────────────────────────────────────────
    # Visualization outputs
    # ─────────────────────────────────────────────
    @property
    def fig_routes_compare(self) -> Path:
        """Path to routes comparison figure."""
        return self.outputs / "fig_routes_compare.png"

    @property
    def fig_tier_coverage(self) -> Path:
        """Path to tier coverage figure."""
        return self.outputs / "fig_tier_coverage.png"

    @property
    def fig_workload_balance(self) -> Path:
        """Path to workload balance figure."""
        return self.outputs / "fig_workload_balance.png"

    @property
    def fig_workload(self) -> Path:
        """Path to workload figure."""
        return self.outputs / "fig_workload.png"

    @property
    def fig_distance_and_served(self) -> Path:
        """Path to distance and served figure."""
        return self.outputs / "fig_distance_and_served.png"

    @property
    def fig_efficiency_vs_safety(self) -> Path:
        """Path to efficiency vs safety figure."""
        return self.outputs / "fig_efficiency_vs_safety.png"

    @property
    def fig_kpi_summary(self) -> Path:
        """Path to KPI summary figure."""
        return self.outputs / "fig_kpi_summary.png"

    @property
    def routes_compare(self) -> Path:
        """Path to routes comparison figure."""
        return self.outputs / "routes_compare.png"

    def viz_file(self, num: int, name: str) -> Path:
        """
        Generate path for numbered visualization file.

        Args:
            num: Visualization number.
            name: Visualization name.

        Returns:
            Path to the visualization file.
        """
        return self.outputs / f"viz_{num}_{name}.png"

    # ─────────────────────────────────────────────
    # Logo
    # ─────────────────────────────────────────────
    @property
    def logo_png(self) -> Path:
        """Path to RASD logo PNG."""
        return LOGO_DIR / "RASD.png"

    # ─────────────────────────────────────────────
    # Frontend paths
    # ─────────────────────────────────────────────
    @property
    def frontend_data(self) -> Path:
        """Path to frontend data directory."""
        return FRONTEND_DATA_DIR

    @property
    def frontend_logo(self) -> Path:
        """Path to frontend logo directory."""
        return FRONTEND_LOGO_DIR


# Default instance
PATHS = PathConfig()
