"""Tests for financial inclusion tool logic."""

import numpy as np
import pandas as pd
import pytest

from emovi_mcp.config import get_weight_col, FINANCIAL_INCLUSION_DIMENSIONS
from emovi_mcp.helpers.weights import weighted_frequency


@pytest.fixture
def inclusion_df():
    """Synthetic financial inclusion DataFrame."""
    rng = np.random.default_rng(99)
    n = 50
    data = {
        "fac_inc": rng.uniform(100, 3000, n),
        "sexo": rng.choice([1, 2], n),
        "entidad": rng.choice([1, 2, 3], n),
    }
    # Add banking variables
    for var in ["p4_1", "p4_2", "p4_3", "p4_4", "p4_5"]:
        data[var] = rng.choice([1, 2], n)
    # Add savings variables
    for var in ["p6_1", "p6_2", "p6_3", "p6_4", "p6_5", "p6_6"]:
        data[var] = rng.choice([1, 2, 3], n)
    # Add credit variables
    for var in ["p7_1", "p7_2", "p7_3", "p7_4", "p7_5"]:
        data[var] = rng.choice([1, 2], n)
    return pd.DataFrame(data)


class TestDynamicWeights:
    def test_entrevistado_weight(self):
        assert get_weight_col("entrevistado") == "factor"

    def test_inclusion_weight(self):
        assert get_weight_col("inclusion_financiera") == "fac_inc"

    def test_unknown_dataset_fallback(self):
        assert get_weight_col("nonexistent") == "factor"


class TestFinancialDimensions:
    def test_all_dimensions_exist(self):
        expected = {"savings", "credit", "banking", "literacy", "discrimination"}
        assert set(FINANCIAL_INCLUSION_DIMENSIONS.keys()) == expected

    def test_banking_variables(self, inclusion_df):
        dim = FINANCIAL_INCLUSION_DIMENSIONS["banking"]
        available = [v for v in dim["variables"] if v in inclusion_df.columns]
        assert len(available) > 0

    def test_weighted_frequency_on_inclusion(self, inclusion_df):
        freq = weighted_frequency(inclusion_df["p4_1"], inclusion_df["fac_inc"])
        assert "proportion" in freq.columns
        assert freq["proportion"].sum() == pytest.approx(1.0, abs=0.01)

    def test_savings_variables(self, inclusion_df):
        dim = FINANCIAL_INCLUSION_DIMENSIONS["savings"]
        available = [v for v in dim["variables"] if v in inclusion_df.columns]
        assert len(available) == 6
