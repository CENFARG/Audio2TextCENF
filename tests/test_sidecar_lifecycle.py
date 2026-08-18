"""Integration tests for sidecar lifecycle.

Tests: spawn sidecar -> send commands -> assert responses.
Uses subprocess to test the actual JSON-line IPC protocol.
"""
import json
import subprocess
import sys
import time
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SIDECAR_PY = PROJECT_ROOT / "backend" / "sidecar_entry.py"


def _start_sidecar():
    """Start sidecar process and return (process, write_pipe, read_pipe)."""
    proc = subprocess.Popen(
        [sys.executable, str(SIDECAR_PY)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(PROJECT_ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc, proc.stdin, proc.stdout


def _send_command(stdin, stdout, command, data=None):
    """Send a JSON command and read the response."""
    cmd = {"command": command}
    if data is not None:
        cmd["data"] = data
    line = json.dumps(cmd) + "\n"
    stdin.write(line)
    stdin.flush()
    response_line = stdout.readline()
    if not response_line:
        return None
    return json.loads(response_line.strip())


def _cleanup(proc):
    """Terminate and fully close a sidecar process."""
    try:
        proc.stdin.close()
    except Exception:
        pass
    try:
        proc.stdout.close()
    except Exception:
        pass
    try:
        proc.stderr.close()
    except Exception:
        pass
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=2)
        except Exception:
            pass


class TestSidecarLifecycle:
    """Full lifecycle: spawn -> commands -> shutdown."""

    def test_spawn_and_health_check(self):
        """Sidecar responds to get_config after spawn."""
        proc, stdin, stdout = _start_sidecar()
        try:
            resp = _send_command(stdin, stdout, "get_config")
            assert resp is not None
            assert resp["status"] == "ok"
            assert isinstance(resp["data"], dict)
        finally:
            _cleanup(proc)

    def test_start_and_stop_recording(self):
        """Sidecar handles start_recording then stop_recording."""
        proc, stdin, stdout = _start_sidecar()
        try:
            start_resp = _send_command(stdin, stdout, "start_recording")
            assert start_resp is not None
            assert start_resp["status"] == "ok"
            assert start_resp["data"]["recording"] is True

            stop_resp = _send_command(stdin, stdout, "stop_recording")
            assert stop_resp is not None
            assert stop_resp["status"] == "ok"
            assert stop_resp["data"]["recording"] is False
        finally:
            _cleanup(proc)

    def test_multiple_commands_sequential(self):
        """Sidecar handles a sequence of different commands."""
        proc, stdin, stdout = _start_sidecar()
        try:
            commands = [
                ("get_config", None),
                ("start_recording", None),
                ("stop_recording", None),
                ("get_history", None),
                ("save_config", {"hotkey": "f12"}),
            ]
            for cmd_name, data in commands:
                resp = _send_command(stdin, stdout, cmd_name, data)
                assert resp is not None, f"No response for {cmd_name}"
                assert resp["status"] == "ok", f"Error for {cmd_name}: {resp}"
        finally:
            _cleanup(proc)

    def test_invalid_json_handled_gracefully(self):
        """Sidecar ignores invalid JSON lines without crashing."""
        proc, stdin, stdout = _start_sidecar()
        try:
            stdin.write("this is not json\n")
            stdin.flush()
            time.sleep(0.1)

            resp = _send_command(stdin, stdout, "get_config")
            assert resp is not None
            assert resp["status"] == "ok"
        finally:
            _cleanup(proc)

    def test_unknown_command_returns_error(self):
        """Sidecar returns error for unknown command."""
        proc, stdin, stdout = _start_sidecar()
        try:
            resp = _send_command(stdin, stdout, "nonexistent_command")
            assert resp is not None
            assert resp["status"] == "error"
            assert "error" in resp
        finally:
            _cleanup(proc)
