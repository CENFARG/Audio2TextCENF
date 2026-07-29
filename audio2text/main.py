"""@File: audio2text/main.py
@Description: Sidecar entry point for Audio2Text v0.16.0.
    Starts the FastAPI REST API server. Designed to be launched by
    the Tauri v2 Rust sidecar as a compiled PyInstaller/Nuitka binary.
    No UI dependencies — frontend is Tauri v2 + Svelte 5.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import uvicorn

from audio2text.api.app import create_app

app = create_app()


def main() -> None:
    """Start the FastAPI server on 127.0.0.1:8765."""
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
