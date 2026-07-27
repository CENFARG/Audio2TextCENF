"""@File: audio2text/api/routes/transcriptions.py
@Description: Transcription history endpoints — GET/DELETE /api/v1/transcriptions.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from audio2text.api.dependencies import get_metadata_service

router = APIRouter(prefix="/api/v1", tags=["transcriptions"])


@router.get("/transcriptions")
async def list_transcriptions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    metadata_service: object = Depends(get_metadata_service),
) -> dict[str, Any]:
    """List transcription history entries.

    Args:
        limit: Maximum number of items to return.
        offset: Number of items to skip.
        metadata_service: Injected MetadataService instance.

    Returns:
        A dict with items list, total count, limit, and offset.
    """
    from audio2text.services.metadata_service import MetadataService

    svc: MetadataService = metadata_service  # type: ignore[assignment]

    all_entries = svc.list_all()
    total = len(all_entries)

    # Apply pagination
    page = all_entries[offset : offset + limit]
    items: list[dict[str, object]] = []
    for entry in page:
        items.append({
            "id": entry.id,
            "filename": entry.filename,
            "emoji": entry.emoji,
            "title": entry.title,
            "tags": entry.tags,
            "notes": entry.notes,
            "created_at": entry.created_at.isoformat(),
            "audio_path": entry.audio_path,
            "provider": getattr(entry, "provider", None),
            "duration_s": getattr(entry, "duration_s", None),
            "text": getattr(entry, "text", None),
        })

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.delete("/transcriptions/{transcription_id}", status_code=204)
async def delete_transcription(
    transcription_id: str,
    metadata_service: object = Depends(get_metadata_service),
) -> None:
    """Delete a transcription entry.

    Args:
        transcription_id: The unique transcription identifier.
        metadata_service: Injected MetadataService instance.

    Raises:
        HTTPException: 404 if the transcription is not found.
    """
    from audio2text.services.metadata_service import MetadataService

    svc: MetadataService = metadata_service  # type: ignore[assignment]

    deleted = svc.delete(transcription_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transcription not found")
