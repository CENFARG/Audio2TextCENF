"""
Unit tests for the A4 Prompter Gate (headless, no Tk).

Covers the pure pieces of backend/prompter_gate.py plus the headless glue of
the Supervisor mixin prompter flow (Tk widgets stay by inspection + smoke):
- evaluate_draft gate heuristics: empty / short / long / points / imperative,
  threshold boundaries and custom thresholds
- build_prompter_messages structure: system/user roles, blocks, target note
- strip_markdown_fences
- select_block_bodies (entry-id order resolution)
- PrompterRunner: injected llm_fn flow, one pass at a time per entry
- PrompterGate: config-driven facade
- full flush -> gate -> pass -> replacement flow against a real
  SupervisorStore with fake textboxes (replacement + store update)
"""

import sys
import threading
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from backend.context_blocks import ContextBlock
from backend.prompter_gate import (
    DEFAULT_MIN_CHARS,
    DEFAULT_MIN_POINTS,
    GateDecision,
    PrompterGate,
    PrompterRunner,
    load_prompter_system_prompt,
    build_prompter_messages,
    evaluate_draft,
    select_block_bodies,
    strip_markdown_fences,
)
from backend.supervisor_store import SupervisorStore
from ui.views.supervisor_view import SupervisorViewMixin

EIGHT_POINTS = "\n".join(f"{i}. punto {i}" for i in range(1, 9))


@pytest.mark.unit
class TestEvaluateDraft:
    """A4 gate heuristics: empty / points / length / imperative."""

    def test_whitespace_only_is_empty_and_never_triggers(self):
        # Assert: spec contract — empty draft reports "empty", no trigger
        for text in ("", "   ", "\n\t \n"):
            decision = evaluate_draft(text)
            assert decision.trigger is False
            assert decision.reasons == ["empty"]

    def test_short_plain_draft_does_not_trigger(self):
        # Act
        decision = evaluate_draft("Hola, esto es una correccion corta.")

        # Assert: below every threshold -> silent no-trigger
        assert decision.trigger is False
        assert decision.reasons == []

    def test_long_draft_triggers_length_reason(self):
        # Arrange: 2400 chars of plain prose
        decision = evaluate_draft("palabra " * 300)

        # Assert
        assert decision.trigger is True
        assert "length" in decision.reasons

    def test_length_boundary_respects_min_chars(self):
        # Act / Assert: exactly at the default boundary (1200)
        assert "length" not in evaluate_draft("a" * (DEFAULT_MIN_CHARS - 1)).reasons
        decision = evaluate_draft("a" * DEFAULT_MIN_CHARS)
        assert decision.trigger is True
        assert "length" in decision.reasons

    def test_length_uses_stripped_text(self):
        # Padding whitespace does not count toward the length threshold
        padded = " " * 500 + "a" * (DEFAULT_MIN_CHARS - 1) + " " * 500

        # Act / Assert
        assert "length" not in evaluate_draft(padded).reasons

    def test_eight_points_trigger(self):
        # Act
        decision = evaluate_draft(EIGHT_POINTS)

        # Assert
        assert decision.trigger is True
        assert "points" in decision.reasons

    def test_points_boundary_seven_vs_eight(self):
        # Arrange: exactly one point below the default threshold
        seven = "\n".join(f"{i}. punto" for i in range(1, 8))

        # Act / Assert
        assert evaluate_draft(seven).trigger is False
        assert "points" in evaluate_draft(EIGHT_POINTS).reasons

    def test_bullets_numbered_and_letters_count_as_points(self):
        # Arrange: bullets (- * •), "N." / "N)" and lettered lists all count
        lines = [
            "- uno",
            "* dos",
            "• tres",
            "1) cuatro",
            "2. cinco",
            "10. seis",
            "3) siete",
            "b) ocho",
        ]

        # Act / Assert
        assert "points" in evaluate_draft("\n".join(lines)).reasons

    def test_custom_thresholds_are_honored(self):
        # Arrange
        two_points = "- uno\n- dos"

        # Act / Assert: defaults keep it silent, lowered thresholds fire
        assert evaluate_draft(two_points).trigger is False
        assert "points" in evaluate_draft(two_points, min_points=2).reasons
        assert "length" in evaluate_draft("hola", min_chars=1).reasons

    def test_multiple_imperative_sentences_trigger(self):
        # Arrange: 3 sentences starting with instruction verbs (voseo forms)
        decision = evaluate_draft("Creá el archivo. Revisá la salida. Corregí el bug.")

        # Assert
        assert decision.trigger is True
        assert "imperative" in decision.reasons

    def test_few_imperative_sentences_do_not_trigger(self):
        # Only one imperative sentence — below IMPERATIVE_MIN_SENTENCES
        decision = evaluate_draft("Creá el archivo. Después avisame como te fue.")

        # Act / Assert
        assert "imperative" not in decision.reasons
        assert decision.trigger is False

    def test_combined_reasons_listed_together(self):
        # Arrange: 8 points AND long prose
        text = EIGHT_POINTS + " " + "palabra " * 200

        # Act
        reasons = evaluate_draft(text).reasons

        # Assert
        assert "points" in reasons
        assert "length" in reasons

    def test_decision_is_a_gate_decision_dataclass(self):
        # Act / Assert
        assert isinstance(evaluate_draft(""), GateDecision)
        assert isinstance(evaluate_draft("borrador").reasons, list)
        assert DEFAULT_MIN_POINTS == 8
        assert DEFAULT_MIN_CHARS == 1200


@pytest.mark.unit
class TestBuildPrompterMessages:
    """Prompt assembly: system expert + user draft (+ blocks, + note)."""

    def test_returns_system_and_user_roles(self):
        # Act
        messages = build_prompter_messages("borrador", [], None)

        # Assert
        assert [m["role"] for m in messages] == ["system", "user"]

    def test_system_message_is_the_prompter_expert(self):
        # Assert: the system message IS the canonical versioned prompt (A4
        # integration) and keeps the single-source + draft-language rules.
        expected = load_prompter_system_prompt()
        assert "única fuente de contenido" in expected
        assert "idioma" in expected
        assert build_prompter_messages("borrador", [], None)[0]["content"] == expected

    def test_user_message_contains_the_draft(self):
        # Act / Assert
        content = build_prompter_messages("el borrador de prueba", [], None)[1]["content"]
        assert "el borrador de prueba" in content

    def test_block_bodies_included_as_context(self):
        # Arrange
        blocks = [
            ContextBlock(id="a", name="A", body="CUERPO-A"),
            ContextBlock(id="b", name="B", body="CUERPO-B"),
        ]

        # Act
        content = build_prompter_messages("borrador", blocks, None)[1]["content"]

        # Assert
        assert "CUERPO-A" in content
        assert "CUERPO-B" in content

    def test_empty_blocks_add_no_block_section(self):
        # Act / Assert
        content = build_prompter_messages("borrador", [], None)[1]["content"]
        assert "BLOQUES DE CONTEXTO" not in content

    def test_target_note_included_when_given(self):
        # Act / Assert
        content = build_prompter_messages("borrador", [], "nota destino")[1]["content"]
        assert "nota destino" in content
        assert "NOTA DESTINO" in content

    def test_target_note_none_adds_no_note_section(self):
        # Act / Assert
        content = build_prompter_messages("borrador", [], None)[1]["content"]
        assert "NOTA DESTINO" not in content


@pytest.mark.unit
class TestStripMarkdownFences:
    """LLM-output fence stripper."""

    def test_plain_text_unchanged(self):
        # Act / Assert
        assert strip_markdown_fences("hola mundo") == "hola mundo"

    def test_simple_fence_removed(self):
        # Act / Assert
        assert strip_markdown_fences("```\ncontenido\n```") == "contenido"

    def test_language_tag_removed(self):
        # Act / Assert
        assert strip_markdown_fences("```markdown\n# Titulo\n```") == "# Titulo"

    def test_surrounding_whitespace_trimmed(self):
        # Act / Assert
        assert strip_markdown_fences("  \n```\n texto \n```\n  ") == "texto"

    def test_unbalanced_opening_fence_removed(self):
        # Act / Assert
        assert strip_markdown_fences('```json\n{"a": 1}') == '{"a": 1}'


@pytest.mark.unit
class TestSelectBlockBodies:
    """Entry block-id -> loaded block resolution (entry order, dedup)."""

    @staticmethod
    def _blocks():
        return [
            ContextBlock(id="alpha", name="Alpha", body="A"),
            ContextBlock(id="bravo", name="Bravo", body="B"),
            ContextBlock(id="charlie", name="Charlie", body="C"),
        ]

    def test_selects_in_entry_order(self):
        # Act / Assert: entry insertion order, NOT loaded (name) order
        selected = select_block_bodies(self._blocks(), ["charlie", "alpha"])
        assert [b.id for b in selected] == ["charlie", "alpha"]

    def test_unknown_ids_ignored_and_duplicates_deduped(self):
        # Act / Assert
        selected = select_block_bodies(self._blocks(), ["bravo", "ghost", "bravo"])
        assert [b.id for b in selected] == ["bravo"]

    def test_empty_ids_or_blocks_select_nothing(self):
        # Act / Assert
        assert select_block_bodies(self._blocks(), []) == []
        assert select_block_bodies([], ["alpha"]) == []


class _RunnerCallbacks:
    """Capture runner outcomes with an event for deterministic waits."""

    def __init__(self):
        self.event = threading.Event()
        self.done = []
        self.errors = []

    def on_done(self, number, text):
        self.done.append((number, text))
        self.event.set()

    def on_error(self, number, error):
        self.errors.append((number, error))
        self.event.set()


@pytest.mark.unit
class TestPrompterRunner:
    """Injected llm_fn flow: worker delivery + one pass at a time per entry."""

    def test_start_runs_llm_and_delivers_stripped_text(self):
        # Arrange
        calls = []
        callbacks = _RunnerCallbacks()
        runner = PrompterRunner(
            llm_fn=lambda messages: (calls.append(messages), "```\nestructura\n```")[1]
        )

        # Act
        assert runner.is_running(1) is False
        started = runner.start(
            1, [{"role": "user", "content": "x"}], callbacks.on_done, callbacks.on_error
        )

        # Assert
        assert started is True
        assert callbacks.event.wait(5)
        runner.join(5)
        assert callbacks.done == [(1, "estructura")]
        assert callbacks.errors == []
        assert runner.is_running(1) is False
        assert calls == [[{"role": "user", "content": "x"}]]

    def test_second_start_for_same_entry_refused_while_running(self):
        # Arrange: llm blocks until the test releases it
        release = threading.Event()
        def blocking_llm(messages):
            release.wait(5)
            return "ok"

        runner = PrompterRunner(llm_fn=blocking_llm)
        callbacks = _RunnerCallbacks()

        # Act
        first = runner.start(1, [], callbacks.on_done, callbacks.on_error)
        second = runner.start(1, [], callbacks.on_done, callbacks.on_error)

        # Assert: in-flight registration is under the lock BEFORE spawning,
        # so the busy refusal is deterministic without sleeping.
        assert first is True
        assert second is False
        release.set()
        assert callbacks.event.wait(5)
        runner.join(5)

    def test_other_entries_can_run_in_parallel(self):
        # Arrange
        release = threading.Event()
        def blocking_llm(messages):
            release.wait(5)
            return "ok"

        runner = PrompterRunner(llm_fn=blocking_llm)
        first, second = _RunnerCallbacks(), _RunnerCallbacks()

        # Act
        assert runner.start(1, [], first.on_done, first.on_error) is True
        assert runner.start(2, [], second.on_done, second.on_error) is True

        # Assert
        release.set()
        assert first.event.wait(5) and second.event.wait(5)
        runner.join(5)
        assert first.done == [(1, "ok")] and second.done == [(2, "ok")]

    def test_error_path_delivers_error_and_clears_running_flag(self):
        # Arrange
        def boom(messages):
            raise RuntimeError("api down")

        runner = PrompterRunner(llm_fn=boom)
        callbacks = _RunnerCallbacks()

        # Act
        assert runner.start(1, [], callbacks.on_done, callbacks.on_error) is True

        # Assert: the failure surfaces via on_error, draft-safe for the caller
        assert callbacks.event.wait(5)
        runner.join(5)
        assert callbacks.errors == [(1, "api down")]
        assert callbacks.done == []
        assert runner.is_running(1) is False

    def test_empty_llm_response_is_an_error_not_a_replacement(self):
        # Replacing a draft with "" would destroy it — must be an error
        runner = PrompterRunner(llm_fn=lambda messages: "```\n```")
        callbacks = _RunnerCallbacks()

        # Act
        assert runner.start(1, [], callbacks.on_done, callbacks.on_error) is True

        # Assert
        assert callbacks.event.wait(5)
        runner.join(5)
        assert callbacks.done == []
        assert len(callbacks.errors) == 1
        assert callbacks.errors[0][0] == 1


@pytest.mark.unit
class TestPrompterGate:
    """Config-driven facade: auto flag, thresholds, runner delegation."""

    def test_auto_enabled_defaults_to_true(self):
        # Act / Assert
        assert PrompterGate({}.get, lambda m: "").auto_enabled() is True
        assert PrompterGate({"prompter_gate_auto": False}.get, lambda m: "").auto_enabled() is False

    def test_evaluate_uses_configured_thresholds(self):
        # Arrange: min_points lowered to 2, min_chars lowered to 5
        gate = PrompterGate(
            {"prompter_gate_min_points": 2, "prompter_gate_min_chars": 5}.get, lambda m: ""
        )

        # Act / Assert
        assert gate.evaluate("- uno\n- dos").trigger is True

    def test_start_and_is_running_delegate_to_runner(self):
        # Arrange
        callbacks = _RunnerCallbacks()
        gate = PrompterGate({}.get, lambda m: "estructura")

        # Act / Assert
        assert gate.is_running(7) is False
        assert gate.start(7, [], callbacks.on_done, callbacks.on_error) is True
        assert callbacks.event.wait(5)
        gate.runner.join(5)
        assert callbacks.done == [(7, "estructura")]
        assert gate.is_running(7) is False


class _FakeTextbox:
    """Minimal CTkTextbox double recording its content."""

    def __init__(self, text: str = "") -> None:
        self.text = text

    def get(self, *_args):
        return self.text

    def delete(self, *_args):
        self.text = ""

    def insert(self, _index, text):
        self.text = text


class _FakeLoc:
    """Localization double: keys pass through unchanged."""

    def get_string(self, key, **_kwargs):
        return key


class _PrompterHost(SupervisorViewMixin):
    """Headless host for the Supervisor prompter glue (no Tk at all)."""

    def __init__(self, store, llm_fn, config_map=None):
        self.supervisor_store = store
        self.config_map = dict(config_map or {})
        self.prompter_gate = PrompterGate(self._config_get, llm_fn)
        self.localization_manager = _FakeLoc()
        self.context_blocks = []
        self.status_messages = []
        self.supervisor_status_label = SimpleNamespace(
            configure=lambda **kw: self.status_messages.append(kw.get("text"))
        )
        self._supervisor_rows = {}
        self.done = threading.Event()

    def _config_get(self, key, default=None):
        return self.config_map.get(key, default)

    def after(self, _ms, fn, *args):
        fn(*args)  # synchronous "Tk thread" delivery
        return 0

    def after_cancel(self, _token):
        return None

    def _supervisor_on_prompter_result(self, number, text, error):
        super()._supervisor_on_prompter_result(number, text, error)
        self.done.set()


@pytest.mark.unit
class TestPrompterSupervisorFlow:
    """Full flush -> gate -> pass -> replacement flow (fake store rows)."""

    def _host(self, tmp_path, llm_fn, config_map=None):
        return _PrompterHost(SupervisorStore(tmp_path / "entries.json"), llm_fn, config_map)

    def _seed_entry(self, host, response, quote=""):
        entry = host.supervisor_store.create_entry(quote=quote, response=response)
        host._supervisor_rows[entry.number] = {
            "quote": _FakeTextbox(quote),
            "response": _FakeTextbox(response),
        }
        return entry.number

    def test_gate_trigger_on_flush_replaces_response_and_store(self, tmp_path):
        # Arrange: structured = fenced LLM output; draft fires the gate (8 points)
        structured = "Estructura:\n1. punto"
        host = self._host(tmp_path, lambda messages: f"```\n{structured}\n```")
        number = self._seed_entry(host, EIGHT_POINTS)

        # Act: the autosave/flush path
        host._supervisor_flush_entry(number)

        # Assert: response REPLACED in store and textbox, localized statuses
        assert host.done.wait(5)
        host.prompter_gate.runner.join(5)
        assert host.supervisor_store.get(number).response == structured
        assert host._supervisor_rows[number]["response"].text == structured
        assert "supervisor_prompter_running" in host.status_messages
        assert host.status_messages[-1] == "supervisor_prompter_done"

    def test_gate_silent_when_auto_disabled(self, tmp_path):
        # Arrange: switch OFF, draft would fire the gate
        calls = []

        def llm(messages):
            calls.append(messages)
            return "x"

        host = self._host(tmp_path, llm, {"prompter_gate_auto": False})
        number = self._seed_entry(host, EIGHT_POINTS)

        # Act
        host._supervisor_flush_entry(number)

        # Assert: no pass, no status churn
        assert calls == []
        assert host.status_messages == []
        assert host.supervisor_store.get(number).response == EIGHT_POINTS

    def test_no_trigger_on_short_draft(self, tmp_path):
        # Arrange
        calls = []

        def llm(messages):
            calls.append(messages)
            return "x"

        host = self._host(tmp_path, llm)
        number = self._seed_entry(host, "correccion corta")

        # Act
        host._supervisor_flush_entry(number)

        # Assert
        assert calls == []
        assert host.status_messages == []

    def test_manual_button_bypasses_gate_and_gate_config(self, tmp_path):
        # Arrange: auto OFF and a draft that would never fire the gate
        host = self._host(
            tmp_path, lambda messages: "estructura final", {"prompter_gate_auto": False}
        )
        number = self._seed_entry(host, "texto sin puntos ni largo")

        # Act: the per-row Prompter button path
        started = host._supervisor_start_prompter(number)

        # Assert
        assert started is True
        assert host.done.wait(5)
        host.prompter_gate.runner.join(5)
        assert host.supervisor_store.get(number).response == "estructura final"
        assert host._supervisor_rows[number]["response"].text == "estructura final"

    def test_error_keeps_draft_and_reports(self, tmp_path):
        # Arrange: LLM failure on a gate-firing draft
        host = self._host(
            tmp_path, lambda messages: (_ for _ in ()).throw(RuntimeError("api down"))
        )
        number = self._seed_entry(host, EIGHT_POINTS)

        # Act
        host._supervisor_flush_entry(number)

        # Assert: draft intact everywhere, localized error status last
        assert host.done.wait(5)
        host.prompter_gate.runner.join(5)
        assert host.supervisor_store.get(number).response == EIGHT_POINTS
        assert host._supervisor_rows[number]["response"].text == EIGHT_POINTS
        assert host.status_messages[-1] == "supervisor_prompter_error"

    def test_one_pass_at_a_time_per_entry(self, tmp_path):
        # Arrange: llm blocked until released
        release = threading.Event()
        host = self._host(tmp_path, lambda messages: release.wait(5) and "estructura")
        number = self._seed_entry(host, EIGHT_POINTS)

        # Act / Assert: second start while in flight is refused
        assert host._supervisor_start_prompter(number) is True
        assert host._supervisor_start_prompter(number) is False
        release.set()
        assert host.done.wait(5)
        host.prompter_gate.runner.join(5)
        assert host.supervisor_store.get(number).response == "estructura"


class TestPromptLoader:
    """Contrato del loader del system prompt versionado (integración A4)."""

    def test_loads_versioned_file_stripping_frontmatter(self):
        from backend.prompter_gate import load_prompter_system_prompt

        text = load_prompter_system_prompt()
        assert text.strip()
        assert not text.startswith("---")
        assert "reestructur" in text.lower() or "prompt" in text.lower()

    def test_fallback_to_inline_constant_when_file_missing(self, monkeypatch, tmp_path):
        import backend.prompter_gate as pg

        monkeypatch.setattr(pg, "_PROMPT_FILE", tmp_path / "missing.md")
        assert pg.load_prompter_system_prompt() == pg.PROMPTER_SYSTEM_PROMPT

    def test_build_prompter_messages_uses_loaded_prompt(self):
        from backend.prompter_gate import build_prompter_messages, load_prompter_system_prompt

        messages = build_prompter_messages("borrador de prueba", [], None)
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == load_prompter_system_prompt()
