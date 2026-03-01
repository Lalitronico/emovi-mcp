"""Configuration: environment variables, file mappings, survey constants."""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Data directory
# ---------------------------------------------------------------------------

def get_data_dir() -> Path:
    """Return the directory containing .dta files.

    Resolution order:
      1. EMOVI_DATA_DIR environment variable
      2. Fallback: searches common relative paths
    """
    env = os.environ.get("EMOVI_DATA_DIR")
    if env:
        p = Path(env)
        if p.is_dir():
            return p
        raise FileNotFoundError(f"EMOVI_DATA_DIR={env!r} is not a valid directory")
    raise EnvironmentError(
        "Set EMOVI_DATA_DIR to the directory containing ESRU-EMOVI .dta files. "
        "Example: EMOVI_DATA_DIR=/path/to/3 BASES DE DATOS/Data"
    )


# ---------------------------------------------------------------------------
# Dataset file mappings
# ---------------------------------------------------------------------------

DATASETS: dict[str, dict] = {
    "entrevistado": {
        "filename": "entrevistado_2023.dta",
        "description": "Datos del entrevistado (principal)",
        "rows_approx": 17_843,
        "cols_approx": 296,
    },
    "hogar": {
        "filename": "hogar_2023.dta",
        "description": "Roster de miembros del hogar",
        "rows_approx": 55_477,
        "cols_approx": 56,
    },
    "ingreso_2017": {
        "filename": "ingreso_2017.dta",
        "description": "Ingreso per capita imputado 2017 (comparacion temporal)",
        "rows_approx": 17_665,
        "cols_approx": 2,
    },
    "inclusion_financiera": {
        "filename": "modulo_inclusion_final.dta",
        "description": "Modulo de inclusion financiera",
        "rows_approx": 5_976,
        "cols_approx": 109,
    },
}

# ---------------------------------------------------------------------------
# Survey design
# ---------------------------------------------------------------------------

WEIGHT_COL = "factor"
PSU_COL = "upm_muestra"
STRATA_COL = "est"

# Per-dataset weight columns
WEIGHT_COLUMNS: dict[str, str] = {
    "entrevistado": "factor",
    "hogar": "factor",
    "ingreso_2017": "factor",
    "inclusion_financiera": "fac_inc",
}


def get_weight_col(dataset: str) -> str:
    """Return the appropriate weight column for a dataset."""
    return WEIGHT_COLUMNS.get(dataset, WEIGHT_COL)


# ---------------------------------------------------------------------------
# Poverty lines from CEEY .do file (monthly per capita, MXN)
# ---------------------------------------------------------------------------

POVERTY_LINES = {
    2023: {
        "moderate": {"rural": 3_165.34, "urban": 4_386.21},
        "extreme": {"rural": 1_701.52, "urban": 2_224.83},
    },
    2017: {
        "moderate": {"rural": 2_234.15, "urban": 3_191.54},
        "extreme": {"rural": 1_130.92, "urban": 1_491.07},
    },
}

# ---------------------------------------------------------------------------
# Financial inclusion dimensions
# ---------------------------------------------------------------------------

FINANCIAL_INCLUSION_DIMENSIONS: dict[str, dict] = {
    "savings": {
        "description": "Ahorro formal e informal",
        "variables": ["p6_1", "p6_2", "p6_3", "p6_4", "p6_5", "p6_6"],
    },
    "credit": {
        "description": "Acceso a credito y deuda",
        "variables": ["p7_1", "p7_2", "p7_3", "p7_4", "p7_5"],
    },
    "banking": {
        "description": "Servicios bancarios y productos financieros",
        "variables": ["p4_1", "p4_2", "p4_3", "p4_4", "p4_5"],
    },
    "literacy": {
        "description": "Educacion financiera y conocimientos",
        "variables": ["p10_1", "p10_2", "p10_3", "p10_4"],
    },
    "discrimination": {
        "description": "Discriminacion en servicios financieros",
        "variables": ["p12_1", "p12_2", "p12_3"],
    },
}

# ---------------------------------------------------------------------------
# Region mappings (from .do file)
# ---------------------------------------------------------------------------

REGION_LABELS: dict[int, str] = {
    1: "Norte",
    2: "Noroccidente",
    3: "Centro-norte",
    4: "Centro",
    5: "Sur",
}

REGION_14_STATES: dict[int, list[int]] = {
    1: [2, 5, 8, 19, 26, 28],       # Norte
    2: [3, 10, 18, 25, 32],          # Noroccidente
    3: [1, 6, 14, 16, 24],           # Centro-norte
    4: [9, 11, 13, 15, 17, 21, 22, 29],  # Centro
    5: [4, 7, 12, 20, 23, 27, 30, 31],   # Sur
}

# ---------------------------------------------------------------------------
# Cohort definitions
# ---------------------------------------------------------------------------

COHORT_LABELS: dict[int, str] = {
    1: "25-34 anios",
    2: "35-44 anios",
    3: "45-54 anios",
    4: "55-64 anios",
}

# ---------------------------------------------------------------------------
# Education labels (from .do line 203, 230)
# ---------------------------------------------------------------------------

EDUC_6_LABELS: dict[int, str] = {
    1: "Sin estudios",
    2: "Primaria incompleta",
    3: "Primaria",
    4: "Secundaria",
    5: "Preparatoria",
    6: "Profesional",
}

EDUC_4_LABELS: dict[int, str] = {
    1: "Primaria o menos",
    2: "Secundaria",
    3: "Media superior",
    4: "Profesional",
}

# ---------------------------------------------------------------------------
# Occupational class labels
# ---------------------------------------------------------------------------

CLASE_LABELS: dict[int, str] = {
    1: "Manual baja calificacion",
    2: "Manual alta calificacion",
    3: "Comercio",
    4: "No manual baja calificacion",
    5: "No manual alta calificacion",
    6: "Agricola",
}

# ---------------------------------------------------------------------------
# Sex labels
# ---------------------------------------------------------------------------

SEX_LABELS: dict[int, str] = {
    1: "Hombre",
    2: "Mujer",
}

# ---------------------------------------------------------------------------
# Mobility dimension configs
# ---------------------------------------------------------------------------

MOBILITY_DIMENSIONS: dict[str, dict] = {
    "education": {
        "origin_var": "padres_edu",   # max(educp, educm) -- built at runtime
        "dest_var": "educ",           # uses educ_2 (4-cat) pre-built in data or we build it
        "labels": EDUC_4_LABELS,
        "description": "Movilidad educativa intergeneracional (4 categorias)",
    },
    "occupation": {
        "origin_var": "clasep",
        "dest_var": "clase",
        "labels": CLASE_LABELS,
        "description": "Movilidad ocupacional intergeneracional",
    },
    "wealth": {
        "origin_var": "quintile_origin",   # built at runtime via PCA on assets
        "dest_var": "quintile_dest",       # built at runtime via PCA on assets
        "labels": {1: "Q1 (mas pobre)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (mas rico)"},
        "description": "Movilidad por quintiles de riqueza (indice PCA de activos)",
    },
}

# ---------------------------------------------------------------------------
# pyreadstat loading options
# ---------------------------------------------------------------------------

DTA_READ_OPTIONS = {
    "apply_value_formats": False,  # convert_categoricals=False equivalent
}
