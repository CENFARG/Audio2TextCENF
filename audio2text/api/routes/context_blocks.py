"""@File: audio2text/api/routes/context_blocks.py
@Description: Context blocks endpoint — GET /api/v1/context-blocks.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from audio2text.api.dependencies import get_block_loader

router = APIRouter(prefix="/api/v1", tags=["context-blocks"])


@router.get("/context-blocks")
async def list_context_blocks(
    block_loader: object = Depends(get_block_loader),
) -> dict[str, Any]:
    """List available context blocks from the configured Grama directory.

    Returns each block's id, name, description, and hotkey.
    Falls back to an empty list if the blocks directory is not configured.

    Args:
        block_loader: Injected BlockLoaderService instance.

    Returns:
        A dict with items list and directory path.
    """
    from audio2text.services.block_loader_service import BlockLoaderService

    svc: BlockLoaderService = block_loader  # type: ignore[assignment]
    blocks = svc.load_blocks()

    return {
        "items": [
            {
                "id": b.id,
                "name": b.name,
                "description": b.description,
                "hotkey": b.hotkey,
            }
            for b in blocks
        ],
        "directory": str(svc._blocks_dir),
    }
