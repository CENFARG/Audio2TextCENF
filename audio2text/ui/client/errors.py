"""@File: audio2text/ui/client/errors.py
@Description: Shared error types for the UI client layer.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class APIError(Exception):
    """Structured API error returned from the backend.

    Attributes:
        status_code: HTTP status code.
        message: Human-readable error message.
        code: Optional machine-readable error code (e.g., "TRANS_001").
        details: Optional structured details dictionary.
    """

    status_code: int
    message: str
    code: str | None = None
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        base = f"[{self.status_code}] {self.message}"
        if self.code:
            base = f"{self.code} {base}"
        return base
