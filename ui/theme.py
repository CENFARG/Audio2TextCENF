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

import json
from pathlib import Path

# ── Bundled themes (JSON, loaded via load_theme/apply_theme) ────────
THEMES_DIR = Path(__file__).resolve().parent.parent / "themes"
_REQUIRED_KEYS = {"name", "colors", "surfaces", "typography", "radii"}

# ── Prototype CSS custom properties (exact) ─────────────────────────
COLORS: dict[str, str] = {
    "bg": "#080D18",  # --bg
    "surface": "#121D30",  # --surface (GR amendment L10: owner token)
    "text": "#F2F7FF",  # --text
    "muted": "#9AAAC2",  # --muted
    "line": "#1D2635",  # --line rgba(160,190,230,.14) composited over bg
    "cyan": "#56E5E3",  # --cyan (primary accent)
    "blue": "#6B8CFF",  # --blue
    "violet": "#AD82FF",  # --violet
    "green": "#77E4B1",  # --green
    # Status tokens (no prototype analogue; sanctioned additions)
    "success": "#77E4B1",
    "warning": "#FFB96B",  # amber from the prototype's warning chips
    "error": "#F87171",
    # Derived interaction tokens (computed states, not prototype values)
    "primary": "#56E5E3",  # alias of cyan: the interactive accent
    "primary_hover": "#3FC4C2",  # cyan darkened ~8%
    "on_primary": "#071018",  # dark ink for cyan fills (S8: white on cyan fails contrast)
    "success_hover": "#5FCF9B",  # green darkened ~8%
    "error_hover": "#E05555",  # red darkened ~8%
}

# ── .app-window gradient endpoints, flattened for CTk ───────────────
SURFACES: dict[str, str] = {
    # GR amendment L10: owner picked #121d30 / #1c3447 from Flor's web palette
    "lo": "#121D30",  # cards / panel backgrounds
    "hi": "#1C3447",  # raised elements (chips, hover fills)
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


def uppercase_label(text: str) -> str:
    """Format a capture/transcript label like the mockup (uppercase).

    The prototype renders section labels as tracked uppercase text
    ("CAPTURANDO AUDIO", "TRANSCRIPCIÓN EN VIVO"); Tk cannot apply
    letter-spacing, so the label text itself is uppercased.

    Args:
        text: Human-readable label text.

    Returns:
        The stripped, uppercased label text.
    """
    return text.strip().upper()


# Alias keys kept in sync with their canonical token (legacy facade support).
ALIASES: dict[str, str] = {
    "background": "bg",
    "text_primary": "text",
    "text_secondary": "muted",
}


def _sync_aliases() -> None:
    """Refresh alias keys from their canonical tokens (post-apply)."""
    for alias, canonical in ALIASES.items():
        if canonical in COLORS:
            COLORS[alias] = COLORS[canonical]


_sync_aliases()


def list_themes() -> list[str]:
    """List the bundled theme names (``themes/*.json`` stems, sorted)."""
    return sorted(p.stem for p in THEMES_DIR.glob("*.json"))


def load_theme(name: str) -> dict:
    """Load and validate one bundled theme.

    Args:
        name: Theme stem (a ``themes/<name>.json`` file).

    Returns:
        The parsed theme dict with ``name``, ``colors``, ``surfaces``,
        ``typography`` and ``radii`` keys.

    Raises:
        FileNotFoundError: If no ``themes/<name>.json`` exists.
        ValueError: If the schema is missing required keys.
    """
    path = THEMES_DIR / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Tema '{name}' no encontrado en {THEMES_DIR} (disponibles: {', '.join(list_themes())})"
        )
    try:
        data: dict = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Tema '{name}' tiene JSON inválido: {exc}") from exc
    missing = _REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(
            f"Tema '{name}' incompleto: faltan {sorted(missing)} (p.ej. colors)"
        )
    return data


def apply_theme(data: dict) -> None:
    """Apply a theme to the module token dicts IN PLACE.

    Importers holding references to ``COLORS``/``SURFACES``/``TYPOGRAPHY``/
    ``RADII`` (including the ``DesignSystem`` facade) see the new values
    without re-importing. Unknown tokens are rejected so typos fail loud.

    Args:
        data: A schema-valid theme (see :func:`load_theme`).

    Raises:
        ValueError: On unknown color/surface keys.
    """
    unknown = set(data["colors"]) - set(COLORS)
    if unknown:
        raise ValueError(f"Tokens desconocidos en el tema: {sorted(unknown)}")
    unknown_surf = set(data["surfaces"]) - set(SURFACES)
    if unknown_surf:
        raise ValueError(f"Superficies desconocidas en el tema: {sorted(unknown_surf)}")

    COLORS.update(data["colors"])
    SURFACES.update(data["surfaces"])
    RADII.update(data["radii"])

    family = data["typography"]["family"]
    sizes: dict[str, tuple[int, str]] = {}
    for key, spec in data["typography"].items():
        if key == "family":
            continue
        size, weight = spec
        sizes[key] = (int(size), str(weight))
    rebuilt = _rebuild_typography(family, sizes)
    TYPOGRAPHY.clear()
    TYPOGRAPHY.update(rebuilt)
    _sync_aliases()


def _rebuild_typography(
    family: str, sizes: dict[str, tuple[int, str]]
) -> dict[str, tuple[str, int, str]]:
    """Build the full typography map (base keys + legacy derived keys).

    The JSON theme carries the five base specs; legacy call sites also
    read heading_large/heading_medium/body_bold/body_medium/body_small/
    link, which are derived here so a theme swap never drops them.
    """
    base = {key: (family, size, weight) for key, (size, weight) in sizes.items()}
    derived = {
        "heading_large": ("Segoe UI Variable Display", sizes["heading"][0] + 2, "bold"),
        "heading_medium": base["heading"],
        "body_bold": (family, sizes["body"][0] - 1, "bold"),
        "body_medium": base["body"],
        "body_small": base["small"],
        "link": (family, sizes["small"][0], "underline"),
    }
    return {**base, **derived}


# ── Corner radii from the prototype (CTk corner_radius values) ──────
RADII: dict[str, int] = {
    "card": 19,  # .app-window
    "chip": 13,
    "pill": 999,  # fully rounded status pills
}


class DesignSystem:
    """Legacy facade from the v0.17 line — LIVE views over theme tokens.

    Existing views keep their ``DesignSystem.COLORS[...]`` call sites;
    the attributes ARE the module dicts (not copies), so
    :func:`apply_theme` swaps propagate to every call site instantly.
    Legacy keys (background, text_primary, text_secondary,
    heading_medium, body_bold, ...) are kept in sync inside the module
    dicts via the alias map and ``_rebuild_typography``.
    """

    COLORS = COLORS
    TYPOGRAPHY = TYPOGRAPHY
    RADII = RADII
    SURFACES = SURFACES
