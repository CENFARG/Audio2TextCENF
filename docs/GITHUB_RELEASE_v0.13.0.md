# 🎉 Audio2Text v0.13.0 - Metadatos LLM + Hotkeys Extendidos

**Fecha de Lanzamiento:** 31 de Marzo de 2026
**Tamaño:** 304 MB

---

## ✨ Novedades Principales

### 🤖 Metadatos Automáticos con LLM
Cada transcripción ahora se analiza automáticamente con Groq Llama 3.1-8b-instant para generar:
- **Título** - Título corto y descriptivo
- **Categoría** - Trabajo, Idea, Personal, Aprendizaje, Técnico
- **Tags** - Palabras clave relevantes
- **Summary** - Resumen de una oración
- **Emoji** - Emoji sugerido según contenido
- **Sentiment** - Positivo, Neutral, Negativo
- **Action Items** - Tareas detectadas

**¿Cómo funciona?**
Pasá el mouse sobre cualquier transcripción en el historial y verás toda esta información en un tooltip flotante.

### ⌨️ Hotkeys con Modificadores
Ahora podés combinar Ctrl, Alt, Shift con cualquier tecla:
- **72+ combinaciones** vs 12 anteriores
- Ejemplos: `Ctrl+F9`, `Alt+Shift+F1`, `Ctrl+Alt+A`
- Configurá tu hotkey favorito desde **Configuración → Hotkey**

### 🎈 Tooltip Flotante Real
Ventana emergente que aparece cerca del cursor mostrando:
- Información del archivo (fecha, tamaño, ruta)
- Transcripción completa
- **Todos los metadatos LLM** generados automáticamente

### 🎨 Selector de Emojis
Personalizá tus transcripciones con emojis:
- 6 categorías (Trabajo, Ideas, Tareas, Personas, Favoritos, Otros)
- 90+ emojis disponibles
- Clic en el botón de emoji al lado de cada transcripción

### 📁 Código Refactorizado
Mejor organización del código para futuro mantenimiento:
- Archivos modulares de ~200 líneas
- Patrón SRP (Single Responsibility Principle)
- Mejor mantenibilidad

---

## 🐛 Bugs Corregidos

✅ Hotkey selector ahora completamente en español
✅ Metadatos automáticos integrados en transcripción
✅ Hotkeys con modificadores funcionando correctamente
✅ Tooltip flotante real implementado
✅ Paths relativos normalizados (sin `./` en tooltips)
✅ Configuración de paths absolutos funcionando

---

## ⚙️ Instalación

**Opción 1: Ejecutable (Recomendado)**
1. Descargá `Audio2Text_CENF_v0.13.0.exe`
2. Creá una carpeta: `C:\Audio2Text\`
3. Colocá el .exe en esa carpeta
4. Ejecutá (no requiere instalación de Python)

**Opción 2: Código fuente**
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

## 📊 Métricas

- **Versión:** 0.13.0
- **Tamaño del exe:** 304 MB
- **Commits:** 8 en esta versión
- **Líneas agregadas:** ~1,500
- **Nuevos módulos:** 7
- **Bugs corregidos:** 6

---

## 🔄 Migración desde v0.12.0

**Sin cambios disruptivos:** Todos tus audios y transcripciones existentes siguen funcionando.

**Actualización opcional:**
- Cambiá las rutas de audio a paths absolutos desde Configuración
- Reconfigurá tu hotkey con modificadores (ej. `Ctrl+F9`)

---

## 📝 Notas Técnicas

**Tecnologías nuevas:**
- Groq Llama 3.1-8b-instant para metadatos (cloud, no impacta tamaño)
- Keyboard library con modifier support
- Custom Tkinter con tooltips personalizados

**Archivos nuevos:**
- `backend/transcription_metadata_generator.py` (280 líneas)
- `backend/hotkey_manager.py` (250 líneas)
- `ui/hotkey_selector.py` (350 líneas)
- `ui/emoji_picker.py` (300 líneas)
- `ui_flet/components/design_system.py` (90 líneas)
- `ui_flet/components/history_tab.py` (280 líneas)

---

## 🎁 Créditos

Versión desarrollada por **Centro de Excelencia en Negocios del Futuro (CENF)**

Mejoras solicitadas por Pablo y la comunidad de Audio2Text.

---

## 🐇 Reportar Bugs

Encontraste un bug? Reportalo en:
https://github.com/CENFARG/Audio2TextCENF/issues

---

## 📄 Licencia

Apache 2.0 - Ver archivo LICENSE para detalles

---

**¡Disfrutá de Audio2Text v0.13.0!** 🎉

*Transcripción inteligente con metadatos automáticos*
