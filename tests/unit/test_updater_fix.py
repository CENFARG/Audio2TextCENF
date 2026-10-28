"""Headless tests for the update-tab UI handoff helpers (S7 / T8).

The UpdateTab must own the app shutdown after a successful install and
must render explicit download states. These tests exercise only the pure
module-level helpers extracted for that purpose — no Tk window, no App.

The exit-ownership contract:
- install_update() returns an InstallResult -> UI schedules shutdown.
- install_update() raises -> UI shows the reason and stays alive.
- Shutdown prefers the host app's full-cleanup path (quit_application)
  and falls back to quit()+destroy() on generic toplevels.

Progress states:
- Known total -> determinate fraction + "N%" label.
- Unknown/zero total (version.json file_size=0 or missing header) ->
  indeterminate: label shows downloaded MB, never "0%".
"""

from backend.updater import InstallResult
from ui.update_tab import (
    format_progress_label,
    format_up_to_date_text,
    progress_fraction,
    resolve_post_install_action,
    resolve_shutdown_callable,
)


def make_install_result() -> InstallResult:
    return InstallResult(
        batch_path="C:/temp/update_install.bat",
        source_path="C:/temp/audio2text_update.exe",
        target_path="C:/app/Audio2Text.exe",
        log_path="C:/temp/update_install.log",
    )


# ---------------------------------------------------------------------------
# Exit ownership: backend outcome -> UI action
# ---------------------------------------------------------------------------


def test_resolve_post_install_action_shutdown_on_install_result() -> None:
    """A successful install hands shutdown ownership to the UI."""
    assert resolve_post_install_action(make_install_result()) == "shutdown"


def test_resolve_post_install_action_error_on_failure() -> None:
    """Anything that is not an InstallResult keeps the app alive."""
    assert resolve_post_install_action(RuntimeError("move failed")) == "error"
    assert resolve_post_install_action(None) == "error"
    assert resolve_post_install_action("shutdown") == "error"


# ---------------------------------------------------------------------------
# Shutdown callable selection (duck-typed, no Tk required)
# ---------------------------------------------------------------------------


def test_resolve_shutdown_callable_prefers_app_full_cleanup() -> None:
    """Hosts exposing quit_application() get their full-cleanup path."""

    class FakeApp:
        def __init__(self) -> None:
            self.calls: list = []

        def quit_application(self) -> None:
            self.calls.append("quit_application")

    app = FakeApp()
    shutdown = resolve_shutdown_callable(app)
    shutdown()
    assert app.calls == ["quit_application"]


def test_resolve_shutdown_callable_fallback_quit_then_destroy() -> None:
    """Generic toplevels fall back to quit() followed by destroy()."""

    class FakeToplevel:
        def __init__(self) -> None:
            self.calls: list = []

        def quit(self) -> None:
            self.calls.append("quit")

        def destroy(self) -> None:
            self.calls.append("destroy")

    toplevel = FakeToplevel()
    shutdown = resolve_shutdown_callable(toplevel)
    shutdown()
    assert toplevel.calls == ["quit", "destroy"]


# ---------------------------------------------------------------------------
# Download progress: determinate vs indeterminate
# ---------------------------------------------------------------------------


def test_progress_fraction_known_total() -> None:
    assert progress_fraction(0, 100) == 0.0
    assert progress_fraction(50, 100) == 0.5
    assert progress_fraction(100, 100) == 1.0


def test_progress_fraction_clamped_over_download() -> None:
    assert progress_fraction(150, 100) == 1.0


def test_progress_fraction_unknown_total_is_indeterminate() -> None:
    assert progress_fraction(100, 0) is None
    assert progress_fraction(100, -1) is None


def test_progress_label_known_total_shows_percent() -> None:
    label = format_progress_label(500, 1000)
    assert "50%" in label


def test_progress_label_unknown_total_shows_mb_and_no_percent() -> None:
    """file_size=0 case: MB downloaded instead of a stuck 0%."""
    label = format_progress_label(3 * 1024 * 1024, 0)
    assert "3.0 MB" in label
    assert "%" not in label


def test_progress_label_zero_downloaded_unknown_total_not_zero_percent() -> None:
    label = format_progress_label(0, 0)
    assert "0.0 MB" in label
    assert "%" not in label


# ---------------------------------------------------------------------------
# Up-to-date state shows the current version
# ---------------------------------------------------------------------------


def test_up_to_date_text_includes_current_version() -> None:
    text = format_up_to_date_text("0.16.1")
    assert "0.16.1" in text


def test_up_to_date_text_is_positive() -> None:
    text = format_up_to_date_text("0.16.1")
    assert any(mark in text for mark in ("✅", "última", "latest"))


def test_helpers_never_import_tk() -> None:
    """The helper module import must not require a display."""
    import ui.update_tab as module

    assert module is not None
    assert callable(module.resolve_post_install_action)
    assert callable(module.resolve_shutdown_callable)
