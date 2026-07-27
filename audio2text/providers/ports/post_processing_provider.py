"""
PostProcessingBlock Protocol — contract for post-transcription block adapters.

Blocks like TaskExtractor, Summary, KeywordExtractor satisfy this Protocol.
Injected as a list into TranscriptionService (Slice 9).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PostProcessingBlock(Protocol):
    """Structural contract for post-transcription processing blocks.

    Each block processes transcription text and returns a BlockResult.
    Blocks are injected into TranscriptionService and executed in order.
    """

    def process(self, text: str) -> Any:
        """Process transcription text and return structured result."""
        ...

    @property
    def name(self) -> str:
        """Unique block identifier (e.g., "task_extractor", "summary")."""
        ...

    @property
    def enabled(self) -> bool:
        """Whether this block is active."""
        ...