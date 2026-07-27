"""@File: audio2text/ui/hotkey_listener.py
@Description: Global hotkey listener using the keyboard library.
    Runs in a background daemon thread. Registers/unregisters hotkeys
    that work system-wide (even when the app is not focused).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)


class HotkeyListener:
    """Global hotkey listener backed by the ``keyboard`` library.

    Usage::

        listener = HotkeyListener()
        listener.register("f8", on_toggle)
        listener.start()  # blocking — run in a thread
        ...
        listener.stop()
    """

    def __init__(self) -> None:
        """Initialize an empty hotkey listener."""
        self._hotkeys: dict[str, Callable[[], None]] = {}
        self._thread: threading.Thread | None = None
        self._running: bool = False

    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        """Register a global hotkey with a callback.

        The callback fires when the hotkey combination is pressed,
        regardless of which application has focus.

        Args:
            hotkey: Keyboard shortcut string (e.g., "f8", "ctrl+shift+r").
            callback: Function to call when the hotkey is pressed.
        """
        import keyboard  # type: ignore[import-untyped]

        self._hotkeys[hotkey] = callback
        try:
            keyboard.add_hotkey(hotkey, callback)
            logger.info("Registered hotkey: %s", hotkey)
        except Exception as exc:
            logger.warning("Failed to register hotkey %s: %s", hotkey, exc)

    def unregister(self, hotkey: str) -> None:
        """Remove a previously registered hotkey.

        Args:
            hotkey: The keyboard shortcut to unregister.
        """
        import keyboard  # type: ignore[import-untyped]

        if hotkey in self._hotkeys:
            try:
                keyboard.remove_hotkey(hotkey)
                logger.info("Unregistered hotkey: %s", hotkey)
            except Exception as exc:
                logger.warning("Failed to unregister hotkey %s: %s", hotkey, exc)
            del self._hotkeys[hotkey]

    def start(self) -> None:
        """Start the keyboard listener in a background daemon thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("HotkeyListener started")

    def stop(self) -> None:
        """Stop the listener and clean up all registered hotkeys."""
        import keyboard  # type: ignore[import-untyped]

        self._running = False
        for hotkey in list(self._hotkeys.keys()):
            self.unregister(hotkey)
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        logger.info("HotkeyListener stopped")

    def _run_loop(self) -> None:
        """Internal blocking loop that keeps the listener alive."""
        import keyboard  # type: ignore[import-untyped]

        try:
            while self._running:
                keyboard.wait()
        except Exception as exc:
            logger.error("HotkeyListener loop error: %s", exc)

    @property
    def is_running(self) -> bool:
        """Whether the listener thread is active."""
        return self._running and self._thread is not None and self._thread.is_alive()
