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

import argparse
import os
from pathlib import Path

import uvicorn

from audio2text.api.app import create_app

app = create_app()


def _resolve_resource_dir(explicit: str | None) -> Path:
    """Resolve canonical resource dir for history/data.

    Priority: CLI --resource-dir > TAURI_RESOURCE_DIR env > repo root (Path(__file__).parents[1]).
    The Rust sidecar can inject TAURI_RESOURCE_DIR; local dev falls back to repo root.
    """
    if explicit:
        return Path(explicit)
    env = os.environ.get("TAURI_RESOURCE_DIR")
    if env:
        return Path(env)
    # Canonical: repo root is parents[1] from audio2text/main.py
    return Path(__file__).parents[1]


def main() -> None:
    """Start the FastAPI server on 127.0.0.1:8765.

    Accepts --resource-dir or TAURI_RESOURCE_DIR env injected by Tauri Rust.
    Ensures data/history.jsonl resolves canonically as <resource_dir>/data/history.jsonl.
    """
    parser = argparse.ArgumentParser(description="Audio2Text sidecar")
    parser.add_argument("--resource-dir", dest="resource_dir", default=None, help="Canonical resource dir")
    args, _unknown = parser.parse_known_args()

    resource_dir = _resolve_resource_dir(args.resource_dir)
    # Expose for downstream consumers (schema.py, app.py) — single source of truth
    os.environ["TAURI_RESOURCE_DIR"] = str(resource_dir)
    # Ensure data dir exists so history_file Path(resource_dir)/data/history.jsonl never fails on first write
    (resource_dir / "data").mkdir(parents=True, exist_ok=True)

    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
