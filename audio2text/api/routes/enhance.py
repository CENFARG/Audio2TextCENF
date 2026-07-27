"""@File: audio2text/api/routes/enhance.py
@Description: AI enhancement endpoint — POST /api/v1/enhance.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from audio2text.api.dependencies import get_ai_enhancement, get_metadata_service
from audio2text.api.schemas.enhancement import EnhanceRequest, EnhanceResponse

router = APIRouter(prefix="/api/v1", tags=["enhance"])


@router.post("/enhance", response_model=EnhanceResponse)
async def enhance_text(
    request: EnhanceRequest,
    ai_service: object = Depends(get_ai_enhancement),
    metadata_service: object = Depends(get_metadata_service),
) -> EnhanceResponse:
    """Enhance a transcription using AI.

    Applies the selected enhancement profile to the given transcription.
    Metadata is updated with enhancement results.

    Args:
        request: Enhancement request with transcription_id, profile, provider, block_ids.
        ai_service: Injected AIEnhancementService instance.
        metadata_service: Injected MetadataService instance.

    Returns:
        An EnhanceResponse with raw and enhanced text.

    Raises:
        HTTPException: 404 if transcription not found.
        HTTPException: 503 if AI service is unavailable.
    """
    import time

    from audio2text.services.ai_enhancement_service import (
        AIEnhancementService,
        EnhancementProfile,
    )
    from audio2text.services.metadata_service import MetadataService

    ai: AIEnhancementService = ai_service  # type: ignore[assignment]
    meta: MetadataService = metadata_service  # type: ignore[assignment]

    if not ai.is_available():
        raise HTTPException(status_code=503, detail="AI enhancement service unavailable")

    # Retrieve original text from metadata
    entry = meta.get(request.transcription_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Transcription not found")

    # Map string profile to enum
    profile_map = {
        "light": EnhancementProfile.LIGHT,
        "medium": EnhancementProfile.MEDIUM,
        "aggressive": EnhancementProfile.AGGRESSIVE,
    }
    profile = profile_map.get(request.profile, EnhancementProfile.MEDIUM)

    # Original text might be stored in notes or we need the transcription text
    original_text = entry.notes or entry.title or "No text available"

    start = time.monotonic()
    enhanced_text = ai.enhance(original_text, profile=profile)
    latency_ms = int((time.monotonic() - start) * 1000)

    return EnhanceResponse(
        transcription_id=request.transcription_id,
        raw=original_text,
        enhanced=enhanced_text,
        profile=request.profile,
        provider=request.provider,
        blocks_used=request.block_ids,
        latency_ms=latency_ms,
    )
