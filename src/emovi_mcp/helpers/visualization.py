"""Visualization helpers for transition matrices and mobility data.

Requires optional dependencies: matplotlib, seaborn.
Install with: pip install emovi-mcp[viz]
"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    import matplotlib.figure


def _check_viz_deps() -> None:
    """Raise ImportError with helpful message if viz deps are missing."""
    try:
        import matplotlib
        import seaborn  # noqa: F401
    except ImportError:
        raise ImportError(
            "Visualization requires matplotlib and seaborn. "
            "Install with: pip install emovi-mcp[viz]"
        )


def _fig_to_base64(fig: matplotlib.figure.Figure, dpi: int = 150) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG data URI."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    return f"data:image/png;base64,{b64}"


def heatmap_transition_matrix(
    matrix: pd.DataFrame,
    title: str = "Transition Matrix",
    annot_fmt: str = ".1%",
    cmap: str = "YlOrRd",
    figsize: tuple[int, int] = (8, 6),
) -> str:
    """Generate a heatmap of a transition matrix.

    Returns a base64 PNG data URI string.
    """
    _check_viz_deps()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, ax = plt.subplots(figsize=figsize)

    sns.heatmap(
        matrix,
        annot=True,
        fmt=annot_fmt,
        cmap=cmap,
        vmin=0,
        vmax=matrix.values.max() * 1.1,
        linewidths=0.5,
        linecolor="white",
        ax=ax,
        cbar_kws={"label": "Proportion"},
    )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Destination", fontsize=12)
    ax.set_ylabel("Origin", fontsize=12)
    ax.tick_params(axis="both", labelsize=10)

    # Rotate x labels for readability
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)

    result = _fig_to_base64(fig)
    plt.close(fig)
    return result


def sankey_mobility(
    matrix: pd.DataFrame,
    title: str = "Mobility Flows",
    figsize: tuple[int, int] = (10, 7),
) -> str:
    """Generate a Sankey-like alluvial diagram of mobility flows.

    Uses matplotlib to draw flow bands between origin and destination categories.
    Returns a base64 PNG data URI string.
    """
    _check_viz_deps()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch

    n = matrix.shape[0]
    labels = list(matrix.index)

    fig, ax = plt.subplots(figsize=figsize)

    # Color palette
    colors = plt.cm.Set2(np.linspace(0, 1, n))

    # Positions for origin (left) and destination (right)
    left_x = 0.1
    right_x = 0.9
    y_positions = np.linspace(0.9, 0.1, n)

    # Draw origin labels
    for i, label in enumerate(labels):
        ax.text(left_x - 0.05, y_positions[i], label, ha="right", va="center",
                fontsize=11, fontweight="bold")
        ax.text(right_x + 0.05, y_positions[i], label, ha="left", va="center",
                fontsize=11, fontweight="bold")

    # Draw flow bands
    for i in range(n):
        for j in range(n):
            flow = matrix.iloc[i, j]
            if flow < 0.01:
                continue  # skip tiny flows

            alpha = max(0.15, min(0.8, flow))
            linewidth = max(0.5, flow * 15)

            arrow = FancyArrowPatch(
                (left_x, y_positions[i]),
                (right_x, y_positions[j]),
                connectionstyle="arc3,rad=0.1",
                arrowstyle="-",
                linewidth=linewidth,
                color=colors[i],
                alpha=alpha,
            )
            ax.add_patch(arrow)

            # Annotate significant flows
            if flow >= 0.10:
                mid_x = (left_x + right_x) / 2
                mid_y = (y_positions[i] + y_positions[j]) / 2
                ax.text(mid_x, mid_y, f"{flow:.0%}", ha="center", va="center",
                        fontsize=8, color="gray", alpha=0.7)

    # Draw vertical bars at origin and destination
    bar_width = 0.02
    for i in range(n):
        ax.add_patch(plt.Rectangle(
            (left_x - bar_width / 2, y_positions[i] - 0.03),
            bar_width, 0.06, color=colors[i], zorder=3
        ))
        ax.add_patch(plt.Rectangle(
            (right_x - bar_width / 2, y_positions[i] - 0.03),
            bar_width, 0.06, color=colors[i], zorder=3
        ))

    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(0, 1)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.text(left_x, 0.98, "Origin", ha="center", fontsize=12, fontstyle="italic")
    ax.text(right_x, 0.98, "Destination", ha="center", fontsize=12, fontstyle="italic")
    ax.axis("off")

    result = _fig_to_base64(fig)
    plt.close(fig)
    return result


def bar_chart_prais(
    prais: dict[str, float],
    title: str = "Prais Escape Probabilities",
    figsize: tuple[int, int] = (8, 5),
) -> str:
    """Bar chart of Prais index (escape probabilities) by category.

    Returns a base64 PNG data URI string.
    """
    _check_viz_deps()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    categories = list(prais.keys())
    values = list(prais.values())

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(categories, values, color=plt.cm.RdYlGn(np.array(values)))
    ax.set_ylabel("Escape Probability (1 - p_ii)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylim(0, 1)

    # Add value labels on bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{val:.1%}", ha="center", va="bottom", fontsize=10)

    result = _fig_to_base64(fig)
    plt.close(fig)
    return result
