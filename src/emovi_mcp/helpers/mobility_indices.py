"""Formal mobility indices for transition matrices."""

from __future__ import annotations

import numpy as np
import pandas as pd


def shorrocks_m(matrix: pd.DataFrame) -> float:
    """Shorrocks Mobility Index: M = (n - trace(P)) / (n - 1).

    M=0 means perfect immobility (identity matrix).
    M=1 means maximum mobility (uniform transitions).
    """
    n = min(matrix.shape)
    if n <= 1:
        return 0.0
    trace = sum(matrix.iloc[i, i] for i in range(n))
    return float((n - trace) / (n - 1))


def prais_index(matrix: pd.DataFrame) -> dict[str, float]:
    """Prais Index: 1 - p_ii for each origin category.

    Returns a dict mapping row labels to escape probabilities.
    Higher values mean more mobility out of that category.
    """
    n = min(matrix.shape)
    result = {}
    for i in range(n):
        label = str(matrix.index[i])
        result[label] = float(1.0 - matrix.iloc[i, i])
    return result


def intergenerational_correlation(
    origin: pd.Series,
    dest: pd.Series,
    weights: pd.Series,
) -> float:
    """Weighted Pearson correlation between origin and destination.

    Higher absolute values indicate stronger intergenerational persistence.
    """
    valid = origin.notna() & dest.notna() & weights.notna()
    o = origin[valid].astype(float).values
    d = dest[valid].astype(float).values
    w = weights[valid].values

    if len(o) < 2 or w.sum() == 0:
        return float("nan")

    w_sum = w.sum()
    mean_o = np.average(o, weights=w)
    mean_d = np.average(d, weights=w)

    cov = np.sum(w * (o - mean_o) * (d - mean_d)) / w_sum
    var_o = np.sum(w * (o - mean_o) ** 2) / w_sum
    var_d = np.sum(w * (d - mean_d) ** 2) / w_sum

    denom = np.sqrt(var_o * var_d)
    if denom == 0:
        return float("nan")

    return float(cov / denom)


def corner_odds_ratios(matrix: pd.DataFrame) -> dict[str, float]:
    """Odds ratios from the four corners of the transition matrix.

    For an n×n matrix:
    - top_left: OR for staying in Q1 vs moving to Qn from Q1
    - bottom_right: OR for staying in Qn vs moving to Q1 from Qn
    - cross: (p11 * pnn) / (p1n * pn1)

    Higher values indicate stronger barriers at the extremes.
    """
    n = min(matrix.shape)
    if n < 2:
        return {"top_left": float("nan"), "bottom_right": float("nan"), "cross": float("nan")}

    p11 = matrix.iloc[0, 0]
    p1n = matrix.iloc[0, n - 1]
    pn1 = matrix.iloc[n - 1, 0]
    pnn = matrix.iloc[n - 1, n - 1]

    eps = 1e-10  # avoid division by zero

    top_left = float((p11 * (1 - p1n)) / (p1n * (1 - p11) + eps)) if p1n > eps else float("inf")
    bottom_right = float((pnn * (1 - pn1)) / (pn1 * (1 - pnn) + eps)) if pn1 > eps else float("inf")
    cross = float((p11 * pnn) / (p1n * pn1 + eps))

    return {
        "top_left": top_left,
        "bottom_right": bottom_right,
        "cross": cross,
    }


def compute_all_indices(
    matrix: pd.DataFrame,
    df: pd.DataFrame,
    weight_col: str,
) -> dict:
    """Compute all mobility indices for a transition matrix.

    Returns a dict with keys that can be merged into the summary.
    """
    result: dict = {}

    result["shorrocks_m"] = shorrocks_m(matrix)
    result["prais_index"] = prais_index(matrix)

    # Intergenerational correlation requires raw data
    if "_origin" in df.columns and "_dest" in df.columns:
        result["intergenerational_r"] = intergenerational_correlation(
            df["_origin"], df["_dest"], df[weight_col]
        )

    result["corner_odds_ratios"] = corner_odds_ratios(matrix)

    return result
