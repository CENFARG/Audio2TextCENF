import ast
from pathlib import Path


APP_PATH = Path(__file__).parents[1] / "ui" / "app.py"


def _app_source_tree():
    return ast.parse(APP_PATH.read_text(encoding="utf-8"))


def test_normal_startup_has_no_tutorial_manager_path_even_with_legacy_flags():
    """Legacy tutorial flags must not activate onboarding during startup."""
    tree = _app_source_tree()
    source = APP_PATH.read_text(encoding="utf-8")

    assert "TutorialManager" not in source
    assert "ui.tutorial" not in source
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "should_start"
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "start"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "tutorial_manager"
        for node in ast.walk(tree)
    )


def test_tutorial_module_is_removed_when_startup_has_no_active_references():
    assert not (APP_PATH.parent / "tutorial.py").exists()
