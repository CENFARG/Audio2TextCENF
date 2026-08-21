"""
QA tests for window geometry 590x590 — robust validation + migration.

Covers:
- default geometry is square 590x590+200+100 on fresh install
- invalid geometry in config.json is corrected to default
- App._load_window_geometry fallback to 590x590 on invalid without crash
"""
import json
import os
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config_manager import ConfigManager


@pytest.mark.unit
def test_default_geometry_is_square():
    """ConfigManager sin config.json -> window_geometry == 590x590+200+100"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        tmp = f.name
    # ensure file does NOT exist
    if os.path.exists(tmp):
        os.unlink(tmp)
    try:
        cm = ConfigManager(config_file=tmp)
        geo = cm.get("window_geometry")
        assert geo == "590x590+200+100", f"expected 590x590+200+100, got {geo!r}"
        assert geo.startswith("590x590")
        # default_config also must be 590
        assert cm.default_config["window_geometry"] == "590x590+200+100"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@pytest.mark.unit
def test_invalid_geometry_fallback():
    """config.json con window_geometry = 'invalid' -> load_config lo corrige a 590x590*"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        tmp = f.name
        json.dump({"window_geometry": "invalid"}, f)
    try:
        cm = ConfigManager(config_file=tmp)
        geo = cm.get("window_geometry")
        # debe corregir a default 590x590+200+100
        assert geo == "590x590+200+100" or geo.startswith("590x590"), f"fallback failed, got {geo!r}"
        # también probar otro inválido: vacío
        # escribir vacío y recargar
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"window_geometry": ""}, fh)
        cm2 = ConfigManager(config_file=tmp)
        assert cm2.get("window_geometry").startswith("590x590")
        # probar legacy migration: 650x550 debe migrar a 590
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"window_geometry": "650x550+100+100"}, fh)
        cm3 = ConfigManager(config_file=tmp)
        assert cm3.get("window_geometry") == "590x590+200+100", f"legacy migration failed, got {cm3.get('window_geometry')!r}"
        # custom válido no legacy no debe pisarse
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"window_geometry": "700x800+50+50", "_geometry_migrated": True}, fh)
        cm4 = ConfigManager(config_file=tmp)
        assert cm4.get("window_geometry") == "700x800+50+50"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@pytest.mark.unit
def test_app_load_geometry_fallback():
    """mock App _load_window_geometry con geometry inválida debe fallback a 590x590 sin crash"""
    from ui.app import App

    # Crear instancia sin llamar __init__ (evita Tk)
    app = App.__new__(App)
    app.logger = Mock()
    app.config_manager = Mock()

    applied = {}

    def fake_geometry(val=None):
        if val is not None:
            applied["geometry"] = val
            return None
        return applied.get("geometry", "590x590")

    app.geometry = Mock(side_effect=fake_geometry)

    # Caso 1: geometry inválida
    app.config_manager.get.return_value = "invalid"
    app._load_window_geometry()
    assert applied.get("geometry") == "590x590", f"expected fallback 590x590, got {applied.get('geometry')!r}"

    # Caso 2: geometry muy pequeña < minsize
    applied.clear()
    app.config_manager.get.return_value = "100x100+0+0"
    app._load_window_geometry()
    assert applied.get("geometry") == "590x590", f"minsize fallback failed, got {applied.get('geometry')!r}"

    # Caso 3: geometry válida 590 debe aplicarse tal cual
    applied.clear()
    app.config_manager.get.return_value = "590x590+200+100"
    app._load_window_geometry()
    assert applied.get("geometry") == "590x590+200+100"

    # Caso 4: exception en get debe fallback sin crash
    applied.clear()
    app.config_manager.get.side_effect = Exception("boom")
    app._load_window_geometry()
    assert applied.get("geometry") == "590x590"

    # Caso 5: geometry vacía / None
    app.config_manager.get.side_effect = None
    app.config_manager.get.return_value = None
    applied.clear()
    app._load_window_geometry()
    assert applied.get("geometry") == "590x590"
