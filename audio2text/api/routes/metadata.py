"""@File: audio2text/api/routes/metadata.py
@Description: Metadata endpoints — PUT /api/v1/metadata/:id.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from audio2text.api.dependencies import get_metadata_service

router = APIRouter(prefix="/api/v1", tags=["metadata"])


class MetadataPatch(BaseModel):
    """Request body for updating transcription metadata.

    Attributes:
        emoji: Optional emoji character.
        title: Optional human-readable title.
        tags: Optional list of tags.
        notes: Optional free-form notes.
    """

    emoji: str | None = None
    title: str | None = None
    tags: list[str] | None = None
    notes: str | None = None


@router.put("/metadata/{metadata_id}")
async def update_metadata(
    metadata_id: str,
    patch: MetadataPatch,
    metadata_service: object = Depends(get_metadata_service),
) -> dict[str, Any]:
    """Update metadata fields for a transcription.

    Args:
        metadata_id: The unique transcription identifier.
        patch: A MetadataPatch body with the fields to update.
        metadata_service: Injected MetadataService instance.

    Returns:
        The updated metadata as a dict.

    Raises:
        HTTPException: 404 if the transcription is not found.
    """
    from audio2text.services.metadata_service import MetadataService

    svc: MetadataService = metadata_service  # type: ignore[assignment]

    # Build update kwargs from non-None fields
    updates: dict[str, object] = {}
    if patch.emoji is not None:
        updates["emoji"] = patch.emoji
    if patch.title is not None:
        updates["title"] = patch.title
    if patch.tags is not None:
        updates["tags"] = patch.tags
    if patch.notes is not None:
        updates["notes"] = patch.notes

    result = svc.update(metadata_id, **updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return {
        "id": result.id,
        "filename": result.filename,
        "emoji": result.emoji,
        "title": result.title,
        "tags": result.tags,
        "notes": result.notes,
        "created_at": result.created_at.isoformat(),
        "audio_path": result.audio_path,
    }
