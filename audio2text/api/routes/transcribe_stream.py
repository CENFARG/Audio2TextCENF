"""@File: audio2text/api/routes/transcribe_stream.py
@Description: WebSocket streaming endpoint — WS /api/v1/transcribe/stream.
    Buffers incoming PCM audio frames, runs periodic partial transcription
    via the configured provider, and streams results back as JSON frames.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import io
import logging
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf  # type: ignore[import-untyped]
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from audio2text.api.ws.connection_manager import WSConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["streaming"])

# Global connection manager instance for the streaming endpoint
_stream_manager = WSConnectionManager()

# Buffer threshold in seconds before attempting partial transcription
_PARTIAL_INTERVAL_S: float = 1.5
_SAMPLE_RATE: int = 16000


@router.websocket("/transcribe/stream")
async def transcribe_stream(websocket: WebSocket) -> None:
    """Real-time audio transcription streaming endpoint with real transcription.

    Lifecycle:
    1. Client connects → server accepts and sends welcome.
    2. Client sends binary audio frames (PCM16 LE, 16kHz, mono).
    3. Server buffers frames and runs partial transcription every ~1.5s.
    4. Server sends JSON frames with type "partial" containing real text.
    5. On disconnect, server sends final transcription and cleans up.

    Args:
        websocket: The connected WebSocket client.
    """
    global _stream_manager

    await _stream_manager.connect(websocket)

    # Send welcome status
    await websocket.send_json({
        "seq": 0,
        "type": "status",
        "final": False,
        "text": "connected",
    })

    buffer: list[np.ndarray] = []
    seq: int = 0
    last_partial_time: float = time.monotonic()

    try:
        while True:
            # Receive binary audio data from client
            try:
                data = await websocket.receive_bytes()
            except WebSocketDisconnect:
                break

            # Convert bytes to numpy int16 array
            try:
                chunk = np.frombuffer(data, dtype=np.int16)
                buffer.append(chunk)
            except Exception as exc:
                logger.debug("Skipping malformed audio chunk: %s", exc)
                continue

            # Check if enough time has elapsed for a partial transcription
            elapsed = time.monotonic() - last_partial_time
            if elapsed >= _PARTIAL_INTERVAL_S and len(buffer) > 0:
                seq += 1
                partial_text = _transcribe_buffer(buffer)
                if partial_text:
                    await websocket.send_json({
                        "seq": seq,
                        "type": "partial",
                        "final": False,
                        "text": partial_text,
                    })
                last_partial_time = time.monotonic()

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("Stream error: %s", exc)
        try:
            await websocket.send_json({
                "seq": -1,
                "type": "error",
                "final": True,
                "text": None,
                "error": {
                    "code": "WS_001",
                    "message": str(exc),
                },
            })
        except Exception:
            pass
    finally:
        # Send final transcription of remaining buffer
        if buffer:
            seq += 1
            try:
                final_text = _transcribe_buffer(buffer)
                await websocket.send_json({
                    "seq": seq,
                    "type": "final",
                    "final": True,
                    "text": final_text or "",
                })
            except Exception as exc:
                logger.error("Failed to send final transcription: %s", exc)

        await _stream_manager.disconnect(websocket)


def _transcribe_buffer(buffer: list[np.ndarray]) -> str:
    """Transcribe the current audio buffer.

    Combines all chunks into one numpy array, writes to a temporary
    WAV file, and calls the transcription service.

    Args:
        buffer: List of numpy int16 audio chunks.

    Returns:
        Transcribed text string, or empty string on failure.
    """
    if not buffer:
        return ""

    try:
        audio_data = np.concatenate(buffer, axis=0)
    except ValueError:
        return ""

    if audio_data.size < _SAMPLE_RATE * 0.3:  # Minimum 300ms
        return ""

    # Write to temporary WAV file
    import os

    fd, temp_path = tempfile.mkstemp(suffix=".wav", prefix="a2t_ws_")
    os.close(fd)

    try:
        sf.write(temp_path, audio_data, _SAMPLE_RATE)
    except Exception as exc:
        logger.debug("Failed to write WS temp WAV: %s", exc)
        return ""

    try:
        from audio2text.api.dependencies import get_transcription_service

        svc = get_transcription_service()
        if svc is None:
            return ""

        result = svc.transcribe(temp_path, language="es")
        if result is None:
            return ""
        return result.text or ""
    except Exception as exc:
        logger.debug("Transcription failed in stream: %s", exc)
        return ""
    finally:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass
