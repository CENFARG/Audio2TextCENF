"""Tests for audio2text.services.hotkey_service — hotkey management with IPC fallback."""

from __future__ import annotations

import pytest

from audio2text.services.hotkey_service import HotkeyBinding, HotkeyService


class TestHotkeyBinding:
    """Tests for HotkeyBinding dataclass."""

    def test_to_keyboard_format(self):
        """Should convert to keyboard library format."""
        b = HotkeyBinding(key="f1", modifiers=("ctrl", "shift"))
        assert b.to_keyboard_format() == "ctrl+shift+f1"

    def test_to_display_string(self):
        """Should convert to human-readable format."""
        b = HotkeyBinding(key="f1", modifiers=("ctrl", "shift"))
        assert b.to_display_string() == "Ctrl+Shift+F1"

    def test_with_mouse_button(self):
        """Should include mouse button in display string."""
        b = HotkeyBinding(key="f1", modifiers=("ctrl",), mouse_button="left")
        assert b.to_display_string() == "Ctrl+Left+F1"
        assert b.is_mouse_hotkey is True

    def test_without_mouse_button(self):
        """Should not be a mouse hotkey."""
        b = HotkeyBinding(key="f1", modifiers=("ctrl",))
        assert b.is_mouse_hotkey is False


class TestHotkeyService:
    """Tests for HotkeyService."""

    def test_parse_simple(self):
        """Should parse simple function key."""
        svc = HotkeyService()
        binding = svc.parse("f1")
        assert binding is not None
        assert binding.key == "f1"
        assert binding.modifiers == ()

    def test_parse_with_modifiers(self):
        """Should parse hotkey with modifiers."""
        svc = HotkeyService()
        binding = svc.parse("ctrl+shift+f1")
        assert binding is not None
        assert binding.key == "f1"
        assert binding.modifiers == ("ctrl", "shift")

    def test_parse_with_mouse(self):
        """Should parse hotkey with mouse button."""
        svc = HotkeyService()
        binding = svc.parse("ctrl+left+f1")
        assert binding is not None
        assert binding.key == "f1"
        assert binding.mouse_button == "left"

    def test_parse_invalid_key(self):
        """Should return None for invalid key."""
        svc = HotkeyService()
        assert svc.parse("ctrl+invalid") is None

    def test_parse_invalid_modifier(self):
        """Should return None for invalid modifier."""
        svc = HotkeyService()
        assert svc.parse("super+f1") is None

    def test_parse_empty(self):
        """Should return None for empty string."""
        svc = HotkeyService()
        assert svc.parse("") is None

    def test_validate_valid(self):
        """Should validate correct hotkey."""
        svc = HotkeyService()
        assert svc.validate("ctrl+shift+f1") is True

    def test_validate_invalid(self):
        """Should reject invalid hotkey."""
        svc = HotkeyService()
        assert svc.validate("ctrl+invalid") is False

    def test_get_available(self):
        """Should return list of available hotkeys."""
        svc = HotkeyService()
        hotkeys = svc.get_available()
        assert "f1" in hotkeys
        assert "ctrl+f1" in hotkeys
        assert "alt+f1" in hotkeys
        assert len(hotkeys) > 10

    def test_ipc_fallback_toggle(self):
        """Should toggle IPC fallback."""
        svc = HotkeyService()
        assert svc.is_ipc_fallback_enabled is True
        svc.enable_ipc_fallback(False)
        assert svc.is_ipc_fallback_enabled is False
