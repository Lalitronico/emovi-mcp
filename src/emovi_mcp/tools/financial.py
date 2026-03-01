"""Tool: financial_inclusion_summary — financial inclusion module analysis."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from emovi_mcp.config import FINANCIAL_INCLUSION_DIMENSIONS, get_weight_col
from emovi_mcp.data_loader import get_dataframe
from emovi_mcp.helpers.formatting import df_to_markdown, stats_summary_markdown
from emovi_mcp.helpers.validation import apply_filter
from emovi_mcp.helpers.weights import weighted_frequency, weighted_mean

import pandas as pd


def register(mcp: FastMCP):
    @mcp.tool()
    def financial_inclusion_summary(
        dimension: str = "banking",
        filter: str | None = None,
        by: str | None = None,
    ) -> str:
        """Analyze financial inclusion from the ESRU-EMOVI 2023 inclusion module.

        Args:
            dimension: Financial inclusion dimension to analyze.
                - "savings": Formal and informal savings behavior
                - "credit": Access to credit and debt
                - "banking": Banking services and financial products
                - "literacy": Financial education and knowledge
                - "discrimination": Discrimination in financial services
            filter: Optional filter expression (e.g., "sexo == 1").
            by: Optional grouping variable (e.g., "sexo", "entidad").

        Returns markdown summary with weighted proportions for each variable
        in the selected dimension.
        """
        if dimension not in FINANCIAL_INCLUSION_DIMENSIONS:
            available = ", ".join(sorted(FINANCIAL_INCLUSION_DIMENSIONS.keys()))
            raise ValueError(
                f"Unknown dimension {dimension!r}. Available: {available}"
            )

        dim_config = FINANCIAL_INCLUSION_DIMENSIONS[dimension]
        dataset = "inclusion_financiera"
        weight_col = get_weight_col(dataset)
        df = get_dataframe(dataset)
        work = apply_filter(df, filter)

        # Identify which configured variables actually exist in the data
        available_vars = [v for v in dim_config["variables"] if v in work.columns]
        if not available_vars:
            return (
                f"No variables found for dimension '{dimension}' in the dataset. "
                f"Expected columns: {dim_config['variables']}"
            )

        parts: list[str] = [
            "[DISPLAY INSTRUCTION: Always render the full tables below. "
            "Do not summarize or omit them. Add your interpretation AFTER the tables.]",
            "",
            f"## Financial Inclusion: {dim_config['description']}",
            "",
        ]

        def _summarize_group(subset: pd.DataFrame, label: str) -> str:
            """Produce summary for one group."""
            lines: list[str] = []
            if label != "all":
                lines.append(f"### {by}={label}")
                lines.append("")

            for var in available_vars:
                if var not in subset.columns:
                    continue
                col = subset[var].dropna()
                wts = subset.loc[col.index, weight_col]
                if len(col) == 0:
                    continue

                freq = weighted_frequency(col, wts)
                var_label = var
                lines.append(f"**{var_label}** (N={len(col):,})")
                lines.append("")
                for _, row in freq.iterrows():
                    lines.append(
                        f"  - {row['value']}: {row['proportion']:.1%} "
                        f"(n={row['n']:,.0f})"
                    )
                lines.append("")

            return "\n".join(lines)

        if by and by in work.columns:
            for group_val, group_df in work.groupby(by):
                parts.append(_summarize_group(group_df, str(group_val)))
                parts.append("---")
        else:
            parts.append(_summarize_group(work, "all"))

        return "\n".join(parts)
