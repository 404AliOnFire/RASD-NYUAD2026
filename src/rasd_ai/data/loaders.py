"""
Data loading utilities for RASD project.
"""

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd


def load_json(path: Path) -> Any:
    """Load JSON file and return parsed data."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj: Any, indent: int = 2) -> None:
    """Save object to JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=indent, ensure_ascii=False), encoding="utf-8")


def load_csv(path: Path) -> pd.DataFrame:
    """Load CSV file into DataFrame."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    return pd.read_csv(path)


def save_csv(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    """Save DataFrame to CSV file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)


def load_numpy(path: Path) -> np.ndarray:
    """Load numpy array from file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Numpy file not found: {path}")
    return np.load(path)


def save_numpy(path: Path, arr: np.ndarray) -> None:
    """Save numpy array to file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, arr)


def load_json_safe(path: Path, default: Any = None) -> Optional[Any]:
    """Load JSON file, return default if not found."""
    try:
        return load_json(path)
    except FileNotFoundError:
        return default


def load_csv_safe(path: Path, default: Optional[pd.DataFrame] = None) -> Optional[pd.DataFrame]:
    """Load CSV file, return default if not found."""
    try:
        return load_csv(path)
    except FileNotFoundError:
        return default
