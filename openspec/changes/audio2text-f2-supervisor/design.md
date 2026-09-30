# Design: F2 Supervisor

## Technical approach

Two pure modules + one thin UI mixin:

1. **`backend/supervisor_store.py` (NEW, pure)**
   - `SupervisorEntry` dataclass: number, quote, response, blocks, status, created_at, updated_at
   - `SupervisorStore(path)`: `load()`, `create_entry() -> SupervisorEntry`,
     `update_entry(number, **fields)`, `delete_entry(number)`, `set_status(number, status)`,
     `all() -> list[SupervisorEntry]`, `get(number)`. Every mutation calls `_save()`
     (atomic: `.tmp` + `os.replace`). Corrupt file → backup + empty start.
   - Numbers are assigned `max(existing)+1` and NEVER reassigned on delete.
   - `_entry_to_dict` / `_entry_from_dict` for JSON; `updated_at` refreshed on mutation.

2. **`backend/context_blocks.py` (NEW, pure)**
   - `ContextBlock` dataclass: id, name, description, body
   - `load_context_blocks(directory: str | Path) -> list[ContextBlock]` — parses
     YAML frontmatter (`---\nid: ...\n---`) with a minimal parser (no PyYAML dep:
     flat `key: value` lines), body = text after frontmatter; unreadable/missing
     dir → `[]` + warning log; sorted by name.
   - `assemble_entry(entry) -> str` — `N. "quote"\n: response` (quote omitted if empty)
   - `assemble_all(entries) -> str` — entries joined by blank line

3. **`backend/supervisor_recorder.py` (NEW, pure-ish)**
   - `SupervisorRecorder(on_text, transcribe_fn, config)`: `toggle() -> bool`;
     captures 16 kHz mono via sounddevice to temp WAV in a thread; on stop calls
     `transcribe_fn(path)` (injected = `transcriber.transcribe_with_groq`) and
     delivers text via callback (UI thread via `self.after`). Refuses to start when
     `transcriber.is_recording` is True. One instance per app.

4. **`ui/views/supervisor_view.py` (NEW, mixin ≤400 lines)**
   - `SupervisorViewMixin.create_supervisor_tab()`: entries list (numbered, status chip),
     per-entry quote Text (plain) + response Text (editable) + record toggle + copy N +
     delete + sent/reopen; top bar: "Nueva respuesta", context-blocks selectbox + insert,
     "Copiar todo"; bottom status label.
   - Autosave: `Tk.after` debounce (500 ms) on every Text `<<Modified>>`/KeyRelease →
     `store.update_entry`.
   - Insert block: gets cursor index `text.index("insert")`, inserts body, records id.
   - Follows FilesViewMixin structural patterns (grid, scrollable frame, logger).

5. **`ui/app.py` (bounded)**
   - Import mixin + `create_supervisor_tab()` registration (tab after main), construct
     `SupervisorStore(config.get("supervisor_data_path", "supervisor_entries.json"))`,
     `load_context_blocks(config.get("context_blocks_dir", DEFAULT_CONTEXT_BLOCKS_DIR))`,
     `SupervisorRecorder`. DEFAULT_CONTEXT_BLOCKS_DIR constant lives in
     `backend/context_blocks.py` (documented default, config-overridable per ARCH-003).

## Config

- `supervisor_data_path` (default `supervisor_entries.json`)
- `context_blocks_dir` (default `C:\Dropbox\DOC.RECA\.amBotHs\contextBlocks`)
- Both documented in config.json.example.

## Test strategy (TDD)

- `tests/unit/test_supervisor_store.py`: create/update/delete/status/persist-reload/
  corrupt-file-backup/number-stability-after-delete — RED first
- `tests/unit/test_context_blocks.py`: frontmatter parse, body extraction, missing dir,
  malformed file skipped, assemble_entry with/without quote, assemble_all ordering
- `tests/unit/test_supervisor_recorder.py`: toggle states, refuse-while-main-recording,
  transcribe callback delivery (mocked transcribe_fn, no real audio)
- Full suite after: 0 failed / 0 errors expected (known flakes excluded), cov ≥ 40
- UI wiring: import smoke + live test by GR (C5-equivalent for F2)
