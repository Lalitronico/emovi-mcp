"""Load .dta files with pyreadstat, cache in memory, expose metadata."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat

from emovi_mcp.config import DATASETS, DTA_READ_OPTIONS, get_data_dir

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

_cache: dict[str, dict[str, Any]] = {}


def _find_file(filename: str, data_dir: Path) -> Path:
    """Find a .dta file, searching recursively if needed."""
    direct = data_dir / filename
    if direct.is_file():
        return direct
    # Recursive search
    matches = list(data_dir.rglob(filename))
    if matches:
        return matches[0]
    raise FileNotFoundError(
        f"Cannot find {filename!r} in {data_dir} (searched recursively)"
    )


def load_dataset(name: str) -> dict[str, Any]:
    """Load a dataset by logical name. Returns cached result if available.

    Returns dict with keys:
      - df: pandas DataFrame
      - meta: pyreadstat metadata object
      - variable_labels: dict[str, str]
      - value_labels: dict[str, dict[int, str]]
    """
    if name in _cache:
        return _cache[name]

    if name not in DATASETS:
        available = ", ".join(sorted(DATASETS.keys()))
        raise ValueError(f"Unknown dataset {name!r}. Available: {available}")

    info = DATASETS[name]
    data_dir = get_data_dir()
    path = _find_file(info["filename"], data_dir)

    logger.info("Loading %s from %s", name, path)
    df, meta = pyreadstat.read_dta(
        str(path),
        apply_value_formats=DTA_READ_OPTIONS["apply_value_formats"],
    )

    result = {
        "df": df,
        "meta": meta,
        "variable_labels": dict(
            zip(meta.column_names, meta.column_labels)
        ) if meta.column_labels else {},
        "value_labels": meta.value_labels if meta.value_labels else {},
    }
    _cache[name] = result
    logger.info(
        "Loaded %s: %d rows x %d cols", name, len(df), len(df.columns)
    )
    return result


def get_dataframe(name: str = "entrevistado") -> pd.DataFrame:
    """Convenience: return just the DataFrame."""
    return load_dataset(name)["df"]


def get_metadata(name: str = "entrevistado") -> dict[str, Any]:
    """Return variable_labels and value_labels for a dataset."""
    data = load_dataset(name)
    return {
        "variable_labels": data["variable_labels"],
        "value_labels": data["value_labels"],
    }


def list_datasets() -> dict[str, dict]:
    """Return info about all available datasets."""
    return {k: {kk: vv for kk, vv in v.items() if kk != "filename"}
            for k, v in DATASETS.items()}


def clear_cache() -> None:
    """Clear the in-memory cache (useful for testing)."""
    _cache.clear()
