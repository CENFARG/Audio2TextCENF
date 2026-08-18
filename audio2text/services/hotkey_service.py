"""@File: audio2text/services/hotkey_service.py
@Description: HotkeyService — manages keyboard/mouse hotkey registration with
    IPC fallback for mouse-button hotkeys that can't be registered via
    Tauri's native global-shortcut plugin.
@Version: 0.16.0
@Author: Audio2Text Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HotkeyBinding:
    """Represents a parsed hotkey binding.

    Attributes:
        key: Primary key (e.g., "f1", "a", "1").
        modifiers: List of modifiers (e.g., ["ctrl", "shift"]).
        mouse_button: Optional mouse button (e.g., "left", "right").
    """

    key: str
    modifiers: tuple[str, ...] = ()
    mouse_button: Optional[str] = None

    def to_keyboard_format(self) -> str:
        """Convert to format understood by the `keyboard` library.

        Returns:
            String like "ctrl+shift+f1".
        """
        parts = list(self.modifiers)
        parts.append(self.key)
        return "+".join(parts)

    def to_display_string(self) -> str:
        """Convert to human-readable format.

        Returns:
            String like "Ctrl+Shift+F1".
        """
        parts = [m.capitalize() for m in self.modifiers]
        if self.mouse_button:
            parts.append(self.mouse_button.capitalize())
        parts.append(self.key.upper())
        return "+".join(parts)

    @property
    def is_mouse_hotkey(self) -> bool:
        """True if this hotkey involves a mouse button."""
        return self.mouse_button is not None


class HotkeyService:
    """Manages hotkey registration with IPC fallback.

    Supports:
    - Keyboard modifiers: Ctrl, Alt, Shift, and combinations
    - Function keys F1-F12 and alphanumeric keys
    - Mouse buttons: left, right, middle, side, extra
    - Combinations of keyboard + mouse

    When Tauri's native global-shortcut plugin can't handle mouse buttons,
    this service falls back to the Python `keyboard` library via IPC.
    """

    # Supported modifiers
    MODIFIERS = frozenset({"ctrl", "alt", "shift"})

    # Supported mouse buttons
    MOUSE_BUTTONS = frozenset({"left", "right", "middle", "side", "extra"})

    # Supported function keys
    F_KEYS = frozenset(f"f{i}" for i in range(1, 13))

    # Valid alphanumeric keys
    LETTER_KEYS = frozenset(chr(i) for i in range(ord("a"), ord("z") + 1))
    DIGIT_KEYS = frozenset(str(i) for i in range(10))
    VALID_KEYS = F_KEYS | LETTER_KEYS | DIGIT_KEYS

    def __init__(self) -> None:
        """Initialize the hotkey service."""
        self._registered: dict[str, str] = {}  # hotkey_str -> display string
        self._ipc_fallback_enabled: bool = True

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def parse(self, hotkey_str: str) -> HotkeyBinding | None:
        """Parse a hotkey string into a HotkeyBinding.

        Args:
            hotkey_str: Hotkey string like "ctrl+shift+f1", "alt+f5", "f12".

        Returns:
            HotkeyBinding if valid, None if invalid.
        """
        parts = [p.strip() for p in hotkey_str.lower().split("+") if p.strip()]
        if not parts:
            return None

        key = parts[-1]
        modifiers = tuple(p for p in parts[:-1] if p not in self.MOUSE_BUTTONS)
        mouse_button = next((p for p in parts if p in self.MOUSE_BUTTONS), None)

        # Validate key
        if key not in self.VALID_KEYS:
            logger.warning("Invalid key: %s", key)
            return None

        # Validate modifiers
        for mod in modifiers:
            if mod not in self.MODIFIERS:
                logger.warning("Invalid modifier: %s", mod)
                return None

        return HotkeyBinding(key=key, modifiers=modifiers, mouse_button=mouse_button)

    def validate(self, hotkey_str: str) -> bool:
        """Validate a hotkey string without registering it.

        Args:
            hotkey_str: Hotkey string to validate.

        Returns:
            True if valid, False otherwise.
        """
        return self.parse(hotkey_str) is not None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        hotkey_str: str,
        callback: Callable[[], None],
        suppress: bool = True,
        use_ipc_fallback: bool = True,
    ) -> bool:
        """Register a hotkey with optional IPC fallback.

        For mouse-button hotkeys, falls back to the Python `keyboard`
        library if Tauri native registration is not available.

        Args:
            hotkey_str: Hotkey string like "ctrl+shift+f1".
            callback: Function to call when hotkey is pressed.
            suppress: If True, suppress the key event.
            use_ipc_fallback: If True, allow IPC fallback for mouse hotkeys.

        Returns:
            True if registration succeeded.
        """
        binding = self.parse(hotkey_str)
        if binding is None:
            return False

        # For mouse hotkeys, use IPC fallback if available
        if binding.is_mouse_hotkey and use_ipc_fallback and self._ipc_fallback_enabled:
            return self._register_via_ipc(binding, callback, suppress)

        # Try native registration (keyboard library)
        return self._register_native(binding, callback, suppress)

    def _register_native(
        self,
        binding: HotkeyBinding,
        callback: Callable[[], None],
        suppress: bool,
    ) -> bool:
        """Register via the keyboard library."""
        try:
            import keyboard

            keyboard.add_hotkey(
                binding.to_keyboard_format(),
                callback,
                suppress=suppress,
            )
            self._registered[binding.to_keyboard_format()] = binding.to_display_string()
            logger.info("Hotkey registered (native): %s", binding.to_display_string())
            return True
        except ImportError:
            logger.warning("keyboard library not available")
            return False
        except Exception as e:
            logger.error("Failed to register hotkey %s: %s", binding.to_display_string(), e)
            return False

    def _register_via_ipc(
        self,
        binding: HotkeyBinding,
        callback: Callable[[], None],
        suppress: bool,
    ) -> bool:
        """Register via IPC bridge (fallback for mouse-button hotkeys).

        This is called from the sidecar when Rust native hotkey registration
        fails for mouse-button hotkeys.
        """
        if not binding.is_mouse_hotkey:
            return False

        # Use the keyboard library as IPC fallback
        return self._register_native(binding, callback, suppress)

    def unregister(self, hotkey_str: str) -> bool:
        """Unregister a hotkey.

        Args:
            hotkey_str: Hotkey string to unregister.

        Returns:
            True if unregistration succeeded.
        """
        binding = self.parse(hotkey_str)
        if binding is None:
            return False

        try:
            import keyboard

            keyboard.remove_hotkey(binding.to_keyboard_format())
            self._registered.pop(binding.to_keyboard_format(), None)
            logger.info("Hotkey unregistered: %s", binding.to_display_string())
            return True
        except Exception as e:
            logger.error("Failed to unregister hotkey %s: %s", binding.to_display_string(), e)
            return False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_registered(self) -> dict[str, str]:
        """Return all registered hotkeys.

        Returns:
            Mapping of hotkey format string to display string.
        """
        return dict(self._registered)

    def get_available(self) -> list[str]:
        """Return a list of commonly available hotkey strings.

        Returns:
            List of hotkey strings.
        """
        hotkeys = []
        for f in sorted(self.F_KEYS):
            hotkeys.append(f)
            hotkeys.append(f"ctrl+{f}")
            hotkeys.append(f"alt+{f}")
            hotkeys.append(f"shift+{f}")
            hotkeys.append(f"ctrl+shift+{f}")
            hotkeys.append(f"ctrl+alt+{f}")
        return hotkeys

    def enable_ipc_fallback(self, enabled: bool) -> None:
        """Enable or disable IPC fallback for mouse hotkeys.

        Args:
            enabled: True to enable, False to disable.
        """
        self._ipc_fallback_enabled = enabled

    @property
    def is_ipc_fallback_enabled(self) -> bool:
        """True if IPC fallback is enabled."""
        return self._ipc_fallback_enabled
