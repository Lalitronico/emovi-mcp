"""Tool: income_comparison — temporal income analysis (2017 vs 2023)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from emovi_mcp.config import POVERTY_LINES, WEIGHT_COL
from emovi_mcp.data_loader import get_dataframe
from emovi_mcp.helpers.formatting import stats_summary_markdown
from emovi_mcp.helpers.validation import apply_filter
from emovi_mcp.helpers.weights import weighted_mean, weighted_median, weighted_std
from emovi_mcp.stats_engine import merge_income_2017

import numpy as np
import pandas as pd


def register(mcp: FastMCP):
    @mcp.tool()
    def income_comparison(
        metric: str = "change",
        filter: str | None = None,
        by: str | None = None,
    ) -> str:
        """Compare income between 2017 and 2023 for matched respondents.

        Merges the 2017 income module with the 2023 respondent data on folio.

        Args:
            metric: What to compute.
                - "change": Income change statistics (absolute and relative).
                - "poverty": Poverty transition rates using CEEY poverty lines.
                - "summary": Full summary with both income change and poverty.
            filter: Optional filter expression (e.g., "sexo == 1", "rururb == 1").
            by: Optional grouping variable (e.g., "sexo", "rururb", "cohorte").

        Returns markdown summary with weighted statistics on temporal income dynamics.
        """
        df_ent = get_dataframe("entrevistado")
        df_ing = get_dataframe("ingreso_2017")
        merged = merge_income_2017(df_ent, df_ing)
        work = apply_filter(merged, filter)

        if len(work) == 0:
            return "No matched observations found between 2017 and 2023 datasets."

        parts: list[str] = [
            "[DISPLAY INSTRUCTION: Always render the full tables below. "
            "Do not summarize or omit them. Add your interpretation AFTER the tables.]",
            "",
        ]

        def _income_change_stats(subset: pd.DataFrame, label: str) -> str:
            """Compute income change statistics for a subset."""
            lines: list[str] = []
            title = "Income Change 2017-2023"
            if label != "all":
                title += f" ({by}={label})"
            lines.append(f"## {title}")
            lines.append("")

            wts = subset[WEIGHT_COL]
            inc_2023 = subset["ingc_pc"]
            inc_2017 = subset["ingc_pc_2017"]
            change = inc_2023 - inc_2017
            pct_change = change / inc_2017.replace(0, np.nan)

            valid = change.notna() & wts.notna()
            v_change = change[valid]
            v_wts = wts[valid]
            v_pct = pct_change[valid & pct_change.notna()]
            v_pct_wts = wts[valid & pct_change.notna()]

            lines.append(f"- **N (matched)**: {int(valid.sum()):,}")
            lines.append(f"- **Mean income 2017**: {weighted_mean(inc_2017[valid], v_wts):,.2f}")
            lines.append(f"- **Mean income 2023**: {weighted_mean(inc_2023[valid], v_wts):,.2f}")
            lines.append(f"- **Mean absolute change**: {weighted_mean(v_change, v_wts):,.2f}")
            lines.append(f"- **Median absolute change**: {weighted_median(v_change, v_wts):,.2f}")
            if len(v_pct) > 0:
                lines.append(f"- **Mean % change**: {weighted_mean(v_pct, v_pct_wts):.1%}")
                lines.append(f"- **Median % change**: {weighted_median(v_pct, v_pct_wts):.1%}")
            lines.append(f"- **% with income increase**: "
                         f"{weighted_mean((v_change > 0).astype(float), v_wts):.1%}")
            lines.append(f"- **% with income decrease**: "
                         f"{weighted_mean((v_change < 0).astype(float), v_wts):.1%}")
            lines.append("")
            return "\n".join(lines)

        def _poverty_stats(subset: pd.DataFrame, label: str) -> str:
            """Compute poverty transition statistics."""
            lines: list[str] = []
            title = "Poverty Transitions 2017-2023"
            if label != "all":
                title += f" ({by}={label})"
            lines.append(f"## {title}")
            lines.append("")

            wts = subset[WEIGHT_COL]
            inc_2023 = subset["ingc_pc"]
            inc_2017 = subset["ingc_pc_2017"]
            is_rural = subset.get("rururb", pd.Series(2, index=subset.index))

            # Use urban poverty lines by default, rural when rururb==1
            pl_2023_mod = np.where(
                is_rural == 1,
                POVERTY_LINES[2023]["moderate"]["rural"],
                POVERTY_LINES[2023]["moderate"]["urban"],
            )
            pl_2023_ext = np.where(
                is_rural == 1,
                POVERTY_LINES[2023]["extreme"]["rural"],
                POVERTY_LINES[2023]["extreme"]["urban"],
            )
            pl_2017_mod = np.where(
                is_rural == 1,
                POVERTY_LINES[2017]["moderate"]["rural"],
                POVERTY_LINES[2017]["moderate"]["urban"],
            )
            pl_2017_ext = np.where(
                is_rural == 1,
                POVERTY_LINES[2017]["extreme"]["rural"],
                POVERTY_LINES[2017]["extreme"]["urban"],
            )

            poor_mod_2017 = (inc_2017 < pl_2017_mod).astype(float)
            poor_mod_2023 = (inc_2023 < pl_2023_mod).astype(float)
            poor_ext_2017 = (inc_2017 < pl_2017_ext).astype(float)
            poor_ext_2023 = (inc_2023 < pl_2023_ext).astype(float)

            valid = inc_2017.notna() & inc_2023.notna() & wts.notna()
            v_wts = wts[valid]

            lines.append("### Moderate Poverty")
            lines.append(f"- **2017 rate**: {weighted_mean(poor_mod_2017[valid], v_wts):.1%}")
            lines.append(f"- **2023 rate**: {weighted_mean(poor_mod_2023[valid], v_wts):.1%}")
            fell = ((poor_mod_2017[valid] == 0) & (poor_mod_2023[valid] == 1)).astype(float)
            escaped = ((poor_mod_2017[valid] == 1) & (poor_mod_2023[valid] == 0)).astype(float)
            lines.append(f"- **Fell into poverty**: {weighted_mean(fell, v_wts):.1%}")
            lines.append(f"- **Escaped poverty**: {weighted_mean(escaped, v_wts):.1%}")
            lines.append("")

            lines.append("### Extreme Poverty")
            lines.append(f"- **2017 rate**: {weighted_mean(poor_ext_2017[valid], v_wts):.1%}")
            lines.append(f"- **2023 rate**: {weighted_mean(poor_ext_2023[valid], v_wts):.1%}")
            fell_ext = ((poor_ext_2017[valid] == 0) & (poor_ext_2023[valid] == 1)).astype(float)
            escaped_ext = ((poor_ext_2017[valid] == 1) & (poor_ext_2023[valid] == 0)).astype(float)
            lines.append(f"- **Fell into extreme poverty**: {weighted_mean(fell_ext, v_wts):.1%}")
            lines.append(f"- **Escaped extreme poverty**: {weighted_mean(escaped_ext, v_wts):.1%}")
            lines.append("")
            return "\n".join(lines)

        def _process_group(subset: pd.DataFrame, label: str):
            if metric in ("change", "summary"):
                parts.append(_income_change_stats(subset, label))
            if metric in ("poverty", "summary"):
                parts.append(_poverty_stats(subset, label))

        if by and by in work.columns:
            for group_val, group_df in work.groupby(by):
                _process_group(group_df, str(group_val))
                parts.append("---\n")
        else:
            _process_group(work, "all")

        return "\n".join(parts)
