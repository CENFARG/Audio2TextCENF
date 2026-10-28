"""Regenerate the window icon from the brand logo (S3 unification).

Renders ``assets/logos/logo.png`` onto a square transparent canvas and
writes a multi-size ``assets/icons/icono.ico`` (16..256 px) so Windows
renders a sharp titlebar/taskbar icon identical to the main-tab logo.

Usage:
    python scripts/generate_icons.py

Author: CENF development team.
License: Apache 2.0.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = ROOT / "assets" / "logos" / "logo.png"
ICO_PATH = ROOT / "assets" / "icons" / "icono.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]


def render_square(logo: Image.Image, size: int) -> Image.Image:
    """Fit the logo on a square transparent canvas.

    Args:
        logo: RGBA logo image (any dimensions).
        size: Square canvas edge in pixels.

    Returns:
        The logo contained and centered on a ``size x size`` RGBA canvas.
    """
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    scaled = logo.copy()
    scaled.thumbnail((size, size), Image.Resampling.LANCZOS)
    x = (size - scaled.size[0]) // 2
    y = (size - scaled.size[1]) // 2
    canvas.paste(scaled, (x, y), scaled)
    return canvas


def main() -> None:
    """Regenerate the multi-size .ico from the brand logo."""
    logo = Image.open(LOGO_PATH).convert("RGBA")
    base = render_square(logo, SIZES[-1])
    ICO_PATH.parent.mkdir(parents=True, exist_ok=True)
    base.save(ICO_PATH, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"[+] wrote {ICO_PATH} ({SIZES[-1]}px base, sizes {SIZES})")


if __name__ == "__main__":
    main()
