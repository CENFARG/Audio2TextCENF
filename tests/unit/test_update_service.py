"""@File: tests/unit/test_update_service.py
@Description: Unit tests for UpdateService — in-app version check and update.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# RED phase — UpdateService does NOT exist yet
# ---------------------------------------------------------------------------


class TestUpdateServiceCompareVersions:
    """Semantic version comparison tests."""

    def test_compare_equal_versions(self) -> None:
        """0.16.0 == 0.16.0 → 0."""
        from audio2text.services.update_service import UpdateService

        assert UpdateService.compare_versions("0.16.0", "0.16.0") == 0

    def test_compare_latest_is_newer_patch(self) -> None:
        """0.16.1 > 0.16.0."""
        from audio2text.services.update_service import UpdateService

        assert UpdateService.compare_versions("0.16.0", "0.16.1") < 0

    def test_compare_latest_is_newer_minor(self) -> None:
        """0.17.0 > 0.16.0."""
        from audio2text.services.update_service import UpdateService

        assert UpdateService.compare_versions("0.16.0", "0.17.0") < 0

    def test_compare_latest_is_newer_major(self) -> None:
        """1.0.0 > 0.16.0."""
        from audio2text.services.update_service import UpdateService

        assert UpdateService.compare_versions("0.16.0", "1.0.0") < 0

    def test_compare_current_is_newer(self) -> None:
        """0.16.0 > 0.15.9."""
        from audio2text.services.update_service import UpdateService

        assert UpdateService.compare_versions("0.16.0", "0.15.9") > 0

    def test_compare_handles_v_prefix(self) -> None:
        """Strips 'v' prefix: v0.17.0 > 0.16.0."""
        from audio2text.services.update_service import UpdateService

        assert UpdateService.compare_versions("0.16.0", "v0.17.0") < 0

    def test_compare_two_digit_versions(self) -> None:
        """Handles versions like '1.0' → '1.0.0'."""
        from audio2text.services.update_service import UpdateService

        assert UpdateService.compare_versions("1.0", "1.1") < 0


class TestUpdateServiceCheckForUpdates:
    """Tests for check_for_updates using mocked HTTP."""

    @pytest.fixture
    def mock_releases_response(self) -> dict:
        """Mock GitHub Releases API response."""
        return {
            "tag_name": "v0.17.0",
            "name": "Release v0.17.0",
            "assets": [
                {
                    "name": "Audio2Text.exe",
                    "browser_download_url": "https://github.com/CENFARG/Audio2Text/releases/download/v0.17.0/Audio2Text.exe",
                    "size": 115_000_000,
                }
            ],
        }

    def test_check_for_updates_returns_latest_when_newer(
        self, mock_releases_response: dict
    ) -> None:
        """When GitHub has a newer version, returns update info."""
        from audio2text.services.update_service import UpdateService

        service = UpdateService(current_version="0.16.0")

        with patch.object(service, "_fetch_latest_release", return_value=mock_releases_response):
            result = service.check_for_updates()

        assert result is not None
        assert result["latest_version"] == "0.17.0"
        assert result["has_update"] is True
        assert result["download_url"].endswith("Audio2Text.exe")

    def test_check_for_updates_returns_none_when_same_version(
        self, mock_releases_response: dict
    ) -> None:
        """When current == latest, returns None (no update needed)."""
        from audio2text.services.update_service import UpdateService

        mock_releases_response["tag_name"] = "v0.16.0"
        service = UpdateService(current_version="0.16.0")

        with patch.object(service, "_fetch_latest_release", return_value=mock_releases_response):
            result = service.check_for_updates()

        assert result is None

    def test_check_for_updates_handles_network_error(self) -> None:
        """When GitHub is unreachable, returns None gracefully."""
        from audio2text.services.update_service import UpdateService

        service = UpdateService(current_version="0.16.0")

        with patch.object(service, "_fetch_latest_release", side_effect=OSError("Network error")):
            result = service.check_for_updates()

        assert result is None

    def test_check_for_updates_handles_invalid_response(self) -> None:
        """When GitHub returns unexpected data, returns None."""
        from audio2text.services.update_service import UpdateService

        service = UpdateService(current_version="0.16.0")

        with patch.object(service, "_fetch_latest_release", return_value={"no_tag": True}):
            result = service.check_for_updates()

        assert result is None


class TestUpdateServiceDownload:
    """Tests for download_update."""

    def test_download_update_calls_progress_callback(
        self, tmp_path: Path
    ) -> None:
        """download_update invokes the progress callback."""
        from audio2text.services.update_service import UpdateService

        service = UpdateService(current_version="0.16.0")
        dest = tmp_path / "update.exe"
        progress_calls: list[dict] = []

        def _progress_callback(downloaded: int, total: int) -> None:
            progress_calls.append({"downloaded": downloaded, "total": total})

        # Use mock response with iter_bytes (the method actually called)
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "1000"}
        # iter_bytes must return a generator yielding chunks
        mock_response.iter_bytes = lambda chunk_size: iter([b"x" * 500, b"y" * 500])
        mock_response.raise_for_status = lambda: None

        with patch("httpx.stream", return_value=MagicMock(__enter__=lambda _: mock_response, __exit__=lambda *_: None)):
            service.download_update(
                "https://example.com/update.exe",
                dest,
                progress_callback=_progress_callback,
            )

        # Progress callback was called
        assert len(progress_calls) == 2
        # Verify the file was created
        assert dest.exists()

    def test_download_update_without_callback_works(
        self, tmp_path: Path
    ) -> None:
        """Download works without a progress callback."""
        from audio2text.services.update_service import UpdateService

        service = UpdateService(current_version="0.16.0")
        dest = tmp_path / "update_no_cb.exe"

        mock_response = MagicMock()
        mock_response.headers = {"content-length": "500"}
        mock_response.iter_bytes = lambda chunk_size: iter([b"data"])
        mock_response.raise_for_status = lambda: None

        with patch("httpx.stream", return_value=MagicMock(__enter__=lambda _: mock_response, __exit__=lambda *_: None)):
            service.download_update("https://example.com/update.exe", dest)

        assert dest.exists()
