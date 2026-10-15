# 📦 GitHub Release Assets - Audio2Text v0.13.0

---

## 🇺🇸 ENGLISH VERSION

### Release Title
```
Audio2Text v0.13.0: AI-Powered Transcription with Smart Metadata & Extended Hotkeys
```

### Release Description (English)
```markdown
# 🎉 Audio2Text v0.13.0: AI-Powered Transcription with Smart Metadata

**Release Date:** March 31, 2026
**Executable Size:** 304 MB
**License:** Apache 2.0

---

## ✨ What's New

### 🤖 AI-Powered Automatic Metadata
Every transcription is now automatically analyzed using **Groq Llama 3.1-8b-instant** to generate:
- **Smart Title** - Concise, descriptive title
- **Category** - Auto-classified: Work, Ideas, Personal, Learning, Technical
- **Tags** - Relevant keywords extracted
- **Summary** - One-sentence content summary
- **Emoji** - Contextually appropriate emoji
- **Sentiment** - Positive, Neutral, or Negative
- **Action Items** - Tasks and action items detected

**How it works:** Hover over any transcription in history to see complete metadata in a floating tooltip.

### ⌨️ Extended Hotkey Support
Now combine **Ctrl, Alt, Shift** with any key:
- **72+ combinations** vs previous 12
- Examples: `Ctrl+F9`, `Alt+Shift+F1`, `Ctrl+Alt+A`
- Configure from **Settings → Hotkey**

### 🎈 Real Floating Tooltips
Interactive popup windows showing:
- File information (date, size, path)
- Full transcription text
- **All AI-generated metadata**

### 🎨 Emoji Picker
Personalize your transcriptions with emojis:
- 6 categories (Work, Ideas, Tasks, People, Favorites, Other)
- 90+ emojis available
- Click emoji button next to any transcription

### 📁 Code Refactoring
Improved codebase organization for maintainability:
- Modular files (~200 lines each)
- Single Responsibility Principle (SRP)
- Better maintainability

---

## 🐛 Bug Fixes

✅ Hotkey selector fully localized in Spanish
✅ Auto metadata integrated into all transcription methods
✅ Modifier hotkeys working correctly
✅ Real floating tooltips implemented
✅ Relative paths normalized (no more `./` artifacts)
✅ Absolute path configuration working

---

## 📥 Installation

### Option 1: Standalone Executable (Recommended)
1. Download `Audio2Text_CENF_v0.13.0.exe`
2. Create folder: `C:\Audio2Text\`
3. Place the `.exe` in that folder
4. Run (no Python installation required)

### Option 2: Source Code
```bash
git clone https://github.com/CENFARG/Audio2TextCENF.git
cd Audio2TextCENF
pip install -r requirements.txt
python main.py
```

---

## ⚙️ Recommended Configuration

From **Settings** in the application:

```
Audio Path: C:\Audio2Text\audio
Transcriptions Path: C:\Audio2Text\transcriptions
Hotkey: Ctrl+F9
Service: faster-whisper (local)
Model: base
```

---

## 📊 Release Metrics

- **Version:** 0.13.0
- **Executable Size:** 304 MB
- **Commits:** 8 in this release
- **Lines Added:** ~1,500
- **New Modules:** 7
- **Bugs Fixed:** 6

---

## 🔄 Migration from v0.12.0

**No breaking changes:** All existing audio files and transcriptions remain compatible.

**Optional updates:**
- Change audio paths to absolute paths from Settings
- Reconfigure hotkey with modifiers (e.g., `Ctrl+F9`)

---

## 🔧 Technical Highlights

**New Technologies:**
- Groq Llama 3.1-8b-instant for metadata (cloud-based, no local impact)
- Keyboard library with modifier support
- Custom Tkinter with custom tooltips

**New Files:**
- `backend/transcription_metadata_generator.py` (280 lines)
- `backend/hotkey_manager.py` (250 lines)
- `ui/hotkey_selector.py` (350 lines)
- `ui/emoji_picker.py` (300 lines)
- `ui_flet/components/design_system.py` (90 lines)
- `ui_flet/components/history_tab.py` (280 lines)

---

## 🎁 Credits

Developed by **Centro de Excelencia en Negocios del Futuro (CENF)**

Features requested by Pablo and the Audio2Text community.

---

## 🐛 Bug Reports

Found a bug? Report it at:
https://github.com/CENFARG/Audio2TextCENF/issues

---

## 📄 License

Apache 2.0 - See LICENSE file for details

---

**Enjoy Audio2Text v0.13.0!** 🎉

*Intelligent transcription with automatic AI metadata*
```

---

## 🇪🇸 SPANISH VERSION

### Título de Release
```
Audio2Text v0.13.0: Transcripción con IA, Metadatos Inteligentes y Hotkeys Extendidos
```

### Descripción de Release (Español)
```markdown
# 🎉 Audio2Text v0.13.0: Transcripción Inteligente con Metadatos Automáticos

**Fecha de Lanzamiento:** 31 de Marzo de 2026
**Tamaño del Ejecutable:** 304 MB
**Licencia:** Apache 2.0

---

## ✨ Novedades

### 🤖 Metadatos Automáticos con IA
Cada transcripción se analiza automáticamente con **Groq Llama 3.1-8b-instant** para generar:
- **Título Inteligente** - Título corto y descriptivo
- **Categoría** - Clasificación automática: Trabajo, Ideas, Personal, Aprendizaje, Técnico
- **Tags** - Palabras clave relevantes
- **Resumen** - Resumen de una oración
- **Emoji** - Emoji apropiado según el contexto
- **Sentimiento** - Positivo, Neutral o Negativo
- **Tareas** - Items de acción detectados

**Cómo funciona:** Pasá el mouse sobre cualquier transcripción en el historial para ver los metadatos completos en un tooltip flotante.

### ⌨️ Hotkeys Extendidos
Ahora podés combinar **Ctrl, Alt, Shift** con cualquier tecla:
- **72+ combinaciones** vs 12 anteriores
- Ejemplos: `Ctrl+F9`, `Alt+Shift+F1`, `Ctrl+Alt+A`
- Configurá desde **Configuración → Hotkey**

### 🎈 Tooltips Flotantes Reales
Ventanas emergentes interactivas que muestran:
- Información del archivo (fecha, tamaño, ruta)
- Transcripción completa
- **Todos los metadatos generados por IA**

### 🎨 Selector de Emojis
Personalizá tus transcripciones con emojis:
- 6 categorías (Trabajo, Ideas, Tareas, Personas, Favoritos, Otros)
- 90+ emojis disponibles
- Hacé clic en el botón de emoji al lado de cada transcripción

### 📁 Código Refactorizado
Mejor organización del código para mayor mantenibilidad:
- Archivos modulares (~200 líneas cada uno)
- Principio de Responsabilidad Única (SRP)
- Mejor mantenibilidad

---

## 🐛 Bugs Corregidos

✅ Selector de hotkeys completamente en español
✅ Metadatos automáticos integrados en todos los métodos de transcripción
✅ Hotkeys con modificadores funcionando correctamente
✅ Tooltips flotantes reales implementados
✅ Paths relativos normalizados (sin artefactos `./`)
✅ Configuración de paths absolutos funcionando

---

## 📥 Instalación

### Opción 1: Ejecutable Standalone (Recomendado)
1. Descargá `Audio2Text_CENF_v0.13.0.exe`
2. Creá una carpeta: `C:\Audio2Text\`
3. Colocá el `.exe` en esa carpeta
4. Ejecutá (no requiere instalación de Python)

### Opción 2: Código Fuente
```bash
git clone https://github.com/CENFARG/Audio2TextCENF.git
cd Audio2TextCENF
pip install -r requirements.txt
python main.py
```

---

## ⚙️ Configuración Recomendada

Desde **Configuración** en la aplicación:

```
Ruta de Audio: C:\Audio2Text\audio
Ruta de Transcripciones: C:\Audio2Text\transcriptions
Hotkey: Ctrl+F9
Servicio: faster-whisper (local)
Modelo: base
```

---

## 📊 Métricas de la Release

- **Versión:** 0.13.0
- **Tamaño del ejecutable:** 304 MB
- **Commits:** 8 en esta release
- **Líneas agregadas:** ~1,500
- **Nuevos módulos:** 7
- **Bugs corregidos:** 6

---

## 🔄 Migración desde v0.12.0

**Sin cambios disruptivos:** Todos los audios y transcripciones existentes siguen siendo compatibles.

**Actualizaciones opcionales:**
- Cambiá las rutas de audio a paths absolutos desde Configuración
- Reconfigurá el hotkey con modificadores (ej: `Ctrl+F9`)

---

## 🔧 Aspectos Técnicos

**Nuevas tecnologías:**
- Groq Llama 3.1-8b-instant para metadatos (basado en cloud, sin impacto local)
- Keyboard library con soporte de modificadores
- Custom Tkinter con tooltips personalizados

**Nuevos archivos:**
- `backend/transcription_metadata_generator.py` (280 líneas)
- `backend/hotkey_manager.py` (250 líneas)
- `ui/hotkey_selector.py` (350 líneas)
- `ui/emoji_picker.py` (300 líneas)
- `ui_flet/components/design_system.py` (90 líneas)
- `ui_flet/components/history_tab.py` (280 líneas)

---

## 🎁 Créditos

Desarrollado por **Centro de Excelencia en Negocios del Futuro (CENF)**

Features solicitadas por Pablo y la comunidad de Audio2Text.

---

## 🐛 Reportar Bugs

¿Encontraste un bug? Reportalo en:
https://github.com/CENFARG/Audio2TextCENF/issues

---

## 📄 Licencia

Apache 2.0 - Ver archivo LICENSE para detalles

---

**¡Disfrutá de Audio2Text v0.13.0!** 🎉

*Transcripción inteligente con metadatos automáticos por IA*
```

---

## 📋 Resumen Rápido (Quick Reference)

### English Title
```
Audio2Text v0.13.0: AI-Powered Transcription with Smart Metadata & Extended Hotkeys
```

### Spanish Title
```
Audio2Text v0.13.0: Transcripción con IA, Metadatos Inteligentes y Hotkeys Extendidos
```

### Short Description (English - for GitHub preview)
```
AI-powered real-time audio transcription with automatic metadata generation, extended hotkey support (Ctrl/Alt/Shift modifiers), floating tooltips, and emoji customization. Now with smarter organization powered by Llama 3.1.
```

### Descripción Corta (Español - para preview de GitHub)
```
Transcripción de audio en tiempo real con metadatos automáticos por IA, hotkeys extendidos con modificadores (Ctrl/Alt/Shift), tooltips flotantes y personalización con emojis. Ahora con organización más inteligente impulsada por Llama 3.1.
```

---

## 🎯 Tips para una Release de Calidad

1. **Usar emojis moderadamente** - Solo al inicio de secciones principales
2. **Mantener párrafos cortos** - Máximo 3-4 líneas por párrafo
3. **Usar negritas estratégicamente** - Para features y beneficios clave
4. **Incluir métricas** - Números concretos (tamaño, commits, líneas de código)
5. **Links funcionales** - Verificar que todos los links sean válidos
6. **Secciones claras** - Usar headers con emojis para navegación visual
7. **Call-to-action final** - Invitar a reportar bugs y contribuir
