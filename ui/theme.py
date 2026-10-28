"""Design tokens for the Audio2Text desktop UI (v0.18.0 restyling, R1).

Single source of truth mirrored from the approved landing prototype
(docs/design/landing_prototipo.html, CSS custom properties). Values are
EXACT so they transfer 1:1 to the React Native design system later;
never hardcode hex colors in views — import them from here.

Status colors (success/warning/error) have no landing analogue and live
here as the only sanctioned additions (never inline in views).

Author: CENF development team.
License: Apache 2.0.
"""

from __future__ import annotations

# ── Prototype CSS custom properties (exact) ─────────────────────────
COLORS: dict[str, str] = {
    "bg": "#080D18",        # --bg
    "surface": "#101827",   # --surface
    "text": "#F2F7FF",      # --text
    "muted": "#9AAAC2",     # --muted
    "line": "#1D2635",      # --line rgba(160,190,230,.14) composited over bg
    "cyan": "#56E5E3",      # --cyan (primary accent)
    "blue": "#6B8CFF",      # --blue
    "violet": "#AD82FF",    # --violet
    "green": "#77E4B1",     # --green
    # Status tokens (no prototype analogue; sanctioned additions)
    "success": "#77E4B1",
    "warning": "#FFB96B",   # amber from the prototype's warning chips
    "error": "#F87171",
    # Derived interaction tokens (computed states, not prototype values)
    "primary": "#56E5E3",        # alias of cyan: the interactive accent
    "primary_hover": "#3FC4C2",  # cyan darkened ~8%
    "success_hover": "#5FCF9B",  # green darkened ~8%
    "error_hover": "#E05555",    # red darkened ~8%
}

# ── .app-window gradient endpoints, flattened for CTk ───────────────
SURFACES: dict[str, str] = {
    "hi": "#162237",  # rgba(22,34,55,.96)
    "lo": "#0C1423",  # rgba(12,20,35,.96)
}

# ── Typography hierarchy (Segoe UI Variable family, Tk tuples) ──────
TYPOGRAPHY: dict[str, tuple[str, int, str]] = {
    "heading": ("Segoe UI Variable Display", 20, "bold"),
    "subheading": ("Segoe UI Variable Text", 16, "bold"),
    "body": ("Segoe UI Variable Text", 14, "normal"),
    "small": ("Segoe UI Variable Text", 12, "normal"),
    "label": ("Segoe UI Variable Text", 11, "bold"),  # uppercase capture labels
}


def composite_rgba(rgba: tuple[int, int, int, float], bg_hex: str) -> str:
    """Flatten an RGBA color over a solid background into solid hex.

    CTk borders/fills accept solid colors only, so prototype rgba()
    borders are pre-composited over ``--bg`` with standard alpha
    blending: ``result = fg * a + bg * (1 - a)``.

    Args:
        rgba: ``(r, g, b, a)`` with channels 0-255 and alpha 0.0-1.0.
        bg_hex: Opaque background hex (``#RRGGBB``).

    Returns:
        The composited color as lowercase ``#rrggbb`` (CSS convention).
    """
    r, g, b, a = rgba
    bg = bg_hex.lstrip("#")
    br, bg_, bb = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
    mixed = (
        round(r * a + br * (1 - a)),
        round(g * a + bg_ * (1 - a)),
        round(b * a + bb * (1 - a)),
    )
    return "#{:02x}{:02x}{:02x}".format(*mixed)


# ── Corner radii from the prototype (CTk corner_radius values) ──────
RADII: dict[str, int] = {
    "card": 19,   # .app-window
    "chip": 13,
    "pill": 999,  # fully rounded status pills
}


class DesignSystem:
    """Legacy facade from the v0.17 line, resolving to theme tokens.

    Existing views keep their ``DesignSystem.COLORS[...]`` call sites
    while R2 migrates them to the token dicts directly; values now come
    from the prototype palette instead of the retired one.
    """

    COLORS: dict[str, str] = {
        **COLORS,
        "background": COLORS["bg"],
        "text_primary": COLORS["text"],
        "text_secondary": COLORS["muted"],
    }
    TYPOGRAPHY: dict[str, tuple[str, int, str]] = {
        **TYPOGRAPHY,
        "heading_large": ("Segoe UI Variable Display", 22, "bold"),
        "heading_medium": TYPOGRAPHY["heading"],
        "body_bold": ("Segoe UI Variable Text", 13, "bold"),
        "body_medium": TYPOGRAPHY["body"],
        "body_small": TYPOGRAPHY["small"],
        "link": ("Segoe UI Variable Text", 12, "underline"),
    }
