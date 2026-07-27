"""@File: audio2text/api/routes/update.py
@Description: Update check endpoint — GET /api/v1/update/check.
    Delegates to UpdateService for GitHub Releases comparison.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from audio2text import __version__
from audio2text.services.update_service import UpdateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["update"])


@router.get("/update/check")
async def check_update() -> dict[str, object]:
    """Check for application updates via GitHub Releases API.

    Returns current version, whether an update is available, and
    the latest version info.

    Returns:
        A dict with current_version, has_update, and optional latest_version.
    """
    svc = UpdateService(current_version=__version__)
    try:
        result = svc.check_for_updates()
    except Exception as exc:
        logger.warning("Update check failed: %s", exc)
        return {
            "current_version": __version__,
            "has_update": False,
            "error": str(exc),
        }

    if result is None:
        return {
            "current_version": __version__,
            "has_update": False,
        }

    return {
        "current_version": __version__,
        "has_update": True,
        "latest_version": result.get("latest_version", ""),
        "release_name": result.get("release_name", ""),
        "download_url": result.get("download_url", ""),
        "size_bytes": result.get("size_bytes", 0),
    }
