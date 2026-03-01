"""Tests for visualization helpers."""

import numpy as np
import pandas as pd
import pytest

# Skip all tests if matplotlib/seaborn not installed
mpl = pytest.importorskip("matplotlib")
sns = pytest.importorskip("seaborn")

from emovi_mcp.helpers.visualization import (
    _fig_to_base64,
    bar_chart_prais,
    heatmap_transition_matrix,
    sankey_mobility,
)


@pytest.fixture
def sample_matrix():
    """Simple 3x3 transition matrix."""
    labels = ["Q1", "Q2", "Q3"]
    data = np.array([
        [0.5, 0.3, 0.2],
        [0.2, 0.5, 0.3],
        [0.1, 0.2, 0.7],
    ])
    return pd.DataFrame(data, index=labels, columns=labels)


class TestFigToBase64:
    def test_returns_data_uri(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3])
        result = _fig_to_base64(fig)
        plt.close(fig)

        assert result.startswith("data:image/png;base64,")
        assert len(result) > 100  # should have actual content

    def test_valid_base64(self):
        import base64
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.bar([1, 2], [3, 4])
        result = _fig_to_base64(fig)
        plt.close(fig)

        # Extract base64 portion and decode
        b64_str = result.split(",", 1)[1]
        decoded = base64.b64decode(b64_str)
        # PNG magic bytes
        assert decoded[:4] == b"\x89PNG"


class TestHeatmap:
    def test_returns_data_uri(self, sample_matrix):
        result = heatmap_transition_matrix(sample_matrix, title="Test Heatmap")
        assert result.startswith("data:image/png;base64,")

    def test_custom_params(self, sample_matrix):
        result = heatmap_transition_matrix(
            sample_matrix, title="Custom", cmap="Blues", figsize=(6, 4)
        )
        assert result.startswith("data:image/png;base64,")


class TestSankey:
    def test_returns_data_uri(self, sample_matrix):
        result = sankey_mobility(sample_matrix, title="Test Sankey")
        assert result.startswith("data:image/png;base64,")


class TestPraisBar:
    def test_returns_data_uri(self):
        prais = {"Q1": 0.5, "Q2": 0.5, "Q3": 0.3}
        result = bar_chart_prais(prais, title="Test Prais")
        assert result.startswith("data:image/png;base64,")

    def test_values_in_range(self):
        prais = {"Low": 0.8, "High": 0.2}
        result = bar_chart_prais(prais)
        assert len(result) > 100
