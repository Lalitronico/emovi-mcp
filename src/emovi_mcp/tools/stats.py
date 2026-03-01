"""Tool: weighted_stats — descriptive statistics."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from emovi_mcp.config import WEIGHT_COL
from emovi_mcp.data_loader import get_dataframe
from emovi_mcp.helpers.formatting import stats_summary_markdown
from emovi_mcp.stats_engine import compute_descriptive_stats


def register(mcp: FastMCP):
    @mcp.tool()
    def weighted_stats(
        variable: str,
        filter: str | None = None,
        by: str | None = None,
        dataset: str = "entrevistado",
    ) -> str:
        """Compute weighted descriptive statistics for a variable.

        Args:
            variable: The numeric variable to analyze (e.g., 'ingc_pc', 'educ').
            filter: Optional filter expression (e.g., "sexo == 1").
            by: Optional grouping variable (e.g., "region", "sexo", "cohorte").
            dataset: Which dataset to use (default: entrevistado).

        Returns weighted mean, median, std, percentiles (25th, 75th), min, max,
        and sample sizes. If 'by' is specified, returns stats per group.
        """
        df = get_dataframe(dataset)
        results = compute_descriptive_stats(
            df,
            variable=variable,
            weight_col=WEIGHT_COL,
            filter_expr=filter,
            by=by,
        )

        parts: list[str] = []
        for group_key, stats in results.items():
            title = f"Statistics: `{variable}`"
            if group_key != "all":
                title += f" ({by}={group_key})"
            if filter:
                title += f" [filter: {filter}]"
            parts.append(stats_summary_markdown(stats, title=title))

        return "\n\n---\n\n".join(parts)
