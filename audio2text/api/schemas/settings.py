"""@File: audio2text/api/schemas/settings.py
@Description: Pydantic schemas for settings retrieval and partial updates.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SettingsResponse(BaseModel):
    """Full application configuration response.

    Attributes:
        config: The complete application configuration as a nested dict.
                Secrets are masked (never exposed via API).
    """

    config: dict[str, Any]


class SettingsUpdate(BaseModel):
    """Partial settings update request.

    Attributes:
        config: A dict of keys to update. Only provided keys are changed;
                missing keys are left as-is. Supports nested updates via
                dot-separated or nested-dict paths.
    """

    config: dict[str, Any]
