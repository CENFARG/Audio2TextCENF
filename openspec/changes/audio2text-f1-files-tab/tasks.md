# Tasks: F1 — Files Tab

## 1. Contract tests first (RED)

- [ ] 1.1 `tests/unit/test_file_import.py`: tests for `is_audio_file`,
      `filter_audio_paths` (dedup + reasons), `paths_from_clipboard_text`,
      CF_HDROP parse behind monkeypatched accessor — all FAILING
- [ ] 1.2 Verify RED: `pytest tests/unit/test_file_import.py` exits non-zero

## 2. Pure module (GREEN)

- [ ] 2.1 Implement `backend/file_import.py` (typed, docstrings, ≤400 lines)
- [ ] 2.2 `pytest tests/unit/test_file_import.py` green
- [ ] 2.3 Commit: `feat(files): add file import validation and clipboard path extraction`

## 3. UI wiring

- [ ] 3.1 Add i18n keys (es/en): tab_files, files_title, files_load, files_paste,
      files_transcribe, files_clear, files_status_pending, files_status_transcribing,
      files_status_done, files_status_error, files_drop_hint, files_rejected
- [ ] 3.2 `ui/views/files_view.py` mixin: queue UI + sequential worker
- [ ] 3.3 `ui/app.py`: register tab, mix in FilesViewMixin, tkinterdnd2 recipe with
      graceful degradation, Ctrl-V binding, read `audio_import_extensions` from config
- [ ] 3.4 `requirements.txt`: add tkinterdnd2; `config.json.example`: document key
- [ ] 3.5 Commit: `feat(ui): add Files tab with picker, drag-drop and clipboard import`

## 4. Verification

- [ ] 4.1 Full `pytest` green (cov gate holds)
- [ ] 4.2 App boots without tkinterdnd2 (degradation check)
- [ ] 4.3 Live test by GR: load, drag, paste → transcription + history entry
- [ ] 4.4 Commit evidence into this change folder; mark task 3 done in
      odd/tasks/audio2text-ux-track.md
