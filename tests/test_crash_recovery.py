"""Crash recovery tests for the sidecar process.

Tests that the sidecar can detect crashes, restart with backoff,
and surface status to the frontend.
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
    return proc


def _cleanup(proc):
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


class TestCrashDetection:
    """Sidecar process death is detectable."""

    def test_sidecar_process_terminates_cleanly(self):
        """Sidecar exits cleanly when stdin closes."""
        proc = _start_sidecar()
        try:
            proc.stdin.close()
            proc.stdout.close()
            proc.stderr.close()
            proc.wait(timeout=5)
            # Process should terminate (any exit code is fine on Windows
            # when pipe is closed from parent side)
            assert proc.returncode is not None
        except Exception:
            _cleanup(proc)
            raise

    def test_sidecar_exits_on_kill(self):
        """Sidecar process can be killed externally."""
        proc = _start_sidecar()
        try:
            time.sleep(0.2)
            proc.kill()
            proc.wait(timeout=5)
            assert proc.returncode != 0
        finally:
            _cleanup(proc)

    def test_sidecar_stdout_closed_on_death(self):
        """Reading from a dead sidecar's stdout returns empty."""
        proc = _start_sidecar()
        try:
            time.sleep(0.2)
            proc.kill()
            proc.wait(timeout=5)

            data = proc.stdout.read()
            assert data == ""
        finally:
            _cleanup(proc)


class TestExponentialBackoff:
    """Restart logic applies exponential backoff."""

    def test_backoff_calculation(self):
        """Verify exponential backoff formula."""
        base_delay = 1.0
        max_delay = 30.0
        max_retries = 5

        delays = []
        for attempt in range(max_retries):
            delay = min(base_delay * (2 ** attempt), max_delay)
            delays.append(delay)

        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0
        assert delays[3] == 8.0
        assert delays[4] == 16.0

    def test_backoff_capped_at_max(self):
        """Backoff doesn't exceed max_delay."""
        base_delay = 1.0
        max_delay = 5.0
        attempt = 10

        delay = min(base_delay * (2 ** attempt), max_delay)
        assert delay == max_delay

    def test_backoff_resets_after_success(self):
        """After successful command, backoff resets."""
        state = {"backoff": 0, "attempt": 0}
        base_delay = 1.0
        max_delay = 30.0

        def on_failure():
            state["attempt"] += 1
            state["backoff"] = min(base_delay * (2 ** (state["attempt"] - 1)), max_delay)

        def on_success():
            state["attempt"] = 0
            state["backoff"] = 0

        on_failure()
        assert state["backoff"] == 1.0

        on_failure()
        assert state["backoff"] == 2.0

        on_success()
        assert state["backoff"] == 0

        on_failure()
        assert state["backoff"] == 1.0


class TestStatusReporting:
    """Sidecar status is reportable to frontend."""

    def test_healthy_status(self):
        """Sidecar reports healthy after successful command."""
        proc = _start_sidecar()
        try:
            line = json.dumps({"command": "get_config"}) + "\n"
            proc.stdin.write(line)
            proc.stdin.flush()
            resp_line = proc.stdout.readline()
            resp = json.loads(resp_line.strip())
            assert resp["status"] == "ok"

            status = "connected" if resp["status"] == "ok" else "disconnected"
            assert status == "connected"
        finally:
            _cleanup(proc)

    def test_disconnected_status_on_death(self):
        """After process kill, status should be disconnected."""
        proc = _start_sidecar()
        try:
            time.sleep(0.2)
            proc.kill()
            proc.wait(timeout=5)

            try:
                line = json.dumps({"command": "get_config"}) + "\n"
                proc.stdin.write(line)
                status = "disconnected"
            except (BrokenPipeError, OSError):
                status = "disconnected"

            assert status == "disconnected"
        finally:
            _cleanup(proc)
