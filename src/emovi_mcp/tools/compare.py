"""Tool: compare_groups — compare a variable across groups."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from emovi_mcp.config import WEIGHT_COL
from emovi_mcp.data_loader import get_dataframe
from emovi_mcp.helpers.formatting import df_to_markdown
from emovi_mcp.helpers.validation import apply_filter, validate_column
from emovi_mcp.helpers.weights import (
    weighted_frequency,
    weighted_mean,
    weighted_median,
)

import pandas as pd


def register(mcp: FastMCP):
    @mcp.tool()
    def compare_groups(
        variable: str,
        group_var: str,
        metric: str = "mean",
        filter: str | None = None,
        dataset: str = "entrevistado",
    ) -> str:
        """Compare a variable across groups defined by another variable.

        Args:
            variable: The variable to compare (e.g., 'ingc_pc', 'educ').
            group_var: The grouping variable (e.g., 'sexo', 'region', 'cohorte').
            metric: Which metric to compute: 'mean', 'median', or 'distribution'.
            filter: Optional filter expression.
            dataset: Which dataset to use (default: entrevistado).

        Returns a comparison table showing the metric for each group.
        """
        df = get_dataframe(dataset)
        work = apply_filter(df, filter)
        validate_column(work, variable)
        validate_column(work, group_var)
        validate_column(work, WEIGHT_COL)

        rows = []
        for group_val, group_df in work.groupby(group_var):
            vals = group_df[variable]
            wts = group_df[WEIGHT_COL]

            if metric == "mean":
                value = weighted_mean(vals, wts)
                rows.append({
                    group_var: group_val,
                    "mean": value,
                    "n": int(vals.notna().sum()),
                })
            elif metric == "median":
                value = weighted_median(vals, wts)
                rows.append({
                    group_var: group_val,
                    "median": value,
                    "n": int(vals.notna().sum()),
                })
            elif metric == "distribution":
                freq = weighted_frequency(vals, wts)
                for _, frow in freq.iterrows():
                    rows.append({
                        group_var: group_val,
                        "value": frow["value"],
                        "proportion": frow["proportion"],
                        "n": frow["n"],
                    })

        if not rows:
            return "No data available for the given parameters."

        result_df = pd.DataFrame(rows)
        title = f"Comparison: `{variable}` by `{group_var}` ({metric})"
        if filter:
            title += f" [filter: {filter}]"

        fmt = ".1%" if metric == "distribution" else ".2f"
        return df_to_markdown(result_df, title=title, float_format=fmt)
