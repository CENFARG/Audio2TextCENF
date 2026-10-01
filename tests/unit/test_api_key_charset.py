"""
LT-3: Groq API key charset validation — save-time and check-time.

Live log 2026-09-25: App ERROR "Error verificando API Key de Groq:
'ascii' codec can't encode character '\xe1' / '\xbf'" repeated on every
config save when the stored Groq key contains non-ASCII characters (a user
pasted a key with stray accented chars). The Groq SDK puts the key in the
Authorization header; the HTTP client cannot encode non-ASCII header values
and the check crashes with a raw ascii-codec error instead of a friendly
message.

Contract under test:
- ``validate_api_key_charset`` strips surrounding whitespace, detects
  non-ASCII content ('á', '¿', ...) and reports a typed issue instead of
  letting the network call crash.
- Save-time: ConfigManager sanitizes the Groq key on every write path
  (``set``, ``set_multiple``, ``set_groq_api_key``) and logs a localized
  friendly warning when the charset is invalid.
- Check-time: ui/app.py validates the charset BEFORE any Groq network call
  and surfaces a localized friendly error (no ascii-codec crash).
"""

import json
from unittest.mock import Mock

import pytest

from backend.config_manager import ConfigManager, validate_api_key_charset


class TestValidateApiKeyCharset:
    """Pure charset validation: strip, detect non-ASCII, pass valid keys."""

    def test_valid_key_passes(self):
        cleaned, issue = validate_api_key_charset("gsk_ABCdef123xyz456UVW")

        assert cleaned == "gsk_ABCdef123xyz456UVW"
        assert issue is None

    def test_surrounding_spaces_are_stripped(self):
        cleaned, issue = validate_api_key_charset("  gsk_ABCdef123  ")

        assert cleaned == "gsk_ABCdef123"
        assert issue is None

    def test_accented_char_detected(self):
        cleaned, issue = validate_api_key_charset("gsk_ábc123")

        assert issue == "non_ascii"
        assert cleaned == "gsk_ábc123"  # kept so the UI can show it back

    def test_inverted_question_mark_detected(self):
        cleaned, issue = validate_api_key_charset("gsk_¿abc")

        assert issue == "non_ascii"

    def test_empty_key_reports_empty(self):
        cleaned, issue = validate_api_key_charset("")

        assert cleaned == ""
        assert issue == "empty"

    def test_whitespace_only_key_reports_empty(self):
        cleaned, issue = validate_api_key_charset("   ")

        assert cleaned == ""
        assert issue == "empty"

    def test_none_is_tolerated(self):
        cleaned, issue = validate_api_key_charset(None)

        assert cleaned == ""
        assert issue == "empty"


@pytest.mark.unit
class TestSaveTimeSanitization:
    """ConfigManager must sanitize the Groq key on every save path."""

    @pytest.fixture
    def config_manager(self, tmp_path):
        cm = ConfigManager(config_file=str(tmp_path / "config.json"))
        # Isolate from the real lang files: the localized warning is a Mock
        cm.localization_manager = Mock()
        cm.localization_manager.get_string.return_value = "friendly charset error"
        return cm

    def test_set_groq_api_key_strips_and_accepts_valid(self, config_manager):
        config_manager.set_groq_api_key("  gsk_ABCdef123  ", use_keyring=False)

        assert config_manager.get("groq_api_key") == "gsk_ABCdef123"
        config_manager.localization_manager.get_string.assert_not_called()

    def test_set_groq_api_key_detects_non_ascii(self, config_manager):
        config_manager.set_groq_api_key("gsk_ábc123", use_keyring=False)

        # Key stored (stripped) so check-time can report it friendly,
        # and the localized warning is raised for the log.
        assert config_manager.get("groq_api_key") == "gsk_ábc123"
        config_manager.localization_manager.get_string.assert_called_with("api_key_charset_error")

    def test_set_sanitizes_groq_key(self, config_manager):
        config_manager.set("groq_api_key", "  gsk_ábc  ")

        assert config_manager.get("groq_api_key") == "gsk_ábc"
        config_manager.localization_manager.get_string.assert_called_with("api_key_charset_error")

    def test_set_multiple_sanitizes_groq_key(self, config_manager):
        config_manager.set_multiple(
            {"groq_api_key": " gsk_¿key ", "show_transcription_panel": True}
        )

        assert config_manager.get("groq_api_key") == "gsk_¿key"
        config_manager.localization_manager.get_string.assert_called_with("api_key_charset_error")

    def test_set_multiple_leaves_other_keys_untouched(self, config_manager):
        settings = {"groq_api_key": "gsk_clean", "max_audio_files": 50}

        config_manager.set_multiple(settings)

        assert config_manager.get("groq_api_key") == "gsk_clean"
        assert config_manager.get("max_audio_files") == 50
        config_manager.localization_manager.get_string.assert_not_called()

    def test_sanitized_key_persists_stripped(self, config_manager, tmp_path):
        config_manager.set("groq_api_key", "  gsk_ABCdef123  ")

        on_disk = json.loads((tmp_path / "config.json").read_text("utf-8"))
        # Obfuscated on disk — decode back and verify it was stripped
        decoded = config_manager._decode_gift_key(on_disk["groq_api_key"])
        assert decoded == "gsk_ABCdef123"


@pytest.mark.unit
class TestCheckTimeValidation:
    """ui/app.py must validate the charset BEFORE the Groq network call."""

    def test_check_api_key_validates_before_network_call(self):
        import inspect

        import ui.app as app_module

        source = inspect.getsource(app_module.App._check_api_key)
        validate_pos = source.find("validate_api_key_charset")
        groq_pos = source.find("Groq(")

        assert validate_pos != -1, "_check_api_key must call validate_api_key_charset"
        assert groq_pos != -1, "_check_api_key must build the Groq client"
        assert validate_pos < groq_pos, "charset validation must run BEFORE any Groq network call"
        # Friendly localized error instead of the raw ascii-codec crash
        assert "api_key_charset_error" in source

    def test_app_imports_validate_api_key_charset(self):
        import ui.app as app_module

        assert hasattr(app_module, "validate_api_key_charset")
