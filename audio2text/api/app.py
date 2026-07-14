"""@File: audio2text/api/app.py
@Description: FastAPI application factory — creates and configures the Audio2Text REST API.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI

from audio2text.api.lifespan import lifespan
from audio2text.api.middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    configure_cors,
)
from cenf_core.logging.manager import LoggerManager
from cenf_core.logging.profiles import LogProfile

# ── Logging — API backend ──────────────────────────────────────────────────
# Configured ONCE at module import so all api.* loggers inherit DEBUG level.
# Attaches console handler (DEVELOPMENT profile) + logs/api.log RotatingFileHandler.

_API_LOG_DIR = Path("logs")

_api_logger_manager = LoggerManager(
    profile=LogProfile.DEVELOPMENT,
    log_dir=_API_LOG_DIR,
)

# Suppress noisy third-party libraries in API context
_api_logger_manager.suppress_library("httpx", logging.INFO)
_api_logger_manager.suppress_library("httpcore.connection", logging.INFO)
_api_logger_manager.suppress_library("httpcore.http11", logging.INFO)
_api_logger_manager.suppress_library("asyncio", logging.INFO)
_api_logger_manager.suppress_library("urllib3", logging.INFO)

# Add dedicated api.log RotatingFileHandler (in addition to cenf_dev.log from
# the LoggerManager profile).  This is the canonical API log file.
_API_LOG_DIR.mkdir(parents=True, exist_ok=True)
_api_log_path = _API_LOG_DIR / "api.log"

# Session separator — raw write before the handler opens, so it is the first
# thing in the file for this run.
_api_separator = (
    f"========== Audio2Text API v0.16.0 — SESSION START "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==========\n"
)
with _api_log_path.open("a", encoding="utf-8") as _f:
    _f.write(_api_separator)

_api_file_handler = RotatingFileHandler(
    str(_api_log_path),
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=3,
    encoding="utf-8",
    delay=False,
)
_api_file_handler.setLevel(logging.DEBUG)
_api_file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s:%(lineno)d: %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
)
logging.getLogger().addHandler(_api_file_handler)

_api_logger = _api_logger_manager.get_logger("api.app")
_api_logger.info("API logging configured — DEVELOPMENT profile (DEBUG), logs/api.log active")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Sets up:
    - Application metadata (title, version, docs).
    - Lifespan events (startup/shutdown).
    - CORS middleware for localhost origins.
    - Error handling middleware for structured error responses.
    - Request/response logging middleware.
    - Route registrations (added as routes are implemented).

    Returns:
        A fully configured FastAPI application instance ready to serve.
    """
    app = FastAPI(
        title="Audio2Text CENF",
        version="0.16.0",
        description="REST API for real-time audio transcription using AI.",
        lifespan=lifespan,
    )

    # --- Middleware (order matters: last added = outermost) ---
    configure_cors(app)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)

    # --- Register all API routes ---
    from audio2text.api.routes.context_blocks import router as context_blocks_router
    from audio2text.api.routes.enhance import router as enhance_router
    from audio2text.api.routes.health import router as health_router
    from audio2text.api.routes.metadata import router as metadata_router
    from audio2text.api.routes.settings import router as settings_router
    from audio2text.api.routes.transcribe import router as transcribe_router
    from audio2text.api.routes.transcribe_stream import router as transcribe_stream_router
    from audio2text.api.routes.transcriptions import router as transcriptions_router
    from audio2text.api.routes.update import router as update_router
    from audio2text.api.routes.vocabulary import router as vocabulary_router

    app.include_router(health_router)
    app.include_router(transcribe_router)
    app.include_router(transcribe_stream_router)
    app.include_router(transcriptions_router)
    app.include_router(enhance_router)
    app.include_router(context_blocks_router)
    app.include_router(vocabulary_router)
    app.include_router(metadata_router)
    app.include_router(settings_router)
    app.include_router(update_router)

    return app
