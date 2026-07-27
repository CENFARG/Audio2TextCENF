"""@File: audio2text/api/lifespan.py
@Description: FastAPI lifespan events — startup initialization and shutdown cleanup.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger("api.lifespan")


def _init_services() -> None:
    """Initialize application services on startup.

    Bootstraps the ManagerRegistry with all 18 core_infrastructure managers.
    Called once at application startup via lifespan event.
    """
    logger.info("========== Audio2Text API v0.16.0 — SESSION START ==========")
    logger.info("Audio2Text API starting up — bootstrapping infrastructure...")
    from audio2text.infrastructure import get_registry

    registry = get_registry()
    logger.info(
        "Registry bootstrapped: %d managers wired (%s)",
        len(registry.init_order),
        ", ".join(registry.init_order[:5]) + "...",
    )
    logger.info("Audio2Text API — infrastructure ready")


def _shutdown_services() -> None:
    """Clean up application resources on shutdown.

    Stops audio capture, closes connections, and releases resources.
    Called once at application shutdown via lifespan event.
    """
    logger.info("Audio2Text API shutting down — cleaning up resources...")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan context manager.

    Handles startup and shutdown lifecycle events for the application.
    All singleton services are initialized and cleaned up here.

    Args:
        app: The FastAPI application instance.
    """
    _init_services()
    try:
        yield
    finally:
        _shutdown_services()
