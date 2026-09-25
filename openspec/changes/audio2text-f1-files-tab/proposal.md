# Proposal: F1 — Files Tab (audio file transcription)

## Intent

Add a new "Archivos" tab to the CustomTkinter UI that transcribes EXISTING audio
files through the same transcription machinery used by live recording. Files enter
the queue through three sources: file picker, drag & drop, and clipboard paste.

## Why

User request (GR, 2026-09-24). Today transcribing an existing file requires the
hidden retranscription path. A visible tab makes batch/file transcription a
first-class feature with zero new transcription logic.

## Approach

Reuse the proven flow `ui/app.py:_start_retranscription(file_path)` →
`transcriber.transcribe_with_groq(path)` → `display_transcription` → history entry.
New code is limited to: a pure-logic import module (`backend/file_import.py`),
queue UI in a new tab, and input sources (picker / drag-drop / clipboard).

## Capabilities

### New: files-tab
- File import from picker, drag & drop (tkinterdnd2), clipboard paste (CF_HDROP
  with text-path fallback)
- Import validation: audio extension allowlist (configurable), existence check,
  de-duplication against the pending queue
- Sequential transcription queue with per-file status (pending / transcribing /
  done / error)
- Graceful degradation: if tkinterdnd2 is unavailable the app runs with drag-drop
  disabled and a logged warning

## Non-goals

- Parallel file transcription (pipeline chunking already parallelizes internally)
- Folder-recursive import
- Changes to post-processing, blocks, or metadata generation
- faster-whisper / nvidia-specific paths (this line is Groq-first)

## Risks

- tkinterdnd2 + CustomTkinter root-window mix is a known recipe but must degrade
  cleanly when the dependency is missing (distributed builds).
- Windows clipboard file reads need CF_HDROP via ctypes/win32clipboard; text-path
  fallback keeps the feature usable everywhere.
