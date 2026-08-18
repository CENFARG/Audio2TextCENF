"""Tests that en.json contains all keys from es.json with non-empty values.

Phase 1 of audio2text-ui-sync-fixes: en.json completion.
"""

import json
from pathlib import Path

import pytest

LANG_DIR = Path(__file__).resolve().parent.parent / "lang"


def _load_json(filename: str) -> dict:
    path = LANG_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def es_keys():
    return set(_load_json("es.json").keys())


@pytest.fixture(scope="module")
def en_keys():
    return set(_load_json("en.json").keys())


@pytest.fixture(scope="module")
def en_values():
    return _load_json("en.json")


class TestEnJsonParity:
    """en.json SHALL contain all keys from es.json."""

    def test_en_json_has_all_keys_from_es_json(self, es_keys, en_keys):
        missing = es_keys - en_keys
        assert not missing, f"en.json is missing keys from es.json: {sorted(missing)}"

    def test_all_en_values_are_non_empty_strings(self, en_values):
        for key, value in en_values.items():
            assert isinstance(value, str), f"Key '{key}' value is not a string: {type(value)}"
            assert value.strip(), f"Key '{key}' has an empty or whitespace-only value"

    def test_key_counts_match(self, es_keys, en_keys):
        assert len(en_keys) == len(es_keys), (
            f"Key count mismatch: en.json has {len(en_keys)}, es.json has {len(es_keys)}"
        )
