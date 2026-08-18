"""@File: audio2text/services/operation_tracker.py
@Description: OperationTracker — bounded, correlation-aware state machine for
    tracking transcription operations. Prevents duplicate processing and provides
    observability into the transcription pipeline.
@Version: 0.16.0
@Author: Audio2Text Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class OperationState(str, Enum):
    """Valid states for a transcription operation."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TranscriptionFailure:
    """Recoverable, UI-safe description of the last failed transcription."""

    code: str
    message: str
    recoverable: bool = True


def _normalized_text(text: str) -> str:
    """Normalize text for consistent hashing."""
    return " ".join(str(text or "").split())


def text_sha256(text: str) -> str:
    """SHA-256 hash of normalized text for deduplication."""
    return hashlib.sha256(_normalized_text(text).encode("utf-8")).hexdigest()


class OperationTracker:
    """Bounded, correlation-aware state machine for one user operation.

    Tracks the lifecycle of a transcription operation from start to finish,
    preventing duplicate processing and providing event history for debugging.

    Invariants:
    - An operation can only transition to COMPLETED or FAILED from PENDING.
    - Duplicate claims on the same stage are rejected.
    - Event history is bounded (max_events) to prevent memory leaks.
    """

    def __init__(
        self,
        operation_id: Optional[str] = None,
        max_events: int = 256,
    ) -> None:
        """Initialize the operation tracker.

        Args:
            operation_id: Optional UUID. Generated if not provided.
            max_events: Maximum events to retain in history.
        """
        self.operation_id: str = operation_id or str(uuid.uuid4())
        self.state: OperationState = OperationState.PENDING
        self.events: deque = deque(maxlen=max_events)
        self._claims: set[str] = set()
        self.created_at: float = time.time()
        self.completed_at: Optional[float] = None

    def event(
        self,
        event_type: str,
        text: str = "",
        chunk_index: Optional[int] = None,
        attempt: Optional[int] = None,
    ) -> dict:
        """Record an event in the operation history.

        Args:
            event_type: Type of event (e.g., "started", "chunk_transcribed").
            text: Optional text content (hashed for privacy).
            chunk_index: Optional chunk index for chunked transcription.
            attempt: Optional attempt number for retries.

        Returns:
            The event dict that was recorded.
        """
        event_data = {
            "operation_id": self.operation_id,
            "event_type": event_type,
            "text_sha256": text_sha256(text),
            "timestamp": time.time(),
        }
        if chunk_index is not None:
            event_data["chunk_index"] = chunk_index
        if attempt is not None:
            event_data["attempt"] = attempt
        self.events.append(event_data)
        return event_data

    def claim(self, stage: str, text: str = "", chunk_index: Optional[int] = None, attempt: Optional[int] = None) -> bool:
        """Claim a processing stage (exactly-once semantics).

        If the stage has already been claimed or the operation is in a
        terminal state, the claim is rejected.

        Args:
            stage: Stage name to claim (e.g., "transcription", "pipeline").
            text: Optional text content.
            chunk_index: Optional chunk index.
            attempt: Optional attempt number.

        Returns:
            True if claim succeeded, False if rejected.
        """
        if stage in self._claims or self.state in {OperationState.COMPLETED, OperationState.FAILED, OperationState.CANCELLED}:
            self.event("rejected_duplicate", text, chunk_index, attempt)
            logger.debug(
                "Operation %s: rejected duplicate claim on stage '%s'",
                self.operation_id,
                stage,
            )
            return False
        self._claims.add(stage)
        self.event(stage, text, chunk_index, attempt)
        return True

    def finish(
        self,
        state: OperationState,
        text: str = "",
        attempt: Optional[int] = None,
    ) -> bool:
        """Mark the operation as finished.

        Only allows transition to COMPLETED, FAILED, or CANCELLED from PENDING.

        Args:
            state: Final state (must be terminal).
            text: Optional final text.
            attempt: Optional attempt number.

        Returns:
            True if finish succeeded, False if state transition invalid.
        """
        if state not in {OperationState.COMPLETED, OperationState.FAILED, OperationState.CANCELLED}:
            logger.warning(
                "Operation %s: invalid finish state '%s'",
                self.operation_id,
                state,
            )
            return False
        if self.state != OperationState.PENDING:
            self.event("rejected_duplicate", text, attempt=attempt)
            logger.debug(
                "Operation %s: rejected finish from state '%s'",
                self.operation_id,
                self.state,
            )
            return False

        self.state = state
        self.completed_at = time.time()
        self.event(f"finished_{state.value}", text, attempt=attempt)
        return True

    @property
    def duration_ms(self) -> float:
        """Operation duration in milliseconds (or 0 if not completed)."""
        if self.completed_at is None:
            return 0.0
        return (self.completed_at - self.created_at) * 1000.0

    def __repr__(self) -> str:
        return (
            f"OperationTracker(id={self.operation_id[:8]}, "
            f"state={self.state.value}, events={len(self.events)})"
        )


class OperationRegistry:
    """Registry for tracking multiple concurrent operations.

    Provides bounded storage with automatic cleanup of old completed operations.
    """

    def __init__(self, max_operations: int = 100) -> None:
        """Initialize the registry.

        Args:
            max_operations: Maximum operations to retain (oldest completed removed).
        """
        self._operations: dict[str, OperationTracker] = {}
        self._max_operations = max_operations

    def create(self, operation_id: Optional[str] = None) -> OperationTracker:
        """Create and register a new operation.

        Args:
            operation_id: Optional UUID. Generated if not provided.

        Returns:
            The new OperationTracker instance.
        """
        tracker = OperationTracker(operation_id=operation_id)
        self._operations[tracker.operation_id] = tracker
        self._cleanup()
        return tracker

    def get(self, operation_id: str) -> OperationTracker | None:
        """Get an operation by ID."""
        return self._operations.get(operation_id)

    def _cleanup(self) -> None:
        """Remove oldest completed operations if over limit."""
        if len(self._operations) <= self._max_operations:
            return

        # Find completed operations sorted by completion time
        completed = [
            (oid, op)
            for oid, op in self._operations.items()
            if op.state in {OperationState.COMPLETED, OperationState.FAILED, OperationState.CANCELLED}
            and op.completed_at is not None
        ]
        completed.sort(key=lambda x: x[1].completed_at)

        # Remove oldest until under limit
        to_remove = len(self._operations) - self._max_operations
        for oid, _ in completed[:to_remove]:
            del self._operations[oid]
            logger.debug("Cleaned up old operation %s", oid)

    @property
    def active_count(self) -> int:
        """Number of active (non-terminal) operations."""
        return sum(
            1
            for op in self._operations.values()
            if op.state == OperationState.PENDING
        )

    @property
    def total_count(self) -> int:
        """Total operations in registry."""
        return len(self._operations)
