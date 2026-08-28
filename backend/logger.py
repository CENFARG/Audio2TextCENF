# -*- coding: utf-8 -*-
"""
Deterministic transcription logger — Slice A hardening + 12m smoke root-cause.

Writes logs/transcription_debug.log (append, flush per record) with
timestamp, chunk_id, duration, file_size, api attempt, latency, error code,
circuit state, queue depth. Never loses logs on crash (flush + FileHandler).

Usage:
    from backend.logger import get_transcription_logger, ensure_transcription_debug_handler
    log = get_transcription_logger()
    log.debug("chunk start", extra={"chunk_id": 1})

Main.py calls ensure_transcription_debug_handler() once after basicConfig.
Transcriber also calls it lazily.

CAP TRANSITORIO A - reevaluar post B
"""
import logging
import os
import sys
from pathlib import Path

_TRANSCRIPTION_DEBUG_LOGGER = "transcription_debug"
_TRANSCRIPTION_DEBUG_FILE = "transcription_debug.log"


def _resolve_logs_dir() -> Path:
    # Prefer external_path next to config when frozen, else project root/logs
    if getattr(sys, "frozen", False):
        base = Path(os.getcwd())
        # main.py uses external_path = dirname(executable); we fallback to cwd
        try:
            exe_dir = Path(sys.executable).parent
            if exe_dir.exists():
                base = exe_dir
        except Exception:
            pass
    else:
        base = Path(__file__).resolve().parent.parent  # audio2text-v0150-groq-fix/
    logs_dir = base / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


class _FlushFileHandler(logging.FileHandler):
    """FileHandler that flushes after each emit (crash-safe)."""

    def emit(self, record):
        super().emit(record)
        try:
            self.flush()
        except Exception:
            pass


def get_transcription_logger() -> logging.Logger:
    return logging.getLogger(_TRANSCRIPTION_DEBUG_LOGGER)


def ensure_transcription_debug_handler(logs_dir: Path | None = None) -> Path:
    """
    Ensure transcription_debug.log handler exists on both
    transcription_debug logger and Transcriber logger.
    Idempotent, safe to call multiple times.
    Returns path to log file.
    """
    if logs_dir is None:
        logs_dir = _resolve_logs_dir()
    else:
        logs_dir = Path(logs_dir)
        logs_dir.mkdir(parents=True, exist_ok=True)

    log_path = logs_dir / _TRANSCRIPTION_DEBUG_FILE

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler singleton keyed by path on root
    for logger_name in (_TRANSCRIPTION_DEBUG_LOGGER, "Transcriber", "transcription"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        # evita duplicar handler si ya existe para este archivo
        already = any(
            isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == str(log_path)
            for h in logger.handlers
        )
        if not already:
            try:
                fh = _FlushFileHandler(str(log_path), encoding="utf-8", delay=False)
                fh.setLevel(logging.DEBUG)
                fh.setFormatter(fmt)
                logger.addHandler(fh)
                # no propagar doble al root para este logger evita duplicado en app_*.log
                # pero dejamos propagate True para que también quede en app_ log si hace falta diagnóstico cruzado
                logger.propagate = True
            except Exception as e:
                print(f"[logger] no se pudo crear {log_path}: {e}")

    # También enganchar al root para capturar cualquier DEBUG que ya se emita antes de init
    root = logging.getLogger()
    has_root = any(
        isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == str(log_path)
        for h in root.handlers
    )
    if not has_root:
        try:
            rfh = _FlushFileHandler(str(log_path), encoding="utf-8", delay=False)
            rfh.setLevel(logging.DEBUG)
            rfh.setFormatter(fmt)
            root.addHandler(rfh)
        except Exception:
            pass

    return log_path


def log_transcription_event(
    level: int,
    msg: str,
    *,
    chunk_id: str | int | None = None,
    duration: float | None = None,
    file_size_mb: float | None = None,
    attempt: int | None = None,
    latency_s: float | None = None,
    error_code: str | None = None,
    circuit: str | None = None,
    queue_depth: int | None = None,
    extra_fields: dict | None = None,
):
    """
    Helper to log with structured suffix:
    [chunk=3/28 dur=25.1s size=0.78MB attempt=2 latency=1.23s err=429 circuit=closed q=12/64]
    """
    parts = []
    if chunk_id is not None:
        parts.append(f"chunk={chunk_id}")
    if duration is not None:
        parts.append(f"dur={duration:.1f}s")
    if file_size_mb is not None:
        parts.append(f"size={file_size_mb:.2f}MB")
    if attempt is not None:
        parts.append(f"attempt={attempt}")
    if latency_s is not None:
        parts.append(f"latency={latency_s:.3f}s")
    if error_code is not None:
        parts.append(f"err={error_code}")
    if circuit is not None:
        parts.append(f"circuit={circuit}")
    if queue_depth is not None:
        parts.append(f"q={queue_depth}")
    if extra_fields:
        for k, v in extra_fields.items():
            parts.append(f"{k}={v}")
    suffix = f" [{' '.join(parts)}]" if parts else ""
    log = get_transcription_logger()
    log.log(level, f"{msg}{suffix}")
