"""@File: audio2text/ui/client/api_client.py
@Description: Async HTTP and WebSocket client for the Audio2Text REST API.
    Provides typed methods for every endpoint. Handles connection errors,
    loading states, empty states, and error states consistently.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

import flet as ft
import httpx

from audio2text.ui.client.errors import APIError
from audio2text.ui.client.streaming import StreamingMixin


class APIClient(StreamingMixin):
    """Typed facade for the Audio2Text REST API.

    Designed to be used from Flet components. Every method is async and
    raises ``APIError`` on non-2xx responses. Connection errors (timeout,
    DNS, etc.) are wrapped in ``APIError`` with status 0.

    Usage::

        client = APIClient(base_url="http://127.0.0.1:8765")
        settings = await client.get_settings()
    """

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8765",
        timeout_s: float = 30.0,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url: Root URL of the Audio2Text API (no trailing slash).
            timeout_s: Request timeout in seconds.
        """
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url: str = base_url
        self.timeout_s: float = timeout_s
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        """Build a full URL from a path.

        Args:
            path: URL path, with or without leading slash.

        Returns:
            Full URL string.
        """
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{path}"

    # ------------------------------------------------------------------
    # JSON serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_json(data: dict[str, Any]) -> bytes:
        """Serialize a dict to JSON bytes.

        Args:
            data: Dictionary to serialize.

        Returns:
            JSON-encoded UTF-8 bytes.
        """
        return json.dumps(data, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _from_json(raw: bytes) -> dict[str, Any] | list[dict[str, Any]]:
        """Deserialize JSON bytes to a dict or list.

        Args:
            raw: JSON-encoded UTF-8 bytes.

        Returns:
            Decoded dict or list.
        """
        result: object = json.loads(raw.decode("utf-8"))
        if not isinstance(result, (dict, list)):
            return {}
        return result

    @staticmethod
    def _parse_error_body(raw: bytes, status: int) -> APIError:
        """Parse the standard error body.

        Args:
            raw: Response body bytes.
            status: HTTP status code.

        Returns:
            An APIError instance.
        """
        if not raw:
            return APIError(status_code=status, message="Connection error")
        try:
            body = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            msg = raw.decode("utf-8", errors="replace")
            return APIError(status_code=status, message=msg or "Unknown error")

        return APIError(
            status_code=status,
            message=body.get("message", "Unknown error"),
            code=body.get("code"),
            details=body.get("details"),
        )

    # ------------------------------------------------------------------
    # Visual error display
    # ------------------------------------------------------------------

    @staticmethod
    def show_error(page: ft.Page | None, message: str) -> None:
        """Display an error message to the user via SnackBar.

        Safe to call even when ``page`` is ``None`` (no-op).
        Components call this after catching API or connection errors
        so the user sees a visible failure instead of a silent one.

        Args:
            page: The Flet page reference (or None for defensive no-op).
            message: Human-readable error message to display.
        """
        if page is None:
            return
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_900,
            open=True,
        )
        page.snack_bar = snack
        page.update()

    # ------------------------------------------------------------------
    # Health endpoint
    # ------------------------------------------------------------------

    def get_health(self) -> dict[str, Any]:
        """Fetch backend health status synchronously.

        Returns:
            Health status dict with keys like ``status``, ``version``.

        Raises:
            APIError: On non-2xx or connection failure.
        """
        import httpx

        try:
            response = httpx.get(
                self._url("/api/v1/health"),
                timeout=10.0,
            )
            response.raise_for_status()
            return self._from_json(response.content)
        except httpx.HTTPError as exc:
            raw = getattr(exc, "response", None)
            content = raw.content if raw else b""
            status = raw.status_code if raw else 0
            raise self._parse_error_body(content, status) from exc

    def post(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a POST request synchronously.

        Args:
            path: URL path relative to base_url.
            data: Optional JSON body.

        Returns:
            Parsed JSON response dict.

        Raises:
            APIError: On non-2xx or connection failure.
        """
        import httpx

        try:
            response = httpx.post(
                self._url(path),
                json=data,
                timeout=10.0,
            )
            response.raise_for_status()
            return self._from_json(response.content)
        except httpx.HTTPError as exc:
            raw = getattr(exc, "response", None)
            content = raw.content if raw else b""
            status = raw.status_code if raw else 0
            raise self._parse_error_body(content, status) from exc

    def get(self, path: str) -> dict[str, Any]:
        """Execute a GET request synchronously.

        Args:
            path: URL path relative to base_url.

        Returns:
            Parsed JSON response dict.

        Raises:
            APIError: On non-2xx or connection failure.
        """
        import httpx

        try:
            response = httpx.get(
                self._url(path),
                timeout=10.0,
            )
            response.raise_for_status()
            return self._from_json(response.content)
        except httpx.HTTPError as exc:
            raw = getattr(exc, "response", None)
            content = raw.content if raw else b""
            status = raw.status_code if raw else 0
            raise self._parse_error_body(content, status) from exc

    def put(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a PUT request synchronously.

        Args:
            path: URL path relative to base_url.
            data: Optional JSON body.

        Returns:
            Parsed JSON response dict.

        Raises:
            APIError: On non-2xx or connection failure.
        """
        import httpx

        try:
            response = httpx.put(
                self._url(path),
                json=data,
                timeout=10.0,
            )
            response.raise_for_status()
            return self._from_json(response.content)
        except httpx.HTTPError as exc:
            raw = getattr(exc, "response", None)
            content = raw.content if raw else b""
            status = raw.status_code if raw else 0
            raise self._parse_error_body(content, status) from exc

    def delete(self, path: str) -> None:
        """Execute a DELETE request synchronously.

        Args:
            path: URL path relative to base_url.

        Raises:
            APIError: On non-2xx or connection failure.
        """
        import httpx

        try:
            response = httpx.delete(
                self._url(path),
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raw = getattr(exc, "response", None)
            content = raw.content if raw else b""
            status = raw.status_code if raw else 0
            raise self._parse_error_body(content, status) from exc

    # ------------------------------------------------------------------
    # Typed endpoint methods
    # ------------------------------------------------------------------

    def get_settings(self) -> dict[str, Any]:
        """Fetch current settings from the backend.

        Returns:
            Settings dict. Unwraps ``config`` key if present.
        """
        result = self.get("/api/v1/settings")
        # Backend wraps: {"config": {...}} → unwrap
        config = result.get("config", result)
        # Flatten nested keys for store compatibility
        flat: dict[str, Any] = {}
        providers = config.get("providers")
        if isinstance(providers, dict):
            primary = providers.get("primary")
            if isinstance(primary, str):
                flat["provider"] = primary
        localization = config.get("localization")
        if isinstance(localization, dict):
            lang = localization.get("language")
            if isinstance(lang, str):
                flat["language"] = lang
        flat.update(config)
        return flat

    def update_settings(self, partial: dict[str, Any]) -> dict[str, Any]:
        """Update settings with a partial payload (sync, uses PUT).

        Args:
            partial: Dict with settings keys to update.

        Returns:
            Merged settings dict from the backend.
        """
        return self.put("/api/v1/settings", data={"config": partial})

    def get_context_blocks(self) -> list[dict[str, Any]]:
        """Fetch available context blocks from the backend.

        Returns:
            List of context block dicts.
        """
        result = self.get("/api/v1/context-blocks")
        items = result.get("items", result)
        if isinstance(items, list):
            return items
        return []

    def get_history(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch paginated transcription history.

        Returns:
            List of transcription dicts.
        """
        result = self.get(
            f"/api/v1/transcriptions?limit={limit}&offset={offset}"
        )
        items = result.get("items", result)
        if isinstance(items, list):
            return items
        return []

    def delete_history(self, tx_id: str) -> None:
        """Delete a transcription by ID."""
        self.delete(f"/api/v1/transcriptions/{tx_id}")

    def start_recording(self) -> dict[str, Any]:
        """Signal the backend to start a recording session.

        Returns:
            Dict with session_id and status.
        """
        return self.post("/api/v1/transcribe/start")

    def stop_recording(self) -> dict[str, Any]:
        """Signal the backend to stop the active recording session.

        Returns:
            Dict with session_id and status=stopped.
        """
        return self.post("/api/v1/transcribe/stop")

    def check_for_updates(self) -> dict[str, Any]:
        """Check for available application updates.

        Returns:
            Dict with current_version, has_update, etc.
        """
        return self.get("/api/v1/update/check")

    # ------------------------------------------------------------------
    # Async lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Initialize the async HTTP client (idempotent)."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout_s)

    async def aclose(self) -> None:
        """Close the async HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Async endpoint methods
    # ------------------------------------------------------------------

    async def get_health(self) -> dict[str, Any]:
        """Fetch backend health status asynchronously."""
        await self._ensure_started()
        assert self._client is not None
        try:
            response = await self._client.get(self._url("/api/v1/health"))
            response.raise_for_status()
            return self._from_json(response.content)
        except httpx.HTTPError as exc:
            raise self._map_http_error(exc) from exc

    async def get_settings(self) -> dict[str, Any]:
        """Fetch current settings asynchronously."""
        await self._ensure_started()
        assert self._client is not None
        try:
            response = await self._client.get(self._url("/api/v1/settings"))
            response.raise_for_status()
            result = self._from_json(response.content)
            config = result.get("config", result)
            flat: dict[str, Any] = {}
            providers = config.get("providers")
            if isinstance(providers, dict):
                primary = providers.get("primary")
                if isinstance(primary, str):
                    flat["provider"] = primary
            localization = config.get("localization")
            if isinstance(localization, dict):
                lang = localization.get("language")
                if isinstance(lang, str):
                    flat["language"] = lang
            flat.update(config)
            return flat
        except httpx.HTTPError as exc:
            raise self._map_http_error(exc) from exc

    async def update_settings_async(self, partial: dict[str, Any]) -> dict[str, Any]:
        """Update settings asynchronously (PUT)."""
        await self._ensure_started()
        assert self._client is not None
        try:
            response = await self._client.put(
                self._url("/api/v1/settings"),
                json={"config": partial},
            )
            response.raise_for_status()
            result = self._from_json(response.content)
            config = result.get("config", result)
            return config
        except httpx.HTTPError as exc:
            raise self._map_http_error(exc) from exc

    async def get_context_blocks(self) -> list[dict[str, Any]]:
        """Fetch context blocks asynchronously."""
        await self._ensure_started()
        assert self._client is not None
        try:
            response = await self._client.get(self._url("/api/v1/context-blocks"))
            response.raise_for_status()
            result = self._from_json(response.content)
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                items = result.get("items", result)
                if isinstance(items, list):
                    return items
            return []
        except httpx.HTTPError as exc:
            raise self._map_http_error(exc) from exc

    async def get_history(
        self, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch history asynchronously."""
        await self._ensure_started()
        assert self._client is not None
        try:
            response = await self._client.get(
                self._url(f"/api/v1/transcriptions?limit={limit}&offset={offset}")
            )
            response.raise_for_status()
            result = self._from_json(response.content)
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                items = result.get("items", result)
                if isinstance(items, list):
                    return items
            return []
        except httpx.HTTPError as exc:
            raise self._map_http_error(exc) from exc

    async def delete_history(self, tx_id: str) -> None:
        """Delete a transcription asynchronously."""
        await self._ensure_started()
        assert self._client is not None
        try:
            response = await self._client.delete(
                self._url(f"/api/v1/transcriptions/{tx_id}")
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raw = getattr(exc, "response", None)
            content = raw.content if raw else b""
            status = raw.status_code if raw else 0
            raise self._parse_error_body(content, status) from exc

    async def update_metadata(
        self, tx_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update transcription metadata asynchronously via PUT /metadata/{id}."""
        await self._ensure_started()
        assert self._client is not None
        try:
            response = await self._client.put(
                self._url(f"/api/v1/metadata/{tx_id}"),
                json=data,
            )
            response.raise_for_status()
            return self._from_json(response.content)
        except httpx.HTTPError as exc:
            raw = getattr(exc, "response", None)
            content = raw.content if raw else b""
            status = raw.status_code if raw else 0
            raise self._parse_error_body(content, status) from exc

    async def enhance_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Enhance text asynchronously."""
        await self._ensure_started()
        assert self._client is not None
        try:
            response = await self._client.post(
                self._url("/api/v1/enhance"), json=payload
            )
            response.raise_for_status()
            return self._from_json(response.content)
        except httpx.HTTPError as exc:
            raw = getattr(exc, "response", None)
            content = raw.content if raw else b""
            status = raw.status_code if raw else 0
            raise self._parse_error_body(content, status) from exc

    async def check_for_updates(self) -> dict[str, Any]:
        """Check for available application updates asynchronously.

        Returns:
            Dict with current_version, latest_version, has_update, etc.
        """
        await self._ensure_started()
        assert self._client is not None
        try:
            response = await self._client.get(
                self._url("/api/v1/update/check")
            )
            response.raise_for_status()
            return self._from_json(response.content)
        except httpx.HTTPError as exc:
            raw = getattr(exc, "response", None)
            content = raw.content if raw else b""
            status = raw.status_code if raw else 0
            raise self._parse_error_body(content, status) from exc

    async def start_recording(self) -> dict[str, Any]:
        """Start a recording session asynchronously."""
        return await self._run_sync(self._sync_start_recording)

    async def stop_recording(self) -> None:
        """Stop the active recording session asynchronously."""
        await self._ensure_started()
        assert self._client is not None
        try:
            response = await self._client.post(
                self._url("/api/v1/transcribe/stop")
            )
            if response.status_code != 204:
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raw = getattr(exc, "response", None)
            content = raw.content if raw else b""
            status = raw.status_code if raw else 0
            raise self._parse_error_body(content, status) from exc

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _ensure_started(self) -> None:
        """Ensure the async client is started (auto-starts if needed)."""
        if self._client is None:
            await self.start()

    @staticmethod
    def _map_http_error(exc: httpx.HTTPError) -> APIError:
        """Map an httpx error to an APIError, preserving connection messages."""
        raw = getattr(exc, "response", None)
        if raw is not None:
            return APIClient._parse_error_body(raw.content, raw.status_code)
        # Connection errors: use the exception message
        msg = str(exc) or "Connection error"
        return APIError(status_code=0, message=msg)

    def _sync_start_recording(self) -> dict[str, Any]:
        """Sync version of start_recording (used in async wrapper)."""
        return self.post("/api/v1/transcribe/start")

    async def _run_sync(self, fn: Any) -> Any:
        """Run a sync method in a thread to not block the event loop."""
        await self._ensure_started()
        return await asyncio.to_thread(fn)
