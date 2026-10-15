"""
A4 Prompter Gate — semantic gate + structured-rewrite pass for Supervisor drafts.

Pure module (no Tk, no I/O beyond injected callables): it decides WHEN a
supervisor draft needs restructuring (``evaluate_draft`` heuristics), builds
the LLM conversation that restructures it WITHOUT inventing content
(``build_prompter_messages``) and runs that pass off the caller's thread
(:class:`PrompterRunner` — SupervisorRecorder pattern: injected ``llm_fn`` +
callbacks; the UI owns thread-bridging via ``Tk.after``).

Gate heuristics (simple, documented, threshold-driven):
- ``"empty"``: whitespace-only draft — never triggers.
- ``"points"``: number of numbered/bulleted list lines (``- x``, ``* x``,
  ``• x``, ``N.``/``N)`` or lettered ``X.``/``X)`` markers) >= ``min_points``
  (default 8) — a draft that already reads like a list is likely a
  structured instruction set worth cleaning up.
- ``"length"``: stripped draft length >= ``min_chars`` (default 1200) —
  long rambling drafts restructure poorly by hand.
- ``"imperative"``: ``IMPERATIVE_MIN_SENTENCES`` (3) or more sentences
  starting with a frequent Spanish/English instruction verb
  (``IMPERATIVE_VERBS``) — spoken instruction lists rarely use bullets but
  keep imperative phrasing.

The gate fires when ANY reason (besides ``"empty"``) is present; the caller
then replaces the draft with the LLM's structured version (the manual button
bypasses the gate entirely).
"""

from __future__ import annotations

import logging
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

#: Default gate thresholds (config keys ``prompter_gate_min_points`` /
#: ``prompter_gate_min_chars``).
DEFAULT_MIN_POINTS = 8
DEFAULT_MIN_CHARS = 1200

#: Imperative-starting sentences needed for the ``"imperative"`` reason.
IMPERATIVE_MIN_SENTENCES = 3

#: Frequent Spanish/English instruction verbs (imperative heuristic, lowercase,
#: voseo and tuteo forms included).
IMPERATIVE_VERBS = frozenset(
    {
        "hacé",
        "hace",
        "haz",
        "hacelo",
        "creá",
        "crea",
        "agregá",
        "agrega",
        "añadí",
        "añade",
        "escribí",
        "escribe",
        "generá",
        "genera",
        "enumerá",
        "enumera",
        "listá",
        "lista",
        "explicá",
        "explica",
        "revisá",
        "revisa",
        "corregí",
        "corrige",
        "usá",
        "usa",
        "implementá",
        "implementa",
        "probá",
        "proba",
        "verificá",
        "verifica",
        "completá",
        "completa",
        "definí",
        "diseñá",
        "diseña",
        "prepará",
        "prepara",
        "armá",
        "arma",
        "corré",
        "corre",
        "testeá",
        "testea",
        "make",
        "create",
        "add",
        "write",
        "generate",
        "list",
        "explain",
        "review",
        "fix",
        "use",
        "implement",
        "run",
        "test",
        "check",
        "define",
        "build",
        "include",
        "ensure",
        "provide",
        "update",
        "refactor",
        "verify",
        "do",
    }
)

#: One numbered/bulleted list line (``- x``, ``* x``, ``• x``, ``1. x``,
#: ``1) x``, ``b) x``) — requires whitespace after the marker.
_POINT_LINE = re.compile(r"^\s*(?:[-*•·]|\d+[.)]|[a-zA-Z][.)])\s+\S")

#: Markdown code-fence wrappers (opening fence carries an optional lang tag).
_FENCE_OPEN = re.compile(r"^```[\w.+-]*[ \t]*\r?\n?")
_FENCE_CLOSE = re.compile(r"\r?\n?```[ \t]*$")

#: Sentence terminator split for the imperative heuristic.
_SENTENCE_SPLIT = re.compile(r"[.!?…]+")

#: System prompt for the restructure pass: expert that NEVER invents content.
PROMPTER_SYSTEM_PROMPT = (
    "Sos un experto en prompt engineering. Reestructurás borradores dictados "
    "en instrucciones claras para un agente de IA: título corto, puntos "
    "numerados, una sola instrucción por punto. Regla absoluta: reestructurás "
    "sin inventar contenido nuevo — usás únicamente el borrador y, si los hay, "
    "los bloques de contexto como guía de estilo y limitaciones (nunca como "
    "contenido a incorporar). Mantené el idioma del borrador y no agregues "
    "secciones que el borrador no pida."
)


@dataclass
class GateDecision:
    """Result of the A4 gate evaluation for one draft.

    Attributes:
        trigger: Whether the Prompter pass should run.
        reasons: Why — ``"empty"``, ``"points"``, ``"length"`` and/or
            ``"imperative"``; empty list when the draft is fine as-is.
    """

    trigger: bool
    reasons: list[str] = field(default_factory=list)


def _starts_with_imperative(sentence: str) -> bool:
    """Whether a sentence starts with a known imperative instruction verb.

    Args:
        sentence: Raw sentence fragment (from the terminator split).

    Returns:
        ``True`` when the sentence's first word is a known instruction verb.
    """
    words = sentence.strip().split()
    return bool(words) and words[0].lower().strip(",;:") in IMPERATIVE_VERBS


def evaluate_draft(
    text: str,
    *,
    min_points: int = DEFAULT_MIN_POINTS,
    min_chars: int = DEFAULT_MIN_CHARS,
) -> GateDecision:
    """Decide whether a supervisor draft needs the Prompter pass (A4).

    Heuristic (documented at module level): fires on >= ``min_points``
    numbered/bulleted lines, stripped length >= ``min_chars``, or
    ``IMPERATIVE_MIN_SENTENCES`` imperative-starting sentences. Any one of
    them is enough to trigger.

    Args:
        text: Draft text (the entry response being autosaved).
        min_points: List-line threshold for the ``"points"`` reason.
        min_chars: Stripped-length threshold for the ``"length"`` reason.

    Returns:
        :class:`GateDecision` with ``trigger`` and the detected ``reasons``;
        whitespace-only text yields ``trigger=False`` with ``["empty"]``.
    """
    stripped = (text or "").strip()
    if not stripped:
        return GateDecision(False, ["empty"])
    reasons: list[str] = []
    points = sum(1 for line in stripped.splitlines() if _POINT_LINE.match(line))
    if points >= min_points:
        reasons.append("points")
    if len(stripped) >= min_chars:
        reasons.append("length")
    imperative = sum(
        1 for sentence in _SENTENCE_SPLIT.split(stripped) if _starts_with_imperative(sentence)
    )
    if imperative >= IMPERATIVE_MIN_SENTENCES:
        reasons.append("imperative")
    return GateDecision(bool(reasons), reasons)


def build_prompter_messages(draft: str, blocks: list, target_note: str | None = None) -> list[dict]:
    """Build the Prompter conversation for one draft (system + user).

    Args:
        draft: The raw draft text to restructure.
        blocks: Context blocks (:class:`~backend.context_blocks.ContextBlock`
            or any object with ``.body``) whose bodies act as style/constraint
            guides — never as new content.
        target_note: Optional note about the destination/agent the
            restructured prompt targets (e.g. the AI excerpt being corrected).

    Returns:
        ``[{"role": "system", ...}, {"role": "user", ...}]``; the user message
        carries the draft, the block bodies (when any) and the target note.
    """
    user_sections = [f"BORRADOR A REESTRUCTURAR:\n{draft}"]
    bodies = [body for body in (str(block.body or "").strip() for block in blocks) if body]
    if bodies:
        user_sections.append(
            "BLOQUES DE CONTEXTO (solo estilo/limitaciones, no contenido nuevo):\n"
            + "\n\n".join(bodies)
        )
    note = str(target_note or "").strip()
    if note:
        user_sections.append(f"NOTA DESTINO:\n{note}")
    return [
        {"role": "system", "content": PROMPTER_SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(user_sections)},
    ]


def strip_markdown_fences(text: str) -> str:
    """Strip one surrounding markdown code fence (and its language tag).

    Args:
        text: LLM output that may be wrapped in ``` / ```lang fences.

    Returns:
        The inner text trimmed; plain text comes back only trimmed.
    """
    stripped = str(text or "").strip()
    stripped = _FENCE_OPEN.sub("", stripped, count=1)
    stripped = _FENCE_CLOSE.sub("", stripped, count=1)
    return stripped.strip()


def select_block_bodies(blocks: list, ids: list) -> list:
    """Resolve an entry's block ids to its loaded block objects (pure glue).

    Args:
        blocks: Every loaded context block (sorted by name).
        ids: The entry's recorded block ids (insertion order, may repeat).

    Returns:
        Blocks in the ENTRY's id order (deduped); unknown ids ignored.
    """
    by_id = {block.id: block for block in blocks}
    selected: list = []
    seen: set[str] = set()
    for block_id in ids:
        block = by_id.get(block_id)
        if block is not None and block_id not in seen:
            seen.add(block_id)
            selected.append(block)
    return selected


class PrompterRunner:
    """One Prompter LLM pass at a time per entry, off the caller's thread.

    SupervisorRecorder pattern: the INJECTED ``llm_fn`` (``messages -> str``,
    e.g. a Groq ``client.chat.completions.create`` wrapper) runs on a daemon
    worker thread and the outcome is delivered through ``on_done(number, text)``
    / ``on_error(number, error)`` callbacks; the UI owns thread-bridging
    (deliver via ``Tk.after``). The LLM text is fence/whitespace-stripped
    before delivery and an EMPTY structured result is an error — replacing a
    draft with ``""`` would destroy it. A ``start`` for an entry already in
    flight is refused with ``False`` and never spawns a second thread.
    """

    def __init__(self, llm_fn: Callable[[list], str]) -> None:
        self._llm_fn = llm_fn
        self._inflight: set[int] = set()
        self._threads: dict[int, threading.Thread] = {}
        self._lock = threading.Lock()

    def is_running(self, number: int) -> bool:
        """Whether a Prompter pass for this entry is currently in flight."""
        with self._lock:
            return number in self._inflight

    def start(
        self,
        number: int,
        messages: list,
        on_done: Callable[[int, str], None],
        on_error: Callable[[int, str], None],
    ) -> bool:
        """Run one pass for ``number`` on a worker thread.

        Args:
            number: Entry number the pass belongs to.
            messages: Conversation built by :func:`build_prompter_messages`.
            on_done: Called with ``(number, structured_text)`` on success.
            on_error: Called with ``(number, error_message)`` on any failure.

        Returns:
            ``True`` when the pass started; ``False`` when this entry already
            has a pass in flight (refusal, nothing spawned).
        """
        with self._lock:
            if number in self._inflight:
                logger.warning("Prompter pass already running on entry #%s; start refused", number)
                return False
            self._inflight.add(number)

        def _work() -> None:
            try:
                text = strip_markdown_fences(self._llm_fn(messages))
                if not text:
                    raise ValueError("empty prompter response")
                on_done(number, text)
            except Exception as exc:
                logger.error("Prompter pass failed on entry #%s: %s", number, exc)
                on_error(number, str(exc))
            finally:
                with self._lock:
                    self._inflight.discard(number)

        thread = threading.Thread(target=_work, name=f"prompter-{number}", daemon=True)
        with self._lock:
            self._threads[number] = thread
        thread.start()
        return True

    def join(self, timeout: float = 5.0) -> None:
        """Wait for every in-flight pass thread (tests/determinism helper)."""
        with self._lock:
            threads = list(self._threads.values())
        for thread in threads:
            thread.join(timeout)


class PrompterGate:
    """Config-driven gate + runner facade for the Supervisor view (pure).

    Args:
        config_get: ``ConfigManager.get``-shaped callable ``(key, default)``.
        llm_fn: Injected ``messages -> str`` LLM call for :class:`PrompterRunner`.
    """

    def __init__(self, config_get: Callable, llm_fn: Callable[[list], str]) -> None:
        self._config_get = config_get
        self.runner = PrompterRunner(llm_fn)

    def auto_enabled(self) -> bool:
        """Whether the auto gate is ON (config key ``prompter_gate_auto``)."""
        return bool(self._config_get("prompter_gate_auto", True))

    def evaluate(self, text: str) -> GateDecision:
        """Evaluate the draft with the configured thresholds."""
        return evaluate_draft(
            text,
            min_points=int(self._config_get("prompter_gate_min_points", DEFAULT_MIN_POINTS)),
            min_chars=int(self._config_get("prompter_gate_min_chars", DEFAULT_MIN_CHARS)),
        )

    def is_running(self, number: int) -> bool:
        """Whether a pass for this entry is in flight (see PrompterRunner)."""
        return self.runner.is_running(number)

    def start(
        self,
        number: int,
        messages: list,
        on_done: Callable[[int, str], None],
        on_error: Callable[[int, str], None],
    ) -> bool:
        """Start one pass (see :meth:`PrompterRunner.start`)."""
        return self.runner.start(number, messages, on_done, on_error)
