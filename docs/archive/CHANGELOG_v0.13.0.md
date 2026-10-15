# Changelog - Audio2Text v0.13.0

## [0.13.0] - 2026-03-31

### ✨ Added
- **Metadatos automáticos con LLM**
  - Generación automática de título, categoría, tags, summary, emoji, sentiment, action items
  - Usa Groq Llama 3.1-8b-instant (cloud, no impacta exe size)
  - Se muestra en tooltips al pasar mouse sobre historial

- **Hotkeys con modificadores (Ctrl, Alt, Shift)**
  - 72+ combinaciones disponibles vs 12 anteriores
  - UI de selección con checkboxes para Ctrl, Alt, Shift
  - Sugerencias rápidas por categoría (Trabajo, Ideas, Personal, Técnico)
  - Localizado completamente en español

- **Tooltip flotante real**
  - Ventana emergente que aparece cerca del cursor
  - Muestra: archivo, fecha, tamaño, transcripción, y metadatos LLM
  - Diseño con colores oscuros matching app theme

- **Selector de emojis**
  - 6 categorías, 90+ emojis
  - Para personalizar transcripciones en historial
  - Auto-confirmación al seleccionar

- **Refactorización de código**
  - Extraído `ui_flet/components/design_system.py` (90 líneas)
  - Extraído `ui_flet/components/history_tab.py` (280 líneas)
  - Patrón SRP: Single Responsibility Principle

### 🔧 Changed
- Mejorada resolución de paths relativos a absolutos
- Normalización de paths con `os.path.normpath()`
- Paths configurables desde UI (Configuración → Ruta de Audio)

### 🐛 Fixed
- Hotkey selector ahora completamente localizado en español
- Metadata generator integrado en los 3 métodos de transcripción (Groq, NVIDIA, faster-whisper)
- Keyboard modifier hotkeys ahora funcionan correctamente
- Tooltip flotante reemplaza status bar tooltip
- Paths relativos mal resueltos en compiled exe
- `./` artifacts eliminados de paths en tooltips

### 📦 Technical
- **7 commits** en esta versión
- **~1,500 líneas** de código agregadas
- **~300 líneas** refactorizadas
- **7 nuevos módulos** creados
- **304 MB** tamaño del exe (sin cambios significativos)

### 🔄 Migration Notes
- Sin cambios disruptivos - todos los audios existentes son compatibles
- Recomendado: Cambiar paths a absolutos en configuración
- Opcional: Reconfigurar hotkey con modificadores (ej. Ctrl+F9)

---

## [0.12.0] - 2026-03-25

### ✨ Added
- faster-whisper integration (local transcription)
- Sistema de bloques POST-transcripción (TaskExtractor, Summary, KeywordExtractor)
- Correcciones de vocabulario custom con UI visible
- Tutorial actualizado con nuevas features
- PyInstaller assets packageando VAD models

---

## [0.11.0] - 2026-03-21

### ✨ Added
- Post-procesamiento de transcripciones con LLM
- Migración UI a Flet
- Validación UTF-8 implementada
- Overlay reactivado
- Actualizaciones automáticas funcionando
- Límite de 100 archivos y limpieza automática

---

## [0.10.0] - 2026-03-18

### ✨ Added
- Versión inicial estable
- Transcripción con Groq Cloud API
- Hotkeys F1-F12
- Interfaz CustomTkinter
- Sistema de actualizaciones
