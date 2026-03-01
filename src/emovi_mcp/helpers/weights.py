"""Weighted statistics utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Compute weighted mean, dropping NaN pairs."""
    mask = values.notna() & weights.notna()
    v, w = values[mask].to_numpy(), weights[mask].to_numpy()
    if len(v) == 0:
        return float("nan")
    return float(np.average(v, weights=w))


def weighted_median(values: pd.Series, weights: pd.Series) -> float:
    """Compute weighted median."""
    return weighted_quantile(values, weights, 0.5)


def weighted_quantile(
    values: pd.Series, weights: pd.Series, q: float
) -> float:
    """Compute weighted quantile using linear interpolation."""
    mask = values.notna() & weights.notna()
    v = values[mask].to_numpy()
    w = weights[mask].to_numpy()
    if len(v) == 0:
        return float("nan")

    order = np.argsort(v)
    v, w = v[order], w[order]
    cum_w = np.cumsum(w)
    total = cum_w[-1]
    # Normalize to [0, 1]
    cum_pct = (cum_w - w / 2) / total
    return float(np.interp(q, cum_pct, v))


def weighted_std(values: pd.Series, weights: pd.Series) -> float:
    """Compute weighted standard deviation."""
    mask = values.notna() & weights.notna()
    v, w = values[mask].to_numpy(), weights[mask].to_numpy()
    if len(v) == 0:
        return float("nan")
    avg = np.average(v, weights=w)
    variance = np.average((v - avg) ** 2, weights=w)
    return float(np.sqrt(variance))


def weighted_frequency(
    series: pd.Series, weights: pd.Series
) -> pd.DataFrame:
    """Weighted frequency table: value, count (unweighted), proportion (weighted).

    Returns proportions, NOT raw weighted counts (per CEEY methodology).
    """
    mask = series.notna() & weights.notna()
    s, w = series[mask], weights[mask]

    groups = s.groupby(s)
    unweighted_n = groups.size()
    weighted_sum = w.groupby(s).sum()
    total_weight = weighted_sum.sum()

    result = pd.DataFrame({
        "value": unweighted_n.index,
        "n": unweighted_n.values,
        "proportion": (weighted_sum / total_weight).values,
    })
    return result.sort_values("value").reset_index(drop=True)


def create_weighted_quintiles(
    values: pd.Series, weights: pd.Series, nq: int = 5
) -> pd.Series:
    """Create weighted quintile assignments (replicates Stata xtile ... [pw=], nq(5))."""
    mask = values.notna() & weights.notna()
    result = pd.Series(np.nan, index=values.index)

    v = values[mask].to_numpy()
    w = weights[mask].to_numpy()
    order = np.argsort(v)
    v_sorted, w_sorted = v[order], w[order]
    cum_w = np.cumsum(w_sorted)
    total = cum_w[-1]

    # Find breakpoints
    breaks = []
    for i in range(1, nq):
        target = total * i / nq
        idx = np.searchsorted(cum_w, target)
        idx = min(idx, len(v_sorted) - 1)
        breaks.append(v_sorted[idx])

    # Assign quintiles
    quintiles = np.digitize(values[mask].to_numpy(), breaks, right=True) + 1
    result[mask] = quintiles
    return result
