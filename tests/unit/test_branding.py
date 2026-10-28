"""S3 brand unification: tray icon and window icon derive from the logo.

Pablo (v0.16.1): the app showed a "blue square" icon (the tray's drawn
accent circle) that did not match the brand logo displayed in the main
tab. These tests pin the unification: the tray renders the logo image,
the window icon is a multi-size square .ico derived from the same logo,
and path resolution is shared by every surface.
"""

import sys
from pathlib import Path
from typing import cast

import pytest
from PIL import Image, ImageChops, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.branding import (
    TRAY_ICON_SIZE,
    build_tray_image,
    logo_candidates,
    resolve_logo_path,
)

ROOT = Path(__file__).resolve().parents[2]
LOGO = ROOT / "assets" / "logos" / "logo.png"
ICO = ROOT / "assets" / "icons" / "icono.ico"
_RESAMPLE = Image.Resampling.LANCZOS


@pytest.mark.unit
class TestTrayImage:
    """The tray image is the brand logo, not a drawn accent circle."""

    def test_tray_renders_the_logo(self):
        # Arrange
        with Image.open(LOGO) as raw:
            logo = raw.convert("RGBA")
        expected = logo.resize((TRAY_ICON_SIZE, TRAY_ICON_SIZE), _RESAMPLE)
        expected_px = expected.convert("RGB").getpixel((32, 32))

        # Act
        img = build_tray_image(LOGO)

        # Assert: same canvas size and the logo's own pixels, no blue circle
        assert img.size == (TRAY_ICON_SIZE, TRAY_ICON_SIZE)
        px = cast(tuple[int, int, int], img.convert("RGB").getpixel((32, 32)))
        assert px == expected_px
        r, g, b = px
        assert not (b > 180 and b > g + 40), f"blue circle leaked: {px}"

    def test_tray_falls_back_to_drawn_circle_without_logo(self):
        # Act
        img = build_tray_image(None, fallback_bg="#0F172A", fallback_fg="#2563EB")

        # Assert: explicit fallback keeps the drawn accent circle
        assert img.size == (TRAY_ICON_SIZE, TRAY_ICON_SIZE)
        assert img.convert("RGB").getpixel((32, 32)) == (37, 99, 235)

    def test_tray_never_raises_on_broken_logo(self, tmp_path):
        # Arrange: corrupt file where the logo should be
        bad = tmp_path / "logo.png"
        bad.write_bytes(b"not-an-image")

        # Act: must not raise; falls back to the drawn circle
        img = build_tray_image(bad, fallback_bg="#0F172A", fallback_fg="#2563EB")

        # Assert
        assert img.size == (TRAY_ICON_SIZE, TRAY_ICON_SIZE)


@pytest.mark.unit
class TestLogoResolution:
    """Shared logo path resolution for tray, tab and window surfaces."""

    def test_prefers_first_existing_candidate(self, tmp_path):
        # Arrange
        (tmp_path / "logo.png").write_bytes(LOGO.read_bytes())
        packaged = tmp_path / "assets" / "logos"
        packaged.mkdir(parents=True)
        (packaged / "logo.png").write_bytes(LOGO.read_bytes())

        # Act
        resolved = resolve_logo_path([tmp_path / "logo.png", packaged / "logo.png"])

        # Assert
        assert resolved == tmp_path / "logo.png"

    def test_returns_none_when_no_candidate_exists(self, tmp_path):
        # Act / Assert
        assert resolve_logo_path([tmp_path / "missing.png"]) is None

    def test_runtime_candidates_cover_frozen_and_dev_layouts(self):
        # Act
        candidates = logo_candidates(ROOT, meipass=str(ROOT / "_meipass_fake"))

        # Assert: bundle root first, packaged assets, then cwd copy
        assert candidates[0] == ROOT / "_meipass_fake" / "logo.png"
        assert ROOT / "assets" / "logos" / "logo.png" in candidates
        assert Path("logo.png") in candidates


@pytest.mark.unit
class TestWindowIconAsset:
    """The window .ico is a square multi-size render of the brand logo."""

    def _largest_frame(self, path: Path) -> tuple[Image.Image, tuple[int, int]]:
        with Image.open(path) as ico:
            frames = []
            for i in range(getattr(ico, "n_frames", 1)):
                ico.seek(i)
                frames.append(ico.size)
            largest = max(frames)
            ico.seek(frames.index(largest))
            return ico.convert("RGBA"), largest

    def test_icon_directory_is_square_and_multi_size(self):
        # Act: ICO directory entries (what Windows picks from), plus frames
        with Image.open(ICO) as ico:
            entries = set(ico.info.get("sizes", set()))
            for i in range(getattr(ico, "n_frames", 1)):
                ico.seek(i)
                entries.add(ico.size)

        # Assert: square entries only, including a sharp 256px one
        assert all(w == h for w, h in entries), f"non-square entries: {entries}"
        assert (256, 256) in entries, f"missing 256px entry: {entries}"
        assert len(entries) >= 3, f"expected multi-size ico, got {entries}"

    def test_icon_matches_the_logo_pixels(self):
        # Arrange: logo fitted on a square transparent canvas (generator rule)
        with Image.open(LOGO) as raw:
            logo = raw.convert("RGBA")
        canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        scaled = logo.copy()
        scaled.thumbnail((256, 256), _RESAMPLE)
        canvas.paste(
            scaled,
            ((256 - scaled.size[0]) // 2, (256 - scaled.size[1]) // 2),
            scaled,
        )

        # Act
        frame, size = self._largest_frame(ICO)
        frame = frame.resize((256, 256), _RESAMPLE).convert("RGB")

        # Assert: mean per-channel difference stays tiny (transparent
        # margins compare as zeros and do not mask logo deviation)
        diff = ImageStat.Stat(ImageChops.difference(canvas.convert("RGB"), frame))
        mean = max(diff.mean)
        assert mean < 15.0, f"icon deviates from logo (mean diff {mean:.1f})"
