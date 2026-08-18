"""Sidecar entry point for Audio2Text Tauri integration.

JSON-line server: reads stdin line-by-line, dispatches commands,
writes JSON responses to stdout.  Importable as module AND runnable as script.
"""
import json
import sys
import os
import logging

logger = logging.getLogger("SidecarEntry")

_transcriber = None


def _get_transcriber():
    global _transcriber
    if _transcriber is None:
        try:
            from backend.transcriber import Transcriber
            from backend.config_manager import ConfigManager
            from backend.sound_manager import SoundManager
            from backend.file_manager import FileManager
            from backend.localization_manager import LocalizationManager

            config = ConfigManager()
            sound = SoundManager()
            file_mgr = FileManager(config)
            loc = LocalizationManager()

            _transcriber = Transcriber(
                config_manager=config,
                sound_manager=sound,
                file_manager=file_mgr,
                update_status_callback=lambda msg, color: None,
                transcription_callback=lambda data: None,
                localization_manager=loc,
            )
            logger.info("Transcriber initialized successfully")
        except Exception:
            logger.exception("Failed to initialize Transcriber")
            raise
    return _transcriber


def parse_line(line):
    """Parse a single JSON line.  Returns dict or None on empty/invalid."""
    if not line or not line.strip():
        return None
    try:
        return json.loads(line.strip())
    except (json.JSONDecodeError, ValueError):
        return None


def _make_response(status, data=None, error=None):
    resp = {"status": status}
    if data is not None:
        resp["data"] = data
    if error is not None:
        resp["error"] = error
    return resp


def _handle_start_recording(cmd):
    try:
        t = _get_transcriber()
        t.start_recording()
        return _make_response("ok", {"recording": True})
    except Exception as e:
        return _make_response("error", error=str(e))


def _handle_stop_recording(cmd):
    try:
        t = _get_transcriber()
        t.stop_recording()
        return _make_response("ok", {"recording": False})
    except Exception as e:
        return _make_response("error", error=str(e))


def _handle_get_config(cmd):
    config_path = os.path.join(os.getcwd(), "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return _make_response("ok", config)
        return _make_response("ok", {})
    except Exception as e:
        return _make_response("error", error=str(e))


def _handle_save_config(cmd):
    config_data = cmd.get("data", {})
    config_path = os.path.join(os.getcwd(), "config.json")
    try:
        existing = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing.update(config_data)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        return _make_response("ok", existing)
    except Exception as e:
        return _make_response("error", error=str(e))


def _handle_get_history(cmd):
    return _make_response("ok", [])


def _handle_register_hotkey(cmd):
    """Register a hotkey through the Python keyboard library (fallback)."""
    hotkey_str = cmd.get("hotkey", "")
    if not hotkey_str:
        return _make_response("error", error="Missing 'hotkey' field")

    try:
        from backend.hotkey_manager import HotkeyManager
        manager = HotkeyManager()
        success = manager.register_via_ipc(hotkey_str)
        if success:
            return _make_response("ok", {"registered": True})
        else:
            return _make_response("error", error=f"Failed to register hotkey: {hotkey_str}")
    except Exception as e:
        logger.exception("register_hotkey handler error")
        return _make_response("error", error=str(e))


def _handle_clear_audio(cmd):
    try:
        from backend.file_manager import FileManager
        from backend.config_manager import ConfigManager
        fm = FileManager(ConfigManager())
        fm.clear_audio_files()
        return _make_response("ok", {"cleared": True})
    except Exception as e:
        return _make_response("error", error=str(e))


def _handle_clear_transcriptions(cmd):
    try:
        from backend.file_manager import FileManager
        from backend.config_manager import ConfigManager
        fm = FileManager(ConfigManager())
        fm.clear_transcriptions()
        return _make_response("ok", {"cleared": True})
    except Exception as e:
        return _make_response("error", error=str(e))


def _handle_get_status(cmd):
    """Return sidecar health and transcriber state."""
    try:
        t = _get_transcriber()
        return _make_response("ok", {
            "transcriber_ready": True,
            "is_recording": getattr(t, "is_recording", False),
        })
    except Exception as e:
        logger.exception("get_status handler error")
        return _make_response("error", error=f"Transcriber init failed: {e}")


_COMMAND_HANDLERS = {
    "start_recording": _handle_start_recording,
    "stop_recording": _handle_stop_recording,
    "get_config": _handle_get_config,
    "save_config": _handle_save_config,
    "get_history": _handle_get_history,
    "register_hotkey": _handle_register_hotkey,
    "clear_audio": _handle_clear_audio,
    "clear_transcriptions": _handle_clear_transcriptions,
    "get_status": _handle_get_status,
}


def dispatch_command(cmd):
    """Dispatch a parsed command dict and return a response dict."""
    if not isinstance(cmd, dict):
        return _make_response("error", error="Invalid command format")
    command = cmd.get("command")
    if not command:
        return _make_response("error", error="Missing 'command' field")
    handler = _COMMAND_HANDLERS.get(command)
    if handler is None:
        return _make_response("error", error=f"Unknown command: {command}")
    try:
        return handler(cmd)
    except Exception as e:
        logger.exception("Handler error for command %s", command)
        return _make_response("error", error=str(e))


def main():
    """Run the JSON-line sidecar server on stdin/stdout."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stderr,
    )
    logger.info("Sidecar started (stdin JSON-line mode)")
    for line in sys.stdin:
        cmd = parse_line(line)
        if cmd is None:
            continue
        resp = dispatch_command(cmd)
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
    logger.info("Sidecar stdin closed, exiting")


if __name__ == "__main__":
    main()
