"""Apply human-readable labels to coded values."""

from __future__ import annotations

from typing import Any

import pandas as pd


def apply_value_labels(
    series: pd.Series,
    label_map: dict[int, str] | None = None,
) -> pd.Series:
    """Replace numeric codes with string labels.

    If label_map is None, returns the series unchanged.
    Values not in label_map keep their original value.
    """
    if not label_map:
        return series
    return series.map(lambda x: label_map.get(int(x), x) if pd.notna(x) else x)


def get_label_for_value(
    value: Any, label_map: dict[int, str] | None
) -> str:
    """Get label for a single value."""
    if label_map and pd.notna(value):
        return label_map.get(int(value), str(value))
    return str(value)
