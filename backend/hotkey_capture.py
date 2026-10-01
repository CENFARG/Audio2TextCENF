"""
F3 global hotkey capture: clipboard -> supervisor workbench (pure module, no UI imports).

A global hotkey (registered by ``ui/app.py``) hands the clipboard text to
:class:`HotkeyCaptureHandler`. The pure decision logic
(:func:`decide_capture_action`) compares the clipboard against the LAST
workbench entry response with a strip-compare: identical text replaces the
last entry instead of creating a duplicate, an empty/whitespace clipboard is
ignored, and anything else creates a new entry whose ``response`` is the
clipboard text.

``on_trigger`` returns a :class:`CaptureResult` carrying a localization
message key (``supervisor_captured_new`` / ``supervisor_captured_replaced``);
the UI layer renders it with the affected entry number. Clipboard read
failures are logged as a warning and treated as "no capture" — a global
hotkey must never crash the app.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .supervisor_store import SupervisorEntry, SupervisorStore

logger = logging.getLogger(__name__)

#: Status message key: a new entry was created from the clipboard.
MESSAGE_KEY_NEW = "supervisor_captured_new"

#: Status message key: the last entry's response was replaced.
MESSAGE_KEY_REPLACED = "supervisor_captured_replaced"

#: Outcome of the pure capture decision.
CaptureAction = Literal["new", "replace_last", "ignore"]


def decide_capture_action(
    clipboard_text: str | None, last_entry_response: str | None
) -> CaptureAction:
    """Decide what a hotkey trigger should do with the clipboard text.

    Args:
        clipboard_text: Raw clipboard content (``None`` tolerated).
        last_entry_response: Response of the last workbench entry, if any.

    Returns:
        ``"ignore"`` when the clipboard is empty/whitespace, ``"replace_last"``
        when the stripped clipboard equals the stripped last response
        (avoids a duplicate entry), otherwise ``"new"``. Comparison is a
        strip-compare only: case and punctuation are significant.
    """
    text = (clipboard_text or "").strip()
    if not text:
        return "ignore"
    if text == (last_entry_response or "").strip():
        return "replace_last"
    return "new"


def build_capture_entry(clipboard_text: str, next_number: int) -> dict:
    """Return the workbench payload for a fresh capture entry.

    The captured text becomes the entry ``response`` (the workbench field the
    user corrects); ``quote`` stays empty because the clipboard capture has no
    separate AI excerpt. ``SupervisorStore`` assigns authoritative numbers on
    ``create_entry``; ``next_number`` documents the intended sequential slot.

    Args:
        clipboard_text: Non-empty clipboard text (caller decided the action).
        next_number: Intended sequential entry number (``len(all) + 1``).

    Returns:
        A fresh payload dict ``{"number", "quote", "response"}``.
    """
    return {"number": int(next_number), "quote": "", "response": str(clipboard_text)}


@dataclass(frozen=True)
class CaptureResult:
    """Outcome of a non-ignored hotkey trigger.

    Attributes:
        action: ``"new"`` or ``"replace_last"``.
        entry: The created or updated workbench entry.
        message_key: Localization key for the user-visible status message.
    """

    action: str
    entry: SupervisorEntry
    message_key: str


class HotkeyCaptureHandler:
    """Capture the clipboard into the supervisor workbench on a global hotkey.

    Args:
        store: Supervisor workbench store (``SupervisorStore``).
        clipboard_reader: Zero-argument callable returning the clipboard text
            (e.g. ``pyperclip.paste``); injected for testability.
    """

    def __init__(self, store: SupervisorStore, clipboard_reader: Callable[[], str]) -> None:
        self._store = store
        self._clipboard_reader = clipboard_reader

    def on_trigger(self) -> CaptureResult | None:
        """Run one capture cycle.

        Returns:
            A :class:`CaptureResult` when an entry was created or replaced, or
            ``None`` when the clipboard was empty, whitespace, or unreadable.
            The stored response is the stripped clipboard text.
        """
        try:
            text = str(self._clipboard_reader() or "").strip()
        except Exception as exc:
            logger.warning("Supervisor capture: clipboard read failed: %s", exc)
            return None
        entries = self._store.all()
        last_response = entries[-1].response if entries else None
        action = decide_capture_action(text, last_response)
        if action == "ignore":
            return None
        if action == "replace_last":
            return self._replace_last(entries[-1], text)
        return self._create_new(text)

    def _create_new(self, text: str) -> CaptureResult:
        """Create a new entry whose response is the clipboard text.

        Args:
            text: Non-empty clipboard text.

        Returns:
            The capture result pointing at the freshly created entry.
        """
        payload = build_capture_entry(text, len(self._store.all()) + 1)
        entry = self._store.create_entry(quote=payload["quote"], response=payload["response"])
        return CaptureResult(action="new", entry=entry, message_key=MESSAGE_KEY_NEW)

    def _replace_last(self, last: SupervisorEntry, text: str) -> CaptureResult | None:
        """Replace the last entry's response with the clipboard text.

        Args:
            last: The current last workbench entry.
            text: Non-empty clipboard text.

        Returns:
            The capture result pointing at the updated entry, or ``None``
            (with a warning) if the entry vanished between reads.
        """
        updated = self._store.update_entry(last.number, response=text)
        if updated is None:
            logger.warning(
                "Supervisor capture: replace ignored, entry #%s no longer exists", last.number
            )
            return None
        return CaptureResult(action="replace_last", entry=updated, message_key=MESSAGE_KEY_REPLACED)
