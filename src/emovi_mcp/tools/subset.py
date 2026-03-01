"""Tool: filter_data — extract a subset of raw data."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from emovi_mcp.data_loader import get_dataframe
from emovi_mcp.helpers.formatting import df_to_markdown
from emovi_mcp.helpers.validation import apply_filter, validate_columns


def register(mcp: FastMCP):
    @mcp.tool()
    def filter_data(
        variables: list[str],
        filter: str | None = None,
        limit: int = 20,
        dataset: str = "entrevistado",
    ) -> str:
        """Extract a subset of raw data for specific variables.

        Args:
            variables: List of variable names to include
                (e.g., ["sexo", "educ", "ingc_pc"]).
            filter: Optional filter expression (e.g., "sexo == 2 and cohorte == 1").
            limit: Maximum number of rows to return (default: 20, max: 100).
            dataset: Which dataset to use (default: entrevistado).

        Returns a markdown table with the requested data.
        Use this to inspect raw values or extract data for custom analysis.
        """
        limit = min(limit, 100)
        df = get_dataframe(dataset)
        validate_columns(df, variables)
        work = apply_filter(df, filter)

        subset = work[variables].head(limit)

        title = f"Data: {', '.join(variables)}"
        if filter:
            title += f" [filter: {filter}]"
        title += f" ({len(work):,} total rows, showing {len(subset)})"

        return df_to_markdown(subset, title=title)
