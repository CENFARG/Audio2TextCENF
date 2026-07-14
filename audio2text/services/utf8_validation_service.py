"""@File: audio2text/services/utf8_validation_service.py
@Description: UTF8ValidationService — detects and fixes Spanish encoding corruption (mojibake)
    using proper Unicode normalization instead of hardcoded character maps.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """The result of a text validation check.

    Attributes:
        is_valid: True if the text has no encoding issues.
        issues: List of human-readable issue descriptions.
        issues_detected: Number of distinct issues found.
    """

    is_valid: bool
    issues: list[str] = field(default_factory=list)

    @property
    def issues_detected(self) -> int:
        """Number of distinct issues found."""
        return len(self.issues)


# ---------------------------------------------------------------------------
# Mojibake detection: Spanish characters encoded as Latin-1, decoded as UTF-8.
# The corruption pattern is predictable:
#   Spanish char → Latin-1 bytes → decoded as UTF-8 → 2-char garbage pair.
#
# We detect these by looking for the characteristic "Ã" prefix followed
# by a byte in the Latin-1 supplementary range (0x80–0xBF).
# ---------------------------------------------------------------------------

_MOJIBAKE_PATTERN = re.compile(
    r"\xc3([\x80-\xbf])"  # Ã + Latin-1 continuation byte
)


class UTF8ValidationService:
    """Validates and corrects UTF-8 encoding issues in Spanish text.

    Replaces the old bloated utf8_validator.py (~340 lines of hardcoded maps)
    with a lean approach using standard library Unicode tools:

    - ``unicodedata.normalize('NFC', ...)`` for proper Unicode composition.
    - Mojibake detection via regex patterns (Latin-1→UTF-8 corruption).
    - Control character stripping via ``unicodedata.category``.

    This service is ≤250 lines, has no hardcoded character maps, and
    handles all Spanish accented characters generically.
    """

    def __init__(self, source_encoding: str = "latin-1") -> None:
        """Initialize the validation service.

        Args:
            source_encoding: The encoding assumed for mojibake reversal.
                When text was Latin-1-encoded bytes decoded as UTF-8,
                this is the encoding to use for reversal (default "latin-1").
        """
        self._source_encoding = source_encoding

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, text: str) -> ValidationResult:
        """Check text for encoding problems.

        Detects:
        - Mojibake patterns (Latin-1 → UTF-8 corruption).
        - Control characters (category ``Cc`` except common whitespace).
        - Invalid UTF-8 byte sequences that would fail encoding.

        Args:
            text: The text to validate.

        Returns:
            A ``ValidationResult`` indicating validity and listing any issues.
        """
        if not text:
            return ValidationResult(is_valid=True, issues=[])

        issues: list[str] = []

        # 1. Check for mojibake patterns
        mojibake_count = len(_MOJIBAKE_PATTERN.findall(text))
        if mojibake_count > 0:
            issues.append(f"mojibake_detected: {mojibake_count} corrupted chars")

        # 2. Check for control characters (excluding common whitespace)
        control_chars: list[str] = []
        for char in text:
            if unicodedata.category(char) == "Cc":
                cp = ord(char)
                # Allow common whitespace: tab, LF, CR
                if cp not in (0x09, 0x0A, 0x0D):
                    control_chars.append(f"U+{cp:04X}")
        if control_chars:
            issues.append(f"control_characters: {', '.join(control_chars[:10])}")
            if len(control_chars) > 10:
                issues[-1] += f" ({len(control_chars)} total)"

        # 3. Verify UTF-8 roundtrip
        try:
            encoded = text.encode("utf-8")
            encoded.decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError) as exc:
            issues.append(f"utf8_roundtrip_failed: {exc}")

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
        )

    def correct(self, text: str | None) -> str:
        """Correct encoding issues in text.

        Applies these transformations in order:
        1. Reverse mojibake: Latin-1 bytes → UTF-8 decode to recover original chars.
        2. Strip control characters (except tab, LF, CR).
        3. Collapse multiple spaces.

        Args:
            text: The text to correct, or None (returns empty string).

        Returns:
            Corrected text with encoding issues resolved.
        """
        if not text:
            return ""

        result = text

        # Step 1: Reverse mojibake corruption
        result = self._fix_mojibake(result)

        # Step 2: Strip control characters
        result = self._strip_control_chars(result)

        # Step 3: Collapse multiple spaces
        result = re.sub(r" {2,}", " ", result)
        result = result.strip()

        return result

    def normalize(self, text: str) -> str:
        """Normalize Unicode text to NFC (composed) form.

        This ensures decomposed characters (e.g., 'cafe\u0301') are
        composed into their canonical form ('café').

        Args:
            text: The text to normalize.

        Returns:
            NFC-normalized text.
        """
        if not text:
            return ""
        return unicodedata.normalize("NFC", text)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fix_mojibake(self, text: str) -> str:
        """Reverse Latin-1 → UTF-8 mojibake corruption on matched regions only.

        The common corruption path: Spanish accented chars are encoded
        as Latin-1 bytes, then those bytes are decoded as UTF-8.
        This produces pairs like 'Ã±' for 'ñ'.

        We detect the characteristic 'Ã' (U+00C3) prefix pattern and fix
        only those matched regions — other characters (em dashes, etc.)
        are left untouched to avoid collateral damage from Latin-1 encoding.

        Args:
            text: Potentially corrupted text.

        Returns:
            Text with mojibake reversed in matched regions.
        """
        if not _MOJIBAKE_PATTERN.search(text):
            return text

        return _MOJIBAKE_PATTERN.sub(self._replace_mojibake_match, text)

    @staticmethod
    def _replace_mojibake_match(match: re.Match[str]) -> str:
        """Fix a single mojibake match: 'Ã±' → 'ñ'."""
        try:
            raw_bytes = match.group(0).encode("latin-1")
            return raw_bytes.decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return match.group(0)

    @staticmethod
    def _strip_control_chars(text: str) -> str:
        """Remove control characters except tab, LF, and CR.

        Uses ``unicodedata.category`` to identify control characters (Cc).

        Args:
            text: The text to clean.

        Returns:
            Text with control characters removed.
        """
        allowed_cp = {0x09, 0x0A, 0x0D}  # tab, LF, CR
        return "".join(
            char
            for char in text
            if unicodedata.category(char) != "Cc" or ord(char) in allowed_cp
        )
