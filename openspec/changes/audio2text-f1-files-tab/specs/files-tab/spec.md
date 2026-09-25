# Files Tab Specification

## Requirement: File import sources

The system SHALL accept audio files through a file picker dialog, drag & drop onto
the tab, and clipboard paste. All three sources SHALL feed the same pending queue.

### Scenario: Load via picker
- WHEN the user clicks the load button and selects one or more audio files
- THEN each valid file is appended to the pending queue

### Scenario: Drag & drop
- WHEN the user drags files from the OS shell onto the tab
- THEN each valid file is appended to the pending queue
- WHEN the tkinterdnd2 dependency is not installed
- THEN the application still starts, drag & drop is disabled, and a warning is logged

### Scenario: Paste from clipboard
- WHEN the user copies file(s) in the OS shell and activates paste in the tab
- THEN file paths are read from the clipboard (CF_HDROP first, text-path fallback)
  and valid files are appended to the pending queue

## Requirement: Import validation

The system SHALL validate every candidate path before enqueueing: the file MUST
exist and its extension MUST be in the configured allowlist
(`audio_import_extensions`, default: mp3, wav, m4a, ogg, flac, webm, opus, aac).
Duplicate paths already pending SHALL be ignored. Invalid entries SHALL be reported
with a per-entry reason and never crash the UI.

### Scenario: Invalid file
- WHEN a dropped item is not an existing audio file
- THEN it is reported as rejected (reason: invalid type or missing) and the queue
  state is unchanged for valid items

## Requirement: Sequential transcription queue

The system SHALL transcribe queued files one at a time (no parallel files) using
the existing retranscription flow, showing per-file status: pending, transcribing,
done, error. Results SHALL appear through the existing transcription display and be
persisted to history exactly like retranscription does today.

### Scenario: Transcribe all
- WHEN the user starts transcription with N pending files
- THEN files are processed sequentially, each status updates live, and a failure
  marks that file as error without stopping the remaining queue

## Requirement: Internationalization

Every user-visible string in the tab SHALL use the localization manager with keys
present in both `lang/es.json` and `lang/en.json`. Missing keys SHALL follow the
existing MISSING_TRANSLATION fallback behavior.

## Requirement: Code constraints

New modules SHALL stay under 400 lines, functions typed with type hints, Google
docstrings on public functions, and no hardcoded secrets or user-facing literals
(strings via i18n; allowlist via config with documented default).
