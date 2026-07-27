"""@File: audio2text/services/update_service.py
@Description: UpdateService — in-app version check via GitHub Releases API.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GITHUB_API_RELEASES: str = (
    "https://api.github.com/repos/CENFARG/Audio2TextCENF/releases/latest"
)


class UpdateService:
    """Checks for app updates using the GitHub Releases API.

    Pure Python — no batch scripts, no shell execution needed.
    Compares semantic versions and downloads the new .exe when available.

    Attributes:
        current_version: The currently running app version (e.g. "0.16.0").
        releases_url: GitHub API releases endpoint.
    """

    def __init__(
        self,
        current_version: str = "0.16.0",
        releases_url: str = _GITHUB_API_RELEASES,
    ) -> None:
        """Initialize the update service.

        Args:
            current_version: The running app's version string.
            releases_url: The GitHub API URL to fetch latest release info.
        """
        self.current_version: str = current_version
        self.releases_url: str = releases_url

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_for_updates(self) -> dict[str, Any] | None:
        """Check if a newer version is available on GitHub Releases.

        Returns:
            A dict with ``latest_version``, ``has_update``, ``download_url``,
            ``release_name``, and ``size_bytes`` if an update is available.
            None if current is up-to-date or the check failed.
        """
        try:
            release_data = self._fetch_latest_release()
        except Exception as exc:
            logger.warning("Update check failed: %s", exc)
            return None

        latest_tag: str = release_data.get("tag_name", "")
        if not latest_tag:
            logger.warning("Release data has no tag_name: %s", release_data)
            return None

        latest_version = _strip_v_prefix(latest_tag)

        if self.compare_versions(self.current_version, latest_version) >= 0:
            # Current is same or newer
            logger.info(
                "No update available. Current: %s, Latest: %s",
                self.current_version,
                latest_version,
            )
            return None

        # Find the .exe asset
        download_url: str = ""
        size_bytes: int = 0
        for asset in release_data.get("assets", []):
            name = asset.get("name", "")
            if name.lower().endswith(".exe"):
                download_url = asset.get("browser_download_url", "")
                size_bytes = asset.get("size", 0)
                break

        return {
            "latest_version": latest_version,
            "has_update": True,
            "download_url": download_url,
            "release_name": release_data.get("name", latest_tag),
            "size_bytes": size_bytes,
        }

    @staticmethod
    def compare_versions(current: str, latest: str) -> int:
        """Compare two semantic version strings.

        Args:
            current: The currently installed version.
            latest: The latest available version.

        Returns:
            -1 if latest is newer, 0 if equal, 1 if current is newer.
        """
        c_parts = _parse_version(current)
        l_parts = _parse_version(latest)

        for cv, lv in zip(c_parts, l_parts):
            if cv < lv:
                return -1
            if cv > lv:
                return 1
        return 0

    def download_update(
        self,
        url: str,
        dest: Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """Download the update .exe from the given URL.

        Args:
            url: Direct download URL for the .exe.
            dest: Destination file path.
            progress_callback: Optional callback(downloaded_bytes, total_bytes).
        """
        with httpx.stream("GET", url, follow_redirects=True, timeout=600.0) as response:
            response.raise_for_status()

            total = int(response.headers.get("content-length", "0"))
            downloaded = 0

            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(str(dest), "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

        logger.info("Downloaded update to %s (%d bytes)", dest, downloaded)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fetch_latest_release(self) -> dict[str, Any]:
        """Fetch the latest release data from GitHub API.

        Returns:
            Parsed JSON response dict.

        Raises:
            OSError: On network failure.
            ValueError: On invalid JSON.
        """
        response = httpx.get(
            self.releases_url,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------


def _strip_v_prefix(version: str) -> str:
    """Remove a leading 'v' or 'V' from a version string."""
    return version.lstrip("vV")


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse a semantic version string into a tuple of integers.

    Handles formats: "1.2.3", "v1.2.3", "1.2", "1".

    Args:
        version: Version string.

    Returns:
        Tuple of integer components, padded to at least 3 (e.g. (1, 2, 3)).
    """
    cleaned = _strip_v_prefix(version).strip()
    parts = cleaned.split(".")
    # Parse each part as int, defaulting to 0 for non-numeric
    nums: list[int] = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            nums.append(0)
    # Pad to at least 3 components for proper comparison
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)
