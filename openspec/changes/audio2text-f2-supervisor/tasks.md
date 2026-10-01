# Tasks: F2 Supervisor

## 1. Pure modules (TDD)

- [ ] 1.1 RED: tests/unit/test_supervisor_store.py (CRUD, persist-reload, atomic write,
      corrupt backup, number stability) — run, capture RED
- [ ] 1.2 GREEN: backend/supervisor_store.py
- [ ] 1.3 RED: tests/unit/test_context_blocks.py (frontmatter, missing dir, assemble) →
      GREEN: backend/context_blocks.py
- [ ] 1.4 RED: tests/unit/test_supervisor_recorder.py (toggle, refuse-if-recording,
      callback delivery) → GREEN: backend/supervisor_recorder.py
- [ ] 1.5 Commit: `feat(supervisor): entry store, context blocks loader and fragment recorder`

## 2. UI

- [ ] 2.1 ui/views/supervisor_view.py mixin (entries UI, autosave debounce, insert block,
      copy N/all, record toggle, CRUD dialogs)
- [ ] 2.2 ui/app.py wiring + config.json.example keys + i18n keys es/en
- [ ] 2.3 Commit: `feat(ui): Supervisor tab for AI response drafting`

## 3. Verification

- [ ] 3.1 Full suite green (0F/0E, cov ≥ 40) + import smoke
- [ ] 3.2 Live test GR: create → quote+correction → insert block → record → copy all →
      status sent → reopen → delete
- [ ] 3.3 Evidence committed; MASTER updated
