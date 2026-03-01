"""Core statistical computations — all weighted per survey design."""

from __future__ import annotations

import numpy as np
import pandas as pd

from emovi_mcp.config import (
    EDUC_4_LABELS,
    MOBILITY_DIMENSIONS,
    WEIGHT_COL,
)
from emovi_mcp.helpers.labels import apply_value_labels
from emovi_mcp.helpers.validation import apply_filter, validate_column
from emovi_mcp.helpers.weights import (
    create_weighted_quintiles,
    weighted_frequency,
    weighted_mean,
    weighted_median,
    weighted_quantile,
    weighted_std,
)


# ---------------------------------------------------------------------------
# Variable construction (replicates .do file logic)
# ---------------------------------------------------------------------------

def build_padres_edu(df: pd.DataFrame) -> pd.Series:
    """Build max parental education variable.

    Replicates .do lines 603-606:
        egen padres_edu = rowmax(educp educm)
        replace padres_edu = educm if educp==. & educm!=.
        replace padres_edu = educp if educm==. & educp!=.
        replace padres_edu = . if educm==. & educp==.
    """
    if "padres_edu" in df.columns:
        return df["padres_edu"]

    educp = df.get("educp")
    educm = df.get("educm")

    if educp is None or educm is None:
        raise ValueError("Columns 'educp' and 'educm' required to build padres_edu")

    result = pd.concat([educp, educm], axis=1).max(axis=1)
    # Both missing -> NaN
    both_missing = educp.isna() & educm.isna()
    result[both_missing] = np.nan
    return result


def build_wealth_quintiles(
    df: pd.DataFrame, weight_col: str = WEIGHT_COL
) -> tuple[pd.Series, pd.Series]:
    """Build origin and destination wealth quintiles using PCA on household assets.

    Replicates CEEY methodology (.do lines 265-391):
      - Constructs binary asset indicators for origin (age 14) and current households
      - Runs PCA by cohort to produce comparable wealth indices
      - Assigns weighted quintiles to each index

    Returns (quintile_origin, quintile_dest).
    """
    from emovi_mcp.helpers.wealth_index import compute_wealth_index

    index_origin, index_current = compute_wealth_index(
        df, cohort_col="cohorte", weight_col=weight_col
    )
    q_origin = create_weighted_quintiles(index_origin, df[weight_col], nq=5)
    q_dest = create_weighted_quintiles(index_current, df[weight_col], nq=5)
    return q_origin, q_dest


# ---------------------------------------------------------------------------
# Income merge (temporal comparison)
# ---------------------------------------------------------------------------

def merge_income_2017(
    df_ent: pd.DataFrame, df_ing: pd.DataFrame
) -> pd.DataFrame:
    """Left-join 2017 income onto the entrevistado dataset on folio.

    Returns a copy of df_ent with 'ingc_pc_2017' added from df_ing.
    """
    # Identify the income column in the 2017 dataset
    ing_col = None
    for candidate in ("ingc_pc", "ingpc", "ingreso_pc", "ing_pc"):
        if candidate in df_ing.columns:
            ing_col = candidate
            break
    if ing_col is None:
        # Use the first non-folio numeric column
        for c in df_ing.columns:
            if c != "folio" and pd.api.types.is_numeric_dtype(df_ing[c]):
                ing_col = c
                break
    if ing_col is None:
        raise ValueError("Cannot identify income column in ingreso_2017 dataset")

    right = df_ing[["folio", ing_col]].rename(columns={ing_col: "ingc_pc_2017"})
    merged = df_ent.merge(right, on="folio", how="left")
    return merged


# ---------------------------------------------------------------------------
# Transition matrix
# ---------------------------------------------------------------------------

def compute_transition_matrix(
    df: pd.DataFrame,
    dimension: str,
    filter_expr: str | None = None,
    by: str | None = None,
    weight_col: str = WEIGHT_COL,
    origin_filter: int | None = None,
    compute_se: bool = False,
) -> dict:
    """Compute a weighted transition matrix for a mobility dimension.

    Returns dict with:
      - matrices: dict[str, pd.DataFrame] (one per group, or {"all": ...})
      - summary: dict with diagonal persistence, upward/downward mobility
      - dimension_info: metadata about the dimension
    """
    if dimension not in MOBILITY_DIMENSIONS:
        available = ", ".join(sorted(MOBILITY_DIMENSIONS.keys()))
        raise ValueError(f"Unknown dimension {dimension!r}. Available: {available}")

    dim_config = MOBILITY_DIMENSIONS[dimension]
    work = df.copy()
    work = apply_filter(work, filter_expr)

    # Build variables if needed
    if dimension == "education":
        work["_origin"] = build_padres_edu(work)
        work["_dest"] = work.get("educ", pd.Series(dtype=float))
    elif dimension == "occupation":
        work["_origin"] = work[dim_config["origin_var"]]
        work["_dest"] = work[dim_config["dest_var"]]
    elif dimension == "wealth":
        q_orig, q_dest = build_wealth_quintiles(work, weight_col)
        work["_origin"] = q_orig
        work["_dest"] = q_dest

    # Drop rows where origin, dest, or weight is missing
    valid = work["_origin"].notna() & work["_dest"].notna() & work[weight_col].notna()
    work = work[valid]

    # Optional: filter to a single origin category
    if origin_filter is not None:
        work = work[work["_origin"] == origin_filter]

    if len(work) == 0:
        return {"matrices": {}, "summary": {}, "dimension_info": dim_config}

    labels = dim_config["labels"]

    def _matrix_for_subset(subset: pd.DataFrame) -> pd.DataFrame:
        """Weighted crosstab normalized by row (origin)."""
        ct = pd.crosstab(
            subset["_origin"],
            subset["_dest"],
            values=subset[weight_col],
            aggfunc="sum",
            dropna=False,
        )
        # Normalize rows to proportions
        row_sums = ct.sum(axis=1)
        matrix = ct.div(row_sums, axis=0)
        # Apply labels
        matrix.index = [labels.get(int(i), str(i)) for i in matrix.index]
        matrix.columns = [labels.get(int(c), str(c)) for c in matrix.columns]
        return matrix

    def _summary(matrix: pd.DataFrame, n: int) -> dict:
        """Compute mobility summary statistics."""
        diag_values = [
            matrix.iloc[i, i] for i in range(min(matrix.shape))
        ]
        diagonal_persistence = np.mean(diag_values) if diag_values else 0

        # Upward: below diagonal, Downward: above diagonal
        upward = 0.0
        downward = 0.0
        total_cells = 0
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if i < j:
                    upward += matrix.iloc[i, j]
                    total_cells += 1
                elif i > j:
                    downward += matrix.iloc[i, j]
                    total_cells += 1

        n_origins = matrix.shape[0]
        return {
            "n_unweighted": n,
            "diagonal_persistence": float(diagonal_persistence),
            "upward_mobility_avg": float(upward / n_origins) if n_origins else 0,
            "downward_mobility_avg": float(downward / n_origins) if n_origins else 0,
        }

    matrices = {}
    summaries = {}

    if by and by in work.columns:
        for group_val, group_df in work.groupby(by):
            key = str(group_val)
            m = _matrix_for_subset(group_df)
            matrices[key] = m
            summaries[key] = _summary(m, len(group_df))
    else:
        m = _matrix_for_subset(work)
        matrices["all"] = m
        summaries["all"] = _summary(m, len(work))

    # Compute formal mobility indices
    try:
        from emovi_mcp.helpers.mobility_indices import (
            compute_all_indices,
        )
        for key, m in matrices.items():
            summaries[key].update(compute_all_indices(m, work, weight_col))
    except ImportError:
        pass

    # Compute standard errors for matrix cells
    se_matrices = {}
    if compute_se:
        try:
            from emovi_mcp.helpers.survey_variance import (
                transition_matrix_standard_errors,
            )
            from emovi_mcp.config import PSU_COL, STRATA_COL
            se_func = transition_matrix_standard_errors
            if by and by in work.columns:
                for gval, gdf in work.groupby(by):
                    gkey = str(gval)
                    se_matrices[gkey] = se_func(
                        gdf, "_origin", "_dest", weight_col, PSU_COL, STRATA_COL, labels
                    )
            else:
                se_matrices["all"] = se_func(
                    work, "_origin", "_dest", weight_col, PSU_COL, STRATA_COL, labels
                )
        except ImportError:
            pass

    return {
        "matrices": matrices,
        "summary": summaries,
        "dimension_info": dim_config,
        "se_matrices": se_matrices,
    }


# ---------------------------------------------------------------------------
# Weighted crosstab (general purpose)
# ---------------------------------------------------------------------------

def compute_crosstab(
    df: pd.DataFrame,
    row_var: str,
    col_var: str,
    weight_col: str = WEIGHT_COL,
    normalize: str = "row",
    filter_expr: str | None = None,
    row_labels: dict[int, str] | None = None,
    col_labels: dict[int, str] | None = None,
) -> pd.DataFrame:
    """Compute a weighted crosstab.

    normalize: 'row', 'col', 'all', or 'none'
    """
    work = apply_filter(df, filter_expr)
    validate_column(work, row_var)
    validate_column(work, col_var)
    validate_column(work, weight_col)

    ct = pd.crosstab(
        work[row_var],
        work[col_var],
        values=work[weight_col],
        aggfunc="sum",
        dropna=False,
    )

    if normalize == "row":
        ct = ct.div(ct.sum(axis=1), axis=0)
    elif normalize == "col":
        ct = ct.div(ct.sum(axis=0), axis=1)
    elif normalize == "all":
        ct = ct / ct.sum().sum()

    if row_labels:
        ct.index = [row_labels.get(int(i), str(i)) for i in ct.index]
    if col_labels:
        ct.columns = [col_labels.get(int(c), str(c)) for c in ct.columns]

    return ct


# ---------------------------------------------------------------------------
# Weighted descriptive stats
# ---------------------------------------------------------------------------

def compute_descriptive_stats(
    df: pd.DataFrame,
    variable: str,
    weight_col: str = WEIGHT_COL,
    filter_expr: str | None = None,
    by: str | None = None,
) -> dict:
    """Compute weighted descriptive statistics for a variable.

    Returns dict with mean, median, std, p25, p75, min, max, n.
    If 'by' is specified, returns one dict per group.
    """
    work = apply_filter(df, filter_expr)
    validate_column(work, variable)
    validate_column(work, weight_col)

    def _stats(subset: pd.DataFrame) -> dict:
        vals = subset[variable]
        wts = subset[weight_col]
        return {
            "mean": weighted_mean(vals, wts),
            "median": weighted_median(vals, wts),
            "std": weighted_std(vals, wts),
            "p25": weighted_quantile(vals, wts, 0.25),
            "p75": weighted_quantile(vals, wts, 0.75),
            "min": float(vals.min()) if vals.notna().any() else float("nan"),
            "max": float(vals.max()) if vals.notna().any() else float("nan"),
            "n_valid": int(vals.notna().sum()),
            "n_missing": int(vals.isna().sum()),
        }

    if by and by in work.columns:
        return {str(g): _stats(gdf) for g, gdf in work.groupby(by)}
    return {"all": _stats(work)}
