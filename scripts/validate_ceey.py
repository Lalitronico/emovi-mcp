#!/usr/bin/env python3
"""Validate emovi-mcp transition matrices against CEEY 2025 reference values.

Usage:
    python scripts/validate_ceey.py

Requires EMOVI_DATA_DIR to be set to the directory containing .dta files.
Generates a comparison report at validation/comparison_report.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add project to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from emovi_mcp.config import MOBILITY_DIMENSIONS
from emovi_mcp.data_loader import load_dataset
from emovi_mcp.stats_engine import compute_transition_matrix


def load_reference_values() -> dict:
    """Load CEEY reference values from JSON."""
    ref_path = project_root / "validation" / "ceey_reference_values.json"
    with open(ref_path, encoding="utf-8") as f:
        return json.load(f)


def compare_matrices(
    computed: pd.DataFrame,
    reference: list[list[float]],
    labels: list[str],
) -> pd.DataFrame:
    """Compare computed matrix against reference cell-by-cell.

    Returns a DataFrame with columns: row, col, computed, reference, diff, abs_diff
    """
    rows = []
    n = min(computed.shape[0], len(reference))
    for i in range(n):
        for j in range(n):
            c_val = computed.iloc[i, j]
            r_val = reference[i][j]
            rows.append({
                "origin": labels[i] if i < len(labels) else str(i),
                "destination": labels[j] if j < len(labels) else str(j),
                "computed": c_val,
                "reference": r_val,
                "diff": c_val - r_val,
                "abs_diff": abs(c_val - r_val),
            })
    return pd.DataFrame(rows)


def generate_report(results: dict) -> str:
    """Generate markdown comparison report."""
    lines = [
        "# CEEY 2025 Validation Report",
        "",
        f"*Generated automatically by `scripts/validate_ceey.py`*",
        "",
        "## Overview",
        "",
        "This report compares transition matrices computed by emovi-mcp against ",
        "reference values from the CEEY Informe de Movilidad Social en Mexico 2025.",
        "",
        "**Important caveats:**",
        "- CEEY uses MCA (Multiple Correspondence Analysis) for wealth indices; we use PCA",
        "- Small differences are expected due to rounding and methodological choices",
        "- Reference values are approximate (extracted from .do output, not final published tables)",
        "",
    ]

    for dim_name, dim_result in results.items():
        lines.append(f"## {dim_name.title()}")
        lines.append("")

        if dim_result.get("skipped"):
            lines.append(f"*Skipped: {dim_result['reason']}*")
            lines.append("")
            continue

        # Summary stats
        summary = dim_result.get("summary", {})
        if summary:
            lines.append("### Summary Statistics")
            lines.append("")
            for k, v in summary.items():
                if isinstance(v, float):
                    lines.append(f"- **{k}**: {v:.4f}")
                else:
                    lines.append(f"- **{k}**: {v}")
            lines.append("")

        # Cell-by-cell comparison
        comparison = dim_result.get("comparison")
        if comparison is not None and len(comparison) > 0:
            lines.append("### Cell-by-Cell Comparison")
            lines.append("")
            lines.append("| Origin | Destination | Computed | Reference | Diff | Abs Diff |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for _, row in comparison.iterrows():
                lines.append(
                    f"| {row['origin']} | {row['destination']} | "
                    f"{row['computed']:.3f} | {row['reference']:.3f} | "
                    f"{row['diff']:+.3f} | {row['abs_diff']:.3f} |"
                )
            lines.append("")

            # Summary of deviations
            mean_abs_diff = comparison["abs_diff"].mean()
            max_abs_diff = comparison["abs_diff"].max()
            lines.append(f"- **Mean absolute difference**: {mean_abs_diff:.4f}")
            lines.append(f"- **Max absolute difference**: {max_abs_diff:.4f}")
            lines.append(f"- **Cells within 5pp**: {(comparison['abs_diff'] < 0.05).sum()}/{len(comparison)}")
            lines.append("")

        # Computed matrix
        matrix = dim_result.get("matrix")
        if matrix is not None:
            lines.append("### Computed Matrix")
            lines.append("")
            col_labels = [str(c) for c in matrix.columns]
            lines.append(f"| Origen \\\\ Destino | {' | '.join(col_labels)} |")
            lines.append(f"| --- | {' | '.join(['---'] * len(col_labels))} |")
            for idx, row in matrix.iterrows():
                cells = [f"{v:.3f}" for v in row]
                lines.append(f"| {idx} | {' | '.join(cells)} |")
            lines.append("")

    return "\n".join(lines)


def main():
    print("Loading reference values...")
    ref = load_reference_values()

    print("Loading ESRU-EMOVI 2023 data...")
    try:
        df = load_dataset("entrevistado")
    except (EnvironmentError, FileNotFoundError) as e:
        print(f"ERROR: Cannot load data — {e}")
        print("Set EMOVI_DATA_DIR to run validation against real data.")
        sys.exit(1)

    results = {}

    # --- Education ---
    print("Computing education transition matrix...")
    try:
        edu_result = compute_transition_matrix(df, "education")
        edu_matrix = edu_result["matrices"].get("all")
        edu_summary = edu_result["summary"].get("all", {})

        edu_ref = ref.get("education_4cat", {})
        if edu_matrix is not None and edu_ref.get("matrix") is not None:
            comparison = compare_matrices(
                edu_matrix, edu_ref["matrix"], edu_ref.get("labels", [])
            )
            results["education"] = {
                "matrix": edu_matrix,
                "summary": edu_summary,
                "comparison": comparison,
            }
        else:
            results["education"] = {
                "matrix": edu_matrix,
                "summary": edu_summary,
                "comparison": None,
            }
    except Exception as e:
        results["education"] = {"skipped": True, "reason": str(e)}

    # --- Occupation ---
    print("Computing occupation transition matrix...")
    try:
        occ_result = compute_transition_matrix(df, "occupation")
        occ_matrix = occ_result["matrices"].get("all")
        occ_summary = occ_result["summary"].get("all", {})
        results["occupation"] = {
            "matrix": occ_matrix,
            "summary": occ_summary,
            "comparison": None,  # No reference matrix available yet
        }
    except Exception as e:
        results["occupation"] = {"skipped": True, "reason": str(e)}

    # --- Wealth ---
    print("Computing wealth transition matrix (PCA)...")
    try:
        wlth_result = compute_transition_matrix(df, "wealth")
        wlth_matrix = wlth_result["matrices"].get("all")
        wlth_summary = wlth_result["summary"].get("all", {})
        results["wealth"] = {
            "matrix": wlth_matrix,
            "summary": wlth_summary,
            "comparison": None,  # MCA vs PCA — no direct comparison
        }
    except Exception as e:
        results["wealth"] = {"skipped": True, "reason": str(e)}

    # Generate report
    print("Generating comparison report...")
    report = generate_report(results)

    report_path = project_root / "validation" / "comparison_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"Report saved to: {report_path}")

    # Print summary
    print("\n=== Summary ===")
    for dim, res in results.items():
        if res.get("skipped"):
            print(f"  {dim}: SKIPPED — {res['reason']}")
        elif res.get("comparison") is not None:
            mad = res["comparison"]["abs_diff"].mean()
            print(f"  {dim}: Mean abs diff = {mad:.4f}")
        else:
            print(f"  {dim}: Computed (no reference for comparison)")


if __name__ == "__main__":
    main()
