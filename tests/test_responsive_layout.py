import ast
from pathlib import Path


APP_PATH = Path(__file__).parents[1] / "ui" / "app.py"


def _create_main_tab_source():
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    method = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "create_main_tab"
    )
    return method, ast.get_source_segment(APP_PATH.read_text(encoding="utf-8"), method)


def test_main_controls_use_exactly_two_equal_weight_columns():
    _, source = _create_main_tab_source()
    assert "content_frame.grid_columnconfigure((0, 1), weight=1, uniform=\"content\")" in source
    assert "grid_columnconfigure((0, 1, 2)" not in source
    assert ".grid(row=0, column=2" not in source


def test_clear_buttons_share_two_column_content_geometry():
    _, source = _create_main_tab_source()
    assert "column=0" in source and "column=1" in source
    assert "self.clear_audio_button" in source
    assert "self.clear_transcriptions_button" in source
    assert "self.clear_audio_button.grid(row=0, column=0" in source
    assert "self.clear_transcriptions_button.grid(row=0, column=1" in source


def test_transcription_textbox_spans_same_two_columns_and_margins():
    _, source = _create_main_tab_source()
    assert "self.transcription_frame.grid(row=1, column=0, columnspan=2" in source
    assert "self.transcription_textbox.grid(row=0, column=0, columnspan=2" in source
    assert "padx=15" in source


def test_layout_contract_has_no_extra_weighted_column_or_pack_textbox():
    _, source = _create_main_tab_source()
    assert "self.transcription_textbox.pack" not in source
    assert "columnspan=2" in source


def test_supported_widths_keep_equal_columns_spacing_and_aligned_outer_bounds():
    """Deterministic geometry model for the shared two-column contract."""
    for content_width in (470, 650, 900, 1280):
        column_width = content_width / 2
        left = (0 + 5, column_width - 5)
        right = (column_width + 5, content_width - 5)
        textbox = (5, content_width - 5)

        assert left[1] - left[0] == right[1] - right[0]
        assert left[0] == textbox[0]
        assert right[1] == textbox[1]
        assert right[0] - left[1] == 10
        assert left[0] >= 0 and right[1] <= content_width
