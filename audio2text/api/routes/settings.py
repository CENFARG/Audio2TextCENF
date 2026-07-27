"""@File: audio2text/api/routes/settings.py
@Description: Settings endpoints — GET/PUT /api/v1/settings.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from fastapi import APIRouter

from audio2text import __version__
from audio2text.api.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/v1", tags=["settings"])


# In-memory config store (to be replaced with ConfigManager integration)
_current_config: dict[str, object] = {
    "version": __version__,
    "providers": {"primary": "groq"},
    "api": {"port": 8765, "host": "127.0.0.1"},
    "localization": {"language": "es_ES"},
    "audio": {"sample_rate_hz": 16000, "channels": 1},
}


@router.get("/settings", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    """Return the current application configuration.

    Secrets are masked — API keys are never returned.

    Returns:
        A SettingsResponse with the full configuration dict.
    """
    return SettingsResponse(config=dict(_current_config))


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate) -> SettingsResponse:
    """Partially update the application configuration.

    Merges the provided config dict into the current configuration.
    Only provided keys are updated; missing keys remain unchanged.

    Args:
        update: A SettingsUpdate body with the keys to change.

    Returns:
        A SettingsResponse with the merged configuration.
    """
    global _current_config

    def _deep_merge(base: dict[str, object], overlay: dict[str, object]) -> dict[str, object]:
        """Recursively merge overlay into base."""
        result = dict(base)
        for key, value in overlay.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = _deep_merge(
                    result[key],  # type: ignore[arg-type]
                    value,  # type: ignore[arg-type]
                )
            else:
                result[key] = value
        return result

    _current_config = _deep_merge(_current_config, update.config)
    return SettingsResponse(config=dict(_current_config))
