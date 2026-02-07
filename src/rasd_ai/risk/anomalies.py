"""
Anomaly detection utilities for risk assessment.
"""

import numpy as np


def sigmoid(x: float) -> float:
    """Standard sigmoid function."""
    return 1.0 / (1.0 + np.exp(-x))


def robust_z(x_now: float, history: np.ndarray, eps: float = 1e-6) -> float:
    """
    Compute robust Z-score using median absolute deviation.

    Args:
        x_now: Current value
        history: Historical values for comparison
        eps: Small epsilon to avoid division by zero

    Returns:
        Robust Z-score
    """
    h = np.asarray(history, dtype=float)
    med = np.median(h)
    mad = np.median(np.abs(h - med)) + eps
    return (x_now - med) / mad


def clamp01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    return float(np.clip(x, 0.0, 1.0))
