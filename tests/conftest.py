"""Shared test fixtures — synthetic data that mirrors ESRU-EMOVI structure."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    """Minimal DataFrame mimicking entrevistado_2023.dta structure."""
    rng = np.random.default_rng(42)
    n = 200

    df = pd.DataFrame({
        "factor": rng.uniform(100, 5000, n),
        "upm_muestra": rng.choice(["upm_01", "upm_02", "upm_03"], n),
        "est": rng.choice([1, 2, 3, 4, 5], n),
        "sexo": rng.choice([1, 2], n),
        "cohorte": rng.choice([1, 2, 3, 4], n),
        "region": rng.choice([1, 2, 3, 4, 5], n),
        "region_14": rng.choice([1, 2, 3, 4, 5], n),
        "rururb": rng.choice([1, 2], n),
        "educ": rng.choice([1, 2, 3, 4], n),
        "educp": rng.choice([1, 2, 3, 4, np.nan], n),
        "educm": rng.choice([1, 2, 3, 4, np.nan], n),
        "clase": rng.choice([1, 2, 3, 4, 5, 6], n),
        "clasep": rng.choice([1, 2, 3, 4, 5, 6, np.nan], n),
        "ingc_pc": rng.lognormal(mean=8.5, sigma=0.8, size=n),
        "entidad": rng.choice(range(1, 33), n),
    })
    return df


@pytest.fixture
def simple_df():
    """Very small DataFrame for deterministic unit tests."""
    return pd.DataFrame({
        "factor": [100.0, 200.0, 300.0, 400.0],
        "var_a": [1, 1, 2, 2],
        "var_b": [10.0, 20.0, 30.0, 40.0],
        "group": ["A", "A", "B", "B"],
    })
