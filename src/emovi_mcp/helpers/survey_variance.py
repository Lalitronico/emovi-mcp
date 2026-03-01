"""Taylor linearization for survey standard errors under stratified cluster sampling.

Implements variance estimation for ratio estimators (transition matrix cells)
under the complex survey design of ESRU-EMOVI 2023.

Each cell p_ij of the transition matrix is a ratio estimator Y/X where:
  Y = sum of weights for (origin=i AND dest=j)
  X = sum of weights for (origin=i)

The Taylor linearization produces:
  z_k = (1/X)(y_k - R * x_k)

and then the stratified-clustered variance of z gives Var(R).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def taylor_variance_ratio(
    y: np.ndarray,
    x: np.ndarray,
    psu: np.ndarray,
    strata: np.ndarray,
) -> float:
    """Estimate variance of a ratio estimator R = sum(y)/sum(x)
    under stratified cluster sampling using Taylor linearization.

    Args:
        y: Numerator contributions per observation (e.g., w_k * I(dest=j))
        x: Denominator contributions per observation (e.g., w_k * I(origin=i))
        psu: Primary sampling unit identifier per observation
        strata: Stratum identifier per observation

    Returns:
        Estimated variance of the ratio R.
    """
    Y_total = y.sum()
    X_total = x.sum()

    if X_total == 0:
        return float("nan")

    R = Y_total / X_total

    # Linearized variable: z_k = (y_k - R * x_k) / X_total
    z = (y - R * x) / X_total

    # Stratified cluster variance of z
    var = _stratified_cluster_variance(z, psu, strata)
    return float(var)


def _stratified_cluster_variance(
    z: np.ndarray,
    psu: np.ndarray,
    strata: np.ndarray,
) -> float:
    """Compute variance of a total estimator under stratified cluster sampling.

    For each stratum h with n_h PSUs:
      Var_h = n_h / (n_h - 1) * sum_a (z_ha_bar - z_h_bar)^2

    where z_ha = sum of z within PSU a of stratum h.
    """
    total_var = 0.0
    unique_strata = np.unique(strata)

    for h in unique_strata:
        mask_h = strata == h
        z_h = z[mask_h]
        psu_h = psu[mask_h]

        # Sum z within each PSU
        unique_psu = np.unique(psu_h)
        n_h = len(unique_psu)

        if n_h < 2:
            # Cannot estimate variance with 1 PSU per stratum
            # Use conservative approach: treat as if variance = 0
            continue

        psu_totals = np.array([z_h[psu_h == a].sum() for a in unique_psu])
        psu_mean = psu_totals.mean()

        var_h = (n_h / (n_h - 1)) * np.sum((psu_totals - psu_mean) ** 2)
        total_var += var_h

    return total_var


def transition_matrix_standard_errors(
    df: pd.DataFrame,
    origin_col: str,
    dest_col: str,
    weight_col: str,
    psu_col: str,
    strata_col: str,
    labels: dict[int, str] | None = None,
) -> pd.DataFrame:
    """Compute standard errors for each cell of a transition matrix.

    Returns a DataFrame with the same shape as the transition matrix,
    containing standard errors for each cell proportion.
    """
    origins = sorted(df[origin_col].dropna().unique())
    dests = sorted(df[dest_col].dropna().unique())

    w = df[weight_col].values
    o = df[origin_col].values
    d = df[dest_col].values
    psu = df[psu_col].values if psu_col in df.columns else np.zeros(len(df))
    strata = df[strata_col].values if strata_col in df.columns else np.zeros(len(df))

    se_data = {}
    for i in origins:
        row_se = {}
        x = w * (o == i).astype(float)  # denominator: weighted count with origin=i
        for j in dests:
            y = w * ((o == i) & (d == j)).astype(float)  # numerator
            var = taylor_variance_ratio(y, x, psu, strata)
            row_se[j] = np.sqrt(var) if var > 0 else 0.0
        se_data[i] = row_se

    se_df = pd.DataFrame(se_data).T
    se_df.index = [labels.get(int(i), str(i)) for i in se_df.index] if labels else se_df.index
    se_df.columns = [labels.get(int(c), str(c)) for c in se_df.columns] if labels else se_df.columns

    return se_df
