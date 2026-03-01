"""Variable dictionary: search, list, and detail lookup."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DICT_PATH = Path(__file__).parent / "data" / "dictionary.json"
_dictionary: dict[str, Any] | None = None


def _load_dictionary() -> dict[str, Any]:
    """Load dictionary.json lazily."""
    global _dictionary
    if _dictionary is not None:
        return _dictionary

    if not _DICT_PATH.is_file():
        logger.warning(
            "dictionary.json not found at %s. Run `python -m scripts.build_dictionary` first.",
            _DICT_PATH,
        )
        _dictionary = {}
        return _dictionary

    with open(_DICT_PATH, encoding="utf-8") as f:
        _dictionary = json.load(f)
    logger.info("Loaded dictionary with %d variables", len(_dictionary))
    return _dictionary


def get_variable_info(variable: str) -> dict[str, Any] | None:
    """Get full info for a variable by name."""
    d = _load_dictionary()
    return d.get(variable)


def search_variables(query: str, dataset: str | None = None) -> list[dict]:
    """Search variables by name or description substring (case-insensitive).

    Returns list of {name, label, dataset, section} dicts.
    """
    d = _load_dictionary()
    q = query.lower()
    results = []
    for name, info in d.items():
        if dataset and info.get("dataset") != dataset:
            continue
        searchable = f"{name} {info.get('label', '')} {info.get('section', '')}".lower()
        if q in searchable:
            results.append({
                "name": name,
                "label": info.get("label", ""),
                "dataset": info.get("dataset", ""),
                "section": info.get("section", ""),
            })
    return results


def list_all_variables(
    dataset: str | None = None, section: str | None = None
) -> list[dict]:
    """List all variables, optionally filtered by dataset and/or section."""
    d = _load_dictionary()
    results = []
    for name, info in d.items():
        if dataset and info.get("dataset") != dataset:
            continue
        if section and section.lower() not in info.get("section", "").lower():
            continue
        results.append({
            "name": name,
            "label": info.get("label", ""),
            "dataset": info.get("dataset", ""),
            "section": info.get("section", ""),
        })
    return results


def list_sections(dataset: str | None = None) -> list[str]:
    """List unique sections in the dictionary."""
    d = _load_dictionary()
    sections = set()
    for info in d.values():
        if dataset and info.get("dataset") != dataset:
            continue
        s = info.get("section", "")
        if s:
            sections.add(s)
    return sorted(sections)
