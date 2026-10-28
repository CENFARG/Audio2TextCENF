"""Headless tests for the updater backend (S7 / T8).

All network and process side effects are mocked. No Tk window is created,
no real download is performed, and no subprocess is spawned.

Covers:
- install_update() returns an InstallResult and never terminates the
  process itself (the UI layer owns the shutdown).
- The generated install batch retries the move of the running executable
  and logs a manual-install fallback path when it finally fails.
- install_update() rejects non-frozen mode and missing/empty downloads
  with the typed UpdaterError.
- download_update() verifies the payload is non-empty and reports
  progress even when the server omits content-length.
- check_for_updates() detection contract is preserved.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from unittest.mock import MagicMock

import pytest
import requests

from backend.updater import InstallResult, Updater, UpdaterError


def make_updater() -> Updater:
    """Build an Updater with a simulated outdated version."""
    return Updater(current_version="0.16.0", github_repo="CENFARG/Audio2Text")


class FakeDownloadResponse:
    """Streamed-download stub for requests.get."""

    def __init__(self, chunks: List[bytes], headers: Optional[Dict[str, str]] = None):
        self._chunks = chunks
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int = 8192) -> Iterator[bytes]:
        yield from self._chunks


class FakeVersionResponse:
    """version.json stub for requests.get."""

    def __init__(self, status_code: int, payload: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> Dict[str, Any]:
        return self._payload


def make_source_file(tmp_path: Path) -> Path:
    """Create a fake downloaded installer payload."""
    source = tmp_path / "audio2text_update.exe"
    source.write_bytes(b"MZ" + b"\x00" * 30)
    return source


def patch_frozen_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Simulate a frozen (PyInstaller) app whose exe lives in tmp_path."""
    target = tmp_path / "Audio2Text.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(target))
    monkeypatch.setenv("TEMP", str(tmp_path))
    return target


def patch_popen(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Prevent any real subprocess spawn; return the mock for assertions."""
    popen = MagicMock()
    monkeypatch.setattr("subprocess.Popen", popen)
    return popen


# ---------------------------------------------------------------------------
# install_update: exit ownership moves to the UI layer
# ---------------------------------------------------------------------------


def test_install_update_returns_result_and_never_terminates_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """install_update returns an InstallResult; the UI decides to shut down."""
    updater = make_updater()
    source = make_source_file(tmp_path)
    target = patch_frozen_env(monkeypatch, tmp_path)
    popen = patch_popen(monkeypatch)

    result = updater.install_update(str(source))

    assert isinstance(result, InstallResult)
    assert result.source_path == str(source)
    assert result.target_path == str(target)
    assert Path(result.batch_path).name == "update_install.bat"
    assert Path(result.log_path).name == "update_install.log"
    assert popen.called


def test_install_batch_retries_move_and_logs_manual_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Batch retries the locked-exe move; on final failure keeps the file."""
    updater = make_updater()
    source = make_source_file(tmp_path)
    patch_frozen_env(monkeypatch, tmp_path)
    patch_popen(monkeypatch)

    result = updater.install_update(str(source))
    batch = Path(result.batch_path).read_text(encoding="utf-8")

    # The move of a running exe usually fails: a retry with delay must exist.
    assert batch.count("move /y") >= 2
    assert "timeout /t 3" in batch
    # The batch writes its outcome to a log file next to the batch.
    assert str(result.log_path) in batch
    # On final failure the downloaded installer is kept and its path logged.
    assert str(source) in batch
    assert "kept at" in batch
    # The batch deletes only itself, never the downloaded installer.
    assert 'del "%~f0"' in batch
    # And it relaunches the app after a successful move.
    assert 'start ""' in batch


def test_install_update_rejects_non_frozen_mode_with_typed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Outside a frozen build install is impossible: UpdaterError, no exit."""
    source = make_source_file(tmp_path)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setenv("TEMP", str(tmp_path))
    patch_popen(monkeypatch)

    with pytest.raises(UpdaterError):
        make_updater().install_update(str(source))


@pytest.mark.parametrize("payload", [None, b""])
def test_install_update_rejects_missing_or_empty_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: Optional[bytes]
) -> None:
    """A missing or 0-byte download must be rejected before any install."""
    updater = make_updater()
    patch_frozen_env(monkeypatch, tmp_path)
    patch_popen(monkeypatch)

    if payload is None:
        source = tmp_path / "does_not_exist.exe"
    else:
        source = tmp_path / "empty_update.exe"
        source.write_bytes(payload)

    with pytest.raises(UpdaterError):
        updater.install_update(str(source))


# ---------------------------------------------------------------------------
# download_update: payload verification and indeterminate progress
# ---------------------------------------------------------------------------


def test_download_update_writes_all_chunks_and_returns_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Chunks are written in order and the returned path holds the payload."""
    monkeypatch.setenv("TEMP", str(tmp_path))
    chunks = [b"a" * 8192, b"b" * 10]
    monkeypatch.setattr(
        "backend.updater.requests.get",
        lambda *a, **k: FakeDownloadResponse(
            chunks, headers={"content-length": str(8192 + 10)}
        ),
    )

    path = make_updater().download_update("https://example.com/app.exe")

    assert Path(path).read_bytes() == b"a" * 8192 + b"b" * 10


def test_download_update_empty_payload_raises_typed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 0-byte download must fail loudly instead of staging a broken exe."""
    monkeypatch.setenv("TEMP", str(tmp_path))
    monkeypatch.setattr(
        "backend.updater.requests.get",
        lambda *a, **k: FakeDownloadResponse([b""], headers={}),
    )

    with pytest.raises(UpdaterError):
        make_updater().download_update("https://example.com/app.exe")


def test_download_update_progress_with_unknown_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without content-length the callback still reports downloaded bytes
    with total=0 so the UI can show an indeterminate state."""
    monkeypatch.setenv("TEMP", str(tmp_path))
    chunks = [b"x" * 100, b"y" * 50]
    monkeypatch.setattr(
        "backend.updater.requests.get",
        lambda *a, **k: FakeDownloadResponse(chunks, headers={}),
    )
    calls: List[tuple] = []

    make_updater().download_update(
        "https://example.com/app.exe", progress_callback=lambda d, t: calls.append((d, t))
    )

    assert calls[-1] == (150, 0)


# ---------------------------------------------------------------------------
# check_for_updates: detection contract is preserved
# ---------------------------------------------------------------------------


def test_check_for_updates_detects_newer_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A newer version.json yields available=True with asset metadata."""
    payload = {
        "version": "0.16.1",
        "download_url": "https://example.com/app.exe",
        "changelog": "fixes",
        "release_date": "2026-10-28",
        "file_size": 48_000_000,
    }
    monkeypatch.setattr(
        "backend.updater.requests.get",
        lambda *a, **k: FakeVersionResponse(200, payload),
    )

    info = make_updater().check_for_updates()

    assert info["available"] is True
    assert info["version"] == "0.16.1"
    assert info["download_url"] == "https://example.com/app.exe"


def test_check_for_updates_up_to_date(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same or older version yields available=False and no error."""
    monkeypatch.setattr(
        "backend.updater.requests.get",
        lambda *a, **k: FakeVersionResponse(200, {"version": "0.16.0"}),
    )

    info = make_updater().check_for_updates()

    assert info == {"available": False}


def test_check_for_updates_http_error_carries_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HTTP failures return available=False plus a human-readable reason."""
    monkeypatch.setattr(
        "backend.updater.requests.get",
        lambda *a, **k: FakeVersionResponse(404),
    )

    info = make_updater().check_for_updates()

    assert info["available"] is False
    assert "404" in info["error"]


def test_check_for_updates_connection_error_carries_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Network failures are reported as a reason, never raised."""
    def raise_conn(*a: Any, **k: Any) -> Any:
        raise requests.exceptions.ConnectionError("no network")

    monkeypatch.setattr("backend.updater.requests.get", raise_conn)

    info = make_updater().check_for_updates()

    assert info["available"] is False
    assert info["error"]
