"""MCP tool: visualize mobility data."""

from __future__ import annotations

from emovi_mcp.config import DATASETS, MOBILITY_DIMENSIONS, get_weight_col
from emovi_mcp.data_loader import load_dataset
from emovi_mcp.helpers.formatting import matrix_to_markdown
from emovi_mcp.stats_engine import compute_transition_matrix


def register(mcp):
    @mcp.tool()
    def visualize_mobility(
        dimension: str = "wealth",
        chart_type: str = "heatmap",
        filter: str | None = None,
        by: str | None = None,
    ) -> str:
        """Generate a visualization of mobility transition matrix.

        Args:
            dimension: Mobility dimension — "education", "occupation", or "wealth"
            chart_type: Type of chart — "heatmap", "sankey", or "prais_bar"
            filter: Optional filter expression (e.g., "sexo == 1")
            by: Optional grouping variable
        """
        valid_charts = ("heatmap", "sankey", "prais_bar")
        if chart_type not in valid_charts:
            return f"Unknown chart_type '{chart_type}'. Use one of: {', '.join(valid_charts)}"

        # Check if viz deps available
        try:
            from emovi_mcp.helpers.visualization import (
                bar_chart_prais,
                heatmap_transition_matrix,
                sankey_mobility,
            )
        except ImportError as e:
            return (
                f"Visualization dependencies not available: {e}\n"
                "Install with: pip install emovi-mcp[viz]\n\n"
                "Falling back to text output..."
            )

        dataset = "entrevistado"
        weight_col = get_weight_col(dataset)
        df = load_dataset(dataset)

        result = compute_transition_matrix(
            df, dimension, filter_expr=filter, by=by, weight_col=weight_col
        )

        if not result["matrices"]:
            return "No data available for the specified parameters."

        parts: list[str] = []

        for key, matrix in result["matrices"].items():
            group_label = f" ({key})" if key != "all" else ""
            dim_desc = result["dimension_info"]["description"]
            title = f"{dim_desc}{group_label}"

            try:
                if chart_type == "heatmap":
                    img = heatmap_transition_matrix(matrix, title=title)
                    parts.append(f"### {title}\n\n![Heatmap]({img})")
                elif chart_type == "sankey":
                    img = sankey_mobility(matrix, title=title)
                    parts.append(f"### {title}\n\n![Sankey]({img})")
                elif chart_type == "prais_bar":
                    summary = result["summary"].get(key, {})
                    prais = summary.get("prais_index", {})
                    if prais:
                        img = bar_chart_prais(prais, title=f"Prais Index — {title}")
                        parts.append(f"### {title}\n\n![Prais]({img})")
                    else:
                        parts.append(f"### {title}\n\nPrais index not available.")
            except Exception as e:
                # Fallback to text if rendering fails
                parts.append(f"### {title}\n\nVisualization failed: {e}")
                parts.append(matrix_to_markdown(matrix, title))

            # Always include numeric table as fallback
            parts.append("")
            parts.append(matrix_to_markdown(matrix, f"Data — {title}"))

        return "\n\n".join(parts)
