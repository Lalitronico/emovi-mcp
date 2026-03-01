"""Input validation utilities."""

from __future__ import annotations

import pandas as pd


def validate_column(df: pd.DataFrame, col: str) -> None:
    """Raise ValueError if *col* is not in *df*."""
    if col not in df.columns:
        raise ValueError(
            f"Column {col!r} not found. Available columns (first 30): "
            f"{', '.join(df.columns[:30])}"
        )


def validate_columns(df: pd.DataFrame, cols: list[str]) -> None:
    """Raise ValueError if any column in *cols* is missing."""
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Columns not found: {', '.join(missing)}")


def apply_filter(df: pd.DataFrame, filter_expr: str | None) -> pd.DataFrame:
    """Apply a pandas query expression to filter rows.

    Returns the original df if filter_expr is None or empty.
    """
    if not filter_expr:
        return df
    try:
        return df.query(filter_expr)
    except Exception as exc:
        raise ValueError(
            f"Invalid filter expression: {filter_expr!r}. Error: {exc}"
        ) from exc
