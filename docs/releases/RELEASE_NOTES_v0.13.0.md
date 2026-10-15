# Audio2Text v0.13.0 - Notas de Release

**Fecha de Lanzamiento:** 31 de Marzo de 2026
**Versión:** 0.13.0
**Tamaño del .exe:** 304 MB
**Commits:** 7 commits en esta versión

---

## 🎯 RESUMEN EJECUTIVO

Audio2Text v0.13.0 introduce **metadatos automáticos con LLM**, **hotkeys extendidos con modificadores**, y **tooltips flotantes interactivos**. Esta versión mejora significativamente la experiencia del usuario con información contextual automática y más opciones de personalización.

---

## 🚀 NUEVAS CARACTERÍSTICAS

### 1. Metadatos Automáticos con LLM 🤖

**Descripción:**
Generación automática de metadatos inteligentes para cada transcripción usando Groq Llama 3.1-8b-instant.

**Metadatos generados:**
- **🏷️ Título** - Título corto y descriptivo (máx 50 caracteres)
- **📁 Categoría** - Clasificación automática: Trabajo, Idea, Personal, Aprendizaje, Técnico
- **🏷️ Tags** - Palabras clave relevantes (hasta 5 tags)
- **📝 Summary** - Resumen de una oración (máx 100 caracteres)
- **😊 Emoji** - Emoji sugerido según el contenido
- **😊/😐/😔 Sentiment** - Análisis de sentimiento: Positivo, Neutral, Negativo
- **✅ Action Items** - Tareas y acciones detectadas (hasta 3)

**Tecnología:**
- Groq Llama 3.1-8b-instant (cloud, no aumenta tamaño del exe)
- Generación automática post-transcripción
- Se guarda en `transcription_metadata.json` bajo clave `"auto"`

---

### 2. Hotkeys con Modificadores ⌨️

**Descripción:**
Expansión del sistema de hotkeys para soportar modificadores (Ctrl, Alt, Shift).

**Combinaciones disponibles:**
- **72+ combinaciones** vs 12 anteriores
- F1-F12 × 6 tipos de modificadores:
  - `F1-F12` (sin modificadores)
  - `Ctrl+F1` a `Ctrl+F12`
  - `Alt+F1` a `Alt+F12`
  - `Shift+F1` a `Shift+F12`
  - `Ctrl+Alt+F1` a `Ctrl+Alt+F12`
  - `Ctrl+Shift+F1` a `Ctrl+Shift+F12`
  - `Alt+Shift+F1` a `Alt+Shift+F12`
  - `Ctrl+Alt+Shift+F1` a `Ctrl+Alt+Shift+F12`
- Soporte para teclas A-Z y 0-9 con modificadores
- Soporte futuro para botones de mouse

**UI mejorada:**
- Selector de hotkeys con checkboxes para Ctrl, Alt, Shift
- Preview en tiempo real: "CTRL+SHIFT+F1"
- Sugerencias rápidas por categoría (Trabajo, Ideas, Personal, Técnico)
- Localizado completamente en español

---

### 3. Tooltip Flotante Real 🎈

**Descripción:**
Ventanas emergentes flotantes que aparecen cerca del cursor al pasar el mouse sobre archivos del historial.

**Información mostrada:**

*Básica:*
- 📁 Nombre del archivo
- 📅 Fecha y hora de grabación
- 💾 Tamaño del archivo
- 📍 Ruta completa
- 💬 Transcripción (si existe)

*Metadatos LLM (si disponibles):*
- 🏷️ Título generado
- 💼/💡/👤/📚/🔧 Categoría con icono
- 🏷️ Tags relevantes
- 📝 Resumen del contenido
- 😊/😐/😔 Sentiment
- ✅ Tareas/Action items

**Tecnología:**
- Clase `ToolTip` personalizada para CustomTkinter
- Usa `tk.Toplevel` con `overrideredirect(True)`
- Colores oscuros matching el design system
- Posicionamiento inteligente cerca del cursor

---

### 4. Selector de Emojis 🎨

**Descripción:**
Selector de emojis para personalizar transcripciones en el historial.

**Características:**
- 6 categorías: Trabajo, Ideas, Tareas, Personas, Favoritos, Otros
- 90+ emojis disponibles
- Búsqueda de emojis
- Auto-confirmación al seleccionar
- Se guarda en `transcription_metadata.json`

---

### 5. Refactorización de Código 📁

**Descripción:**
Reorganización del código siguiendo el principio de responsabilidad única (SRP).

**Módulos extraídos:**
- `ui_flet/components/design_system.py` (90 líneas)
  - Design tokens: colores, tipografías, espaciados, iconos
- `ui_flet/components/history_tab.py` (280 líneas)
  - Funcionalidad completa del historial
  - Tooltip con metadatos
  - Emoji picker button

**Objetivo:**
- Archivos de ~200 líneas cada uno
- Mantenibilidad mejorada
- Reutilización de componentes

---

### 6. Paths Absolutos Configurables 📁

**Descripción:**
Sistema mejorado de resolución de paths para consistencia entre desarrollo y ejecutable compilado.

**Características:**
- `os.path.normpath()` para eliminar `./` artifacts
- Paths relativos convertidos a absolutos correctamente
- Mismo comportamiento en `python main.py` y `.exe`
- Configurable desde UI: **Configuración → Ruta de Audio/Transcripciones**

**Recomendación:**
Usar paths absolutos en configuración para máxima consistencia:
```
audio_path: "C:\ruta\a\audio"
transcriptions_path: "C:\ruta\a\transcriptions"
```

---

## 🐛 BUGS CORREGIDOS

1. **Hotkey selector no localizado** - Ahora muestra todos los strings en español
2. **Metadata generator no integrado** - Se integró en los 3 métodos de transcripción (Groq, NVIDIA, faster-whisper)
3. **Keyboard modifier hotkeys no funcionaban** - Arreglado para usar `add_hotkey()` en lugar de `on_press_key()`
4. **Tooltip solo mostraba en status bar** - Implementado tooltip flotante real
5. **Paths relativos mal resueltos** - Normalizados con `os.path.normpath()`
6. **Paths mostraban `./` en tooltips** - Eliminados artifacts de `./`

---

## 📦 INSTALACIÓN

**Opción 1: Ejecutable (Recomendado)**
1. Descargar `Audio2Text_CENF_v0.13.0.exe` (304 MB)
2. Colocar en carpeta deseada
3. Ejecutar (no requiere instalación de Python)
4. Configurar paths en Configuración

**Opción 2: Código fuente**
1. Clonar repositorio: `git clone https://github.com/CENFARG/Audio2TextCENF.git`
2. Instalar dependencias: `pip install -r requirements.txt`
3. Ejecutar: `python main.py`

---

## ⚙️ CONFIGURACIÓN

**Paths recomendados (absolutos):**
```json
{
  "audio_path": "C:\\Audio2Text\\audio",
  "transcriptions_path": "C:\\Audio2Text\\transcriptions"
}
```

**Hotkey por defecto:**
```
Ctrl+F9 (modo toggle)
```

**Servicio de transcripción por defecto:**
```
faster-whisper (modelo base, local)
```

---

## 📊 MÉTRICAS

- **Líneas de código agregadas:** ~1,500
- **Líneas de código refactorizadas:** ~300
- **Nuevos módulos:** 7
- **Commits:** 7
- **Tamaño del exe:** 304 MB (sin cambios significativos vs v0.12.0)
- **Tiempo de compilación:** ~5 minutos
- **Tiempo de inicio:** ~8 segundos (carga de modelos)

---

## 🔄 MIGRACIÓN DESDE v0.12.0

**Sin cambios disruptivos:** Todos los audios y transcripciones existentes son compatibles.

**Actualización de configuración:**
1. Opcional: Cambiar `audio_path` y `transcriptions_path` a paths absolutos
2. Opcional: Configurar hotkey con modificadores (ej. `Ctrl+F9`)
3. Opcional: Seleccionar modelo de faster-whisper (tiny, base, small, medium, large-v3)

**Nuevos archivos creados:**
- `transcription_metadata.json` - Metadatos de transcripciones (auto + manual)
- `backend/transcription_metadata_generator.py` - Generador de metadatos LLM
- `backend/hotkey_manager.py` - Gestor de hotkeys con modificadores
- `ui/hotkey_selector.py` - UI de selección de hotkeys
- `ui/emoji_picker.py` - Selector de emojis

---

## 🎁 AGRADECIMIENTOS

Esta versión incluye mejoras solicitadas por Pablo y la comunidad:
- Metadatos automáticos para mejor organización
- Hotkeys extendidos para mayor productividad
- Tooltips informativos para mejor UX

---

## 📝 PRÓXIMAS VERSIONES

**v0.14.0 (Planeada):**
- Optimización de tamaño del exe
- Más modelos de faster-whisper
- Exportación de metadatos a JSON/CSV
- Búsqueda avanzada en historial

**v1.0.0 (Futura):**
- Versión para Linux y macOS
- API REST para integración
- Modo batch para múltiples archivos
- Tests automatizados completos

---

## 🐇 REPORTAR BUGS

GitHub Issues: https://github.com/CENFARG/Audio2TextCENF/issues

---

## 📄 LICENCIA

Apache 2.0 - Ver archivo LICENSE para detalles

---

**¡Disfruta de Audio2Text v0.13.0!** 🎉

*Centro de Excelencia en Negocios del Futuro (CENF)*
