import hashlib

from backend.audio_chunker import transcribe_chunks
from backend.transcriber import OperationTracker, build_operation_envelope


def test_operation_event_contract_and_terminal_state():
    tracker = OperationTracker(operation_id="op-1")
    tracker.event("api", "Hola")
    tracker.event("response", "Hola")
    assert tracker.operation_id == "op-1"
    event = tracker.events[-1]
    assert event["operation_id"] == "op-1"
    assert event["event_type"] == "response"
    assert event["text_sha256"] == hashlib.sha256("Hola".encode()).hexdigest()
    assert tracker.finish("displayed") is True
    assert tracker.finish("displayed") is False
    assert tracker.state == "displayed"


def test_retry_is_attempt_not_new_operation():
    tracker = OperationTracker(operation_id="op-1")
    tracker.event("api", "Hola", attempt=1)
    tracker.event("failed", "", attempt=1)
    tracker.event("api", "Hola", attempt=2)
    assert {event["operation_id"] for event in tracker.events} == {"op-1"}
    assert [event["attempt"] for event in tracker.events if event["event_type"] == "api"] == [1, 2]


def test_chunk_aggregation_is_single_and_removes_overlap(monkeypatch):
    monkeypatch.setattr("backend.audio_chunker.split_audio_on_silence", lambda *args, **kwargs: [[1], [2]])
    calls = []

    def api_call(chunk, prompt=None):
        calls.append(chunk)
        return "uno dos" if len(calls) == 1 else "dos tres"

    result = transcribe_chunks([1, 2], 1, api_call, operation_id="op-1")
    assert result == "uno dos tres"


def test_duplicate_callback_and_display_are_observable_and_rejected():
    tracker = OperationTracker(operation_id="op-1")
    assert tracker.claim("callback") is True
    assert tracker.claim("callback") is False
    assert tracker.events[-1]["event_type"] == "rejected_duplicate"


def test_operation_envelope_has_explicit_identity():
    envelope = build_operation_envelope("op-1", "Hola", attempt=2)
    assert envelope["operation_id"] == "op-1"
    assert envelope["text"] == "Hola"
    assert envelope["attempt"] == 2
