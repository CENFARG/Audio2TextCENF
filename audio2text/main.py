"""@File: audio2text/main.py
@Description: Unified entry point for Audio2Text v0.16.0.
    Starts the FastAPI REST API server in a background thread,
    waits for it to be ready via health check polling,
    then launches the Flet desktop UI.
    On UI close, the server is gracefully shut down.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import threading
import time

import flet as ft
import httpx
import uvicorn

from audio2text.api.app import create_app
from audio2text.ui.app import Audio2TextFletApp


def _wait_for_server(
    base_url: str,
    timeout: float = 30.0,
    interval: float = 0.5,
) -> None:
    """Poll the API health endpoint until the server responds.

    Accepts any HTTP response (including 404) as proof the server is running.
    Retries on connection errors (ConnectError, ConnectTimeout) until timeout.

    Args:
        base_url: Base URL of the API server (e.g. "http://127.0.0.1:8000").
        timeout: Maximum seconds to wait before raising an error.
        interval: Seconds to sleep between health check attempts.

    Raises:
        RuntimeError: If the server does not respond within the timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = httpx.get(f"{base_url}/api/v1/health", timeout=2.0)
            # Any HTTP response means the server is running
            return
        except (httpx.ConnectError, httpx.ConnectTimeout):
            # Server not ready yet — wait and retry
            time.sleep(interval)
        except Exception:
            # Other exceptions (e.g. HTTP errors) — server IS up, return
            return

    raise RuntimeError(
        f"API server failed to start within {timeout}s at {base_url}"
    )


def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Launch Audio2Text — starts API server then Flet UI.

    Orchestration order:
    1. Create FastAPI app and configure uvicorn.
    2. Start server in a daemon background thread.
    3. Poll health endpoint until server is ready.
    4. Launch Flet desktop UI (blocking).
    5. On UI close, signal server to shut down and join the thread.

    Args:
        host: Host address for the API server (default: 127.0.0.1).
        port: Port for the API server (default: 8000).
    """
    # 1. Create FastAPI app and uvicorn config
    app = create_app()
    config = uvicorn.Config(app=app, host=host, port=port, log_level="debug")
    server = uvicorn.Server(config)

    # 2. Start server in a background daemon thread
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # 3. Wait for server to be ready
    base_url = f"http://{host}:{port}"
    _wait_for_server(base_url)

    # 4. Launch Flet UI (blocking until user closes the window)
    flet_app = Audio2TextFletApp(api_base_url=base_url)
    ft.run(flet_app.main)

    # 5. Graceful shutdown — signal server to stop and wait for thread
    server.should_exit = True
    thread.join(timeout=5.0)


if __name__ == "__main__":
    main()
