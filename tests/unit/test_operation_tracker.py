"""Tests for audio2text.services.operation_tracker — exactly-once operation tracking."""

from __future__ import annotations

import time

import pytest

from audio2text.services.operation_tracker import (
    OperationState,
    OperationTracker,
    OperationRegistry,
    TranscriptionFailure,
    text_sha256,
)


class TestTextSha256:
    """Tests for text hashing."""

    def test_deterministic(self):
        """Same text should produce same hash."""
        h1 = text_sha256("hello world")
        h2 = text_sha256("hello world")
        assert h1 == h2

    def test_normalized(self):
        """Text with different whitespace should hash the same."""
        h1 = text_sha256("hello  world")
        h2 = text_sha256("hello world")
        assert h1 == h2

    def test_empty(self):
        """Empty text should hash without error."""
        h = text_sha256("")
        assert len(h) == 64  # SHA-256 hex digest

    def test_different_texts(self):
        """Different texts should produce different hashes."""
        h1 = text_sha256("hello")
        h2 = text_sha256("world")
        assert h1 != h2


class TestOperationTracker:
    """Tests for OperationTracker state machine."""

    def test_creation(self):
        """Tracker should start in PENDING state."""
        op = OperationTracker()
        assert op.state == OperationState.PENDING
        assert op.operation_id is not None
        assert len(op.operation_id) == 36  # UUID format

    def test_custom_id(self):
        """Tracker should accept custom operation ID."""
        op = OperationTracker(operation_id="custom-123")
        assert op.operation_id == "custom-123"

    def test_claim_success(self):
        """First claim on a stage should succeed."""
        op = OperationTracker()
        assert op.claim("transcription") is True

    def test_claim_duplicate_rejected(self):
        """Duplicate claim on same stage should be rejected."""
        op = OperationTracker()
        assert op.claim("transcription") is True
        assert op.claim("transcription") is False

    def test_claim_different_stages(self):
        """Claims on different stages should all succeed."""
        op = OperationTracker()
        assert op.claim("transcription") is True
        assert op.claim("pipeline") is True
        assert op.claim("metadata") is True

    def test_finish_completed(self):
        """Finishing with COMPLETED state should succeed."""
        op = OperationTracker()
        assert op.finish(OperationState.COMPLETED) is True
        assert op.state == OperationState.COMPLETED
        assert op.completed_at is not None

    def test_finish_failed(self):
        """Finishing with FAILED state should succeed."""
        op = OperationTracker()
        assert op.finish(OperationState.FAILED) is True
        assert op.state == OperationState.FAILED

    def test_finish_cancelled(self):
        """Finishing with CANCELLED state should succeed."""
        op = OperationTracker()
        assert op.finish(OperationState.CANCELLED) is True
        assert op.state == OperationState.CANCELLED

    def test_finish_invalid_state(self):
        """Finishing with PENDING state should fail."""
        op = OperationTracker()
        assert op.finish(OperationState.PENDING) is False

    def test_finish_already_completed(self):
        """Finishing an already-completed operation should fail."""
        op = OperationTracker()
        assert op.finish(OperationState.COMPLETED) is True
        assert op.finish(OperationState.COMPLETED) is False

    def test_claim_after_finish_rejected(self):
        """Claims after operation is finished should be rejected."""
        op = OperationTracker()
        op.finish(OperationState.COMPLETED)
        assert op.claim("new_stage") is False

    def test_event_recording(self):
        """Events should be recorded in history."""
        op = OperationTracker()
        op.event("started")
        op.event("chunk_transcribed", chunk_index=0)
        assert len(op.events) == 2
        assert op.events[0]["event_type"] == "started"
        assert op.events[1]["chunk_index"] == 0

    def test_event_history_bounded(self):
        """Event history should be bounded by max_events."""
        op = OperationTracker(max_events=10)
        for i in range(20):
            op.event(f"event_{i}")
        assert len(op.events) == 10
        # Should contain the last 10 events
        assert op.events[0]["event_type"] == "event_10"

    def test_duration_ms(self):
        """Duration should be computed from creation to completion."""
        op = OperationTracker()
        time.sleep(0.01)
        op.finish(OperationState.COMPLETED)
        assert op.duration_ms > 0

    def test_repr(self):
        """String representation should be useful for debugging."""
        op = OperationTracker()
        r = repr(op)
        assert "OperationTracker" in r
        assert op.operation_id[:8] in r


class TestOperationRegistry:
    """Tests for OperationRegistry."""

    def test_create_operation(self):
        """Creating an operation should add it to registry."""
        reg = OperationRegistry()
        op = reg.create()
        assert op.operation_id in reg._operations
        assert reg.total_count == 1

    def test_get_operation(self):
        """Getting an operation by ID should return it."""
        reg = OperationRegistry()
        op = reg.create(operation_id="test-123")
        found = reg.get("test-123")
        assert found is op

    def test_get_nonexistent(self):
        """Getting a nonexistent operation should return None."""
        reg = OperationRegistry()
        assert reg.get("nonexistent") is None

    def test_cleanup_old_operations(self):
        """Old completed operations should be cleaned up when over limit."""
        reg = OperationRegistry(max_operations=5)
        # Create 10 operations
        ops = []
        for _ in range(10):
            op = reg.create()
            op.finish(OperationState.COMPLETED)
            ops.append(op)
        # Should have cleaned up to max
        assert reg.total_count <= 5

    def test_active_count(self):
        """Active count should reflect non-terminal operations."""
        reg = OperationRegistry()
        op1 = reg.create()
        op2 = reg.create()
        op1.finish(OperationState.COMPLETED)
        assert reg.active_count == 1

    def test_repr(self):
        """String representation should be useful for debugging."""
        reg = OperationRegistry()
        op = reg.create()
        r = repr(op)
        assert "OperationTracker" in r


class TestTranscriptionFailure:
    """Tests for TranscriptionFailure dataclass."""

    def test_creation(self):
        """Failure should store code, message, and recoverable flag."""
        f = TranscriptionFailure(
            code="client_unavailable",
            message="Groq client is not initialized",
            recoverable=True,
        )
        assert f.code == "client_unavailable"
        assert f.recoverable is True

    def test_default_recoverable(self):
        """Default recoverable should be True."""
        f = TranscriptionFailure(code="test", message="test")
        assert f.recoverable is True
