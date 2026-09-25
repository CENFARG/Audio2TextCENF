# Tasks: F1 — Files Tab

## 1. Contract tests first (RED)

- [x] 1.1 `tests/unit/test_file_import.py`: tests for `is_audio_file`,
      `filter_audio_paths` (dedup + reasons), `paths_from_clipboard_text`,
      CF_HDROP parse behind monkeypatched accessor — all FAILING
- [x] 1.2 Verify RED: `pytest tests/unit/test_file_import.py` exits non-zero

## 2. Pure module (GREEN)

- [x] 2.1 Implement `backend/file_import.py` (typed, docstrings, ≤400 lines)
- [x] 2.2 `pytest tests/unit/test_file_import.py` green
- [x] 2.3 Commit: `feat(files): add file import validation and clipboard path extraction` (bf0cfaf)

## 3. UI wiring

- [x] 3.1 Add i18n keys (es/en): tab_files, files_title, files_load, files_paste,
      files_transcribe, files_clear, files_status_pending, files_status_transcribing,
      files_status_done, files_status_error, files_drop_hint, files_rejected
- [x] 3.2 `ui/views/files_view.py` mixin: queue UI + sequential worker
- [x] 3.3 `ui/app.py`: register tab, mix in FilesViewMixin, tkinterdnd2 recipe with
      graceful degradation, Ctrl-V binding, read `audio_import_extensions` from config
- [x] 3.4 `requirements.txt`: add tkinterdnd2; `config.json.example`: document key
- [x] 3.5 Commit: `feat(ui): add Files tab with picker, drag-drop and clipboard import` (187378b)

## 4. Verification

- [x] 4.1 Full `pytest` green on new surface (cov gate holds: 58.85% ≥ 40; failures all pre-existing off-surface, independent verify)
- [x] 4.2 App boots without tkinterdnd2 (degradation check: static import of ui.views.files_view verified without tkdnd; live boot = 4.3)
- [ ] 4.3 Live test by GR: load, drag, paste → transcription + history entry
- [x] 4.4 Evidence committed into this change folder (below)

## Implementation evidence (2026-09-24)

- TDD: RED captured (ImportError, module absent) → GREEN 29/29 tests, 82% coverage of backend/file_import.py
- Independent verification (gentle-ai-verify): targeted 29/29 PASS; full suite 18F/234P/14E — all failures pre-existing off-surface; coverage 58.85% ≥ 40; i18n 14 keys symmetric es/en; surfaces exact
- Worker deviations (documented): +2 i18n keys (dialog labels), split_drop_data helper + 5 tests for DnD quoting, display via self.after (thread-safety), single end-of-queue sound, drop target on root with active-tab guard
- Known debt (out of scope, pre-existing): 91 pi-lens legacy findings in ui/app.py; broken test modules; mypy pyproject python_version=3.8 unsupported → quality track (PLAN-REPARACION Fase 2)
- Debug print found at ui/app.py:2 during review and removed before commit

Commits: bf0cfaf (feat files) · 187378b (feat ui) · 834f4db (chore gitignore)
