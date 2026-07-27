"""@File: audio2text/ui/app.py
@Description: Main Flet application entry point — page setup, theme, routing.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

import flet as ft
from cenf_core.logging.manager import LoggerManager
from cenf_core.logging.profiles import LogProfile

from audio2text.localization.manager import LocalizationManager
from audio2text.ui.client.api_client import APIClient
from audio2text.ui.state.store import AppState
from audio2text.ui.theme.theme import build_theme
from audio2text.ui.views.main_view import MainView

# ── Logging ────────────────────────────────────────────────────────────────

_logger_manager = LoggerManager(
    profile=LogProfile.DEVELOPMENT,
    log_dir=Path("logs"),
)

# Suppress noisy third-party libraries — keeps logs readable (~500k → ~5k)
# while preserving our own [DEBUG] output via DEVELOPMENT profile.
_logger_manager.suppress_library("flet", logging.INFO)
_logger_manager.suppress_library("flet_core", logging.INFO)
_logger_manager.suppress_library("flet_transport", logging.INFO)
_logger_manager.suppress_library("flet_desktop", logging.INFO)
_logger_manager.suppress_library("httpcore.connection", logging.INFO)
_logger_manager.suppress_library("httpcore.http11", logging.INFO)
_logger_manager.suppress_library("httpx", logging.INFO)
_logger_manager.suppress_library("asyncio", logging.INFO)
_logger_manager.suppress_library("urllib3", logging.INFO)

_logger = _logger_manager.get_logger("ui.app")

# ── File logging — auto-save app.log ────────────────────────────────────────


def _configure_app_logging(
    log_dir: Path | None = None,
    root_logger: logging.Logger | None = None,
    version: str = "0.16.0",
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """Add a RotatingFileHandler for ``app.log`` with session separator.

    Captures ALL log output (app + third-party libs) at DEBUG level.
    Each run appends; the file is rotated at *max_bytes* with *backup_count*
    backups.

    Args:
        log_dir: Directory for log files (default: ``logs/``).
        root_logger: Logger to attach handler to (default: root logger).
        version: Version string for the session separator.
        max_bytes: Max file size before rotation (default: 5 MB).
        backup_count: Number of backup files to keep (default: 3).
    """
    _dir = log_dir or Path("logs")
    _root = root_logger or logging.getLogger()

    _dir.mkdir(parents=True, exist_ok=True)
    file_path = _dir / "app.log"

    # Write session separator as raw text before opening handler (so it
    # is the very first line, unformatted, before any log entries).
    separator = (
        f"========== Audio2Text v{version} — "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==========\n"
    )
    with file_path.open("a", encoding="utf-8") as f:
        f.write(separator)

    handler = RotatingFileHandler(
        str(file_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
        delay=False,
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s:%(lineno)d: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
    )
    _root.addHandler(handler)


# Wire at import time — ensures every run has app.log with session marker
_configure_app_logging(log_dir=Path("logs"), version="0.16.0")


def _resolve_locales_dir() -> Path:
    """Resolve the locales directory relative to the package root.

    Returns:
        Path to the locales directory.
    """
    # parent = audio2text/ui → parent.parent = audio2text → locales under audio2text/
    return Path(__file__).resolve().parent.parent / "locales"


class Audio2TextFletApp:
    """Flet application wrapper — sets up page, theme, state, and views.

    Usage::

        ft.run(Audio2TextFletApp().main)
    """

    def __init__(
        self,
        api_base_url: str = "http://127.0.0.1:8765",
        language: str = "es_ES",
    ) -> None:
        """Initialize the Flet app.

        Args:
            api_base_url: Base URL of the Audio2Text REST API.
            language: Initial UI language code.
        """
        _logger.info("Audio2TextFletApp.__init__ — creating API client")
        self._api = APIClient(base_url=api_base_url)

        _logger.info("Audio2TextFletApp.__init__ — initializing AppState")
        self._store = AppState()

        _logger.info(
            "Audio2TextFletApp.__init__ — loading locales from %s (language=%s)",
            _resolve_locales_dir(),
            language,
        )
        self._t = LocalizationManager(
            language=language,
            locales_dir=_resolve_locales_dir(),
        )
        _logger.info("Audio2TextFletApp.__init__ — locales loaded OK")

    async def main(self, page: ft.Page) -> None:
        """Flet app entry point.

        Args:
            page: The Flet Page instance provided by the framework.
        """
        _logger.info("Audio2Text v0.16.0 starting...")
        # ── Page configuration ──────────────────────────────────────
        page.title = self._t.get("app.title")
        _logger.info("Page title set to: %s", page.title)
        page.padding = 0
        page.spacing = 0
        page.theme_mode = ft.ThemeMode.DARK if self._store.is_dark_mode else ft.ThemeMode.LIGHT
        page.theme = ft.Theme(**build_theme(dark_mode=False))
        page.dark_theme = ft.Theme(**build_theme(dark_mode=True))
        page.window.width = 1100
        page.window.height = 760
        page.window.min_width = 800
        page.window.min_height = 600

        # ── Theme change handler ───────────────────────────────────
        def _on_theme_changed(dark: bool) -> None:
            page.theme_mode = ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT
            page.update()

        self._store.on_theme_change = _on_theme_changed

        # ── Language change handler ────────────────────────────────
        def _on_lang_changed(lang: str) -> None:
            page.title = self._t.get("app.title")
            page.update()

        self._store.on_language_change = _on_lang_changed  # type: ignore[assignment]

        # ── Build UI ───────────────────────────────────────────────
        _logger.info("main() — building MainView")
        main_view = MainView(
            page=page,
            store=self._store,
            api=self._api,
            t=self._t,
        )
        _logger.info("main() — MainView built, %d controls", len(main_view.controls))

        page.add(main_view)
        page.update()
        _logger.info("main() — page updated, UI ready")

        # ── Startup hydration (health check → settings → blocks → history) ──
        page.run_task(self._hydrate, page)

    async def _hydrate(self, page: ft.Page) -> None:
        """Hydrate AppState from the backend on startup.

        Calls get_health() first. On success, sequentially fetches
        settings, context blocks, and history — each step is fail-soft.
        """
        _logger.info("_hydrate() — starting hydration sequence")
        await self._api.start()
        try:
            health = await self._api.get_health()
            _logger.info("_hydrate() — health check passed: %s", health)
        except Exception as exc:
            _logger.error("_hydrate() — health check failed: %s", exc)
            self._api.show_error(
                page,
                f"No se pudo conectar al servidor ({self._api.base_url}). [{exc}]",
            )
            return

        # Settings (fail-soft)
        try:
            settings = await self._api.get_settings()
            self._store.hydrate_settings(settings)
            _logger.info("_hydrate() — settings hydrated")
        except Exception as exc:
            _logger.warning("_hydrate() — settings fetch failed: %s", exc)

        # Context blocks (fail-soft)
        try:
            blocks = await self._api.get_context_blocks()
            self._store.hydrate_blocks(blocks)
            _logger.info("_hydrate() — context blocks hydrated: %d", len(blocks))
        except Exception as exc:
            _logger.warning("_hydrate() — context blocks fetch failed: %s", exc)

        # History (fail-soft)
        try:
            history = await self._api.get_history(limit=50, offset=0)
            self._store.hydrate_history(history)
            _logger.info("_hydrate() — history hydrated: %d items", len(history))
        except Exception as exc:
            _logger.warning("_hydrate() — history fetch failed: %s", exc)

        _logger.info("_hydrate() — hydration sequence complete")


def main() -> None:
    """Launch the Flet desktop app."""
    _logger.info("Launching Audio2Text Flet desktop app...")
    app = Audio2TextFletApp()
    _logger.info("Starting ft.run() with Flet 0.85.0")
    ft.run(app.main)


if __name__ == "__main__":
    main()
