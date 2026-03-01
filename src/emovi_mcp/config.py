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
    "income_quintile": {
        "origin_var": "quintile_origin",   # built at runtime from ingc_pc
        "dest_var": "quintile_dest",       # built at runtime from ingc_pc
        "labels": {1: "Q1 (mas pobre)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (mas rico)"},
        "description": "Movilidad por quintiles de ingreso per capita",
    },
}

# ---------------------------------------------------------------------------
# pyreadstat loading options
# ---------------------------------------------------------------------------

DTA_READ_OPTIONS = {
    "apply_value_formats": False,  # convert_categoricals=False equivalent
}
