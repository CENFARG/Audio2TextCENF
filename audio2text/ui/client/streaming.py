"""@File: audio2text/ui/client/streaming.py
@Description: WebSocket streaming methods for the Audio2Text API client.
    Extracted from api_client.py to keep modules under the 250-line limit.
@Version: 0.17.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import websockets
from websockets.asyncio.client import ClientConnection

_logger = logging.getLogger("ui.client.streaming")


class StreamingMixin:
    """Mixin providing WebSocket streaming methods.

    Requires the host class to provide:
    - ``base_url`` — HTTP(S) base URL.
    - ``_ensure_started()`` — raise if client not ready.
    """

    # Required by mixin — declared for type-checking
    base_url: str

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def _ws_url(self, path: str) -> str:
        """Build a WebSocket URL from a path, converting http→ws.

        Args:
            path: URL path (e.g., ``/api/v1/transcribe/stream``).

        Returns:
            Full WebSocket URL string (e.g., ``ws://127.0.0.1:8765/path``).
        """
        if not path.startswith("/"):
            path = f"/{path}"
        ws_base = self.base_url.replace("http://", "ws://").replace(
            "https://", "wss://"
        )
        return f"{ws_base}{path}"

    # ------------------------------------------------------------------
    # WebSocket connection
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def connect_stream(self) -> AsyncIterator[ClientConnection]:
        """Open a WebSocket connection to the transcribe stream endpoint.

        Returns an async context manager yielding a connected
        ``websockets.ClientConnection``. The connection is automatically
        closed when the context exits.

        Yields:
            A connected WebSocket client.

        Raises:
            ConnectionError: If the WebSocket handshake fails.
        """
        ws_url = self._ws_url("/api/v1/transcribe/stream")
        async with websockets.connect(ws_url) as ws:
            yield ws

    # ------------------------------------------------------------------
    # High-level transcription stream listener
    # ------------------------------------------------------------------

    async def listen_transcription_stream(
        self,
        on_chunk: Callable[[str], Any],
        on_error: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        """Connect to the transcribe WS endpoint and process incoming frames.

        Opens a WebSocket to ``/api/v1/transcribe/stream``, reads JSON
        frames in a loop, and dispatches them:

        * ``"partial"`` / ``"final"`` frames with non-empty text → ``on_chunk(text)``.
        * ``"error"`` frames → ``on_error(error_dict)`` if provided.
        * ``"status"`` frames → logged and skipped.
        * Loop stops when a ``"final"`` frame is received.

        On WebSocket disconnect (``ConnectionError``), one automatic
        reconnect is attempted. If the reconnect also fails, the
        ``ConnectionError`` is re-raised.

        Args:
            on_chunk: Called with each transcription text chunk.
            on_error: Called with the error dict for error frames.

        Raises:
            ConnectionError: If both the initial connection and the
                reconnect attempt fail.
        """
        ws_url = self._ws_url("/api/v1/transcribe/stream")

        async def _read_loop(ws: ClientConnection) -> bool:
            """Read frames from *ws* until final or error. Returns True if clean exit."""
            try:
                while True:
                    raw = await ws.recv()
                    frame = json.loads(raw)
                    ftype = frame.get("type", "")
                    text = frame.get("text")

                    if ftype in ("partial", "final"):
                        if text:
                            on_chunk(text)
                        if frame.get("final") is True:
                            return True
                    elif ftype == "error":
                        error_data = frame.get("error") or {}
                        if on_error is not None:
                            on_error(error_data)
                        return True
                    elif ftype == "status":
                        _logger.debug("Stream status: %s", frame)
                    else:
                        _logger.debug("Unknown frame type: %s", ftype)

            except ConnectionError:
                _logger.warning("WebSocket connection dropped")
                raise

            return True

        # Attempt initial connection
        try:
            async with websockets.connect(ws_url) as ws:
                await _read_loop(ws)
        except ConnectionError:
            _logger.info("Attempting reconnect to %s", ws_url)
            try:
                async with websockets.connect(ws_url) as ws:
                    await _read_loop(ws)
            except ConnectionError:
                _logger.error("Reconnect failed — giving up")
                raise
