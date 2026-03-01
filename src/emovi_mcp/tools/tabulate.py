"""Tool: tabulate — weighted crosstab."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from emovi_mcp.config import get_weight_col
from emovi_mcp.data_loader import get_dataframe
from emovi_mcp.helpers.formatting import df_to_markdown
from emovi_mcp.stats_engine import compute_crosstab


def register(mcp: FastMCP):
    @mcp.tool()
    def tabulate(
        row_var: str,
        col_var: str,
        filter: str | None = None,
        normalize: str = "row",
        dataset: str = "entrevistado",
    ) -> str:
        """Compute a weighted crosstab between two variables.

        Args:
            row_var: Variable for rows (e.g., 'educ', 'region').
            col_var: Variable for columns (e.g., 'sexo', 'cohorte').
            filter: Optional filter expression (e.g., "sexo == 1", "cohorte == 3").
            normalize: How to normalize: 'row' (default), 'col', 'all', or 'none'.
            dataset: Which dataset to use (default: entrevistado).

        Returns a markdown table with weighted proportions.
        """
        df = get_dataframe(dataset)
        ct = compute_crosstab(
            df,
            row_var=row_var,
            col_var=col_var,
            weight_col=get_weight_col(dataset),
            normalize=normalize,
            filter_expr=filter,
        )

        title = f"Crosstab: {row_var} x {col_var}"
        if filter:
            title += f" (filter: {filter})"
        title += f" [normalize={normalize}]"

        header = (
            "[DISPLAY INSTRUCTION: Always render the full table below. "
            "Do not summarize or omit it. Add your interpretation AFTER the table.]\n\n"
        )
        return header + df_to_markdown(ct.reset_index(), title=title, float_format=".1%")
