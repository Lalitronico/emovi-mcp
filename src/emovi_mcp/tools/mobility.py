"""Tool: transition_matrix — CORE mobility analysis tool."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from emovi_mcp.config import WEIGHT_COL
from emovi_mcp.data_loader import get_dataframe
from emovi_mcp.helpers.formatting import matrix_to_markdown, stats_summary_markdown
from emovi_mcp.stats_engine import compute_transition_matrix


def register(mcp: FastMCP):
    @mcp.tool()
    def transition_matrix(
        dimension: str = "education",
        filter: str | None = None,
        by: str | None = None,
    ) -> str:
        """Compute an intergenerational mobility transition matrix.

        This is the core analysis tool for social mobility research.

        Args:
            dimension: Type of mobility to analyze.
                - "education": Educational mobility (4x4 matrix).
                  Origin = max(father, mother) education; Destination = respondent education.
                - "occupation": Occupational class mobility.
                  Origin = father's class; Destination = respondent's class.
                - "income_quintile": Income quintile mobility (5x5 matrix).
                  Based on weighted quintiles of per-capita household income.
            filter: Optional filter expression.
                Examples: "sexo == 2" (women only), "cohorte == 1" (ages 25-34),
                "region_14 == 5" (Southern region of origin).
            by: Optional grouping variable to produce separate matrices.
                Examples: "sexo" (by gender), "region_14" (by region of origin),
                "cohorte" (by age cohort).

        Returns markdown transition matrix with row percentages (origin -> destination)
        and summary statistics (diagonal persistence, upward/downward mobility).
        """
        df = get_dataframe("entrevistado")
        result = compute_transition_matrix(
            df,
            dimension=dimension,
            filter_expr=filter,
            by=by,
            weight_col=WEIGHT_COL,
        )

        if not result["matrices"]:
            return f"No data available for dimension={dimension!r} with the given filters."

        dim_info = result["dimension_info"]
        parts: list[str] = []

        for group_key, matrix in result["matrices"].items():
            title = f"Transition Matrix: {dim_info['description']}"
            if group_key != "all":
                title += f" ({by}={group_key})"
            if filter:
                title += f" [filter: {filter}]"

            summary = result["summary"][group_key]
            note = (
                f"N={summary['n_unweighted']:,} (unweighted) | "
                f"Diagonal persistence: {summary['diagonal_persistence']:.1%} | "
                f"Upward: {summary['upward_mobility_avg']:.1%} | "
                f"Downward: {summary['downward_mobility_avg']:.1%}"
            )

            parts.append(matrix_to_markdown(matrix, title=title, note=note))

        return "\n\n---\n\n".join(parts)
