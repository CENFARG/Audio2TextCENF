"""@File: audio2text/api/schemas/common.py
@Description: Shared Pydantic models — ErrorResponse, SuccessResponse, PaginationParams.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response body.

    All API errors return this shape with a machine-readable code,
    a human-readable message, and optional details.

    Attributes:
        code: Machine-readable error code (e.g., "TRANS_001").
        message: Human-readable error description.
        details: Optional structured details about the error.
    """

    code: str
    message: str
    details: dict[str, Any] | None = None


class SuccessResponse(BaseModel):
    """Generic success response wrapper.

    Attributes:
        data: The response payload (any JSON-serializable value).
        message: Optional human-readable success message (default "OK").
    """

    data: Any
    message: str = "OK"


class PaginationParams(BaseModel):
    """Standard pagination query parameters.

    Attributes:
        limit: Maximum number of items per page (1–500, default 50).
        offset: Number of items to skip (default 0).
    """

    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
