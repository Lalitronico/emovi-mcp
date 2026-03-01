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

    def test_income_quintile(self, mobility_df):
        result = compute_transition_matrix(
            mobility_df, dimension="income_quintile"
        )
        assert "all" in result["matrices"]

    def test_summary_stats(self, mobility_df):
        result = compute_transition_matrix(
            mobility_df, dimension="education"
        )
        summary = result["summary"]["all"]
        assert "diagonal_persistence" in summary
        assert "upward_mobility_avg" in summary
        assert "downward_mobility_avg" in summary
        assert summary["n_unweighted"] > 0
