"""@File: audio2text/api/routes/settings.py
@Description: Settings endpoints — GET/PUT /api/v1/settings.
@Version: 0.17.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import asyncio
import copy

from fastapi import APIRouter

from audio2text.api.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/v1", tags=["settings"])


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


def _get_config_dict(config_mgr) -> dict[str, object]:
    """Return a deepcopy of the underlying config dict."""
    if hasattr(config_mgr, "_config") and isinstance(config_mgr._config, dict):  # type: ignore[attr-defined]
        return copy.deepcopy(config_mgr._config)  # type: ignore[attr-defined]
    # fallback: assemble known sections
    cfg: dict[str, object] = {}
    for ns in ("providers", "api", "localization", "audio", "app"):
        try:
            sec = config_mgr.get_section(ns)
            if sec:
                cfg[ns] = sec
        except Exception:
            pass
    return cfg


def _set_config_dotted(config_mgr, dotted_key: str, value: object) -> None:
    """Set a dotted key on the config manager (set_value → _config fallback)."""
    if hasattr(config_mgr, "set_value"):
        try:
            config_mgr.set_value(dotted_key, value)  # type: ignore[attr-defined]
            return
        except Exception:
            pass
    if hasattr(config_mgr, "set"):
        try:
            config_mgr.set(dotted_key, value)  # type: ignore[attr-defined]
            return
        except Exception:
            pass
    # manual dict mutation fallback
    if hasattr(config_mgr, "_config") and isinstance(config_mgr._config, dict):  # type: ignore[attr-defined]
        parts = dotted_key.split(".")
        cur = config_mgr._config  # type: ignore[attr-defined]
        for part in parts[:-1]:
            if part not in cur or not isinstance(cur[part], dict):
                cur[part] = {}
            cur = cur[part]
        cur[parts[-1]] = value


def _flatten_to_dotted(data: dict[str, object], prefix: str = ""):
    """Yield (dotted_key, value) for leaf nodes."""
    for k, v in data.items():
        new_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from _flatten_to_dotted(v, new_key)  # type: ignore[arg-type]
        else:
            yield new_key, v


@router.get("/settings", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    """Return the current application configuration.

    Secrets are masked — API keys are never returned.

    Returns:
        A SettingsResponse with the full configuration dict.
    """
    from audio2text.infrastructure import get_registry

    config_mgr = get_registry().get_config()
    sec_mgr = get_registry().get_secrets()

    config_dict: dict[str, object] = _get_config_dict(config_mgr)

    # Ensure providers.primary is present via get_string
    try:
        primary = config_mgr.get_string("providers.primary", "groq")
        if "providers" not in config_dict or not isinstance(config_dict.get("providers"), dict):
            config_dict["providers"] = {"primary": primary}
        elif "primary" not in config_dict["providers"]:  # type: ignore[operator]
            config_dict["providers"]["primary"] = primary  # type: ignore[index]
        else:
            # ensure consistency with registry
            config_dict["providers"]["primary"] = primary  # type: ignore[index]
    except Exception:
        if "providers" not in config_dict:
            config_dict["providers"] = {"primary": "groq"}

    # Mask secrets if they exist (***)
    for key in ("groq_api_key", "nvidia_api_key"):
        try:
            val = await sec_mgr.get_secret(key)
            if val:
                config_dict[key] = "***"
                if "secrets" not in config_dict or not isinstance(config_dict["secrets"], dict):
                    config_dict["secrets"] = {}
                config_dict["secrets"][key] = "***"  # type: ignore[index]
        except Exception:
            pass

    return SettingsResponse(config=dict(config_dict))


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate) -> SettingsResponse:
    """Partially update the application configuration.

    Merges the provided config dict into the current configuration.
    Only provided keys are updated; missing keys remain unchanged.
    Supports both legacy flat secrets and nested secrets shape.

    Args:
        update: A SettingsUpdate body with the keys to change.

    Returns:
        A SettingsResponse with the merged configuration.
    """
    from audio2text.infrastructure import get_registry

    config_mgr = get_registry().get_config()
    sec_mgr = get_registry().get_secrets()

    overlay: dict[str, object] = dict(update.config) if update.config else {}

    # Normalize secrets: support both {secrets:{...}} and flat groq_api_key
    secrets_to_set: dict[str, str] = {}

    # Nested secrets dict
    if "secrets" in overlay and isinstance(overlay["secrets"], dict):
        nested = overlay.pop("secrets")  # type: ignore[assignment]
        for k, v in list(nested.items()):  # type: ignore[attr-defined]
            if v is None:
                continue
            s = str(v).strip() if isinstance(v, str) else str(v)
            if not s or s in ("***", "••••"):
                continue
            secrets_to_set[str(k)] = s

    # Legacy flat keys
    for flat_key in ("groq_api_key", "nvidia_api_key"):
        if flat_key in overlay:
            v = overlay.pop(flat_key)
            if v is None:
                continue
            s = str(v).strip() if isinstance(v, str) else str(v)
            if not s or s in ("***", "••••"):
                continue
            secrets_to_set[flat_key] = s

    # Also handle legacy flat inside providers? no-op

    # Persist secrets via SecretManager (sync set_secret or async rotate_secret)
    for k, v in secrets_to_set.items():
        persisted = False
        # Try sync set_secret (test helper)
        if hasattr(sec_mgr, "set_secret"):
            try:
                res = sec_mgr.set_secret(k, v)  # type: ignore[attr-defined]
                if asyncio.iscoroutine(res):
                    await res
                persisted = True
            except Exception:
                pass
        # Fallback to rotate_secret (protocol)
        if not persisted and hasattr(sec_mgr, "rotate_secret"):
            try:
                await sec_mgr.rotate_secret(k, v)
                persisted = True
            except Exception:
                pass
        # Final fallback: try set_secret again without await check
        if not persisted:
            try:
                sec_mgr.set_secret(k, v)  # type: ignore[attr-defined]
            except Exception:
                pass
        # Invalidate cache if possible
        try:
            if hasattr(sec_mgr, "invalidate_cache"):
                sec_mgr.invalidate_cache(k)
        except Exception:
            pass

    # Deep merge / dotted set only for real config keys
    if overlay:
        # Use set_value per dotted leaf to respect adapter validation
        has_set_value = hasattr(config_mgr, "set_value") or hasattr(config_mgr, "set")
        if has_set_value or not hasattr(config_mgr, "_config"):
            for dotted, val in _flatten_to_dotted(overlay):
                _set_config_dotted(config_mgr, dotted, val)
        else:
            # Manual deep merge on internal dict
            merged = _deep_merge(config_mgr._config, overlay)  # type: ignore[attr-defined]
            config_mgr._config.clear()  # type: ignore[attr-defined]
            config_mgr._config.update(merged)  # type: ignore[attr-defined]

    # Build response dict (masked)
    config_dict: dict[str, object] = _get_config_dict(config_mgr)

    try:
        primary = config_mgr.get_string("providers.primary", None)  # type: ignore[assignment]
        if primary:
            if "providers" not in config_dict or not isinstance(config_dict.get("providers"), dict):
                config_dict["providers"] = {"primary": primary}
            else:
                config_dict["providers"]["primary"] = primary  # type: ignore[index]
    except Exception:
        pass

    # Mask secrets for response (never return clear text)
    for key in ("groq_api_key", "nvidia_api_key"):
        try:
            val = await sec_mgr.get_secret(key)
            if val:
                config_dict[key] = "***"
                if "secrets" not in config_dict or not isinstance(config_dict["secrets"], dict):
                    config_dict["secrets"] = {}
                config_dict["secrets"][key] = "***"  # type: ignore[index]
        except Exception:
            pass

    # Ensure no clear-text secrets leaked via config merge
    for k in list(config_dict.keys()):
        if k in ("groq_api_key", "nvidia_api_key") and config_dict[k] not in ("***",):
            # If a real secret was merged as config, mask it and also persist as secret
            # (but we already handled secrets extraction, so just mask)
            config_dict[k] = "***"
    if "secrets" in config_dict and isinstance(config_dict["secrets"], dict):
        for k, v in list(config_dict["secrets"].items()):  # type: ignore[attr-defined]
            if k in ("groq_api_key", "nvidia_api_key") and v not in ("***",):
                config_dict["secrets"][k] = "***"  # type: ignore[index]

    return SettingsResponse(config=dict(config_dict))
