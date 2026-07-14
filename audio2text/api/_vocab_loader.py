"""@File: audio2text/api/_vocab_loader.py
@Description: Helper to load vocabulary entries from JSON files into VocabularyConfig.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from audio2text.domain.vocabulary import VocabularyConfig


def load_vocab_from_path(vocab_config: VocabularyConfig, path: Path) -> None:
    """Load vocabulary entries from a JSON file into the config."""
    from audio2text.domain.vocabulary import VocabularyEntry

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    if isinstance(data, dict):
        for word, correction in data.items():
            vocab_config.entries.append(
                VocabularyEntry(word=str(word), correction=str(correction))
            )
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                vocab_config.entries.append(
                    VocabularyEntry(
                        word=str(item.get("word", "")),
                        correction=str(item.get("correction", "")),
                    )
                )
