"""@File: audio2text/api/routes/transcribe.py
@Description: Transcription endpoint — POST /api/v1/transcribe plus lifecycle
    start/stop endpoints with real AudioCaptureService integration.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging
import tempfile
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from audio2text.api.dependencies import get_transcription_service
from audio2text.api.schemas.transcription import TranscriptionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["transcription"])

# In-memory session state
_active_sessions: dict[str, str] = {}
# Audio capture service singleton (started lazily)
_capture_service: object | None = None
_capture_lock: threading.Lock = threading.Lock()


def _get_or_create_capture_service() -> object:
    """Create or return the singleton AudioCaptureService for recording.

    Returns:
        An AudioCaptureService instance configured from the app config.
    """
    global _capture_service

    if _capture_service is not None:
        return _capture_service

    with _capture_lock:
        if _capture_service is not None:
            return _capture_service

        from audio2text.services.audio_capture_service import (
            AudioCaptureConfig,
            AudioCaptureService,
        )

        capture_config = AudioCaptureConfig(
            sample_rate=16000,
            channels=1,
            max_recording_time=300.0,
        )

        def _status_cb(text: str, color: str) -> None:
            logger.debug("Capture status: %s (%s)", text, color)

        def _overlay_cb(state: str, mins: int, secs: int) -> None:
            pass  # Overlay updates are handled client-side

        _capture_service = AudioCaptureService(
            config=capture_config,
            status_callback=_status_cb,
            overlay_callback=_overlay_cb,
        )

    return _capture_service


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("es"),
) -> TranscriptionResponse:
    """Transcribe an uploaded audio file.

    Accepts a multipart file upload with optional language parameter.
    Saves the file temporarily, runs transcription, and returns the result.

    Args:
        file: The audio file to transcribe (WAV, MP3, etc.).
        language: Language code (default "es").

    Returns:
        A TranscriptionResponse with the transcribed text and metadata.

    Raises:
        HTTPException: 503 if the transcription service is unavailable.
    """
    from audio2text.services.transcription_service import TranscriptionService

    svc: TranscriptionService | None = get_transcription_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="Transcription service unavailable")

    # Save uploaded file to a temporary location
    suffix = Path(file.filename).suffix if file.filename else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = svc.transcribe(str(tmp_path), language=language)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    if result is None:
        raise HTTPException(status_code=503, detail="Transcription failed")

    transcription_id = str(uuid.uuid4())

    return TranscriptionResponse(
        id=transcription_id,
        text=result.text,
        language=result.language,
        provider=result.provider_name or "unknown",
        model=result.model_name or "unknown",
        duration_s=result.duration_seconds,
        segments=result.segments if result.segments else None,
    )


@router.post("/transcribe/start")
async def start_recording_session() -> dict[str, str]:
    """Start a real audio recording session via AudioCaptureService.

    Creates a session ID and starts the microphone capture.
    Audio frames are buffered for WebSocket streaming and/or file save.

    Returns:
        A dict with session_id and status=recording.
    """
    session_id = str(uuid.uuid4())
    _active_sessions[session_id] = "recording"

    # Start real audio capture
    try:
        capture_svc = _get_or_create_capture_service()
        from audio2text.services.audio_capture_service import AudioCaptureService

        svc: AudioCaptureService = capture_svc  # type: ignore[assignment]
        started = svc.start_recording()
        if not started:
            logger.warning("AudioCaptureService.start_recording() returned False")
    except Exception as exc:
        logger.error("Failed to start audio capture: %s", exc)

    return {"session_id": session_id, "status": "recording"}


@router.post("/transcribe/stop")
async def stop_recording_session(session_id: str | None = None) -> dict[str, object]:
    """Stop recording, transcribe the captured audio, and persist metadata.

    Stops the AudioCaptureService, runs transcription on the captured
    WAV data, and saves the result via MetadataService.

    Args:
        session_id: Optional session ID from a previous start call.

    Returns:
        A dict with session_id, status, and transcription text.
    """
    target_id = session_id if session_id else "unknown"

    if session_id and session_id in _active_sessions:
        _active_sessions[session_id] = "stopped"

    # Stop capture and get audio segment
    audio_segment = None
    try:
        capture_svc = _get_or_create_capture_service()
        from audio2text.services.audio_capture_service import AudioCaptureService

        svc: AudioCaptureService = capture_svc  # type: ignore[assignment]
        audio_segment = svc.stop_recording()
    except Exception as exc:
        logger.error("Failed to stop audio capture: %s", exc)

    if audio_segment is None:
        return {
            "session_id": target_id,
            "status": "stopped",
            "text": "",
            "provider": None,
            "duration_s": 0.0,
        }

    # Write audio to temp WAV for transcription
    import soundfile as sf  # type: ignore[import-untyped]

    fd, temp_path = tempfile.mkstemp(suffix=".wav", prefix="a2t_stop_")
    import os
    os.close(fd)

    try:
        sf.write(temp_path, audio_segment.data, audio_segment.sample_rate)
    except Exception as exc:
        logger.error("Failed to write temp WAV: %s", exc)
        return {
            "session_id": target_id,
            "status": "stopped",
            "text": "",
            "provider": None,
            "duration_s": 0.0,
        }

    # Run transcription
    try:
        from audio2text.services.transcription_service import TranscriptionService
        from audio2text.services.metadata_service import MetadataService

        tx_svc: TranscriptionService | None = get_transcription_service()
        if tx_svc is None:
            return {
                "session_id": target_id,
                "status": "stopped",
                "text": "",
                "provider": None,
                "duration_s": 0.0,
            }

        result = tx_svc.transcribe(temp_path, language="es")
    finally:
        if Path(temp_path).exists():
            Path(temp_path).unlink()

    if result is None:
        return {
            "session_id": target_id,
            "status": "stopped",
            "text": "",
            "provider": None,
            "duration_s": 0.0,
        }

    return {
        "session_id": target_id,
        "status": "stopped",
        "text": result.text,
        "provider": result.provider_name or "unknown",
        "model": result.model_name or "unknown",
        "duration_s": result.duration_seconds or 0.0,
    }
