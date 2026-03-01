"""Tests for transition matrix computation."""

import numpy as np
import pandas as pd
import pytest

from emovi_mcp.stats_engine import compute_transition_matrix


@pytest.fixture
def mobility_df():
    """DataFrame with known mobility patterns."""
    return pd.DataFrame({
        "factor": [100.0] * 8,
        "educ": [1, 2, 3, 4, 1, 2, 3, 4],
        "educp": [1, 1, 2, 2, 3, 3, 4, 4],
        "educm": [1, 1, 1, 1, 2, 2, 3, 3],
        "clase": [1, 2, 3, 4, 5, 6, 1, 2],
        "clasep": [1, 1, 2, 2, 3, 3, 4, 4],
        "ingc_pc": [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000],
        "sexo": [1, 2, 1, 2, 1, 2, 1, 2],
        "cohorte": [1, 1, 2, 2, 3, 3, 4, 4],
        "region_14": [1, 1, 2, 2, 3, 3, 4, 4],
    })


@pytest.fixture
def wealth_mobility_df():
    """DataFrame with asset variables for wealth dimension testing."""
    rng = np.random.default_rng(42)
    n = 100
    # Simulate binary survey responses (1=Yes, 2=No) for assets
    data = {
        "factor": rng.uniform(100, 5000, n),
        "cohorte": rng.choice([1, 2], n),
        "sexo": rng.choice([1, 2], n),
    }
    # Origin assets (household goods at age 14)
    for var in ["p31a", "p31b", "p31c", "p31d", "p31e", "p31f", "p31g",
                "p31h", "p31i", "p31j", "p31k", "p31l", "p31m", "p31n", "p31o"]:
        data[var] = rng.choice([1, 2], n)
    # Origin property
    for var in ["p32a", "p32b", "p32c", "p32d", "p32e"]:
        data[var] = rng.choice([1, 2], n)
    # Origin services
    for var in ["p26a", "p26b", "p26d", "p26e"]:
        data[var] = rng.choice([1, 2], n)
    # Origin automobiles and overcrowding
    data["p30"] = rng.choice([0, 1, 2], n)
    data["p22"] = rng.integers(1, 10, n).astype(float)
    data["p24"] = rng.integers(1, 5, n).astype(float)
    # Current assets (household goods)
    for var in ["p96a", "p96b", "p96c", "p96d", "p96e", "p96f", "p96g", "p96h",
                "p96i", "p96j", "p96k", "p96l", "p96m", "p96n", "p96o", "p96p",
                "p96q", "p96r"]:
        data[var] = rng.choice([1, 2], n)
    # Current property
    for var in ["p97a", "p97b", "p97c", "p97d", "p97e", "p97f"]:
        data[var] = rng.choice([1, 2], n)
    # Current services
    for var in ["p95a", "p95b", "p95d", "p95e"]:
        data[var] = rng.choice([1, 2], n)
    # Current automobiles and overcrowding
    data["p99"] = rng.choice([0, 1, 2, 3], n)
    data["tamhog"] = rng.integers(1, 10, n).astype(float)
    data["p89"] = rng.integers(1, 5, n).astype(float)

    return pd.DataFrame(data)


class TestTransitionMatrix:
    def test_education_dimension(self, mobility_df):
        result = compute_transition_matrix(
            mobility_df, dimension="education"
        )
        assert "all" in result["matrices"]
        matrix = result["matrices"]["all"]
        # Should be a square matrix with row proportions summing to 1
        for _, row in matrix.iterrows():
            assert row.sum() == pytest.approx(1.0, abs=0.01)

    def test_with_filter(self, mobility_df):
        result = compute_transition_matrix(
            mobility_df, dimension="education", filter_expr="sexo == 1"
        )
        summary = result["summary"]["all"]
        assert summary["n_unweighted"] < len(mobility_df)

    def test_with_by(self, mobility_df):
        result = compute_transition_matrix(
            mobility_df, dimension="education", by="sexo"
        )
        # Should have separate matrices for sexo=1 and sexo=2
        assert len(result["matrices"]) == 2

    def test_invalid_dimension(self, mobility_df):
        with pytest.raises(ValueError, match="Unknown dimension"):
            compute_transition_matrix(mobility_df, dimension="invalid")

    def test_wealth_dimension(self, wealth_mobility_df):
        result = compute_transition_matrix(
            wealth_mobility_df, dimension="wealth"
        )
        assert "all" in result["matrices"]
        matrix = result["matrices"]["all"]
        for _, row in matrix.iterrows():
            assert row.sum() == pytest.approx(1.0, abs=0.01)

    def test_summary_stats(self, mobility_df):
        result = compute_transition_matrix(
            mobility_df, dimension="education"
        )
        summary = result["summary"]["all"]
        assert "diagonal_persistence" in summary
        assert "upward_mobility_avg" in summary
        assert "downward_mobility_avg" in summary
        assert summary["n_unweighted"] > 0

    def test_origin_filter_valid(self, mobility_df):
        """Filter to only origin category 1."""
        result = compute_transition_matrix(
            mobility_df, dimension="education", origin_filter=1
        )
        assert "all" in result["matrices"]
        # The matrix should only have rows with origin=1
        summary = result["summary"]["all"]
        assert summary["n_unweighted"] < len(mobility_df)

    def test_origin_filter_no_match(self, mobility_df):
        """Filter to an origin category that doesn't exist."""
        result = compute_transition_matrix(
            mobility_df, dimension="education", origin_filter=99
        )
        assert result["matrices"] == {}
