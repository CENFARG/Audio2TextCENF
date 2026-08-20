"""Sidecar entry point for Audio2Text Tauri integration.

JSON-line server: reads stdin line-by-line, dispatches commands,
writes JSON responses to stdout.  Importable as module AND runnable as script.
"""
import json
import sys
import os
import logging
import threading
import time

logger = logging.getLogger("SidecarEntry")

_transcriber = None
_pending_result = None
_result_event = threading.Event()


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

            def _on_transcription(data):
                global _pending_result
                _pending_result = data
                _result_event.set()

            _transcriber = Transcriber(
                config_manager=config,
                sound_manager=sound,
                file_manager=file_mgr,
                update_status_callback=lambda msg, color: None,
                transcription_callback=_on_transcription,
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
    global _pending_result
    try:
        t = _get_transcriber()
        _result_event.clear()
        _pending_result = None
        t.stop_recording()
        # Wait up to 120s for transcription to complete (long audio may take time)
        if _result_event.wait(timeout=120):
            failure = getattr(t, "last_transcription_failure", None)
            if failure is not None:
                msg = getattr(failure, "message", str(failure))
                _pending_result = None
                _result_event.clear()
                return _make_response("error", error=msg)
            result = _pending_result
            _pending_result = None
            _result_event.clear()
            text = ""
            if isinstance(result, dict):
                if result.get("error"):
                    return _make_response("error", error=str(result.get("error")))
                text = result.get("text", "")
            elif isinstance(result, str):
                text = result
            return _make_response("ok", {"recording": False, "text": text})
        else:
            failure = getattr(t, "last_transcription_failure", None)
            if failure is not None:
                msg = getattr(failure, "message", str(failure))
                return _make_response("error", error=msg)
            return _make_response("error", error="Transcription timed out")
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
    """Read transcription history from transcriptions_log.jsonl."""
    try:
        from backend.config_manager import ConfigManager
        config = ConfigManager()
        transcriptions_path = config.get("transcriptions_path", "./transcriptions")
        log_file = os.path.join(transcriptions_path, "transcriptions_log.jsonl")
        if not os.path.exists(log_file):
            return _make_response("ok", [])
        entries = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        # Return newest first, limit to 100
        entries.reverse()
        return _make_response("ok", entries[:100])
    except Exception as e:
        logger.exception("get_history error")
        return _make_response("error", error=str(e))


def _handle_register_hotkey(cmd):
    """Hotkey registration is handled by Rust (tauri-plugin-global-shortcut).
    This is a no-op for backward compatibility."""
    return _make_response("ok", {"registered": True, "note": "Managed by Rust"})


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
