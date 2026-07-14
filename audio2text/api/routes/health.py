"""@File: audio2text/api/routes/health.py
@Description: Health check endpoint — GET /api/v1/health.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from fastapi import APIRouter

from audio2text import __version__

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, object]:
    """Return the current health status of the API.

    Returns:
        A dict with status, version, provider availability, and services status.
    """
    return {
        "status": "ok",
        "version": __version__,
        "provider_available": True,
        "services_status": {
            "api": "running",
            "metadata": "available",
            "vocabulary": "available",
        },
    }
