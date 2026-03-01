"""Tests for the statistics engine and weighted helpers."""

import numpy as np
import pandas as pd
import pytest

from emovi_mcp.helpers.weights import (
    create_weighted_quintiles,
    weighted_frequency,
    weighted_mean,
    weighted_median,
    weighted_quantile,
    weighted_std,
)
from emovi_mcp.stats_engine import build_padres_edu, compute_descriptive_stats


class TestWeightedMean:
    def test_equal_weights(self):
        vals = pd.Series([10.0, 20.0, 30.0])
        wts = pd.Series([1.0, 1.0, 1.0])
        assert weighted_mean(vals, wts) == pytest.approx(20.0)

    def test_unequal_weights(self):
        vals = pd.Series([10.0, 20.0])
        wts = pd.Series([3.0, 1.0])
        # (10*3 + 20*1) / 4 = 12.5
        assert weighted_mean(vals, wts) == pytest.approx(12.5)

    def test_with_nans(self):
        vals = pd.Series([10.0, np.nan, 30.0])
        wts = pd.Series([1.0, 1.0, 1.0])
        assert weighted_mean(vals, wts) == pytest.approx(20.0)

    def test_all_nan(self):
        vals = pd.Series([np.nan, np.nan])
        wts = pd.Series([1.0, 1.0])
        assert np.isnan(weighted_mean(vals, wts))


class TestWeightedFrequency:
    def test_basic(self):
        vals = pd.Series([1, 1, 2, 2])
        wts = pd.Series([100.0, 100.0, 300.0, 300.0])
        result = weighted_frequency(vals, wts)
        assert len(result) == 2
        # Value 1: 200/800 = 0.25, Value 2: 600/800 = 0.75
        row_1 = result[result["value"] == 1].iloc[0]
        assert row_1["proportion"] == pytest.approx(0.25)
        row_2 = result[result["value"] == 2].iloc[0]
        assert row_2["proportion"] == pytest.approx(0.75)


class TestWeightedQuantile:
    def test_median(self):
        vals = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        wts = pd.Series([1.0, 1.0, 1.0, 1.0, 1.0])
        med = weighted_median(vals, wts)
        assert med == pytest.approx(3.0, abs=0.5)


class TestWeightedQuintiles:
    def test_five_groups(self):
        vals = pd.Series(range(100), dtype=float)
        wts = pd.Series([1.0] * 100)
        q = create_weighted_quintiles(vals, wts, nq=5)
        # Should have values 1-5
        assert set(q.dropna().unique()) == {1, 2, 3, 4, 5}


class TestBuildPadresEdu:
    def test_max_of_parents(self):
        df = pd.DataFrame({
            "educp": [1, 3, np.nan, np.nan],
            "educm": [2, 1, 4, np.nan],
        })
        result = build_padres_edu(df)
        assert result.iloc[0] == 2  # max(1, 2)
        assert result.iloc[1] == 3  # max(3, 1)
        assert result.iloc[2] == 4  # only mother
        assert pd.isna(result.iloc[3])  # both missing

    def test_uses_existing_column(self):
        df = pd.DataFrame({
            "padres_edu": [1, 2, 3],
            "educp": [4, 4, 4],
            "educm": [4, 4, 4],
        })
        result = build_padres_edu(df)
        # Should return existing column, not recompute
        assert list(result) == [1, 2, 3]


class TestComputeDescriptiveStats:
    def test_basic(self, simple_df):
        result = compute_descriptive_stats(simple_df, "var_b", "factor")
        stats = result["all"]
        assert stats["n_valid"] == 4
        assert stats["min"] == 10.0
        assert stats["max"] == 40.0

    def test_by_group(self, simple_df):
        result = compute_descriptive_stats(simple_df, "var_b", "factor", by="group")
        assert "A" in result
        assert "B" in result
        assert result["A"]["n_valid"] == 2
        assert result["B"]["n_valid"] == 2
