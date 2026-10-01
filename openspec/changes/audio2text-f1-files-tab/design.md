# Design: F1 — Files Tab

## Technical approach

Three layers, all thin:

1. **`backend/file_import.py` (NEW, pure logic, fully unit-testable)**
   - `DEFAULT_AUDIO_EXTENSIONS: frozenset[str]` — mp3, wav, m4a, ogg, flac, webm, opus, aac
   - `is_audio_file(path: str, extensions: frozenset[str] | None = None) -> bool`
   - `filter_audio_paths(paths: Iterable[str], extensions: frozenset[str] | None = None) -> tuple[list[str], list[tuple[str, str]]]`
     — returns (accepted, rejected-with-reason); deduplicates, checks existence
   - `paths_from_clipboard() -> list[str]`
     — Windows: `ctypes` windll user32 `RegisterClipboardFormat("CF_HDROP")` /
       `GetClipboardData` via `win32clipboard` if importable, else text fallback;
       elsewhere text fallback only
   - `paths_from_clipboard_text(text: str) -> list[str]` — splits lines, strips
     quotes, expands user, keeps existing files
   - No UI imports, no logging of user paths at INFO (privacy), typed, Google docstrings

2. **Queue UI in `ui/app.py` (bounded edits, target <120 new lines; heavy markup
   goes to a new mixin `ui/views/files_view.py` following the HistoryViewMixin pattern)**
   - `FilesViewMixin`: builds tab content (buttons row, queue `CTkScrollableFrame`,
     status labels), `add_files_to_queue(paths)`, `transcribe_all()`,
     `_transcribe_queue_thread()` iterating `self._files_queue` sequentially and
     calling the EXISTING `self._start_retranscription(path)`-equivalent path
     (transcribe → display → `file_manager.save_transcription_entry`)
   - Per-file status dict `{path: status}`; statuses via i18n keys
   - Sequential guarantee: one worker thread, `queue.Queue` or guarded list, no
     parallel file transcription

3. **Input sources**
   - Picker: `filedialog.askopenfilename(filetypes=...)`, `multiple` per Tk version —
     if multiple unsupported, loop
   - Drag & drop: `class App(..., TkinterDnD.DnDWrapper)` recipe with
     `TkinterDnD._require(self)` in `__init__`, wrapped in try/except ImportError →
     `self._dnd_available = False`, log warning, tab shows drop hint disabled
   - Clipboard: button + Ctrl-V binding on the tab frame →
     `file_import.paths_from_clipboard()` → `add_files_to_queue`

## Config

- `audio_import_extensions`: list, default from `DEFAULT_AUDIO_EXTENSIONS`, read via
  `self.config_manager.get("audio_import_extensions", None)` falling back to the
  constant; documented in `config.json.example`

## Dependencies

- Add `tkinterdnd2>=2.0.0` to `requirements.txt` (DEP-001: mature, maintained,
  pure Tcl/Tk extension, no known CVEs at time of writing)
- pywin32 optional path guarded by try/except (already used elsewhere on Windows)

## Test strategy (TDD, strict)

- RED first: `tests/unit/test_file_import.py` — contract tests for
  `is_audio_file` (valid/invalid/missing), `filter_audio_paths`
  (dedup, mixed valid/invalid, reasons), `paths_from_clipboard_text`
  (quoted lines, whitespace, non-paths), clipboard CF_HDROP parsing behind a
  monkeypatched clipboard accessor (no real clipboard in CI)
- GREEN: implement `backend/file_import.py`
- UI wiring covered by manual live test (GR) — CustomTkinter automation is out of
  scope for this change; queue logic that is UI-independent lives in the mixin and
  is exercised through the pure module where possible
- Run: `pytest tests/unit/test_file_import.py` then full `pytest` (cov gate ≥40
  must hold)

## Migration / compatibility

- No schema changes; history entries identical to retranscription entries
- App must boot with and without tkinterdnd2 (graceful degradation requirement)
