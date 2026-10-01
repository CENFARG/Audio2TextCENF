# Proposal: F2 — Supervisor Tab (AI response supervision workbench)

## Intent

Add a "Supervisor" tab where GR drafts numbered responses to his AIs: each entry has
a quoted AI excerpt + `:` + his correction, with context-block templates insertable,
voice recording per fragment, autosave persistence (nothing lost on crash/hotkey),
CRUD history, and one-click copy back to the agent TUI.

## Why

User request (GR, 2026-09-24/25). His AI-correction workflow lives in fragile TUIs:
long drafted messages die to hotkeys or hangs. Drafting inside Audio2Text with
autosave makes the work safe; copy buttons bridge back to the TUI.

## Approach

Pure logic first (entry model, store with autosave, context-blocks loader, response
assembler) fully unit-tested; then a thin CustomTkinter mixin (following
FilesViewMixin/HistoryViewMixin patterns) reusing `transcribe_with_groq` for the
per-fragment record button.

## Capabilities

### New: supervisor-tab
- Numbered entries; each entry = quote (AI excerpt) + `:` + correction
- Context blocks selectbox: templates from configurable dir (default
  `C:\Dropbox\DOC.RECA\.amBotHs\contextBlocks\*.md`, YAML frontmatter
  id/name/description) inserted into the correction text
- "Nueva respuesta" resets the workbench for the next number
- CRUD history (create/read/update/delete entries)
- Autosave on every change (store persists immediately; UI debounces keystrokes)
- Per-entry and full-workbench copy (assembled, numbered, ready to paste)
- Entry status: borrador/enviada
- Per-fragment record button (voice → transcription → inserted into correction)

## Non-goals

- Conversation view / AI reply automation (future, per roadmap)
- Global hotkey capture (F3, separate change)
- Multi-session management (single workbench file)

## Risks

- Reading context blocks from a user-configured directory outside the repo — path is
  a config key, read-only, failures degrade to empty list with a logged warning
- Voice recording while main hotkey recording could conflict — supervisor recorder is
  independent and refuses to start if the main Transcriber is recording
