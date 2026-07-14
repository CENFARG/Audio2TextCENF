"""@File: audio2text/api/middleware.py
@Description: FastAPI middleware — error handling, request/response logging, CORS configuration.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


def configure_cors(app: FastAPI, allowed_origins: list[str] | None = None) -> None:
    """Add CORS middleware to the FastAPI application.

    Args:
        app: The FastAPI application instance.
        allowed_origins: List of allowed origin regex patterns.
                         Defaults to localhost patterns and testserver.
    """
    if allowed_origins is None:
        # Use a single regex string that matches localhost, 127.0.0.1, and testserver
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|testserver)(:\d+)?$",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return structured error responses.

    Converts Python exceptions into the standard ``{code, message, details?}``
    JSON body with appropriate HTTP status codes.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process a request, catching any unhandled exceptions.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or endpoint handler.

        Returns:
            The HTTP response (either normal or error).
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.exception("Unhandled exception in request %s %s", request.method, request.url)
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": {"error_type": type(exc).__name__},
                },
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log incoming requests and outgoing responses with timing.

    Records method, path, status code, and elapsed time for every request.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Log request/response timing.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or endpoint handler.

        Returns:
            The HTTP response from the downstream handler.
        """
        start_time = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
