"""Tests for temporal income comparison logic."""

import numpy as np
import pandas as pd
import pytest

from emovi_mcp.stats_engine import merge_income_2017
from emovi_mcp.config import POVERTY_LINES
from emovi_mcp.helpers.weights import weighted_mean


@pytest.fixture
def entrevistado_df():
    """Synthetic entrevistado with income data."""
    return pd.DataFrame({
        "folio": [1, 2, 3, 4, 5],
        "factor": [100.0, 200.0, 300.0, 400.0, 500.0],
        "ingc_pc": [5000.0, 3000.0, 1000.0, 8000.0, 2000.0],
        "rururb": [2, 2, 1, 2, 1],
        "sexo": [1, 2, 1, 2, 1],
        "cohorte": [1, 2, 3, 4, 1],
    })


@pytest.fixture
def ingreso_2017_df():
    """Synthetic 2017 income data."""
    return pd.DataFrame({
        "folio": [1, 2, 3, 4, 6],  # folio 5 missing, folio 6 extra
        "ingc_pc": [4000.0, 4000.0, 1500.0, 6000.0, 9000.0],
    })


class TestMergeIncome:
    def test_merge_basic(self, entrevistado_df, ingreso_2017_df):
        merged = merge_income_2017(entrevistado_df, ingreso_2017_df)
        assert "ingc_pc_2017" in merged.columns
        assert len(merged) == len(entrevistado_df)

    def test_merge_matches_correctly(self, entrevistado_df, ingreso_2017_df):
        merged = merge_income_2017(entrevistado_df, ingreso_2017_df)
        # folio 1 should have 2017 income = 4000
        row1 = merged[merged["folio"] == 1].iloc[0]
        assert row1["ingc_pc_2017"] == 4000.0

    def test_merge_unmatched_is_nan(self, entrevistado_df, ingreso_2017_df):
        merged = merge_income_2017(entrevistado_df, ingreso_2017_df)
        # folio 5 has no match in 2017
        row5 = merged[merged["folio"] == 5].iloc[0]
        assert pd.isna(row5["ingc_pc_2017"])

    def test_merge_alternative_column_name(self, entrevistado_df):
        """Test with non-standard income column name."""
        df_ing = pd.DataFrame({
            "folio": [1, 2, 3],
            "ingreso_pc": [4000.0, 5000.0, 6000.0],  # different name
        })
        merged = merge_income_2017(entrevistado_df, df_ing)
        assert "ingc_pc_2017" in merged.columns
        assert merged.loc[merged["folio"] == 1, "ingc_pc_2017"].iloc[0] == 4000.0


class TestPovertyLines:
    def test_2023_lines_exist(self):
        assert 2023 in POVERTY_LINES
        assert "moderate" in POVERTY_LINES[2023]
        assert "extreme" in POVERTY_LINES[2023]

    def test_2017_lines_exist(self):
        assert 2017 in POVERTY_LINES
        assert "moderate" in POVERTY_LINES[2017]

    def test_urban_higher_than_rural(self):
        for year in (2017, 2023):
            for level in ("moderate", "extreme"):
                assert (
                    POVERTY_LINES[year][level]["urban"]
                    > POVERTY_LINES[year][level]["rural"]
                )

    def test_moderate_higher_than_extreme(self):
        for year in (2017, 2023):
            for area in ("urban", "rural"):
                assert (
                    POVERTY_LINES[year]["moderate"][area]
                    > POVERTY_LINES[year]["extreme"][area]
                )


class TestIncomeChange:
    def test_income_change_computation(self, entrevistado_df, ingreso_2017_df):
        merged = merge_income_2017(entrevistado_df, ingreso_2017_df)
        change = merged["ingc_pc"] - merged["ingc_pc_2017"]
        # folio 1: 5000-4000=1000, folio 2: 3000-4000=-1000
        assert change.iloc[0] == 1000.0
        assert change.iloc[1] == -1000.0
