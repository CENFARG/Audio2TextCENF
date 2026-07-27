"""@File: audio2text/api/ws/connection_manager.py
@Description: WebSocket connection manager — tracks active connections and broadcasts messages.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class WSConnectionManager:
    """Manages active WebSocket connections.

    Tracks connected clients and provides broadcast capabilities
    for pushing messages (transcription segments, status updates, errors)
    to all connected clients simultaneously.

    Thread-safe for async use via ``asyncio.Lock``.
    """

    def __init__(self) -> None:
        """Initialize an empty connection manager."""
        self._active: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection.

        Args:
            websocket: The connected WebSocket client.
        """
        await websocket.accept()
        async with self._lock:
            self._active.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket client to remove.
        """
        async with self._lock:
            self._active.discard(websocket)
        try:
            await websocket.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    async def broadcast_json(self, message: dict[str, Any]) -> None:
        """Send a JSON message to all connected clients.

        Args:
            message: The dict to serialize and send to each client.
        """
        async with self._lock:
            clients = list(self._active)

        results = await asyncio.gather(
            *[self._send_safe(ws, message) for ws in clients],
            return_exceptions=True,
        )

        # Remove clients that failed to send
        for ws, result in zip(clients, results):
            if isinstance(result, Exception):
                await self.disconnect(ws)

    async def broadcast_bytes(self, data: bytes) -> None:
        """Send binary data to all connected clients.

        Args:
            data: The raw bytes to send to each client.
        """
        async with self._lock:
            clients = list(self._active)

        results = await asyncio.gather(
            *[self._send_bytes_safe(ws, data) for ws in clients],
            return_exceptions=True,
        )

        for ws, result in zip(clients, results):
            if isinstance(result, Exception):
                await self.disconnect(ws)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def active_count(self) -> int:
        """Number of currently connected clients."""
        return len(self._active)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _send_safe(websocket: WebSocket, message: dict[str, Any]) -> None:
        """Send JSON to a single client, raising on failure.

        Args:
            websocket: The target WebSocket client.
            message: The dict to send.
        """
        await websocket.send_json(message)

    @staticmethod
    async def _send_bytes_safe(websocket: WebSocket, data: bytes) -> None:
        """Send bytes to a single client, raising on failure.

        Args:
            websocket: The target WebSocket client.
            data: Raw bytes to send.
        """
        await websocket.send_bytes(data)
