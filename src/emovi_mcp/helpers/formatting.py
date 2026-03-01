"""Format results as markdown for LLM consumption."""

from __future__ import annotations

import pandas as pd


def df_to_markdown(
    df: pd.DataFrame,
    title: str | None = None,
    float_format: str = ".1f",
    max_rows: int = 50,
) -> str:
    """Convert a DataFrame to a markdown table string."""
    lines: list[str] = []

    if title:
        lines.append(f"## {title}")
        lines.append("")

    if len(df) > max_rows:
        lines.append(f"*Showing first {max_rows} of {len(df)} rows*")
        lines.append("")
        df = df.head(max_rows)

    # Format floats
    formatted = df.copy()
    for col in formatted.select_dtypes(include=["float"]).columns:
        formatted[col] = formatted[col].map(
            lambda x: f"{x:{float_format}}" if pd.notna(x) else ""
        )

    # Header
    headers = " | ".join(str(c) for c in formatted.columns)
    separator = " | ".join("---" for _ in formatted.columns)
    lines.append(f"| {headers} |")
    lines.append(f"| {separator} |")

    # Rows
    for _, row in formatted.iterrows():
        cells = " | ".join(str(v) for v in row)
        lines.append(f"| {cells} |")

    return "\n".join(lines)


def matrix_to_markdown(
    matrix: pd.DataFrame,
    title: str,
    note: str = "",
    pct: bool = True,
) -> str:
    """Format a transition matrix as a markdown table with row percentages."""
    lines: list[str] = [f"## {title}", ""]

    fmt = ".1%" if pct else ".1f"

    # Header row
    col_labels = [str(c) for c in matrix.columns]
    lines.append(f"| Origen \\\\ Destino | {' | '.join(col_labels)} |")
    lines.append(f"| --- | {' | '.join(['---'] * len(col_labels))} |")

    # Data rows
    for idx, row in matrix.iterrows():
        cells = []
        for v in row:
            if pct:
                cells.append(f"{v:.1%}" if pd.notna(v) else "")
            else:
                cells.append(f"{v:.1f}" if pd.notna(v) else "")
        lines.append(f"| {idx} | {' | '.join(cells)} |")

    if note:
        lines.append("")
        lines.append(f"*{note}*")

    return "\n".join(lines)


def stats_summary_markdown(stats: dict, title: str = "Summary") -> str:
    """Format a dict of statistics as markdown."""
    lines = [f"## {title}", ""]
    for key, val in stats.items():
        if isinstance(val, float):
            lines.append(f"- **{key}**: {val:,.2f}")
        else:
            lines.append(f"- **{key}**: {val}")
    return "\n".join(lines)
