"""Tests for formal mobility indices."""

import numpy as np
import pandas as pd
import pytest

from emovi_mcp.helpers.mobility_indices import (
    shorrocks_m,
    prais_index,
    intergenerational_correlation,
    corner_odds_ratios,
    compute_all_indices,
)


@pytest.fixture
def identity_matrix():
    """Perfect immobility (everyone stays in origin class)."""
    labels = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    data = np.eye(5)
    return pd.DataFrame(data, index=labels, columns=labels)


@pytest.fixture
def uniform_matrix():
    """Maximum mobility (uniform transitions)."""
    labels = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    data = np.full((5, 5), 0.2)
    return pd.DataFrame(data, index=labels, columns=labels)


@pytest.fixture
def asymmetric_matrix():
    """Realistic asymmetric matrix for odds ratio testing."""
    labels = ["Q1", "Q2", "Q3"]
    data = np.array([
        [0.6, 0.3, 0.1],
        [0.2, 0.5, 0.3],
        [0.1, 0.2, 0.7],
    ])
    return pd.DataFrame(data, index=labels, columns=labels)


class TestShorrocks:
    def test_identity_is_zero(self, identity_matrix):
        m = shorrocks_m(identity_matrix)
        assert m == pytest.approx(0.0, abs=1e-10)

    def test_uniform_is_one(self, uniform_matrix):
        m = shorrocks_m(uniform_matrix)
        assert m == pytest.approx(1.0, abs=1e-10)

    def test_intermediate(self, asymmetric_matrix):
        m = shorrocks_m(asymmetric_matrix)
        assert 0 < m < 1

    def test_single_class(self):
        """1x1 matrix should return 0."""
        m = pd.DataFrame([[1.0]], index=["A"], columns=["A"])
        assert shorrocks_m(m) == 0.0


class TestPrais:
    def test_identity_all_zero(self, identity_matrix):
        pi = prais_index(identity_matrix)
        for val in pi.values():
            assert val == pytest.approx(0.0, abs=1e-10)

    def test_uniform_all_equal(self, uniform_matrix):
        pi = prais_index(uniform_matrix)
        for val in pi.values():
            assert val == pytest.approx(0.8, abs=1e-10)

    def test_asymmetric_varies(self, asymmetric_matrix):
        pi = prais_index(asymmetric_matrix)
        # Q3 has 0.7 persistence, so escape = 0.3 (lowest)
        assert pi["Q3"] < pi["Q1"]


class TestIntergenerationalCorrelation:
    def test_perfect_correlation(self):
        origin = pd.Series([1, 2, 3, 4, 5], dtype=float)
        dest = pd.Series([1, 2, 3, 4, 5], dtype=float)
        weights = pd.Series([1.0, 1.0, 1.0, 1.0, 1.0])
        r = intergenerational_correlation(origin, dest, weights)
        assert r == pytest.approx(1.0, abs=1e-10)

    def test_negative_correlation(self):
        # Reverse order: higher origin → lower destination
        origin = pd.Series([1, 2, 3, 4, 5], dtype=float)
        dest = pd.Series([5, 4, 3, 2, 1], dtype=float)
        weights = pd.Series([1.0] * 5)
        r = intergenerational_correlation(origin, dest, weights)
        assert r == pytest.approx(-1.0, abs=1e-10)

    def test_weighted(self):
        origin = pd.Series([1, 1, 5, 5], dtype=float)
        dest = pd.Series([1, 5, 1, 5], dtype=float)
        # Heavy weight on concordant pairs (1,1) and (5,5)
        weights = pd.Series([100.0, 1.0, 1.0, 100.0])
        r = intergenerational_correlation(origin, dest, weights)
        assert r > 0.5

    def test_handles_nan(self):
        origin = pd.Series([1, np.nan, 3], dtype=float)
        dest = pd.Series([1, 2, 3], dtype=float)
        weights = pd.Series([1.0, 1.0, 1.0])
        r = intergenerational_correlation(origin, dest, weights)
        assert not np.isnan(r)


class TestCornerOddsRatios:
    def test_identity_high_corners(self, identity_matrix):
        cors = corner_odds_ratios(identity_matrix)
        assert cors["cross"] > 1  # strong diagonal persistence

    def test_uniform_cross_is_one(self, uniform_matrix):
        cors = corner_odds_ratios(uniform_matrix)
        assert cors["cross"] == pytest.approx(1.0, abs=0.1)

    def test_asymmetric(self, asymmetric_matrix):
        cors = corner_odds_ratios(asymmetric_matrix)
        # p11=0.6, p13=0.1, p31=0.1, p33=0.7
        expected_cross = (0.6 * 0.7) / (0.1 * 0.1)
        assert cors["cross"] == pytest.approx(expected_cross, rel=0.01)

    def test_small_matrix(self):
        """2x2 matrix should work."""
        m = pd.DataFrame([[0.7, 0.3], [0.2, 0.8]], index=["A", "B"], columns=["A", "B"])
        cors = corner_odds_ratios(m)
        assert cors["cross"] > 1


class TestComputeAllIndices:
    def test_with_data(self, asymmetric_matrix):
        # Create fake df with _origin and _dest
        df = pd.DataFrame({
            "_origin": [1, 1, 2, 2, 3, 3],
            "_dest": [1, 2, 2, 3, 3, 1],
            "factor": [100.0] * 6,
        })
        result = compute_all_indices(asymmetric_matrix, df, "factor")
        assert "shorrocks_m" in result
        assert "prais_index" in result
        assert "intergenerational_r" in result
        assert "corner_odds_ratios" in result
