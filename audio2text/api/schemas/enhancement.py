"""@File: audio2text/api/schemas/enhancement.py
@Description: Pydantic schemas for AI text enhancement requests and responses.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EnhanceRequest(BaseModel):
    """Request to enhance a transcription using AI.

    Attributes:
        transcription_id: ID of the transcription to enhance.
        profile: Enhancement intensity — light (punctuation only),
                 medium (grammar + structure), or aggressive (full rewrite).
        provider: AI provider for enhancement — groq or openai.
        block_ids: Optional list of context block IDs to include as context.
    """

    transcription_id: str
    profile: Literal["light", "medium", "aggressive"] = "medium"
    provider: Literal["groq", "openai"] = "groq"
    block_ids: list[str] = Field(default_factory=list)


class EnhanceResponse(BaseModel):
    """Response from an AI enhancement operation.

    Attributes:
        transcription_id: ID of the transcription that was enhanced.
        raw: Original transcription text.
        enhanced: Enhanced/polished text.
        profile: Enhancement profile used.
        provider: AI provider used.
        blocks_used: List of context block IDs that were applied.
        latency_ms: Round-trip latency in milliseconds.
        tokens: Optional token count from the AI provider.
    """

    transcription_id: str
    raw: str
    enhanced: str
    profile: str
    provider: str
    blocks_used: list[str]
    latency_ms: int
    tokens: int | None = None
