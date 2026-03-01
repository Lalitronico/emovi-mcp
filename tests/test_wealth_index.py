"""Tests for wealth index construction via PCA on household assets."""

import numpy as np
import pandas as pd
import pytest

from emovi_mcp.helpers.wealth_index import (
    _build_overcrowding,
    _pca_first_component,
    _recode_binary,
    _recode_count_to_binary,
    build_current_asset_indicators,
    build_origin_asset_indicators,
    compute_wealth_index,
)


class TestRecodeBinary:
    def test_yes_no(self):
        s = pd.Series([1, 2, 1, 2])
        result = _recode_binary(s)
        assert list(result) == [1.0, 0.0, 1.0, 0.0]

    def test_missing_codes(self):
        s = pd.Series([1, 2, 8, 9])
        result = _recode_binary(s)
        assert result.iloc[0] == 1.0
        assert result.iloc[1] == 0.0
        assert pd.isna(result.iloc[2])
        assert pd.isna(result.iloc[3])

    def test_with_nan(self):
        s = pd.Series([1, np.nan, 2])
        result = _recode_binary(s)
        assert result.iloc[0] == 1.0
        assert pd.isna(result.iloc[1])
        assert result.iloc[2] == 0.0


class TestRecodeCountToBinary:
    def test_basic(self):
        s = pd.Series([0, 1, 2, 5])
        result = _recode_count_to_binary(s)
        assert list(result) == [0.0, 1.0, 1.0, 1.0]

    def test_with_nan(self):
        s = pd.Series([0, np.nan, 3])
        result = _recode_count_to_binary(s)
        assert result.iloc[0] == 0.0
        assert pd.isna(result.iloc[1])
        assert result.iloc[2] == 1.0


class TestBuildOvercrowding:
    def test_not_overcrowded(self):
        # 4 people / 2 rooms = 2.0 <= 2.5 -> 1
        hh = pd.Series([4.0])
        rooms = pd.Series([2.0])
        result = _build_overcrowding(hh, rooms)
        assert result.iloc[0] == 1.0

    def test_overcrowded(self):
        # 8 people / 2 rooms = 4.0 > 2.5 -> 0
        hh = pd.Series([8.0])
        rooms = pd.Series([2.0])
        result = _build_overcrowding(hh, rooms)
        assert result.iloc[0] == 0.0

    def test_boundary(self):
        # 5 people / 2 rooms = 2.5 <= 2.5 -> 1
        hh = pd.Series([5.0])
        rooms = pd.Series([2.0])
        result = _build_overcrowding(hh, rooms)
        assert result.iloc[0] == 1.0

    def test_zero_rooms(self):
        hh = pd.Series([4.0])
        rooms = pd.Series([0.0])
        result = _build_overcrowding(hh, rooms)
        assert pd.isna(result.iloc[0])

    def test_missing(self):
        hh = pd.Series([np.nan, 4.0])
        rooms = pd.Series([2.0, np.nan])
        result = _build_overcrowding(hh, rooms)
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])


class TestPCAFirstComponent:
    def test_positive_orientation(self):
        """Scores should correlate positively with sum of indicators."""
        rng = np.random.default_rng(123)
        n = 200
        # Create correlated binary indicators: rich households have more 1s
        wealth = rng.normal(0, 1, n)
        X = np.column_stack([
            (wealth + rng.normal(0, 0.5, n) > 0).astype(float)
            for _ in range(10)
        ])
        scores = _pca_first_component(X)
        # Should positively correlate with asset sum
        corr = np.corrcoef(scores, X.sum(axis=1))[0, 1]
        assert corr > 0.5

    def test_handles_missing(self):
        """PCA should handle NaN values via mean imputation."""
        X = np.array([
            [1.0, 0.0, 1.0],
            [0.0, 1.0, np.nan],
            [1.0, 1.0, 1.0],
            [0.0, 0.0, 0.0],
        ])
        scores = _pca_first_component(X)
        assert len(scores) == 4
        assert not np.any(np.isnan(scores))

    def test_constant_column(self):
        """Should handle columns with zero variance."""
        X = np.array([
            [1.0, 1.0, 1.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 1.0],
            [0.0, 1.0, 0.0],
        ])
        scores = _pca_first_component(X)
        assert len(scores) == 4
        assert not np.any(np.isnan(scores))

    def test_more_assets_higher_score(self):
        """Households with more assets should get higher scores."""
        X = np.array([
            [1.0, 1.0, 1.0, 1.0, 1.0],  # rich
            [1.0, 1.0, 1.0, 1.0, 0.0],
            [1.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0],  # poor
        ])
        scores = _pca_first_component(X)
        assert scores[0] > scores[3]


class TestBuildOriginAssetIndicators:
    def test_builds_correct_columns(self):
        df = pd.DataFrame({
            "p31a": [1, 2], "p31b": [2, 1],
            "p32a": [1, 1],
            "p26a": [1, 2],
            "p30": [0, 2],
            "p22": [4.0, 8.0], "p24": [2.0, 2.0],
        })
        indicators = build_origin_asset_indicators(df)
        assert "p31a" in indicators.columns
        assert "p31b" in indicators.columns
        assert "p32a" in indicators.columns
        assert "p26a" in indicators.columns
        assert "p30_bin" in indicators.columns
        assert "hac_or" in indicators.columns

    def test_recodes_correctly(self):
        df = pd.DataFrame({
            "p31a": [1, 2],  # Yes, No
            "p30": [0, 3],   # No car, 3 cars
            "p22": [4.0, 8.0], "p24": [2.0, 2.0],
        })
        indicators = build_origin_asset_indicators(df)
        assert indicators["p31a"].iloc[0] == 1.0
        assert indicators["p31a"].iloc[1] == 0.0
        assert indicators["p30_bin"].iloc[0] == 0.0
        assert indicators["p30_bin"].iloc[1] == 1.0
        # 4/2=2.0 <= 2.5 -> 1, 8/2=4.0 > 2.5 -> 0
        assert indicators["hac_or"].iloc[0] == 1.0
        assert indicators["hac_or"].iloc[1] == 0.0

    def test_missing_columns_skipped(self):
        df = pd.DataFrame({"p31a": [1, 2]})
        indicators = build_origin_asset_indicators(df)
        assert "p31a" in indicators.columns
        assert "p30_bin" not in indicators.columns
        assert "hac_or" not in indicators.columns


class TestBuildCurrentAssetIndicators:
    def test_builds_correct_columns(self):
        df = pd.DataFrame({
            "p96a": [1, 2], "p96n": [1, 1],
            "p97a": [2, 2],
            "p95a": [1, 2],
            "p99": [1, 0],
            "tamhog": [3.0, 6.0], "p89": [2.0, 1.0],
        })
        indicators = build_current_asset_indicators(df)
        assert "p96a" in indicators.columns
        assert "p96n" in indicators.columns
        assert "p97a" in indicators.columns
        assert "p95a" in indicators.columns
        assert "p99_bin" in indicators.columns
        assert "hac" in indicators.columns


class TestComputeWealthIndex:
    @pytest.fixture
    def asset_df(self):
        """DataFrame with synthetic asset data for wealth index testing."""
        rng = np.random.default_rng(42)
        n = 100
        data = {"factor": rng.uniform(100, 5000, n), "cohorte": rng.choice([1, 2], n)}
        # Origin and current assets
        for var in ["p31a", "p31b", "p31c", "p31d", "p31e"]:
            data[var] = rng.choice([1, 2], n)
        for var in ["p96a", "p96b", "p96c", "p96d", "p96e"]:
            data[var] = rng.choice([1, 2], n)
        return pd.DataFrame(data)

    def test_returns_two_series(self, asset_df):
        idx_orig, idx_curr = compute_wealth_index(asset_df)
        assert isinstance(idx_orig, pd.Series)
        assert isinstance(idx_curr, pd.Series)
        assert len(idx_orig) == len(asset_df)
        assert len(idx_curr) == len(asset_df)

    def test_indices_are_different(self, asset_df):
        """Origin and current indices should NOT be identical."""
        idx_orig, idx_curr = compute_wealth_index(asset_df)
        # They use different variables, so should differ
        assert not np.allclose(
            idx_orig.dropna().values, idx_curr.dropna().values, atol=1e-10
        )

    def test_by_cohort(self, asset_df):
        """Should produce valid results per cohort."""
        idx_orig, idx_curr = compute_wealth_index(asset_df, cohort_col="cohorte")
        assert idx_orig.notna().sum() > 0
        assert idx_curr.notna().sum() > 0

    def test_no_cohort_column(self, asset_df):
        """Should work even without cohort column (single-group PCA)."""
        df = asset_df.drop(columns=["cohorte"])
        idx_orig, idx_curr = compute_wealth_index(df)
        assert idx_orig.notna().sum() > 0
