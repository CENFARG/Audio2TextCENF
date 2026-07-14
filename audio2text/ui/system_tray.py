"""@File: audio2text/ui/system_tray.py
@Description: System tray integration using pystray.
    Minimizes the application to the system tray instead of closing.
    Provides Show/Exit context menu.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from PIL import Image

logger = logging.getLogger(__name__)

# 64x64 blue icon for the tray
_ICON_SIZE: int = 64
_ICON_COLOR: tuple[int, int, int] = (0, 120, 212)


class SystemTray:
    """System tray icon with Show/Exit context menu.

    Usage::

        tray = SystemTray(on_show=window.restore, on_exit=app.quit)
        tray.start()  # blocking — run in a daemon thread
    """

    def __init__(
        self,
        on_show: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        """Initialize the system tray icon.

        Args:
            on_show: Called when "Show" is clicked in the context menu.
            on_exit: Called when "Exit" is clicked in the context menu.
        """
        self._on_show = on_show
        self._on_exit = on_exit
        self._icon: object | None = None
        self._thread: threading.Thread | None = None

    def _create_icon(self) -> object:
        """Create the pystray Icon with context menu.

        Returns:
            A pystray.Icon instance.
        """
        import pystray  # type: ignore[import-untyped]

        image = Image.new("RGB", (_ICON_SIZE, _ICON_SIZE), _ICON_COLOR)

        menu = pystray.Menu(
            pystray.MenuItem(
                "Show",
                self._on_show_item,
                default=True,
            ),
            pystray.MenuItem("Exit", self._on_exit_item),
        )

        return pystray.Icon(
            name="audio2text",
            icon=image,
            title="Audio2Text",
            menu=menu,
        )

    def _on_show_item(self, icon: object, item: object) -> None:
        """Handle Show menu item click.

        Args:
            icon: The pystray.Icon instance (unused).
            item: The pystray.MenuItem instance (unused).
        """
        try:
            self._on_show()
        except Exception as exc:
            logger.error("Show callback failed: %s", exc)

    def _on_exit_item(self, icon: object, item: object) -> None:
        """Handle Exit menu item click — stop tray and call exit callback.

        Args:
            icon: The pystray.Icon instance.
            item: The pystray.MenuItem instance (unused).
        """
        try:
            if hasattr(icon, "stop"):
                icon.stop()  # type: ignore[union-attr]
        except Exception as exc:
            logger.error("Tray icon stop failed: %s", exc)
        try:
            self._on_exit()
        except Exception as exc:
            logger.error("Exit callback failed: %s", exc)

    def start(self) -> None:
        """Start the system tray in a background daemon thread.

        The pystray.Icon.run() call is blocking, so it runs in a thread.
        """
        if self._thread is not None and self._thread.is_alive():
            return

        self._icon = self._create_icon()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("SystemTray started")

    def stop(self) -> None:
        """Stop the system tray icon."""
        if self._icon is not None:
            try:
                icon = self._icon
                if hasattr(icon, "stop"):
                    icon.stop()  # type: ignore[union-attr]
            except Exception as exc:
                logger.warning("Failed to stop tray icon: %s", exc)
            self._icon = None
        logger.info("SystemTray stopped")

    def _run_loop(self) -> None:
        """Blocking loop that runs the pystray icon."""
        try:
            icon = self._icon
            if icon is not None and hasattr(icon, "run"):
                icon.run()  # type: ignore[union-attr]
        except Exception as exc:
            logger.error("SystemTray loop error: %s", exc)
