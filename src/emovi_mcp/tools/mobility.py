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
        origin_category: int | None = None,
        include_se: bool = False,
    ) -> str:
        """Compute an intergenerational mobility transition matrix.

        This is the core analysis tool for social mobility research.

        Args:
            dimension: Type of mobility to analyze.
                - "education": Educational mobility (4x4 matrix).
                  Origin = max(father, mother) education; Destination = respondent education.
                - "occupation": Occupational class mobility.
                  Origin = father's class; Destination = respondent's class.
                - "wealth": Wealth quintile mobility (5x5 matrix).
                  Based on PCA wealth index from household assets (origin vs current).
            filter: Optional filter expression.
                Examples: "sexo == 2" (women only), "cohorte == 1" (ages 25-34),
                "region_14 == 5" (Southern region of origin).
            by: Optional grouping variable to produce separate matrices.
                Examples: "sexo" (by gender), "region_14" (by region of origin),
                "cohorte" (by age cohort).
            origin_category: Optional origin quintile/category to filter.
                Example: 1 for Q1 (poorest) in wealth, or 1 for "Primaria o menos" in education.
                Returns only the destination distribution for that origin.
            include_se: If True, compute Taylor-linearized standard errors
                and 95% confidence intervals for each matrix cell.

        Returns markdown transition matrix with row percentages (origin -> destination),
        summary statistics, formal mobility indices, and optionally standard errors.
        """
        df = get_dataframe("entrevistado")
        result = compute_transition_matrix(
            df,
            dimension=dimension,
            filter_expr=filter,
            by=by,
            weight_col=WEIGHT_COL,
            origin_filter=origin_category,
            compute_se=include_se,
        )

        if not result["matrices"]:
            return f"No data available for dimension={dimension!r} with the given filters."

        dim_info = result["dimension_info"]
        parts: list[str] = [
            "[DISPLAY INSTRUCTION: Always render the full table below. "
            "Do not summarize or omit it. Add your interpretation AFTER the table.]",
            "",
        ]

        for group_key, matrix in result["matrices"].items():
            title = f"Transition Matrix: {dim_info['description']}"
            if group_key != "all":
                title += f" ({by}={group_key})"
            if origin_category is not None:
                title += f" [origin={origin_category}]"
            if filter:
                title += f" [filter: {filter}]"

            summary = result["summary"][group_key]
            note_parts = [
                f"N={summary['n_unweighted']:,} (unweighted)",
                f"Diagonal persistence: {summary['diagonal_persistence']:.1%}",
                f"Upward: {summary['upward_mobility_avg']:.1%}",
                f"Downward: {summary['downward_mobility_avg']:.1%}",
            ]

            # Formal mobility indices
            if "shorrocks_m" in summary:
                note_parts.append(f"Shorrocks M: {summary['shorrocks_m']:.3f}")
            if "intergenerational_r" in summary:
                note_parts.append(f"Intergenerational r: {summary['intergenerational_r']:.3f}")

            note = " | ".join(note_parts)

            parts.append(matrix_to_markdown(matrix, title=title, note=note))

            # Prais indices (per-class escape probability)
            if "prais_index" in summary:
                prais_lines = ["\n### Prais Index (escape probability by origin)", ""]
                for label, val in summary["prais_index"].items():
                    prais_lines.append(f"- {label}: {val:.1%}")
                parts.append("\n".join(prais_lines))

            # Corner odds ratios
            if "corner_odds_ratios" in summary:
                cors = summary["corner_odds_ratios"]
                cor_lines = [
                    "\n### Corner Odds Ratios",
                    "",
                    f"- Top-left (Q1 persistence): {cors['top_left']:.2f}",
                    f"- Bottom-right (Q5 persistence): {cors['bottom_right']:.2f}",
                    f"- Cross (Q1→Q5 vs Q5→Q1): {cors['cross']:.2f}",
                ]
                parts.append("\n".join(cor_lines))

            # Standard errors
            se_matrices = result.get("se_matrices", {})
            if group_key in se_matrices:
                from emovi_mcp.helpers.formatting import matrix_with_se_to_markdown
                parts.append(matrix_with_se_to_markdown(
                    matrix, se_matrices[group_key],
                    title="Standard Errors (95% CI)"
                ))

        return "\n\n---\n\n".join(parts)
