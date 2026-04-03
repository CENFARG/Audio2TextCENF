"""
Unit tests for HotkeyManager class.

This module tests hotkey management functionality including:
- Parsing hotkey strings
- Validating hotkeys
- Formatting hotkeys
- Modifier handling

Author: Audio2Text Development Team
Version: 0.13.0
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.hotkey_manager import HotkeyManager, Hotkey


@pytest.mark.unit
class TestHotkeyDataclass:
    """Tests for Hotkey dataclass."""

    def test_hotkey_creation_simple(self):
        """Test creating a simple hotkey."""
        hotkey = Hotkey(key="f5", modifiers=[])

        assert hotkey.key == "f5"
        assert hotkey.modifiers == []
        assert hotkey.mouse_button is None

    def test_hotkey_creation_with_modifiers(self):
        """Test creating a hotkey with modifiers."""
        hotkey = Hotkey(key="f1", modifiers=["ctrl", "shift"])

        assert hotkey.key == "f1"
        assert hotkey.modifiers == ["ctrl", "shift"]

    def test_hotkey_string_representation(self):
        """Test string representation of hotkey."""
        hotkey = Hotkey(key="f5", modifiers=["ctrl", "shift"])

        result = str(hotkey)

        assert result == "Ctrl+Shift+F5"

    def test_hotkey_to_keyboard_format(self):
        """Test converting to keyboard library format."""
        hotkey = Hotkey(key="f1", modifiers=["alt"])

        result = hotkey.to_keyboard_format()

        assert result == "alt+f1"


@pytest.mark.unit
class TestHotkeyManagerParsing:
    """Tests for hotkey string parsing."""

    @pytest.fixture
    def manager(self):
        """Create a HotkeyManager instance."""
        return HotkeyManager()

    def test_parse_simple_hotkey(self, manager):
        """Test parsing a simple hotkey string."""
        hotkey = manager.parse_hotkey_string("f5")

        assert hotkey.key == "f5"
        assert hotkey.modifiers == []
        assert hotkey.mouse_button is None

    def test_parse_hotkey_with_modifiers(self, manager):
        """Test parsing hotkey with modifiers."""
        hotkey = manager.parse_hotkey_string("ctrl+shift+f1")

        assert hotkey.key == "f1"
        assert hotkey.modifiers == ["ctrl", "shift"]

    def test_parse_hotkey_with_single_modifier(self, manager):
        """Test parsing hotkey with single modifier."""
        hotkey = manager.parse_hotkey_string("alt+f10")

        assert hotkey.key == "f10"
        assert hotkey.modifiers == ["alt"]

    def test_parse_hotkey_case_insensitive(self, manager):
        """Test that parsing is case insensitive."""
        hotkey = manager.parse_hotkey_string("CTRL+Shift+F5")

        assert hotkey.key == "f5"
        assert hotkey.modifiers == ["ctrl", "shift"]

    def test_parse_hotkey_with_alphanumeric_key(self, manager):
        """Test parsing hotkey with alphanumeric key."""
        hotkey = manager.parse_hotkey_string("ctrl+a")

        assert hotkey.key == "a"
        assert hotkey.modifiers == ["ctrl"]


@pytest.mark.unit
class TestHotkeyValidation:
    """Tests for hotkey validation."""

    @pytest.fixture
    def manager(self):
        """Create a HotkeyManager instance."""
        return HotkeyManager()

    def test_valid_simple_hotkey(self, manager):
        """Test validation of valid simple hotkey."""
        assert manager.is_hotkey_valid("f5") == True

    def test_valid_hotkey_with_modifiers(self, manager):
        """Test validation of valid hotkey with modifiers."""
        assert manager.is_hotkey_valid("ctrl+shift+f1") == True
        assert manager.is_hotkey_valid("alt+f10") == True
        assert manager.is_hotkey_valid("shift+a") == True

    def test_invalid_key(self, manager):
        """Test validation with invalid key."""
        assert manager.is_hotkey_valid("invalid") == False
        assert manager.is_hotkey_valid("ctrl+xyz") == False

    def test_invalid_modifier(self, manager):
        """Test validation with invalid modifier."""
        assert manager.is_hotkey_valid("win+f5") == False

    def test_empty_hotkey(self, manager):
        """Test validation of empty hotkey."""
        assert manager.is_hotkey_valid("") == False

    def test_valid_f_keys(self, manager):
        """Test all F keys are valid."""
        for i in range(1, 13):
            assert manager.is_hotkey_valid(f"f{i}") == True

    def test_valid_alphanumeric_keys(self, manager):
        """Test alphanumeric keys are valid."""
        assert manager.is_hotkey_valid("a") == True
        assert manager.is_hotkey_valid("z") == True
        assert manager.is_hotkey_valid("0") == True
        assert manager.is_hotkey_valid("9") == True


@pytest.mark.unit
class TestHotkeyFormatting:
    """Tests for hotkey formatting."""

    @pytest.fixture
    def manager(self):
        """Create a HotkeyManager instance."""
        return HotkeyManager()

    def test_format_simple_hotkey(self, manager):
        """Test formatting simple hotkey."""
        result = manager.format_hotkey_string("f5", [], None)

        assert result == "f5"

    def test_format_hotkey_with_modifiers(self, manager):
        """Test formatting hotkey with modifiers."""
        result = manager.format_hotkey_string("f1", ["ctrl", "shift"], None)

        assert result == "ctrl+shift+f1"

    def test_format_hotkey_with_mouse_button(self, manager):
        """Test formatting hotkey with mouse button."""
        result = manager.format_hotkey_string("f5", [], "left")

        assert result == "left+f5"

    def test_format_hotkey_complete(self, manager):
        """Test formatting complete hotkey."""
        result = manager.format_hotkey_string("f10", ["ctrl"], "right")

        assert result == "ctrl+right+f10"


@pytest.mark.unit
class TestHotkeyConstants:
    """Tests for HotkeyManager constants."""

    def test_modifiers_constant(self):
        """Test MODIFIERS constant."""
        assert "ctrl" in HotkeyManager.MODIFIERS
        assert "alt" in HotkeyManager.MODIFIERS
        assert "shift" in HotkeyManager.MODIFIERS

    def test_mouse_buttons_constant(self):
        """Test MOUSE_BUTTONS constant."""
        assert "left" in HotkeyManager.MOUSE_BUTTONS
        assert "right" in HotkeyManager.MOUSE_BUTTONS
        assert "middle" in HotkeyManager.MOUSE_BUTTONS

    def test_f_keys_constant(self):
        """Test F_KEYS constant."""
        assert len(HotkeyManager.F_KEYS) == 12
        assert "f1" in HotkeyManager.F_KEYS
        assert "f12" in HotkeyManager.F_KEYS


@pytest.mark.unit
class TestHotkeyRegistration:
    """Tests for hotkey registration (mocked)."""

    @pytest.fixture
    def manager(self):
        """Create a HotkeyManager instance."""
        return HotkeyManager()

    def test_register_hotkey_mocked(self, manager):
        """Test hotkey registration with mocked keyboard library."""
        with patch('backend.hotkey_manager.keyboard') as mock_keyboard:
            mock_keyboard.add_hotkey.return_value = True

            callback = Mock()
            result = manager.register_hotkey("ctrl+f5", callback)

            # Verify keyboard.add_hotkey was called
            assert mock_keyboard.add_hotkey.called

    def test_unregister_hotkey_mocked(self, manager):
        """Test hotkey unregistration with mocked keyboard library."""
        with patch('backend.hotkey_manager.keyboard') as mock_keyboard:
            # Simulate registered hotkey
            manager.registered_hotkeys["ctrl+f5"] = Mock()

            manager.unregister_hotkey("ctrl+f5")

            # Verify keyboard.remove_hotkey was called
            assert mock_keyboard.remove_hotkey.called


@pytest.mark.unit
class TestHotkeyEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def manager(self):
        """Create a HotkeyManager instance."""
        return HotkeyManager()

    def test_parse_hotkey_with_extra_plus(self, manager):
        """Test parsing hotkey with extra plus signs."""
        hotkey = manager.parse_hotkey_string("ctrl++shift+f5")

        # Should handle gracefully
        assert hotkey.key == "f5"

    def test_parse_hotkey_with_spaces(self, manager):
        """Test parsing hotkey with spaces."""
        hotkey = manager.parse_hotkey_string("ctrl + shift + f5")

        # Spaces should be handled
        assert "ctrl" in hotkey.modifiers or "shift" in hotkey.modifiers

    def test_multiple_modifiers_same_type(self, manager):
        """Test hotkey with duplicate modifiers."""
        hotkey = manager.parse_hotkey_string("ctrl+ctrl+f5")

        # Should deduplicate or handle gracefully
        assert hotkey.key == "f5"
