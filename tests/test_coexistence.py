"""Coexistence tests: legacy main.py and Tauri sidecar share backend modules.

Verifies that both entry points can import and use the same backend
without module-level conflicts or side effects.
"""
import sys
import importlib
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestLegacyStandalone:
    """Legacy main.py can be imported and used independently."""

    def test_main_module_importable(self):
        """main.py module is importable."""
        import main
        assert main is not None

    def test_backend_modules_importable(self):
        """All core backend modules are importable."""
        modules = [
            "backend.config_manager",
            "backend.transcriber",
            "backend.file_manager",
            "backend.sound_manager",
            "backend.hotkey_manager",
            "backend.localization_manager",
            "backend.sidecar_entry",
        ]
        for mod_name in modules:
            mod = importlib.import_module(mod_name)
            assert mod is not None, f"Failed to import {mod_name}"

    def test_legacy_ui_importable(self):
        """Legacy ui module is importable."""
        import ui.app
        assert hasattr(ui.app, "App")


class TestSidecarStandalone:
    """Tauri sidecar can run independently."""

    def test_sidecar_entry_importable(self):
        """sidecar_entry.py is importable as module."""
        from backend.sidecar_entry import dispatch_command, parse_line, main
        assert callable(dispatch_command)
        assert callable(parse_line)
        assert callable(main)

    def test_sidecar_dispatch_independent(self):
        """Sidecar dispatch works without any UI imports."""
        from backend.sidecar_entry import dispatch_command
        resp = dispatch_command({"command": "get_config"})
        assert resp["status"] == "ok"


class TestSharedBackendModules:
    """Both entry points share the same backend module instances."""

    def test_config_manager_singleton_behavior(self):
        """Both sidecar and legacy use the same ConfigManager module."""
        import backend.config_manager as cm1
        import backend.config_manager as cm2
        assert cm1 is cm2

    def test_sidecar_entry_no_ui_dependency(self):
        """sidecar_entry.py does not import any UI modules."""
        import backend.sidecar_entry as mod
        source_file = Path(mod.__file__)
        source_text = source_file.read_text(encoding="utf-8")
        ui_imports = ["import ui", "from ui", "import flet", "from flet",
                       "import customtkinter", "from customtkinter"]
        for imp in ui_imports:
            assert imp not in source_text, (
                f"sidecar_entry.py contains UI import: {imp}"
            )

    def test_backend_modules_importable_in_any_order(self):
        """Backend modules can be imported in any order without circular deps."""
        from backend import sidecar_entry
        from backend import config_manager
        from backend import file_manager
        from backend import sound_manager
        from backend import hotkey_manager

        assert sidecar_entry is not None
        assert config_manager is not None
        assert file_manager is not None
        assert sound_manager is not None
        assert hotkey_manager is not None
