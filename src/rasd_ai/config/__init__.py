"""
RASD Configuration Module.

Provides centralized configuration for paths, settings, and constants.
"""

from rasd_ai.config.paths import PathConfig, PROJECT_ROOT, OUTPUTS_DIR
from rasd_ai.config.settings import RasdSettings

# Create default instances
PATHS = PathConfig()
SETTINGS = RasdSettings()

__all__ = [
    "PATHS",
    "PROJECT_ROOT",
    "OUTPUTS_DIR",
    "SETTINGS",
    "PathConfig",
    "RasdSettings",
]
