"""Tests for backend/sidecar_entry.py — JSON-line sidecar server.

TDD: These tests define the IPC contract before implementation.
"""
import json
import io
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestCommandRouting:
    """Sidecar routes JSON commands to handlers and returns structured responses."""

    def test_dispatch_returns_ok_for_start_recording(self):
        from backend.sidecar_entry import dispatch_command
        cmd = {"command": "start_recording"}
        resp = dispatch_command(cmd)
        assert resp["status"] == "ok"
        assert "data" in resp

    def test_dispatch_returns_ok_for_stop_recording(self):
        from backend.sidecar_entry import dispatch_command
        cmd = {"command": "stop_recording"}
        resp = dispatch_command(cmd)
        assert resp["status"] == "ok"

    def test_dispatch_returns_ok_for_get_config(self):
        from backend.sidecar_entry import dispatch_command
        cmd = {"command": "get_config"}
        resp = dispatch_command(cmd)
        assert resp["status"] == "ok"
        assert isinstance(resp["data"], dict)

    def test_dispatch_returns_ok_for_save_config(self):
        from backend.sidecar_entry import dispatch_command
        cmd = {"command": "save_config", "data": {"hotkey": "f9"}}
        resp = dispatch_command(cmd)
        assert resp["status"] == "ok"

    def test_dispatch_returns_ok_for_get_history(self):
        from backend.sidecar_entry import dispatch_command
        cmd = {"command": "get_history"}
        resp = dispatch_command(cmd)
        assert resp["status"] == "ok"
        assert isinstance(resp["data"], list)

    def test_dispatch_returns_error_for_unknown_command(self):
        from backend.sidecar_entry import dispatch_command
        cmd = {"command": "nonexistent_command"}
        resp = dispatch_command(cmd)
        assert resp["status"] == "error"
        assert "error" in resp

    def test_dispatch_returns_error_for_missing_command(self):
        from backend.sidecar_entry import dispatch_command
        cmd = {"data": "something"}
        resp = dispatch_command(cmd)
        assert resp["status"] == "error"


class TestResponseFormat:
    """All responses follow the {status, data} contract."""

    def test_success_response_has_status_and_data(self):
        from backend.sidecar_entry import dispatch_command
        resp = dispatch_command({"command": "get_config"})
        assert "status" in resp
        assert "data" in resp

    def test_error_response_has_status_and_error(self):
        from backend.sidecar_entry import dispatch_command
        resp = dispatch_command({"command": "bad"})
        assert resp["status"] == "error"
        assert "error" in resp

    def test_response_is_json_serializable(self):
        from backend.sidecar_entry import dispatch_command
        resp = dispatch_command({"command": "get_config"})
        serialized = json.dumps(resp)
        assert isinstance(serialized, str)


class TestStdinParsing:
    """Parse JSON lines from stdin-like input."""

    def test_parse_valid_json_line(self):
        from backend.sidecar_entry import parse_line
        line = json.dumps({"command": "get_config"})
        result = parse_line(line)
        assert result == {"command": "get_config"}

    def test_parse_empty_line_returns_none(self):
        from backend.sidecar_entry import parse_line
        assert parse_line("") is None

    def test_parse_whitespace_line_returns_none(self):
        from backend.sidecar_entry import parse_line
        assert parse_line("   ") is None

    def test_parse_invalid_json_returns_none(self):
        from backend.sidecar_entry import parse_line
        assert parse_line("{invalid") is None


class TestSidecarAsModule:
    """sidecar_entry must be importable as a module."""

    def test_module_has_dispatch_command(self):
        import backend.sidecar_entry as mod
        assert hasattr(mod, "dispatch_command")
        assert callable(mod.dispatch_command)

    def test_module_has_parse_line(self):
        import backend.sidecar_entry as mod
        assert hasattr(mod, "parse_line")
        assert callable(mod.parse_line)

    def test_module_has_main(self):
        import backend.sidecar_entry as mod
        assert hasattr(mod, "main")
        assert callable(mod.main)
