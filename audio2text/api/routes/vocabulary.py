"""@File: audio2text/api/routes/vocabulary.py
@Description: Vocabulary endpoints — GET/POST/DELETE /api/v1/vocabulary.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from audio2text.api.dependencies import get_vocabulary_service

router = APIRouter(prefix="/api/v1", tags=["vocabulary"])


class VocabEntryBody(BaseModel):
    """Request body for adding a vocabulary correction.

    Attributes:
        word: The word or phrase to replace.
        correction: The replacement text.
        category: Category label (default "custom").
    """

    word: str
    correction: str
    category: str = "custom"


class VocabEntryResponse(BaseModel):
    """Response body for a single vocabulary entry.

    Attributes:
        word: The word or phrase.
        correction: The replacement text.
        category: Category label.
        enabled: Whether the entry is active.
    """

    word: str
    correction: str
    category: str
    enabled: bool = True


@router.get("/vocabulary")
async def list_vocabulary(
    vocab_service: object = Depends(get_vocabulary_service),
) -> dict[str, Any]:
    """List all vocabulary correction entries.

    Args:
        vocab_service: Injected VocabularyService instance.

    Returns:
        A dict with the entries list.
    """
    from audio2text.services.vocabulary_service import VocabularyService

    svc: VocabularyService = vocab_service  # type: ignore[assignment]
    entries = svc.get_entries()

    return {
        "entries": [
            {
                "word": e.word,
                "correction": e.correction,
                "category": e.category,
                "enabled": e.enabled,
            }
            for e in entries
        ]
    }


@router.post("/vocabulary", response_model=VocabEntryResponse)
async def add_vocabulary(
    entry: VocabEntryBody,
    vocab_service: object = Depends(get_vocabulary_service),
) -> VocabEntryResponse:
    """Add or update a vocabulary correction entry.

    Args:
        entry: The vocabulary entry to add/update.
        vocab_service: Injected VocabularyService instance.

    Returns:
        The created/updated entry.
    """
    from audio2text.services.vocabulary_service import VocabularyService

    svc: VocabularyService = vocab_service  # type: ignore[assignment]
    svc.add_entry(entry.word, entry.correction, entry.category)

    return VocabEntryResponse(
        word=entry.word,
        correction=entry.correction,
        category=entry.category,
        enabled=True,
    )


@router.delete("/vocabulary/{word}")
async def delete_vocabulary(
    word: str,
    vocab_service: object = Depends(get_vocabulary_service),
) -> dict[str, str]:
    """Remove a vocabulary correction entry.

    Args:
        word: The word to remove (case-insensitive).
        vocab_service: Injected VocabularyService instance.

    Returns:
        A success message.

    Raises:
        HTTPException: 404 if the entry doesn't exist.
    """
    from audio2text.services.vocabulary_service import VocabularyService

    svc: VocabularyService = vocab_service  # type: ignore[assignment]
    removed = svc.remove_entry(word)
    if not removed:
        raise HTTPException(status_code=404, detail="Vocabulary entry not found")

    return {"status": "deleted", "word": word}
