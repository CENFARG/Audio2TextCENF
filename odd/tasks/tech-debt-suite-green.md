# Tech Debt: Green Test Suite + Hygiene

> Branch: `fix/v0.15.1-ui-polish`
> Source: verification evidence from F1 (2026-09-24) + PLAN-REPARACION Fase 1-2
> Rules: reglas-cenf-maestro.yaml (tests honest, no fake passes; commits ≤250 lines; conventional commits)

## Inventory

- D1 ✅ Untrack test/runtime artifacts (.coverage, coverage.xml, app_log.txt,
  transcription_metadata.json) + gitignore entries
- D2 Collection error: tests/test_long_transcription_hardening.py:12 invalid escape
  `\S` in docstring (promoted to error by pytest filterwarnings=error; broken since 17e8c20)
- D3 Small broken modules: test_vocabulary_fixes (1F), test_blocks (1F),
  test_metadata (1F), test_config_manager (4F), test_file_manager (4F),
  test_hotkey_manager (2F), test_integration (3F)
- D4 test_transcriber drift (2F + 12E AttributeError — likely faster-whisper eradication
  fallout; needs careful triage vs current Transcriber API)
- D5 ruff clean on active line (audio2text-v015 surface)
- D6 mypy pyproject python_version=3.8 unsupported by installed mypy → bump config
- D7 Stray test files in root (TEST-006 violation): test_fixes.py, backend/test_utf8_validator.py
  → move under tests/ with markers or delete with justification
- D8 CLAUDE.md stale (documents faster-whisper integration that this line eradicated)
- D9 (deferred) 91 pi-lens legacy findings in ui/app.py — needs its own batch after suite
  is green (contract tests before refactor)

## Policy

- Tests are fixed to match CURRENT verified behavior; a test that reveals a REAL bug
  in backend code is REPORTED, not silently adjusted
- skip(reason=...) only for tests requiring live API/network — never fake passes
- Tests of eradicated features (faster-whisper) are deleted with justification
- Backend code changes in debt batches require explicit parent approval per finding

## Evidence

- D1: commit 1edc340 — untrack artifacts + gitignore
- D2+D3 batch 1: commit edb2f7e — 18F/234P/14E (cov 58.85%) → 11F/264P/13E (cov 61.29%); collection error gone; all fixes contract-aligned (human diff review + independent verify)
- D3 batch 1b: commits 0a183ab — config_manager 4F fixed, hotkey spaces 1F fixed, checkpoint test relabeled deterministically (sha256 chunk labels; was a TEST bug — racy call-order counter; merge is order-preserving by construction). Suite now 5F/270P/13E, cov 61.29%

## Backend bugs found by debt round (intentionally-failing tests document them)

- BUG-1 hotkey fail-open: parse_hotkey_string drops unknown modifiers → "Modificador inválido" branch unreachable → is_hotkey_valid("win+f5") == True. Evidence: tests/test_hotkey_manager.py::test_invalid_modifier
- BUG-2 keyword min_length ignored in frequency path: _extract_by_frequency hardcodes {4,} regex; min_length=5 still returns 4-char words. Evidence: tests/test_blocks.py::test_min_length_filter

## Live-test bugs found by GR (2026-09-25, F1 files tab)

- LT-1 FIXED: requirements pinned nonexistent tkinterdnd2>=2.0.0 → corrected to >=0.6.3 (4dd8005)
- LT-2: WhatsApp OGG/Opus unreadable by soundfile ("Format not recognised") → import should validate readability upfront + friendly per-file status; ffmpeg transcode fallback = feature decision
- LT-3: Groq API-key check crashes with ascii codec error when stored key contains non-ASCII (á/¿) → validate charset on save + friendly error
- LT-4: queue observability: 3 pending → "1 succeeded" with only 1 error logged — per-file failure reasons must surface in UI status
- LT-5: updater reports latest=0.10.0 (stale version.json on main — resolves with branch consolidation)
