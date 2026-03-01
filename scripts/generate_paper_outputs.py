#!/usr/bin/env python3
"""Generate tables and figures for the academic paper.

Usage:
    python scripts/generate_paper_outputs.py

Requires EMOVI_DATA_DIR to be set to the directory containing .dta files.
Outputs are written to paper/tables/ and paper/figures/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add project to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from emovi_mcp.data_loader import load_dataset
from emovi_mcp.stats_engine import compute_transition_matrix
from emovi_mcp.helpers.mobility_indices import compute_all_indices

TABLES_DIR = project_root / "paper" / "tables"
FIGURES_DIR = project_root / "paper" / "figures"


def ensure_dirs():
    """Create output directories."""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def matrix_to_latex(
    matrix: pd.DataFrame,
    se_matrix: pd.DataFrame | None = None,
    caption: str = "",
    label: str = "",
) -> str:
    """Convert transition matrix to LaTeX tabular with optional SE."""
    n = matrix.shape[0]
    col_labels = [str(c) for c in matrix.columns]

    lines = []
    lines.append("\\begin{table}[H]")
    lines.append("\\centering")
    lines.append("\\small")
    lines.append(f"\\caption{{{caption}}}")
    lines.append(f"\\label{{{label}}}")
    col_spec = "l" + "c" * n
    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append("\\toprule")

    # Header
    header = "\\textbf{Origen $\\backslash$ Destino}"
    for cl in col_labels:
        header += f" & \\textbf{{{cl}}}"
    header += " \\\\"
    lines.append(header)
    lines.append("\\midrule")

    # Rows
    for idx, row in matrix.iterrows():
        row_str = f"\\textbf{{{idx}}}"
        for j, val in enumerate(row):
            if se_matrix is not None:
                se_val = se_matrix.iloc[matrix.index.get_loc(idx), j]
                row_str += f" & {val:.3f} ({se_val:.3f})"
            else:
                row_str += f" & {val:.3f}"
        row_str += " \\\\"
        lines.append(row_str)

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def indices_to_latex(indices: dict, dimension: str) -> str:
    """Convert mobility indices dict to LaTeX table."""
    lines = []
    lines.append("\\begin{table}[H]")
    lines.append("\\centering")
    lines.append("\\small")
    lines.append(f"\\caption{{Índices de movilidad --- {dimension.title()}}}")
    lines.append(f"\\label{{tab:indices_{dimension}}}")
    lines.append("\\begin{tabular}{lr}")
    lines.append("\\toprule")
    lines.append("\\textbf{Índice} & \\textbf{Valor} \\\\")
    lines.append("\\midrule")

    display_names = {
        "shorrocks_m": "Shorrocks $M$",
        "intergenerational_r": "Correlación intergeneracional $r$",
        "corner_odds_ratio": "Razón de momios de esquina $\\theta$",
        "diagonal_persistence": "Persistencia diagonal",
        "upward_pct": "Movilidad ascendente (\\%)",
        "downward_pct": "Movilidad descendente (\\%)",
    }

    for key, val in indices.items():
        if key == "prais":
            # Prais is a dict, handle separately
            continue
        name = display_names.get(key, key)
        if isinstance(val, float):
            lines.append(f"{name} & {val:.4f} \\\\")
        else:
            lines.append(f"{name} & {val} \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    # Prais table
    prais = indices.get("prais", {})
    if prais:
        lines.append("")
        lines.append("\\begin{table}[H]")
        lines.append("\\centering")
        lines.append("\\small")
        lines.append(f"\\caption{{Índice de Prais (probabilidad de escape) --- {dimension.title()}}}")
        lines.append(f"\\label{{tab:prais_{dimension}}}")
        lines.append("\\begin{tabular}{lr}")
        lines.append("\\toprule")
        lines.append("\\textbf{Categoría de origen} & \\textbf{Prob.\\ de escape} \\\\")
        lines.append("\\midrule")
        for cat, val in prais.items():
            lines.append(f"{cat} & {val:.4f} \\\\")
        lines.append("\\bottomrule")
        lines.append("\\end{tabular}")
        lines.append("\\end{table}")

    return "\n".join(lines)


def generate_figures(df: pd.DataFrame):
    """Generate visualization figures for the paper."""
    try:
        from emovi_mcp.helpers.visualization import (
            heatmap_transition_matrix,
            bar_chart_prais,
        )
        from emovi_mcp.helpers.mobility_indices import prais_index
        import base64
    except ImportError:
        print("WARNING: matplotlib/seaborn not installed. Skipping figures.")
        return

    for dimension in ["education", "occupation", "wealth"]:
        try:
            result = compute_transition_matrix(df, dimension)
            matrix = result["matrices"].get("all")
            if matrix is None:
                continue

            # Heatmap
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            b64_uri = heatmap_transition_matrix(
                matrix, title=f"Movilidad {dimension.title()}"
            )
            # Decode and save as PNG
            b64_data = b64_uri.split(",", 1)[1]
            png_bytes = base64.b64decode(b64_data)
            out_path = FIGURES_DIR / f"heatmap_{dimension}.png"
            out_path.write_bytes(png_bytes)
            print(f"  Saved: {out_path}")

            # Prais bar chart
            prais = prais_index(matrix)
            prais_dict = {str(k): v for k, v in zip(matrix.index, prais)}
            b64_uri = bar_chart_prais(
                prais_dict, title=f"Prais --- {dimension.title()}"
            )
            b64_data = b64_uri.split(",", 1)[1]
            png_bytes = base64.b64decode(b64_data)
            out_path = FIGURES_DIR / f"prais_{dimension}.png"
            out_path.write_bytes(png_bytes)
            print(f"  Saved: {out_path}")

        except Exception as e:
            print(f"  WARNING: {dimension} figures failed — {e}")


def main():
    ensure_dirs()

    print("Loading ESRU-EMOVI 2023 data...")
    try:
        df = load_dataset("entrevistado")
    except (EnvironmentError, FileNotFoundError) as e:
        print(f"ERROR: Cannot load data — {e}")
        print("Set EMOVI_DATA_DIR to run paper output generation.")
        sys.exit(1)

    # --- Transition matrices and indices ---
    for dimension in ["education", "occupation", "wealth"]:
        print(f"\nProcessing {dimension}...")
        try:
            result = compute_transition_matrix(df, dimension, compute_se=True)
            matrix = result["matrices"].get("all")
            summary = result["summary"].get("all", {})
            se_matrix = result.get("standard_errors", {}).get("all")

            if matrix is None:
                print(f"  Skipped: no matrix for {dimension}")
                continue

            # Save matrix LaTeX
            caption = f"Matriz de transición intergeneracional --- {dimension.title()}"
            if se_matrix is not None:
                caption += " (errores estándar entre paréntesis)"
            tex = matrix_to_latex(
                matrix,
                se_matrix=se_matrix,
                caption=caption,
                label=f"tab:{dimension}_matrix",
            )
            out_path = TABLES_DIR / f"{dimension}_matrix_se.tex"
            out_path.write_text(tex, encoding="utf-8")
            print(f"  Saved: {out_path}")

            # Save indices LaTeX
            indices = summary.get("indices", {})
            if indices:
                tex = indices_to_latex(indices, dimension)
                out_path = TABLES_DIR / f"mobility_indices_{dimension}.tex"
                out_path.write_text(tex, encoding="utf-8")
                print(f"  Saved: {out_path}")

        except Exception as e:
            print(f"  ERROR: {dimension} — {e}")

    # --- Figures ---
    print("\nGenerating figures...")
    generate_figures(df)

    print("\nDone. Check paper/tables/ and paper/figures/.")


if __name__ == "__main__":
    main()
