"""@File: audio2text/services/vocabulary_service.py
@Description: VocabularyService — wraps custom vocabulary correction logic using domain models.
    Loads entries from configured JSON paths and applies word-boundary corrections.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import re

from audio2text.domain.vocabulary import VocabularyConfig, VocabularyEntry


class VocabularyService:
    """Manages vocabulary correction entries and applies them to text.

    Wraps the existing custom_vocabulary.py logic but uses the domain
    models (VocabularyEntry, VocabularyConfig) and supports add/remove/
    toggle operations.

    Corrections are applied with word-boundary matching to avoid
    replacing substrings inside longer words.
    """

    def __init__(self, config: VocabularyConfig | None = None) -> None:
        """Initialize the vocabulary service.

        Args:
            config: Optional vocabulary configuration. If not provided,
                    creates an empty config with auto_apply enabled.
        """
        self._config = config or VocabularyConfig()
        # Ensure entries are deduplicated by word
        self._entries: dict[str, VocabularyEntry] = {}
        for entry in self._config.entries:
            self._entries[entry.word.lower()] = entry

    # ------------------------------------------------------------------
    # Public API — entry management
    # ------------------------------------------------------------------

    def add_entry(self, word: str, correction: str, category: str = "custom") -> bool:
        """Register or update a vocabulary correction entry.

        Args:
            word: The word to replace (case-insensitive key).
            correction: The replacement text.
            category: Optional category label (default "custom").

        Returns:
            True on success.
        """
        entry = VocabularyEntry(
            word=word.lower(),
            correction=correction,
            category=category,
            enabled=True,
        )
        self._entries[word.lower()] = entry
        return True

    def remove_entry(self, word: str) -> bool:
        """Remove a correction entry.

        Args:
            word: The word key to remove (case-insensitive).

        Returns:
            True if the entry existed and was removed, False otherwise.
        """
        key = word.lower()
        if key in self._entries:
            del self._entries[key]
            return True
        return False

    def toggle_entry(self, word: str, enabled: bool) -> bool:
        """Enable or disable a correction entry.

        Args:
            word: The word key (case-insensitive).
            enabled: True to enable, False to disable.

        Returns:
            True if the entry existed and was toggled, False otherwise.
        """
        key = word.lower()
        entry = self._entries.get(key)
        if entry is not None:
            entry.enabled = enabled
            return True
        return False

    def get_entries(self) -> list[VocabularyEntry]:
        """Return all registered vocabulary entries.

        Returns:
            A list of VocabularyEntry objects (both enabled and disabled).
        """
        return list(self._entries.values())

    # ------------------------------------------------------------------
    # Public API — text correction
    # ------------------------------------------------------------------

    def apply_corrections(self, text: str) -> str:
        """Apply all enabled corrections to the given text.

        Corrections use word-boundary matching (``\\b``) to avoid
        replacing substrings inside longer words. Case handling:

        - If the matched word is ALL CAPS, the correction is uppercased.
        - If the matched word is Title Case, the correction is capitalized.
        - Otherwise, the correction is applied as-is (lowercase).

        Args:
            text: The text to correct.

        Returns:
            Corrected text with all enabled entries applied.
        """
        if not text or not self._entries:
            return text

        result = text
        for entry in self._entries.values():
            if not entry.enabled:
                continue

            pattern = r"\b" + re.escape(entry.word) + r"\b"
            matches = list(re.finditer(pattern, result, re.IGNORECASE))
            if not matches:
                continue

            # Process from right to left to preserve indices
            new_result = result
            for match in reversed(matches):
                matched_text = match.group()
                start, end = match.span()

                if matched_text.isupper():
                    replacement = entry.correction.upper()
                elif matched_text[0].isupper():
                    replacement = entry.correction.capitalize()
                elif any(c.isupper() for c in entry.correction):
                    # Preserve acronym/proper-noun case (e.g., "CENF", "Groq")
                    replacement = entry.correction
                else:
                    replacement = entry.correction.lower()

                new_result = new_result[:start] + replacement + new_result[end:]

            result = new_result

        return result

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_config(self) -> VocabularyConfig:
        """Export current state as a VocabularyConfig.

        Returns:
            A VocabularyConfig populated with all registered entries.
        """
        return VocabularyConfig(
            entries=list(self._entries.values()),
            auto_apply=self._config.auto_apply,
        )

    def load_defaults(self, defaults: dict[str, str]) -> None:
        """Load a batch of default corrections.

        Args:
            defaults: Mapping of incorrect → correct words.
        """
        for wrong, correct in defaults.items():
            self.add_entry(wrong, correct)

    # ------------------------------------------------------------------
    # Import / Export (user-friendly format)
    # ------------------------------------------------------------------

    def export_to_text(self, enabled_only: bool = False) -> str:
        """Export vocabulary entries as user-friendly text.

        Format uses '=' as separator (not '→') for easy manual editing:
            wrong=correct
            another=correction

        Args:
            enabled_only: If True, only export enabled entries.

        Returns:
            Multi-line text with one entry per line.
        """
        lines = []
        for entry in sorted(self._entries.values(), key=lambda e: e.word):
            if enabled_only and not entry.enabled:
                continue
            lines.append(f"{entry.word}={entry.correction}")
        return "\n".join(lines)

    def import_from_text(self, text: str, category: str = "custom") -> int:
        """Import vocabulary entries from user-friendly text.

        Accepts formats:
            - "wrong=correction" (preferred, user-friendly)
            - "wrong→correction" (legacy format)
            - "wrong correct" (space-separated fallback)

        Lines starting with '#' or empty lines are ignored.

        Args:
            text: Multi-line text with vocabulary entries.
            category: Optional category label for imported entries.

        Returns:
            Number of entries imported.
        """
        count = 0
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Try '=' separator first (preferred)
            if "=" in line:
                parts = line.split("=", 1)
                word = parts[0].strip()
                correction = parts[1].strip()
            # Try '→' separator (legacy)
            elif "→" in line:
                parts = line.split("→", 1)
                word = parts[0].strip()
                correction = parts[1].strip()
            # Try space separator (fallback)
            elif " " in line:
                parts = line.split(None, 1)
                word = parts[0].strip()
                correction = parts[1].strip() if len(parts) > 1 else ""
            else:
                continue

            if word and correction:
                self.add_entry(word, correction, category=category)
                count += 1

        return count

    def export_to_json(self) -> list[dict[str, str]]:
        """Export vocabulary entries as JSON-serializable list.

        Returns:
            List of dicts with 'word', 'correction', 'category', 'enabled' keys.
        """
        return [
            {
                "word": entry.word,
                "correction": entry.correction,
                "category": entry.category,
                "enabled": entry.enabled,
            }
            for entry in sorted(self._entries.values(), key=lambda e: e.word)
        ]

    def import_from_json(self, entries: list[dict[str, str]], category: str = "custom") -> int:
        """Import vocabulary entries from JSON-serializable list.

        Args:
            entries: List of dicts with 'word' and 'correction' keys.
            category: Optional category label for imported entries.

        Returns:
            Number of entries imported.
        """
        count = 0
        for entry_data in entries:
            word = entry_data.get("word", "").strip()
            correction = entry_data.get("correction", "").strip()
            if word and correction:
                cat = entry_data.get("category", category)
                self.add_entry(word, correction, category=cat)
                count += 1
        return count
