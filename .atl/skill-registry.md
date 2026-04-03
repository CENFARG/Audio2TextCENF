# Audio2Text Skill Registry

> **Last Updated:** 2026-04-02
> **Project:** Audio2TextCENF
> **Version:** 0.13.0

---

## Project Skills

No project-specific skills configured yet.

---

## Global Skills (Available)

No global skills detected in user directories.

---

## Convention Files

- `CLAUDE.md` - Project memory and context
- `docs/guides/MEJORAS_PROFESIONALES.md` - Professional improvement recommendations

---

## Detected Conventions

**Testing Framework:**
- pytest (based on existing `tests/test_blocks.py`)

**Code Style:**
- No explicit linter/formatter configured
- Python logging module used throughout

**Localization:**
- `lang/es.json` - Spanish strings
- `lang/en.json` - English strings

**Build System:**
- PyInstaller for Windows .exe
- Custom build scripts in `scripts/`

---

## Notes

- Project follows MVC-modified pattern
- Threading used for real-time audio processing
- Config management via JSON with XOR obfuscation
- Semantic versioning (MAJOR.MINOR.PATCH)
