"""
Supervisor entry store for the F2 Supervisor tab (pure module, no UI imports).

A numbered workbench of AI-response corrections: each entry holds an AI quote,
the user's correction, the context-block ids inserted into it and a draft/sent
status. The store persists to a single JSON file (config key
``supervisor_data_path``) and every mutation writes the file immediately with
an atomic temp+``os.replace`` save, so a crash never loses an acknowledged
change. A corrupt file never crashes the app: it is backed up as
``<name>.corrupt-<timestamp>``, an error is logged and the store starts empty.

Entry lifecycle (ARCH-009 state machine): ``draft -> sent -> draft`` (reopen).
Numbers come from a persisted ``next_number`` counter that is saved with every
write and initialized to ``max(existing)+1`` when absent (C-2 migration) — so
numbers are NEVER reused, not even after deleting the highest entry. Illegal
status transitions are no-ops with a warning.

REQ-2 sessions: every entry carries a free-form ``session`` name (default
``"general"``) identifying which agent/work session the response belongs to.
Legacy JSON entries without a ``session`` field migrate to ``"general"`` on
load (backward compatible). The store can list and assemble one session's
entries in numeric order (``entries_by_session`` / ``assemble_session``).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.context_blocks import assemble_all

logger = logging.getLogger(__name__)

#: Entry status: being drafted.
STATUS_DRAFT = "draft"

#: Entry status: already pasted back to the agent TUI.
STATUS_SENT = "sent"

#: Legal status transitions (ARCH-009). Reopen (sent -> draft) is allowed.
_LEGAL_TRANSITIONS: dict[str, set[str]] = {
    STATUS_DRAFT: {STATUS_SENT},
    STATUS_SENT: {STATUS_DRAFT},
}

#: On-disk schema version for the workbench JSON file.
_SCHEMA_VERSION = 1

#: Default session name (REQ-2): entries always belong to some session.
DEFAULT_SESSION = "general"

#: Fields a caller may mutate through :meth:`SupervisorStore.update_entry`.
_MUTABLE_FIELDS = frozenset({"quote", "response", "blocks"})


@dataclass
class SupervisorEntry:
    """One numbered supervisor workbench entry.

    Attributes:
        number: Sequential, historical id (never reassigned after delete).
        quote: AI excerpt being corrected (may be empty).
        response: User correction; may contain inserted context-block text.
        blocks: Context-block ids inserted into this entry (no duplicates).
        status: ``draft`` or ``sent``.
        session: Free-form agent/work-session name (REQ-2, never empty).
        created_at: ISO-8601 creation timestamp (UTC).
        updated_at: ISO-8601 last-mutation timestamp (UTC).
    """

    number: int
    quote: str = ""
    response: str = ""
    blocks: list[str] = field(default_factory=list)
    status: str = STATUS_DRAFT
    session: str = DEFAULT_SESSION
    created_at: str = ""
    updated_at: str = ""


def _utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string.

    Returns:
        ISO-8601 timestamp used for ``created_at`` / ``updated_at``.
    """
    return datetime.now(timezone.utc).isoformat()


def _entry_to_dict(entry: SupervisorEntry) -> dict:
    """Serialize an entry to a JSON-compatible dict.

    Args:
        entry: The entry to serialize.

    Returns:
        Dict with every entry field.
    """
    return {
        "number": entry.number,
        "quote": entry.quote,
        "response": entry.response,
        "blocks": list(entry.blocks),
        "status": entry.status,
        "session": entry.session,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }


def _entry_from_dict(data: dict) -> SupervisorEntry:
    """Rebuild an entry from a persisted dict, tolerating missing fields.

    Args:
        data: Dict as produced by :func:`_entry_to_dict` (possibly partial).

    Returns:
        The reconstructed entry with defaults for absent optional fields.
    """
    status = data.get("status", STATUS_DRAFT)
    if status not in (STATUS_DRAFT, STATUS_SENT):
        status = STATUS_DRAFT
    return SupervisorEntry(
        number=int(data.get("number", 0)),
        quote=str(data.get("quote", "")),
        response=str(data.get("response", "")),
        blocks=[str(b) for b in data.get("blocks", []) if str(b)],
        status=status,
        session=str(data.get("session") or DEFAULT_SESSION),
        created_at=str(data.get("created_at", "")),
        updated_at=str(data.get("updated_at", "")),
    )


class SupervisorStore:
    """JSON-backed CRUD store for supervisor entries with immediate autosave.

    Args:
        path: Target JSON file path (config key ``supervisor_data_path``).
        now_fn: Timestamp provider (injection point for tests).
    """

    def __init__(self, path: str | Path, now_fn: Callable[[], str] | None = None) -> None:
        self._path = Path(path)
        self._now = now_fn or _utc_now_iso
        self._entries: dict[int, SupervisorEntry] = {}
        self._next = 1
        self._load()

    # ── Queries ──────────────────────────────────────────────────────
    def all(self) -> list[SupervisorEntry]:
        """Return every entry ordered by number.

        Returns:
            Entries sorted by their historical number.
        """
        return [self._entries[n] for n in sorted(self._entries)]

    def get(self, number: int) -> SupervisorEntry | None:
        """Return one entry by number.

        Args:
            number: Historical entry number.

        Returns:
            The entry, or ``None`` when the number does not exist.
        """
        return self._entries.get(int(number))

    def entries_by_session(self, session: str) -> list[SupervisorEntry]:
        """Return the entries of one session ordered by number (REQ-2).

        Args:
            session: Session name to filter by (exact match).

        Returns:
            That session's entries in numeric order; empty when none match.
        """
        return [entry for entry in self.all() if entry.session == session]

    def _next_number(self) -> int:
        """Return the next sequential number.

        Returns:
            The persisted ``next_number`` counter (C-2): deleted entries —
            including the highest one — never free their number for reuse.
        """
        return self._next

    @staticmethod
    def _normalize_session(session: str) -> str:
        """Normalize a session name; blank values fall back to the default.

        Args:
            session: Raw session name from a caller or persisted JSON.

        Returns:
            The stripped name, or ``DEFAULT_SESSION`` when blank.
        """
        return str(session).strip() or DEFAULT_SESSION

    # ── Mutations (each persists immediately) ────────────────────────
    def create_entry(
        self, quote: str = "", response: str = "", session: str = DEFAULT_SESSION
    ) -> SupervisorEntry:
        """Append a new draft entry and persist.

        Args:
            quote: Optional AI excerpt.
            response: Optional initial correction text.
            session: Session name this entry belongs to (REQ-2); blank values
                fall back to ``DEFAULT_SESSION``.

        Returns:
            The freshly created entry.
        """
        now = self._now()
        number = self._next_number()
        entry = SupervisorEntry(
            number=number,
            quote=str(quote),
            response=str(response),
            blocks=[],
            status=STATUS_DRAFT,
            session=self._normalize_session(session),
            created_at=now,
            updated_at=now,
        )
        self._next = max(self._next, number + 1)
        self._entries[entry.number] = entry
        self._save()
        return entry

    def update_entry(self, entry_number: int, **fields) -> SupervisorEntry | None:
        """Update editable fields of one entry and persist.

        Args:
            entry_number: Historical entry number.
            **fields: ``quote``, ``response`` and/or ``blocks``. Any other
                key (including ``number``/``status``) is ignored.

        Returns:
            The updated entry, or ``None`` when the number is unknown.
        """
        entry = self.get(entry_number)
        if entry is None:
            logger.warning("Supervisor: update ignored, unknown entry #%s", entry_number)
            return None
        changes: dict[str, Any] = {
            key: (list(value) if key == "blocks" else str(value))
            for key, value in fields.items()
            if key in _MUTABLE_FIELDS
        }
        if not changes:
            return entry
        changes["updated_at"] = self._now()
        updated = replace(entry, **changes)
        self._entries[updated.number] = updated
        self._save()
        return updated

    def delete_entry(self, number: int) -> bool:
        """Delete one entry and persist. Numbers are never reassigned.

        Args:
            number: Historical entry number.

        Returns:
            ``True`` when the entry existed and was deleted.
        """
        number = int(number)
        if number not in self._entries:
            logger.warning("Supervisor: delete ignored, unknown entry #%s", number)
            return False
        del self._entries[number]
        self._save()
        return True

    def set_status(self, number: int, status: str) -> SupervisorEntry | None:
        """Transition an entry's status along the ARCH-009 state machine.

        Args:
            number: Historical entry number.
            status: Target status (``draft`` or ``sent``).

        Returns:
            The updated entry, or ``None`` for unknown numbers or illegal
            transitions (illegal ones log a warning and change nothing).
        """
        entry = self.get(number)
        if entry is None:
            logger.warning("Supervisor: status change ignored, unknown entry #%s", number)
            return None
        if status == entry.status:
            logger.warning(
                "Supervisor: illegal status transition %s -> %s on entry #%s (no-op)",
                entry.status,
                status,
                number,
            )
            return None
        if status not in _LEGAL_TRANSITIONS.get(entry.status, set()):
            logger.warning(
                "Supervisor: illegal status transition %s -> %s on entry #%s (no-op)",
                entry.status,
                status,
                number,
            )
            return None
        updated = replace(entry, status=status, updated_at=self._now())
        self._entries[updated.number] = updated
        self._save()
        return updated

    def set_session(self, number: int, session: str) -> SupervisorEntry | None:
        """Move one entry to another session and persist (REQ-2).

        Args:
            number: Historical entry number.
            session: Target session name; blank values fall back to
                ``DEFAULT_SESSION``.

        Returns:
            The updated entry, or ``None`` when the number is unknown.
        """
        entry = self.get(number)
        if entry is None:
            logger.warning("Supervisor: session change ignored, unknown entry #%s", number)
            return None
        updated = replace(
            entry,
            session=self._normalize_session(session),
            updated_at=self._now(),
        )
        self._entries[updated.number] = updated
        self._save()
        return updated

    def assemble_session(self, session: str) -> str:
        """Assemble one session's entries for copying (REQ-2).

        Same format as :func:`backend.context_blocks.assemble_all` — entries
        joined by a blank line in numeric order, empty ones skipped — but
        restricted to the given session.

        Args:
            session: Session name to assemble.

        Returns:
            The assembled copy payload, or ``""`` when nothing has content.
        """
        return assemble_all(self.entries_by_session(session))

    # ── Persistence ──────────────────────────────────────────────────
    def _load(self) -> None:
        """Load entries from disk, recovering from a corrupt file.

        A missing file means an empty workbench. A corrupt file is backed up
        as ``<name>.corrupt-<timestamp>``, an error is logged and the store
        starts empty. Individually malformed entries are skipped, not fatal.
        A legacy file without ``next_number`` migrates its counter to
        ``max(existing)+1`` (C-2); a stored counter lower than that is
        clamped up so a number can never be handed out twice.
        """
        if not self._path.exists():
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            self._recover_corrupt_file(exc)
            return
        if not isinstance(payload, dict) or not isinstance(payload.get("entries", []), list):
            self._recover_corrupt_file(ValueError("unexpected JSON root"))
            return
        for raw in payload.get("entries", []):
            if not isinstance(raw, dict) or "number" not in raw:
                logger.warning("Supervisor: skipping malformed persisted entry")
                continue
            try:
                entry = _entry_from_dict(raw)
            except (TypeError, ValueError) as exc:
                logger.warning("Supervisor: skipping malformed entry: %s", exc)
                continue
            self._entries[entry.number] = entry
        counter = payload.get("next_number")
        if not isinstance(counter, int) or isinstance(counter, bool) or counter < 1:
            counter = max(self._entries, default=0) + 1
        self._next = max(counter, max(self._entries, default=0) + 1)

    def _recover_corrupt_file(self, exc: Exception) -> None:
        """Back up a corrupt store file and start empty.

        Args:
            exc: The parse/read error that triggered recovery.
        """
        backup = self._path.with_name(
            f"{self._path.name}.corrupt-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        try:
            shutil.copy2(self._path, backup)
            logger.error(
                "Supervisor store corrupt (%s); backed up to %s and starting empty",
                exc,
                backup,
            )
        except OSError as copy_exc:
            logger.error(
                "Supervisor store corrupt (%s) and backup failed (%s); starting empty",
                exc,
                copy_exc,
            )
        self._entries = {}
        self._next = 1

    def _save(self) -> None:
        """Persist all entries atomically (temp file + ``os.replace``)."""
        payload = {
            "version": _SCHEMA_VERSION,
            "next_number": self._next,
            "entries": [_entry_to_dict(e) for e in self.all()],
        }
        tmp_path = self._path.with_name(self._path.name + ".tmp")
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp_path, self._path)
        except OSError as exc:
            logger.error("Supervisor store save failed: %s", exc)
