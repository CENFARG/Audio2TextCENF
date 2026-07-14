"""@File: audio2text/domain/vocabulary.py
@Description: Vocabulary correction domain models — VocabularyEntry and VocabularyConfig.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VocabularyEntry:
    """A single vocabulary correction entry.

    Attributes:
        word: The word or phrase to replace.
        correction: The replacement text.
        category: Category for organizing entries (e.g., "custom", "tech", "general").
        enabled: Whether this entry is active during transcription.
    """

    word: str
    correction: str
    category: str = "custom"
    enabled: bool = True

    def __eq__(self, other: object) -> bool:
        """Two entries are equal if they share the same word."""
        if not isinstance(other, VocabularyEntry):
            return NotImplemented
        return self.word == other.word

    def __hash__(self) -> int:
        return hash(self.word)


@dataclass
class VocabularyConfig:
    """Configuration for vocabulary-based text correction.

    Attributes:
        entries: List of vocabulary correction entries.
        auto_apply: Whether to automatically apply corrections after transcription.
    """

    entries: list[VocabularyEntry] = field(default_factory=list)
    auto_apply: bool = True
