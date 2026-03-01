"""One-time script: build dictionary.json from Excel + .dta metadata.

Usage:
    python -m scripts.build_dictionary --data-dir "path/to/data"

This reads:
  1. Diccionario ESRU EMOVI 2023.xlsx (2 sheets: Hogar, Entrevistado)
  2. .dta file metadata (variable_labels + value_labels)

Output: src/emovi_mcp/data/dictionary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pyreadstat

try:
    import openpyxl  # noqa: F401 — needed by pandas
except ImportError:
    print("Install openpyxl: pip install openpyxl", file=sys.stderr)
    sys.exit(1)

import pandas as pd


def find_file(data_dir: Path, pattern: str) -> Path | None:
    """Find a file matching pattern recursively."""
    matches = list(data_dir.rglob(pattern))
    return matches[0] if matches else None


def extract_dta_metadata(dta_path: Path) -> dict:
    """Extract variable_labels and value_labels from a .dta file."""
    _, meta = pyreadstat.read_dta(
        str(dta_path),
        metadataonly=True,
        apply_value_formats=False,
    )
    var_labels = dict(zip(meta.column_names, meta.column_labels)) if meta.column_labels else {}
    val_labels = meta.value_labels if meta.value_labels else {}
    # Map each variable to its value label set name
    var_to_label_set = {}
    if hasattr(meta, "variable_to_label") and meta.variable_to_label:
        var_to_label_set = dict(meta.variable_to_label)
    return {
        "variable_labels": var_labels,
        "value_labels": val_labels,
        "variable_to_label_set": var_to_label_set,
        "columns": list(meta.column_names),
    }


def parse_excel_dictionary(xlsx_path: Path) -> dict:
    """Parse the CEEY Excel dictionary into a dict of variable info."""
    result = {}
    for sheet_name in ["Entrevistado", "Hogar"]:
        try:
            df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
        except Exception:
            continue

        # Normalize column names — the Excel has varying formats
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Try to find the variable name and description columns
        var_col = None
        desc_col = None
        section_col = None
        for c in df.columns:
            if "variable" in c or "nombre" in c:
                var_col = c
            if "descripci" in c or "etiqueta" in c or "label" in c:
                desc_col = c
            if "secci" in c or "modulo" in c or "section" in c:
                section_col = c

        if var_col is None:
            # Fallback: first column is variable, second is description
            var_col = df.columns[0]
            desc_col = df.columns[1] if len(df.columns) > 1 else None

        dataset = "entrevistado" if sheet_name == "Entrevistado" else "hogar"

        for _, row in df.iterrows():
            name = str(row[var_col]).strip() if pd.notna(row[var_col]) else ""
            if not name or name == "nan":
                continue
            entry = {
                "label": str(row[desc_col]).strip() if desc_col and pd.notna(row.get(desc_col)) else "",
                "dataset": dataset,
                "section": str(row[section_col]).strip() if section_col and pd.notna(row.get(section_col)) else "",
            }
            result[name] = entry

    return result


def enrich_with_dta(dictionary: dict, dta_meta: dict, dataset_name: str) -> dict:
    """Enrich dictionary entries with .dta metadata (labels, value labels)."""
    var_labels = dta_meta["variable_labels"]
    val_labels = dta_meta["value_labels"]
    var_to_ls = dta_meta["variable_to_label_set"]

    for var_name in dta_meta["columns"]:
        if var_name not in dictionary:
            # Variable exists in .dta but not in Excel — add it
            dictionary[var_name] = {
                "label": var_labels.get(var_name, ""),
                "dataset": dataset_name,
                "section": "",
            }

        entry = dictionary[var_name]

        # Prefer .dta label if Excel label is empty
        if not entry.get("label") and var_name in var_labels:
            entry["label"] = var_labels[var_name]

        # Add value labels if available
        label_set_name = var_to_ls.get(var_name)
        if label_set_name and label_set_name in val_labels:
            vl = val_labels[label_set_name]
            # Convert keys to strings for JSON
            entry["value_labels"] = {str(int(k)): v for k, v in vl.items()}

    return dictionary


def main():
    parser = argparse.ArgumentParser(description="Build dictionary.json for emovi-mcp")
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Root directory containing ESRU-EMOVI data files",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        print(f"Error: {data_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    # 1. Parse Excel dictionary
    xlsx = find_file(data_dir, "Diccionario ESRU EMOVI 2023.xlsx")
    if xlsx:
        print(f"Found Excel dictionary: {xlsx}")
        dictionary = parse_excel_dictionary(xlsx)
        print(f"  Parsed {len(dictionary)} variables from Excel")
    else:
        print("Excel dictionary not found, building from .dta metadata only")
        dictionary = {}

    # 2. Enrich with .dta metadata
    for dataset_name, filename in [
        ("entrevistado", "entrevistado_2023.dta"),
        ("hogar", "hogar_2023.dta"),
        ("inclusion_financiera", "modulo_inclusion_final.dta"),
    ]:
        dta = find_file(data_dir, filename)
        if dta:
            print(f"Enriching from {dta}")
            meta = extract_dta_metadata(dta)
            dictionary = enrich_with_dta(dictionary, meta, dataset_name)
            print(f"  Total variables now: {len(dictionary)}")
        else:
            print(f"  Warning: {filename} not found")

    # 3. Write output
    out_path = Path(__file__).parent.parent / "src" / "emovi_mcp" / "data" / "dictionary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(dictionary)} variables to {out_path}")


if __name__ == "__main__":
    main()
