"""Theme token contract vs the approved landing prototype (v0.18.0 R1).

The landing's CSS custom properties (docs/design/landing_prototipo.html)
are the source of truth: ui/theme.py must mirror them exactly so the
tokens transfer 1:1 to the React Native design system later.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from ui.theme import COLORS, RADII, SURFACES, TYPOGRAPHY, composite_rgba

UI_DIR = Path(__file__).resolve().parents[2] / "ui"

PROTO_VARS = {
    "bg": "#080d18",
    "surface": "#101827",
    "text": "#f2f7ff",
    "muted": "#9aaac2",
    "cyan": "#56e5e3",
    "blue": "#6b8cff",
    "violet": "#ad82ff",
    "green": "#77e4b1",
}


@pytest.mark.unit
class TestColorTokens:
    """S4: every prototype CSS var is mirrored exactly."""

    @pytest.mark.parametrize("name,expected", sorted(PROTO_VARS.items()))
    def test_tokens_match_prototype_css_vars(self, name, expected):
        assert str(COLORS[name]).lower() == expected

    def test_mockup_surfaces(self):
        # .app-window gradient endpoints, flattened for CTk
        assert str(SURFACES["hi"]).lower() == "#162237"
        assert str(SURFACES["lo"]).lower() == "#0c1423"

    def test_line_composited_over_bg(self):
        # --line: rgba(160, 190, 230, .14) over --bg
        expected = composite_rgba((160, 190, 230, 0.14), PROTO_VARS["bg"])
        assert str(COLORS["line"]).lower() == expected

    def test_state_tokens_exist_outside_prototype(self):
        # Statuses have no landing analogue; they live in theme (never inline)
        for key in ("success", "warning", "error"):
            assert key in COLORS


@pytest.mark.unit
class TestCompositeRGBA:
    def test_full_alpha_is_the_color(self):
        assert composite_rgba((86, 229, 227, 1.0), "#080d18") == "#56e5e3"

    def test_zero_alpha_is_the_background(self):
        assert composite_rgba((86, 229, 227, 0.0), "#080d18") == "#080d18"

    def test_result_is_solid_hex(self):
        result = composite_rgba((160, 190, 230, 0.5), "#101827")
        assert len(result) == 7 and result.startswith("#")


@pytest.mark.unit
class TestTypography:
    def test_hierarchy_present(self):
        for key in ("heading", "subheading", "body", "small", "label"):
            assert key in TYPOGRAPHY

    def test_label_is_small_and_bold(self):
        # Uppercase capture labels ("CAPTURANDO AUDIO", "TRANSCRIPCIÓN EN VIVO")
        _family, size, weight = TYPOGRAPHY["label"]
        assert weight == "bold" and size <= 12

    def test_heading_is_largest(self):
        sizes = {key: spec[1] for key, spec in TYPOGRAPHY.items()}
        assert sizes["heading"] == max(sizes.values())

    def test_specs_are_font_tuples(self):
        for spec in TYPOGRAPHY.values():
            assert isinstance(spec, tuple) and len(spec) == 3


@pytest.mark.unit
class TestNoHardcodedHex:
    """S5/R1 exit criterion: no raw hex in ui/ outside theme.py."""

    HEX_RE = re.compile(r"#\b[0-9A-Fa-f]{6}\b")

    def test_no_hardcoded_hex_outside_theme(self):
        # Act: scan every ui/*.py except the token source itself
        offenders = []
        for path in sorted(UI_DIR.rglob("*.py")):
            if path.name == "theme.py":
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                if self.HEX_RE.search(line):
                    offenders.append(f"{path.relative_to(UI_DIR)}:{lineno}")

        # Assert: every color comes from theme tokens
        assert offenders == [], f"hardcoded hex colors: {offenders}"


@pytest.mark.unit
class TestRadii:
    def test_radii_match_prototype(self):
        assert RADII["card"] == 19  # .app-window
        assert RADII["chip"] == 13
        assert RADII["pill"] == 999
