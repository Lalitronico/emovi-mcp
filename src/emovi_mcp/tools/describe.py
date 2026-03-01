"""Tool: describe_survey — overview of the ESRU-EMOVI 2023 survey."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from emovi_mcp.config import (
    COHORT_LABELS,
    MOBILITY_DIMENSIONS,
    PSU_COL,
    REGION_LABELS,
    STRATA_COL,
    WEIGHT_COL,
)
from emovi_mcp.data_loader import list_datasets


def register(mcp: FastMCP):
    @mcp.tool()
    def describe_survey() -> str:
        """Get an overview of the ESRU-EMOVI 2023 social mobility survey.

        Returns information about available datasets, survey design,
        mobility dimensions, and key variables.
        """
        datasets = list_datasets()

        lines = [
            "# ESRU-EMOVI 2023 — Encuesta de Movilidad Social en Mexico",
            "",
            "**Produced by:** Centro de Estudios Espinosa Yglesias (CEEY)",
            "**Coverage:** National, ages 25-64",
            f"**Expansion factor:** `{WEIGHT_COL}` (sums to ~60 million)",
            f"**Survey design:** PSU=`{PSU_COL}`, Strata=`{STRATA_COL}`",
            "",
            "## Available datasets",
            "",
        ]

        for name, info in datasets.items():
            lines.append(
                f"- **{name}**: {info['description']} "
                f"(~{info['rows_approx']:,} rows x {info['cols_approx']} cols)"
            )

        lines.extend([
            "",
            "## Mobility dimensions",
            "",
        ])
        for dim, info in MOBILITY_DIMENSIONS.items():
            lines.append(f"- **{dim}**: {info['description']}")

        lines.extend([
            "",
            "## Regions",
            "",
        ])
        for k, v in REGION_LABELS.items():
            lines.append(f"- {k}: {v}")

        lines.extend([
            "",
            "## Cohorts",
            "",
        ])
        for k, v in COHORT_LABELS.items():
            lines.append(f"- {k}: {v}")

        lines.extend([
            "",
            "## Key tools",
            "",
            "- `list_variables` — browse available variables",
            "- `variable_detail` — full info for a specific variable",
            "- `tabulate` — weighted crosstab",
            "- `transition_matrix` — intergenerational mobility matrix",
            "- `weighted_stats` — weighted descriptive statistics",
            "- `compare_groups` — compare a variable across groups",
            "- `filter_data` — extract a data subset",
        ])

        return "\n".join(lines)
