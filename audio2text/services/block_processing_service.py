"""@File: audio2text/services/block_processing_service.py
@Description: BlockProcessingService — orchestrates context block application.
    Lightweight stub for v0.16.0 — full block processing deferred.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class BlockProcessingService:
    """Stub service for processing context blocks against transcriptions.

    Full implementation deferred to a future version.
    """

    def process(self, text: str, block_ids: list[str]) -> str:
        """Placeholder: returns text unchanged.

        Args:
            text: Input transcription text.
            block_ids: List of context block IDs to apply.

        Returns:
            The input text unchanged (stub).
        """
        logger.debug("BlockProcessingService.process — stub, returning text as-is")
        return text
