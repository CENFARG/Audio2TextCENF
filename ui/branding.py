"""Brand asset resolution and tray-image rendering (S3 unification).

The tray icon used to be a drawn accent circle (the "blue square" users
reported), visually different from the brand logo shown in the main tab.
Every surface now derives from ``assets/logos/logo.png``: this module
resolves the logo path across dev/frozen layouts and renders the tray
image from it, keeping the drawn circle only as an explicit fallback.

Author: CENF development team.
License: Apache 2.0.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

#: Square size (px) of the tray image rendered by :func:`build_tray_image`.
TRAY_ICON_SIZE = 64

#: Resampling filter used for logo downscaling.
_RESAMPLE = Image.Resampling.LANCZOS


def resolve_logo_path(candidates: Iterable[Path]) -> Path | None:
    """Return the first existing logo candidate path, or ``None``.

    Args:
        candidates: Path candidates (frozen bundle root, packaged assets,
            working-directory copies) in priority order.

    Returns:
        The first candidate that exists on disk, else ``None``.
    """
    for raw in candidates:
        path = Path(raw)
        if path.is_file():
            return path
    return None


def logo_candidates(base_dir: Path, meipass: str | None = None) -> list[Path]:
    """Build the candidate list for the runtime layout.

    Args:
        base_dir: Repository/package root holding ``assets/logos/logo.png``.
        meipass: PyInstaller ``sys._MEIPASS`` when frozen, else ``None``.

    Returns:
        Ordered candidates: frozen bundle root first, then the packaged
        assets copy, then the working-directory copy.
    """
    entries: list[Path] = []
    if meipass:
        entries.append(Path(meipass) / "logo.png")
    entries.append(base_dir / "assets" / "logos" / "logo.png")
    entries.append(Path("logo.png"))
    return entries


def build_tray_image(
    logo_path: Path | None,
    fallback_bg: str = "#0F172A",
    fallback_fg: str = "#2563EB",
) -> Image.Image:
    """Render the tray image from the brand logo, falling back to a circle.

    Args:
        logo_path: Resolved logo file, or ``None`` for the drawn fallback.
        fallback_bg: Fallback background color (design system background).
        fallback_fg: Fallback accent color for the drawn circle.

    Returns:
        A square RGBA :data:`TRAY_ICON_SIZE` image ready for ``pystray.Icon``.
        Never raises: a broken logo degrades to the fallback circle.
    """
    if logo_path is not None:
        try:
            with Image.open(logo_path) as raw:
                logo = raw.convert("RGBA")
            logo.thumbnail((TRAY_ICON_SIZE, TRAY_ICON_SIZE), _RESAMPLE)
            canvas = Image.new("RGBA", (TRAY_ICON_SIZE, TRAY_ICON_SIZE), (0, 0, 0, 0))
            x = (TRAY_ICON_SIZE - logo.size[0]) // 2
            y = (TRAY_ICON_SIZE - logo.size[1]) // 2
            canvas.paste(logo, (x, y), logo)
            return canvas
        except Exception as exc:  # tray rendering must never crash the app
            logger.warning("Tray logo render failed (%s); using fallback circle", exc)
    image: Image.Image = Image.new("RGB", (TRAY_ICON_SIZE, TRAY_ICON_SIZE), fallback_bg)
    draw = ImageDraw.Draw(image)
    margin = TRAY_ICON_SIZE // 7
    draw.ellipse(
        (margin, margin, TRAY_ICON_SIZE - margin, TRAY_ICON_SIZE - margin),
        fill=fallback_fg,
    )
    return image
