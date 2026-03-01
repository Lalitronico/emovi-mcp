"""Tests for the variable dictionary module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from emovi_mcp import dictionary


@pytest.fixture(autouse=True)
def reset_dict_cache():
    """Reset the module-level cache before each test."""
    dictionary._dictionary = None
    yield
    dictionary._dictionary = None


@pytest.fixture
def sample_dict(tmp_path):
    """Create a temporary dictionary.json for testing."""
    d = {
        "educ": {
            "label": "Nivel educativo del entrevistado",
            "dataset": "entrevistado",
            "section": "Educacion",
            "value_labels": {"1": "Primaria o menos", "2": "Secundaria", "3": "Media superior", "4": "Profesional"},
        },
        "sexo": {
            "label": "Sexo del entrevistado",
            "dataset": "entrevistado",
            "section": "Sociodemograficas",
        },
        "ingc_pc": {
            "label": "Ingreso per capita del hogar imputado",
            "dataset": "entrevistado",
            "section": "Ingreso",
        },
        "tamhog": {
            "label": "Tamano del hogar",
            "dataset": "hogar",
            "section": "Hogar",
        },
    }
    dict_path = tmp_path / "dictionary.json"
    dict_path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return dict_path, d


class TestDictionary:
    def test_get_variable_info(self, sample_dict):
        dict_path, _ = sample_dict
        with patch.object(dictionary, "_DICT_PATH", dict_path):
            info = dictionary.get_variable_info("educ")
            assert info is not None
            assert info["label"] == "Nivel educativo del entrevistado"
            assert "value_labels" in info

    def test_get_missing_variable(self, sample_dict):
        dict_path, _ = sample_dict
        with patch.object(dictionary, "_DICT_PATH", dict_path):
            assert dictionary.get_variable_info("nonexistent") is None

    def test_search_by_name(self, sample_dict):
        dict_path, _ = sample_dict
        with patch.object(dictionary, "_DICT_PATH", dict_path):
            results = dictionary.search_variables("educ")
            names = [r["name"] for r in results]
            assert "educ" in names

    def test_search_by_description(self, sample_dict):
        dict_path, _ = sample_dict
        with patch.object(dictionary, "_DICT_PATH", dict_path):
            results = dictionary.search_variables("ingreso")
            assert len(results) >= 1
            assert results[0]["name"] == "ingc_pc"

    def test_filter_by_dataset(self, sample_dict):
        dict_path, _ = sample_dict
        with patch.object(dictionary, "_DICT_PATH", dict_path):
            results = dictionary.list_all_variables(dataset="hogar")
            assert len(results) == 1
            assert results[0]["name"] == "tamhog"

    def test_list_sections(self, sample_dict):
        dict_path, _ = sample_dict
        with patch.object(dictionary, "_DICT_PATH", dict_path):
            sections = dictionary.list_sections()
            assert "Educacion" in sections
            assert "Ingreso" in sections
