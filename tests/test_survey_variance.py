"""Tests for Taylor linearization survey variance estimation."""

import numpy as np
import pandas as pd
import pytest

from emovi_mcp.helpers.survey_variance import (
    taylor_variance_ratio,
    _stratified_cluster_variance,
    transition_matrix_standard_errors,
)


class TestTaylorVarianceRatio:
    def test_simple_random_sample(self):
        """With 1 stratum and each obs its own PSU, should approximate
        the textbook variance of a proportion under SRS."""
        rng = np.random.default_rng(42)
        n = 1000
        # True proportion p = 0.3
        indicator = (rng.random(n) < 0.3).astype(float)
        weights = np.ones(n)
        y = weights * indicator
        x = weights  # everyone in denominator
        psu = np.arange(n)  # each obs is its own PSU
        strata = np.zeros(n)

        var = taylor_variance_ratio(y, x, psu, strata)
        se = np.sqrt(var)

        # Expected SE for proportion under SRS: sqrt(p(1-p)/n)
        p_hat = indicator.mean()
        expected_se = np.sqrt(p_hat * (1 - p_hat) / n)

        assert se == pytest.approx(expected_se, rel=0.15)

    def test_zero_denominator(self):
        """Zero denominator should return NaN."""
        y = np.array([0.0, 0.0])
        x = np.array([0.0, 0.0])
        psu = np.array([1, 2])
        strata = np.array([1, 1])
        assert np.isnan(taylor_variance_ratio(y, x, psu, strata))

    def test_deterministic_case(self):
        """All in one cell — proportion = 1.0, variance should be ~0."""
        n = 50
        y = np.ones(n)
        x = np.ones(n)
        psu = np.arange(n)
        strata = np.zeros(n)

        var = taylor_variance_ratio(y, x, psu, strata)
        assert var == pytest.approx(0.0, abs=1e-10)


class TestStratifiedClusterVariance:
    def test_multiple_strata(self):
        """Variance should be computed across strata."""
        rng = np.random.default_rng(42)
        z = rng.normal(0, 1, 100)
        psu = np.repeat(np.arange(20), 5)
        strata = np.repeat([1, 2], 50)

        var = _stratified_cluster_variance(z, psu, strata)
        assert var > 0

    def test_single_psu_per_stratum(self):
        """With 1 PSU per stratum, variance contribution should be 0 (conservative)."""
        z = np.array([1.0, 2.0, 3.0])
        psu = np.array([1, 2, 3])
        strata = np.array([1, 2, 3])  # each stratum has 1 PSU

        var = _stratified_cluster_variance(z, psu, strata)
        assert var == 0.0

    def test_identical_values_zero_variance(self):
        """If all PSU totals in a stratum are identical, variance = 0."""
        z = np.ones(10)
        psu = np.repeat([1, 2], 5)
        strata = np.ones(10)

        var = _stratified_cluster_variance(z, psu, strata)
        assert var == pytest.approx(0.0, abs=1e-10)


class TestTransitionMatrixSE:
    def test_basic_output_shape(self):
        """SE matrix should match the transition matrix shape."""
        df = pd.DataFrame({
            "_origin": [1, 1, 1, 2, 2, 2, 1, 2],
            "_dest": [1, 2, 1, 1, 2, 2, 2, 1],
            "w": [100, 100, 100, 100, 100, 100, 100, 100],
            "psu": ["a", "a", "b", "b", "a", "b", "a", "b"],
            "str": [1, 1, 1, 1, 2, 2, 2, 2],
        })
        se = transition_matrix_standard_errors(
            df, "_origin", "_dest", "w", "psu", "str"
        )
        assert se.shape == (2, 2)

    def test_se_values_positive(self):
        """SE values should be non-negative."""
        rng = np.random.default_rng(42)
        n = 200
        df = pd.DataFrame({
            "_origin": rng.choice([1, 2, 3], n),
            "_dest": rng.choice([1, 2, 3], n),
            "w": rng.uniform(100, 1000, n),
            "psu": rng.choice(["a", "b", "c", "d", "e"], n),
            "str": rng.choice([1, 2], n),
        })
        se = transition_matrix_standard_errors(
            df, "_origin", "_dest", "w", "psu", "str"
        )
        assert (se.values >= 0).all()

    def test_with_labels(self):
        """Labels should be applied to SE matrix."""
        df = pd.DataFrame({
            "_origin": [1, 1, 2, 2],
            "_dest": [1, 2, 1, 2],
            "w": [100, 100, 100, 100],
            "psu": ["a", "b", "a", "b"],
            "str": [1, 1, 2, 2],
        })
        labels = {1: "Low", 2: "High"}
        se = transition_matrix_standard_errors(
            df, "_origin", "_dest", "w", "psu", "str", labels=labels
        )
        assert "Low" in se.index
        assert "High" in se.columns

    def test_missing_psu_col(self):
        """Should handle missing PSU column gracefully."""
        df = pd.DataFrame({
            "_origin": [1, 1, 2, 2],
            "_dest": [1, 2, 1, 2],
            "w": [100, 100, 100, 100],
        })
        se = transition_matrix_standard_errors(
            df, "_origin", "_dest", "w", "psu_missing", "str_missing"
        )
        assert se.shape == (2, 2)
