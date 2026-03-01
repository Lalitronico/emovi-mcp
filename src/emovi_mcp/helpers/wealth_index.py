"""Wealth index construction via PCA on household asset indicators.

Replicates CEEY methodology (.do lines 265-398) using PCA instead of MCA.
The CEEY uses Multiple Correspondence Analysis (MCA) with Burt method on
binary asset indicators by cohort. PCA on binary indicators is the standard
alternative (Filmer & Pritchett, 2001) and produces very similar rankings.

Variable mapping (.do -> actual data):
    ORIGIN (age 14):
        p31a-o  -> household goods (stove, washer, fridge, phone, TV, etc.)
        p32a-e  -> property/financial assets (house, land, savings, etc.)
        p26a,b,d,e -> basic services (water, electricity, boiler, domestic)
        p30     -> automobiles (count, recoded to binary)
        p22/p24 -> overcrowding (household_size / sleeping_rooms <= 2.5)

    CURRENT:
        p96a-r  -> household goods
        p97a-n  -> property/financial assets
        p95a,b,d,e -> basic services
        p99     -> automobiles (count, recoded to binary)
        tamhog/p89 -> overcrowding
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Asset variable definitions
# ---------------------------------------------------------------------------

# Origin household assets at age 14 (maps to .do ac_or1-ac_or19 + hac_or)
ORIGIN_ASSET_VARS: list[str] = [
    "p31a",   # ac_or1:  Estufa
    "p31b",   # ac_or3:  Lavadora
    "p31c",   # ac_or5:  Refrigerador
    "p31d",   # ac_or8:  Telefono fijo
    "p31e",   # ac_or7:  Television
    "p31f",   # (extra): Tostador
    "p31g",   # ac_or14: Aspiradora
    "p31h",   # ac_or4:  TV de cable
    "p31i",   # ac_or12: Microondas
    "p31j",   # (extra): Celular
    "p31k",   # ac_or9:  Computadora
    "p31l",   # (extra): Internet
    "p31m",   # ac_or11: VHS/DVD
    "p31n",   # (extra): Motocicleta
    "p31o",   # (extra): Bicicleta
]

ORIGIN_PROPERTY_VARS: list[str] = [
    "p32a",   # ac_or2:  Otra vivienda
    "p32b",   # ac_or13: Local comercial
    "p32c",   # (extra): Terreno
    "p32d",   # (extra): Animales de trabajo
    "p32e",   # ac_or17: Cuenta de ahorro
]

ORIGIN_SERVICE_VARS: list[str] = [
    "p26a",   # ac_or6:  Agua entubada
    "p26b",   # ac_or10: Electricidad
    "p26d",   # ac_or16: Boiler
    "p26e",   # ac_or19: Servicio domestico
]

# Current household assets (maps to .do ac1-ac16 + hac)
CURRENT_ASSET_VARS: list[str] = [
    "p96a",   # ac10: Estufa
    "p96b",   # ac3:  Lavadora
    "p96c",   # (extra): Refrigerador
    "p96d",   # ac8:  Microondas
    "p96e",   # (extra): TV digital
    "p96f",   # (extra): Tostador
    "p96g",   # (extra): Consola videojuegos
    "p96h",   # (extra): Aspiradora
    "p96i",   # ac7:  TV de paga
    "p96j",   # (extra): Telefono fijo
    "p96k",   # (extra): Celular
    "p96l",   # ac4:  Internet
    "p96m",   # (extra): Tableta
    "p96n",   # ac1:  Computadora
    "p96o",   # ac11: Maquinaria agricola
    "p96p",   # (extra): Animales de trabajo
    "p96q",   # (extra): Motocicleta
    "p96r",   # (extra): Bicicleta
]

CURRENT_PROPERTY_VARS: list[str] = [
    "p97a",   # ac14: Otra vivienda
    "p97b",   # ac15: Local comercial
    "p97c",   # ac16: Terreno
    "p97d",   # (extra): Cuenta bancaria
    "p97e",   # ac13: Tarjeta de credito bancaria
    "p97f",   # (extra): Tarjeta de credito tienda
]

CURRENT_SERVICE_VARS: list[str] = [
    "p95a",   # ac5:  Agua entubada
    "p95b",   # (extra): Electricidad
    "p95d",   # ac2:  Boiler
    "p95e",   # ac12: Servicio domestico
]


# ---------------------------------------------------------------------------
# Recoding helpers
# ---------------------------------------------------------------------------

def _recode_binary(series: pd.Series) -> pd.Series:
    """Recode survey binary (1=Yes, 2=No, 8/9=NS) to numeric (1, 0, NaN)."""
    return series.map({1: 1.0, 2: 0.0}).where(series.isin([1, 2]))


def _recode_count_to_binary(series: pd.Series) -> pd.Series:
    """Recode count variable to binary (0 -> 0, 1+ -> 1)."""
    result = pd.Series(np.nan, index=series.index)
    valid = series.notna() & (series >= 0)
    result[valid] = (series[valid] > 0).astype(float)
    return result


def _build_overcrowding(hh_size: pd.Series, rooms: pd.Series) -> pd.Series:
    """Build overcrowding indicator: 1 if persons/rooms <= 2.5, else 0."""
    valid = hh_size.notna() & rooms.notna() & (rooms > 0)
    result = pd.Series(np.nan, index=hh_size.index)
    ratio = hh_size[valid] / rooms[valid]
    result[valid] = (ratio <= 2.5).astype(float)
    return result


# ---------------------------------------------------------------------------
# PCA-based index
# ---------------------------------------------------------------------------

def _pca_first_component(X: np.ndarray) -> np.ndarray:
    """Extract first principal component from a matrix of binary indicators.

    Uses eigendecomposition of the correlation matrix.
    Handles missing values by mean-imputing within each column.
    Ensures positive orientation: higher score = more assets (positive
    correlation with the sum of indicators).

    Returns the scores (projections onto first PC).
    """
    # Mean-impute missing values column-wise
    col_means = np.nanmean(X, axis=0)
    inds = np.where(np.isnan(X))
    X_filled = X.copy()
    X_filled[inds] = np.take(col_means, inds[1])

    # Standardize (zero mean, unit variance)
    means = X_filled.mean(axis=0)
    stds = X_filled.std(axis=0)

    # Drop constant columns (zero variance) before PCA
    varying = stds > 0
    if varying.sum() < 2:
        # Not enough varying columns for meaningful PCA
        return np.zeros(X.shape[0])

    X_var = X_filled[:, varying]
    means_var = means[varying]
    stds_var = stds[varying]
    Z = (X_var - means_var) / stds_var

    # Correlation matrix eigendecomposition
    corr = np.corrcoef(Z, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(corr)

    # eigh returns in ascending order; take the last (largest)
    first_pc = eigenvectors[:, -1]
    scores = Z @ first_pc

    # Ensure positive orientation: scores should correlate positively
    # with the sum of asset indicators (more assets = higher score)
    asset_sum = np.nansum(X, axis=1)
    if np.corrcoef(scores, asset_sum)[0, 1] < 0:
        scores = -scores

    return scores


def build_origin_asset_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Build binary indicator matrix for origin household (age 14).

    Returns DataFrame with one column per indicator, same index as df.
    """
    indicators = {}

    # Household goods (p31a-o): 1=Yes, 2=No, 8=NS
    for var in ORIGIN_ASSET_VARS:
        if var in df.columns:
            indicators[var] = _recode_binary(df[var])

    # Property/financial (p32a-e): 1=Yes, 2=No, 8=NS
    for var in ORIGIN_PROPERTY_VARS:
        if var in df.columns:
            indicators[var] = _recode_binary(df[var])

    # Basic services (p26a,b,d,e): 1=Yes, 2=No, 8=NS
    for var in ORIGIN_SERVICE_VARS:
        if var in df.columns:
            indicators[var] = _recode_binary(df[var])

    # Automobiles at 14 (p30): count -> binary
    if "p30" in df.columns:
        indicators["p30_bin"] = _recode_count_to_binary(df["p30"])

    # Overcrowding at 14: p22 (household size) / p24 (sleeping rooms)
    if "p22" in df.columns and "p24" in df.columns:
        indicators["hac_or"] = _build_overcrowding(df["p22"], df["p24"])

    return pd.DataFrame(indicators, index=df.index)


def build_current_asset_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Build binary indicator matrix for current household.

    Returns DataFrame with one column per indicator, same index as df.
    """
    indicators = {}

    # Household goods (p96a-r): 1=Yes, 2=No
    for var in CURRENT_ASSET_VARS:
        if var in df.columns:
            indicators[var] = _recode_binary(df[var])

    # Property/financial (p97a-n): 1=Yes, 2=No
    for var in CURRENT_PROPERTY_VARS:
        if var in df.columns:
            indicators[var] = _recode_binary(df[var])

    # Basic services (p95a,b,d,e): 1=Yes, 2=No
    for var in CURRENT_SERVICE_VARS:
        if var in df.columns:
            indicators[var] = _recode_binary(df[var])

    # Automobiles (p99): count -> binary
    if "p99" in df.columns:
        indicators["p99_bin"] = _recode_count_to_binary(df["p99"])

    # Overcrowding: tamhog / p89
    if "tamhog" in df.columns and "p89" in df.columns:
        indicators["hac"] = _build_overcrowding(df["tamhog"], df["p89"])

    return pd.DataFrame(indicators, index=df.index)


def compute_wealth_index(
    df: pd.DataFrame,
    cohort_col: str = "cohorte",
    weight_col: str = "factor",
) -> tuple[pd.Series, pd.Series]:
    """Compute comparable wealth indices for origin and current households.

    Runs PCA on binary asset indicators separately for each cohort
    (replicating .do lines 291-297, 371-377), then combines into a
    single index per household.

    Returns (index_origin, index_current): continuous wealth scores.
    """
    origin_indicators = build_origin_asset_indicators(df)
    current_indicators = build_current_asset_indicators(df)

    index_origin = pd.Series(np.nan, index=df.index)
    index_current = pd.Series(np.nan, index=df.index)

    if cohort_col in df.columns:
        cohorts = df[cohort_col].dropna().unique()
    else:
        cohorts = [None]

    for cohort in sorted(cohorts):
        if cohort is not None:
            mask = df[cohort_col] == cohort
        else:
            mask = pd.Series(True, index=df.index)

        # Origin index
        X_or = origin_indicators.loc[mask].to_numpy()
        if X_or.shape[0] > 0 and X_or.shape[1] > 0:
            # Need at least some non-NaN rows
            valid_rows = ~np.all(np.isnan(X_or), axis=1)
            if valid_rows.sum() > 1:
                scores = _pca_first_component(X_or[valid_rows])
                # Sign auto-corrected by _pca_first_component
                full_scores = np.full(mask.sum(), np.nan)
                full_scores[valid_rows] = scores
                index_origin.loc[mask] = full_scores

        # Current index
        X_cur = current_indicators.loc[mask].to_numpy()
        if X_cur.shape[0] > 0 and X_cur.shape[1] > 0:
            valid_rows = ~np.all(np.isnan(X_cur), axis=1)
            if valid_rows.sum() > 1:
                scores = _pca_first_component(X_cur[valid_rows])
                # Sign auto-corrected by _pca_first_component
                full_scores = np.full(mask.sum(), np.nan)
                full_scores[valid_rows] = scores
                index_current.loc[mask] = full_scores

    return index_origin, index_current
