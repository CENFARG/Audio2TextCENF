**[Español](CHANGELOG.md) | [English](CHANGELOG_EN.md)**

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.0] - 2026-03-18

### 🎯 BREAKING CHANGES
- **New Post-Processing Architecture:** LLM-based linguistic normalization system
- **UTF-8 Validator:** Automatic validation and correction of Spanish characters
- **File Limits:** Implementation of 100 file limit with automatic cleanup

### ✨ Added
- **PHASE 1 - LLM Post-Processing:**
  - `backend/post_processor.py` (450+ lines) - Transcription normalization
  - Technical vocabularies: `backend/vocabulary/ia_tech.json` (1000+ terms)
  - General vocabulary: `backend/vocabulary/general.json` (500+ terms)
  - Punctuation and capitalization restoration
  - Technical vocabulary normalization (AI, Prompt, ChatGPT, Gemini)
  - Filler word and repetition removal
  - Rioplatense Spanish support

- **PHASE 2 - Flet Migration:**
  - `ui_flet/main.py` (~1,100 lines) - Complete UI with Flet
  - `ui_flet/components/recording_overlay.py` - LED status overlay
  - Flutter-based modern interface
  - Better performance and future cross-platform support
  - CustomTkinter preserved as legacy

- **PHASE 3 - UTF-8 Correction:**
  - `backend/utf8_validator.py` (337 lines) - Spanish UTF-8 validator
  - Automatic correction of á, é, í, ó, ú, ñ, ¿, ¡
  - Integration in `backend/transcriber.py`
  - `utf8_validation` configuration in `config.json`

- **PHASE 4 - Overlay Reactivated:**
  - Recording overlay reactivated in `ui/app.py`
  - LED states: Ready (blue), Recording (red), Processing (yellow), Error (orange)
  - Real-time timer

- **PHASE 5 - Updates Fixed:**
  - URL corrected from root to `config/version.json`
  - Fully functional update system
  - Version verification from GitHub

- **PHASE 6 - File Management:**
  - 100 audio file limit (`max_audio_files`)
  - Automatic cleanup of old files (30 days)
  - Methods: `maintain_audio_file_limit()`, `clean_old_audio_files()`
  - History load optimization

- **PHASE 7 - SmartScreen:**
  - Complete documentation: `docs/GUIA_SMARTSCREEN.md`
  - Optimized build with `--noupx` flag
  - Professional version metadata
  - User installation guide

### 🔧 Changed
- `backend/transcriber.py` - UTF8Validator integration
- `backend/file_manager.py` - +150 lines for limits and cleanup
- `backend/config_manager.py` - utf8_validation configuration
- `ui/app.py` - Overlay reactivated, history variables
- `lang/es.json` and `lang/en.json` - app_title updated to 0.10.0
- `scripts/build.py` - Version 0.10.0, emojis removed
- All build scripts updated to v0.10.0

### 🐛 Fixed
- Freezes with tildes and ñ (UTF-8)
- Update system (incorrect URL)
- Hang with many files
- Window title showing incorrect version

### 📦 Distribution
- Executable: `Audio2Text_CENF_0.10.0.exe` (45 MB)
- Location: `scripts/dist/`

### 📝 Documentation
- CHANGELOG.md updated to v0.10.0
- CLAUDE.md updated to v0.10.0
- All project memories updated

---

## [0.9.4] - 2025-12-31

### ✨ Added
- **Sanitized Public Release:**
  - Removed all PRO features and internal documentation.
  - Reset Git history for a clean Community Edition.
  - Added bilingual documentation (`README_EN.md`, etc.).
  - Corrected all URLs to `cenfarg.com.ar`.

## [0.9.2] - 2025-12-23

### 🎯 BREAKING CHANGES
- **Project Structure:** Complete reorganization to enterprise structure
  - Content moved from `audio2text_v0.9.2/` to project root
  - Existing users must re-clone the repository

### ✨ Added
- **Professional Enterprise Structure:**
  - Folders organized by type: `assets/`, `backend/`, `config/`, `docs/`, `lang/`, `scripts/`, `templates/`, `ui/`
  - Clear separation of concerns
  - Build artifacts organized by variant in `_build_artifacts/`
  
- **Standard Project Files:**
  - `setup.py` - Distribution configuration
  - `pyproject.toml` - Modern Python configuration
  - `LICENSE` - Apache 2.0 License
  - `CHANGELOG.md` - This file
  - `CONTRIBUTING.md` - Contribution guide
  - `CODE_OF_CONDUCT.md` - Code of conduct
  - `SECURITY.md` - Security policy
  - `MANIFEST.in` - Files to include in distribution

- **Anti-SmartScreen Solutions:**
  - Professional version metadata in executables
  - Optimized build with `--noupx`
  - Complete documentation for users (`docs/INSTALACION.md`)
  - Expected reduction: 30-40% in SmartScreen warnings

- **Custom Variants:**
  - Build GENERAL (CENF)
  - Build CONTRERAS (Contreras Hnos)
  - Build CUTIGNOLA
  - Each variant with its own logo and metadata

- **Automated Build Scripts:**
  - `scripts/build_all_v2.py` - Compile all variants
  - `scripts/build_GENERAL_v2.py` - Specific GENERAL build
  - `scripts/build_CONTRERAS_v2.py` - Specific CONTRERAS build
  - `scripts/build_CUTIGNOLA_v2.py` - Specific CUTIGNOLA build
  - Logs with timestamp for traceability

- **Complete Documentation:**
  - `docs/README_ESTRUCTURA_PROFESIONAL.md` - Architecture guide
  - `docs/INSTALACION.md` - Instructions for end users
  - `docs/GUIA_SMARTSCREEN.md` - Technical solutions to warnings
  - `docs/COMPLETADO_v0.9.2.md` - Detailed development changelog
  - `docs/installer.nsi` - Updated NSIS script

### 🔧 Changed
- **File Organization:**
  - Old versions archived in `_old_versions_archive/` (local only)
  - `.gitignore` updated for clean structure
  - Paths in build scripts updated

- **Build Improvements:**
  - Separation of artifacts by variant
  - Logs organized with timestamp
  - Specs organized by client

### 🐛 Fixed
- Incorrect paths in build scripts
- Missing metadata in executables
- Disorganized project structure

### 📦 Distribution
- Executables available for download in [Releases](https://github.com/CENFARG/Audio2Text/releases/tag/v0.9.2)
- Professional NSIS installer included

---

## [0.9.0] - 2024-12-17

### ✨ Added
- GUI with CustomTkinter
- Real-time transcription with Groq API (Whisper Large v3)
- Multi-language support (Spanish/English)
- Configurable hotkeys (F1-F12)
- Complete configuration panel
- Auto-update system
- System tray integration
- Automatic file and log management

### 🔧 Changed
- Migration from version 0.8.x to modular architecture
- Separation of UI and backend

---

## [0.8.1] - 2024-11-XX

### ✨ Added
- First functional version
- Basic audio transcription
- WAV file saving

---

## Change Types

- `✨ Added` - for new features
- `🔧 Changed` - for changes in existing functionality
- `🗑️ Deprecated` - for soon-to-be removed features
- `🐛 Fixed` - for any bug fixes
- `🔒 Security` - in case of vulnerabilities
- `📦 Distribution` - changes in packaging/distribution
- `📝 Documentation` - changes in documentation only

---

[0.9.4]: https://github.com/CENFARG/Audio2Text/compare/v0.9.2...v0.9.4
[0.9.2]: https://github.com/CENFARG/Audio2Text/compare/v0.9.0...v0.9.2
[0.9.0]: https://github.com/CENFARG/Audio2Text/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/CENFARG/Audio2Text/releases/tag/v0.8.1
