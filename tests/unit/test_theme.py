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

from ui.theme import (
    COLORS,
    RADII,
    SURFACES,
    TYPOGRAPHY,
    composite_rgba,
    uppercase_label,
)

UI_DIR = Path(__file__).resolve().parents[2] / "ui"
LANG_DIR = Path(__file__).resolve().parents[2] / "lang"

PROTO_VARS = {
    "bg": "#080d18",
    # GR amendment L10: owner picked #121d30 over --surface #101827
    "surface": "#121d30",
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
        # GR amendment L10: owner picked #121d30 / #1c3447 from Flor's palette
        assert str(SURFACES["hi"]).lower() == "#1c3447"
        assert str(SURFACES["lo"]).lower() == "#121d30"

    def test_line_composited_over_bg(self):
        # --line: rgba(160, 190, 230, .14) over --bg
        expected = composite_rgba((160, 190, 230, 0.14), PROTO_VARS["bg"])
        assert str(COLORS["line"]).lower() == expected

    def test_state_tokens_exist_outside_prototype(self):
        # Statuses have no landing analogue; they live in theme (never inline)
        for key in ("success", "warning", "error", "on_primary"):
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
class TestPresentationHelpers:
    """S2: uppercase capture labels like the mockup (● CAPTURANDO AUDIO)."""

    def test_uppercase_label(self):
        assert uppercase_label("Capturando audio") == "CAPTURANDO AUDIO"

    def test_uppercase_label_strips_whitespace(self):
        assert uppercase_label("  transcripción en vivo  ") == "TRANSCRIPCIÓN EN VIVO"


@pytest.mark.unit
class TestMainScreenLangKeys:
    """S2: new i18n keys for the mockup main screen (live label + footer)."""

    def test_main_screen_keys_exist_in_both_languages(self):
        import json

        es = json.loads(LANG_DIR.joinpath("es.json").read_text(encoding="utf-8"))
        en = json.loads(LANG_DIR.joinpath("en.json").read_text(encoding="utf-8"))
        for key in ("transcription_live", "model_footer", "connected", "no_api_key"):
            assert key in es, f"missing {key} in lang/es.json"
            assert key in en, f"missing {key} in lang/en.json"


@pytest.mark.unit
class TestRadii:
    def test_radii_match_prototype(self):
        assert RADII["card"] == 19  # .app-window
        assert RADII["chip"] == 13
        assert RADII["pill"] == 999


@pytest.mark.unit
class TestThemeJSON:
    """S5/G: themes/*.json load, validate and apply in place."""

    def test_list_themes_finds_builtins(self):
        from ui.theme import list_themes

        assert "midnight-aurora" in list_themes()
        assert "deep-violet" in list_themes()

    def test_load_theme_returns_schema(self):
        from ui.theme import load_theme

        data = load_theme("midnight-aurora")
        for key in ("name", "colors", "surfaces", "typography", "radii"):
            assert key in data, f"missing {key}"

    def test_load_theme_missing_raises_clear_error(self):
        from ui.theme import load_theme

        with pytest.raises(FileNotFoundError, match="no-existe"):
            load_theme("no-existe")

    def test_load_theme_invalid_schema_rejected(self, tmp_path):
        from ui.theme import THEMES_DIR, load_theme

        bad = THEMES_DIR / "roto.json"
        bad.write_text('{"name": "roto"}', encoding="utf-8")
        try:
            with pytest.raises(ValueError, match="colors"):
                load_theme("roto")
        finally:
            bad.unlink()

    def test_apply_theme_mutates_in_place(self):
        import ui.theme as theme_mod

        data = theme_mod.load_theme("deep-violet")
        before = theme_mod.COLORS["bg"]
        theme_mod.apply_theme(data)
        try:
            assert theme_mod.COLORS["bg"] == data["colors"]["bg"]
            assert theme_mod.COLORS["bg"] != before
            # live view: importers holding the dict see the change
            assert theme_mod.DesignSystem.COLORS is theme_mod.COLORS
        finally:
            theme_mod.apply_theme(theme_mod.load_theme("midnight-aurora"))

    def test_apply_theme_rejects_unknown_color(self):
        from ui.theme import apply_theme

        bad = {"colors": {"no-existe-token": "#000000"}}
        with pytest.raises(ValueError, match="no-existe-token"):
            apply_theme(bad)

    def test_roundtrip_restores_exact_values(self):
        import ui.theme as theme_mod

        snapshot = dict(theme_mod.COLORS)
        theme_mod.apply_theme(theme_mod.load_theme("deep-violet"))
        theme_mod.apply_theme(theme_mod.load_theme("midnight-aurora"))
        assert theme_mod.COLORS == snapshot


@pytest.mark.unit
class TestThemeFilesAccessibility:
    """KB (Color y Percepción): AA contrast is a gate, not a wish."""

    @staticmethod
    def _luminance(hex_color: str) -> float:
        def channel(c: float) -> float:
            c /= 255.0
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        h = hex_color.lstrip("#")
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

    def _contrast(self, a: str, b: str) -> float:
        la, lb = self._luminance(a), self._luminance(b)
        lighter, darker = max(la, lb), min(la, lb)
        return (lighter + 0.05) / (darker + 0.05)

    def test_every_builtin_theme_passes_aa_on_body_text(self):
        import json

        from ui.theme import THEMES_DIR

        for theme_file in sorted(THEMES_DIR.glob("*.json")):
            data = json.loads(theme_file.read_text(encoding="utf-8"))
            colors = data["colors"]
            for surface_key in ("bg", "surface"):
                ratio = self._contrast(colors["text"], colors[surface_key])
                assert ratio >= 4.5, (
                    f"{theme_file.name}: text on {surface_key} = {ratio:.2f} (<4.5)"
                )

    def test_on_primary_contrasts_with_primary(self):
        import json

        from ui.theme import THEMES_DIR

        for theme_file in sorted(THEMES_DIR.glob("*.json")):
            data = json.loads(theme_file.read_text(encoding="utf-8"))
            colors = data["colors"]
            ratio = self._contrast(colors["on_primary"], colors["primary"])
            assert ratio >= 4.5, (
                f"{theme_file.name}: on_primary on primary = {ratio:.2f} (<4.5)"
            )
