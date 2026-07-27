"""@File: audio2text/ui/theme/theme.py
@Description: Design tokens and theme builder for Audio2Text Flet frontend.
    Provides color palette, spacing scale, typography sizes, and a
    ``build_theme()`` function that produces a Flet-compatible theme dict.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any


class Colors:
    """Semantic color tokens for dark and light themes.

    All values are hex strings suitable for ``ft.colors.with_opacity()``
    or direct use in Flet controls.
    """

    # ── Primary ─────────────────────────────────────────────────────
    PRIMARY_DARK: str = "#2563EB"
    PRIMARY_LIGHT: str = "#3B82F6"

    # ── Surfaces ────────────────────────────────────────────────────
    SURFACE_DARK: str = "#1E293B"
    SURFACE_LIGHT: str = "#FFFFFF"
    BACKGROUND_DARK: str = "#0F172A"
    BACKGROUND_LIGHT: str = "#F8FAFC"

    # ── Text ────────────────────────────────────────────────────────
    TEXT_PRIMARY_DARK: str = "#F8FAFC"
    TEXT_SECONDARY_DARK: str = "#CBD5E1"
    TEXT_PRIMARY_LIGHT: str = "#1E293B"
    TEXT_SECONDARY_LIGHT: str = "#64748B"

    # ── Semantic ────────────────────────────────────────────────────
    ERROR: str = "#EF4444"
    SUCCESS: str = "#10B981"
    WARNING: str = "#F59E0B"
    INFO: str = "#3B82F6"

    # ── Recording LED ───────────────────────────────────────────────
    LED_RECORDING: str = "#FF0000"
    LED_PAUSED: str = "#F59E0B"
    LED_IDLE: str = "#6B7280"

    # ── Border ──────────────────────────────────────────────────────
    BORDER_DARK: str = "#334155"
    BORDER_LIGHT: str = "#E2E8F0"

    # ── Overlay ─────────────────────────────────────────────────────
    OVERLAY_BG: str = "rgba(0,0,0,0.7)"


class Spacing:
    """Consistent spacing scale (multiples of 4)."""

    XS: int = 4
    SM: int = 8
    MD: int = 16
    LG: int = 24
    XL: int = 32
    XXL: int = 48


class Typography:
    """Font size scale in logical pixels."""

    SIZE_XS: int = 10
    SIZE_SM: int = 12
    SIZE_MD: int = 14
    SIZE_LG: int = 18
    SIZE_XL: int = 24

    FONT_FAMILY: str = "Segoe UI"


def build_theme(dark_mode: bool = True) -> dict[str, Any]:
    """Build a Flet-compatible theme dictionary.

    Args:
        dark_mode: If ``True``, build a dark theme; otherwise light.

    Returns:
        A dict that can be unpacked into ``ft.app(theme=..., dark_theme=...)``
        or passed to ``ft.Page.theme`` / ``ft.Page.dark_theme``.
    """
    color_seed = Colors.PRIMARY_DARK if dark_mode else Colors.PRIMARY_LIGHT

    theme: dict[str, Any] = {
        "color_scheme_seed": color_seed,
        "visual_density": "comfortable",
        "font_family": Typography.FONT_FAMILY,
    }

    if dark_mode:
        theme["color_scheme"] = {
            "primary": Colors.PRIMARY_DARK,
            "surface": Colors.SURFACE_DARK,
            "background": Colors.BACKGROUND_DARK,
            "error": Colors.ERROR,
            "on_primary": Colors.TEXT_PRIMARY_DARK,
            "on_surface": Colors.TEXT_PRIMARY_DARK,
            "on_background": Colors.TEXT_PRIMARY_DARK,
        }
    else:
        theme["color_scheme"] = {
            "primary": Colors.PRIMARY_LIGHT,
            "surface": Colors.SURFACE_LIGHT,
            "background": Colors.BACKGROUND_LIGHT,
            "error": Colors.ERROR,
            "on_primary": "#FFFFFF",
            "on_surface": Colors.TEXT_PRIMARY_LIGHT,
            "on_background": Colors.TEXT_PRIMARY_LIGHT,
        }

    return theme
