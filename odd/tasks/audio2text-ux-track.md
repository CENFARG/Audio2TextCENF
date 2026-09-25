# Audio2Text UX Track — Task Document

> Branch: `fix/v0.15.1-ui-polish` (PR #3)
> Author identity: CENFARG <cenf.arg@gmail.com> (GR) — Pablo commits as `Pablo <pablo@local>`
> Rules: reglas-cenf-maestro.yaml (GitFlow, micro-commits ≤250 lines, files ≤400 lines, SDD→TDD, I18n, no AI attribution)

## Context

GR defined a product/UX track to run in parallel with the strategic initiatives 1-10
(docs/informes/ROADMAP_AUDIO2TEXT_MASTER.md). UI target: `ui/app.py` (CustomTkinter,
CTkTabview with 5 tabs). Transcription machinery: `backend/transcriber.py` (Slices A/B/C
streaming implemented). i18n: `lang/es.json`, `lang/en.json`.

## Tasks

### F1 — Tab "Archivos" (audio file transcription)
- [ ] Spec SDD (proposal/spec/design/tasks) following openspec conventions
- [ ] Contract tests BEFORE implementation (regla PROC-004 / TEST rules)
- [ ] Tab UI: file picker (filedialog), drag & drop (tkinterdnd2), paste from clipboard
      (Windows CF_HDROP via pyperclip/ctypes)
- [ ] Reuse backend/transcriber.py pipeline (batch path, not recording session)
- [ ] i18n labels in lang/es.json + en.json
- [ ] Work-unit commits ≤250 lines each

### F2 — Tab "Supervisor" (AI response supervision workbench)
- [ ] Spec SDD
- [ ] Numbered entries, each with two parts: quoted AI excerpt ("...") + `:` + user correction
- [ ] Context blocks selectbox: loads templates from `%AMBotHS%/contextBlocks/*.md`
      (YAML frontmatter: id/name/description/hotkey) and inserts into the response
      (12 blocks today: abstracciones, busquedaenperplexity, consultas_necesarias,
      inferencia, iterativo-acumulativo, justificacion_ia, marco_epistemologico,
      no_generar, no_negativa, obsequioso, parafrase, supervision)
- [ ] "Nueva respuesta" button clears the supervisor for the next numbered entry
- [ ] CRUD of entry history (create, read, update, delete)
- [ ] Autosave on every keystroke (debounced) to local JSON — nothing is lost on crash/hotkey
- [ ] Per-fragment "escribir" or "record" button (voice -> backend/transcriber.py)
- [ ] "Copy response N" / "Copy all" buttons (bridge back to agent TUI)
- [ ] Entry status: borrador / enviada
- [ ] State machine (ARCH-009): capture -> draft -> record -> copy -> sent

### F3 — Global hotkey clipboard capture
- [ ] Global hotkey (keyboard lib already in deps) captures clipboard as new entry
- [ ] Re-copy logic: if clipboard content equals the last captured entry, replace the
      last ordinal instead of creating a new one
- [ ] Runs only while the Supervisor tab feature (F2) is enabled

## Done
- [x] Design closed with GR (2026-09-24)
- [x] Engram store cleanup: 33 dead sync targets removed (doctor repair --apply)
- [x] Bug report to Gentleman-Programming/gentle-shell (see task 2 in todo)

## Evidence
- Commits:
  - d1aa677 docs(roadmap): Track A + reorg two tracks
  - 91f8deb docs(tasks): roadmap commit + issue link
  - d63ff85 docs(spec): F1 openspec change
  - bf0cfaf feat(files): import validation + clipboard paths (TDD 29/29)
  - 187378b feat(ui): Files tab (picker, drag-drop, clipboard)
  - 834f4db chore: ignore local .atl runtime state
- Upstream report: https://github.com/Gentleman-Programming/gentle-shell/issues/1414
  - bug(memory): session-bound memory writes fail permanently with "session has already ended" until pi is restarted
  - Labels: bug, status:needs-review (readback verified)
