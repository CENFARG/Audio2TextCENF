"""@File: audio2text/localization/manager.py
@Description: YAML-based localization manager with fallback chain.
    All user-facing strings must be defined in locale YAML files.
    No hardcoded text anywhere in Python.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class LocalizationManager:
    """Loads locale YAML files and resolves dot-path keys.

    Supports a primary language with fallback to a secondary language.
    All user-facing string retrieval goes through ``get()``.

    Usage::

        mgr = LocalizationManager(language="es_ES", locales_dir=Path("locales"))
        label = mgr.get("ui.recording")  # => "Grabando..."
        label = mgr.get("ui.count", n=5)  # => "Hay 5 elementos"
    """

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(
        self,
        language: str = "es_ES",
        locales_dir: Path | None = None,
        fallback_language: str = "en_US",
    ) -> None:
        """Initialize the localization manager.

        Args:
            language: Primary language code (e.g., "es_ES" or "en_US").
            locales_dir: Directory containing ``{lang}.yaml`` files.
                Defaults to ``audio2text/locales/`` relative to the package.
            fallback_language: Language used when a key is missing in the
                primary language.
        """
        self._language: str = language
        self._fallback_language: str = fallback_language

        if locales_dir is None:
            locales_dir = Path(__file__).resolve().parent.parent / "locales"
        self._locales_dir: Path = locales_dir

        self._primary: dict[str, Any] = {}
        self._fallback: dict[str, Any] = {}

        self._load_all()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_all(self) -> None:
        """Load primary and fallback locale files into memory."""
        self._primary = self._load_file(self._language)
        self._fallback = self._load_file(self._fallback_language)

        # If primary couldn't be loaded at all, use fallback as primary
        if not self._primary and self._fallback:
            self._primary = dict(self._fallback)

    def _load_file(self, language: str) -> dict[str, Any]:
        """Load a single locale YAML file.

        Args:
            language: Language code for the file to load.

        Returns:
            Parsed YAML content as a nested dict, empty if file not found.
        """
        file_path = self._locales_dir / f"{language}.yaml"
        if not file_path.is_file():
            return {}
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        except (yaml.YAMLError, OSError):
            return {}

    # ------------------------------------------------------------------
    # String retrieval
    # ------------------------------------------------------------------

    def get(self, key_path: str, **kwargs: Any) -> str:
        """Retrieve a localized string by dot-path.

        Falls back from primary → fallback → placeholder.
        Supports ``str.format(**kwargs)`` interpolation.

        Args:
            key_path: Dot-separated key (e.g., ``"ui.recording"``).
            **kwargs: Values for string interpolation.

        Returns:
            The localized string, or a placeholder like ``??ui.recording??``
            if the key is not found.
        """
        value = self._resolve(key_path, self._primary)
        if value is None:
            value = self._resolve(key_path, self._fallback)
        if value is None:
            return f"??{key_path}??"

        if kwargs:
            try:
                return str(value).format(**kwargs)
            except (KeyError, ValueError, IndexError):
                return str(value)

        return str(value)

    @staticmethod
    def _resolve(key_path: str, data: dict[str, Any]) -> Any | None:
        """Walk a dot-path through a nested dict.

        Args:
            key_path: Dot-separated key.
            data: Nested dictionary to search.

        Returns:
            The value if found, otherwise None.
        """
        keys = key_path.split(".")
        current: Any = data
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
            if current is None:
                return None
        return current

    # ------------------------------------------------------------------
    # Language switching
    # ------------------------------------------------------------------

    def set_language(self, language: str) -> None:
        """Switch the active language and reload locale files.

        Args:
            language: New language code.
        """
        if language != self._language:
            self._language = language
            self._load_all()

    @property
    def current_language(self) -> str:
        """The currently active language code."""
        return self._language

    @property
    def available_languages(self) -> list[str]:
        """List of available language codes found in the locales directory."""
        if not self._locales_dir.is_dir():
            return []
        langs: list[str] = []
        for f in self._locales_dir.glob("*.yaml"):
            langs.append(f.stem)
        return sorted(langs)
