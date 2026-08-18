# Audio2Text - Memoria del Proyecto para Claude

> **Última actualización:** 2026-04-10
> **Versión:** 0.14.0
> **Estado:** Producción estable - LLM Blocks + Dynamic Title + Duration Selector + faster-whisper + Groq API renovada

---

## 📋 ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura Actual](#arquitectura-actual)
3. [Stack Tecnológico](#stack-tecnológico)
4. [Decisiones Técnicas Históricas](#decisiones-técnicas-históricas)
5. [Mejoras Planificadas](#mejoras-planificadas)
6. [Problemas Conocidos](#problemas-conocidos)
7. [Roadmap](#roadmap)
8. [Enlaces Rápidos](#enlaces-rápidos)

---

## 🎯 RESUMEN EJECUTIVO

**Audio2Text** es una aplicación profesional de **transcripción de audio en tiempo real** que utiliza inteligencia artificial para convertir voz a texto.

### Propósito Principal
- Transcribir audio en tiempo real usando 3 servicios: Groq Cloud (online), faster-whisper (local), NVIDIA Riva (oculto)
- Multiidioma: Español e Inglés
- Hotkeys globales configurables (F1-F12)
- Sistema de actualizaciones automáticas
- Interfaz moderna con CustomTkinter
- Sistema de Bloques POST: TaskExtractor, Summary, KeywordExtractor
- Correcciones de vocabulario custom (ej: CENF → zenf)

### Variantes del Producto
1. **GENERAL** (CENF) - Logo genérico de CENF
2. **CONTRERAS** (Contreras Hnos) - Logo personalizado
3. **CUTIGNOLA** - Logo personalizado

### Métricas del Proyecto
- **Líneas de Código:** ~10,000+ líneas de Python
- **Módulos Backend:** 11 (transcriber.py, faster_whisper_asr.py, nvidia_asr.py, blocks/, config_manager.py, etc.)
- **Módulos UI:** 4 (CustomTkinter) + 5 (Flet)
- **Versión Actual:** 0.12.0 (estable - 25/03/2026)
- **Licencia:** Apache 2.0

---

## 🏗️ ARQUITECTURA ACTUAL

### Patrón de Diseño
**MVC (Model-View-Controller) modificado** con programación orientada a objetos y threading.

### Estructura de Directorios

```
Audio2Text/
├── backend/              # Lógica de negocio (9 módulos)
│   ├── config_manager.py      # Gestión de configuración
│   ├── file_manager.py        # Gestión de archivos
│   ├── localization_manager.py # Soporte multiidioma
│   ├── sound_manager.py       # Efectos de sonido
│   ├── startup_manager.py     # Inicio con Windows
│   ├── transcriber.py         # Motor de transcripción
│   ├── updater.py             # Sistema de actualizaciones
│   ├── post_processor.py      # Post-procesamiento de transcripciones (FASE 1)
│   ├── utf8_validator.py      # Validación y corrección UTF-8 (FASE 3)
│   └── vocabulary/            # Diccionarios técnicos
│       ├── ia_tech.json       # Vocabulario AI/tech (1000+ términos)
│       ├── general.json       # Vocabulario general (500+ términos)
│       └── custom.json        # Vocabulario personalizado (plantilla)
├── ui/                  # Interfaz gráfica CustomTkinter (4 módulos)
│   ├── app.py                # Aplicación principal (~1,000 líneas)
│   ├── recording_overlay.py   # Overlay de grabación
│   ├── tutorial.py           # Tutorial interactivo
│   └── update_tab.py         # Pestaña de actualizaciones
├── ui_flet/             # Interfaz gráfica Flet (5 módulos) [NUEVO]
│   ├── main.py               # Aplicación principal Flet (~1,100 líneas)
│   └── components/           # Componentes Flet
│       └── recording_overlay.py
├── lang/                # Archivos de idioma
│   ├── es.json              # Español
│   └── en.json              # Inglés
├── config/              # Configuraciones
│   ├── version_info.txt
│   ├── version_info_GENERAL.txt
│   ├── version_info_CONTRERAS.txt
│   └── version_info_CUTIGNOLA.txt
├── scripts/             # Scripts de build
├── docs/                # Documentación
├── docs/living-docs/    # Documentos vivos (10 documentos)
├── assets/              # Recursos visuales
├── templates/           # Templates HTML
├── memory-bank/         # Memoria del proyecto
└── main.py              # Punto de entrada
```

### Archivos Clave

**Backend:**
- `backend/transcriber.py` (400+ líneas) - Motor de transcripción con Groq API, faster-whisper local, NVIDIA Riva ASR
- `backend/faster_whisper_asr.py` (234 líneas) - Cliente faster-whisper para transcripción local sin Docker [NUEVO v0.12.0]
- `backend/nvidia_asr.py` (268 líneas) - Cliente NVIDIA Riva ASR con gRPC [ACTUALIZADO v0.12.0]
- `backend/blocks/` - Sistema de bloques POST-transcripción:
  - `block_manager.py` - Orquestador de bloques
  - `task_extractor_block.py` - Extractor de tareas
  - `summary_block.py` - Generador de resúmenes
  - `keyword_extractor_block.py` - Extractor de palabras clave [NUEVO v0.12.0]
- `backend/config_manager.py` (200+ líneas) - Configuración con ofuscación de API keys + faster-whisper settings
- `backend/custom_vocabulary.py` - Sistema de correcciones de vocabulario (ej: CENF → zenf) [NUEVO v0.12.0]
- `backend/post_processor.py` (450+ líneas) - Post-procesamiento con LLM para normalización de texto
- `backend/utf8_validator.py` (337 líneas) - Validación y corrección UTF-8 para español
- `backend/file_manager.py` (118 líneas) - Gestión de archivos de audio y transcripciones
- `backend/sound_manager.py` (47 líneas) - Efectos de sonido del sistema
- `backend/localization_manager.py` (38 líneas) - Soporte multiidioma
- `backend/startup_manager.py` (127 líneas) - Integración con inicio de Windows
- `backend/updater.py` (183 líneas) - Sistema de actualizaciones automáticas
- `backend/vocabulary/ia_tech.json` (1000+ términos) - Vocabulario técnico AI/tech [NUEVO]
- `backend/vocabulary/general.json` (500+ términos) - Vocabulario general español [NUEVO]
- `backend/vocabulary/custom.json` (plantilla) - Vocabulario personalizable [NUEVO]

**UI:**
- `ui/app.py` (~1,000+ líneas) - Aplicación principal con CustomTkinter [LEGACY]
- `ui_flet/main.py` (~1,100+ líneas) - Aplicación principal con Flet [NUEVO]
- `ui_flet/components/recording_overlay.py` (200+ líneas) - Overlay Flet con estados [NUEVO]
- `ui/recording_overlay.py` (90 líneas) - Overlay flotante de grabación [LEGACY]
- `ui/tutorial.py` - Tutorial interactivo de onboarding
- `ui/update_tab.py` - Pestaña de gestión de actualizaciones

---

## 🔧 STACK TECNOLÓGICO

### Core
- **Lenguaje:** Python 3.8+
- **Framework UI:** CustomTkinter 5.2.0+
- **Servicios de Transcripción:** Groq Cloud (Whisper Large v3), faster-whisper (local), NVIDIA Riva ASR
- **Empaquetado:** PyInstaller 6.0.0+

### Dependencias Principales

```python
# UI y Gráficos
customtkinter>=5.2.0    # UI moderna (legacy)
flet>=0.21.0           # NUEVO: UI Framework alternativo
Pillow>=10.0.0         # Procesamiento de imágenes

# Audio y Transcripción
groq>=0.4.0            # API de transcripción
faster-whisper>=1.0.0  # Transcripción local con Whisper (NUEVO v0.12.0)
torch>=2.0.0           # PyTorch para faster-whisper (114.6 MB)
ctranslate2>=4.0.0     # Motor de optimización para faster-whisper
sounddevice>=0.4.6     # Captura de audio
soundfile>=0.12.1      # Procesamiento de audio

# Interacción y Sistema
keyboard>=0.13.5       # Hotkeys globales
pystray>=0.19.4        # System tray
pyperclip>=1.8.2       # Portapapeles
pyautogui>=0.9.54      # Automatización UI
psutil>=5.9.0          # Información del sistema
numpy>=1.24.0          # Procesamiento numérico
pywin32>=306           # Integración Windows

# Utilidades
requests>=2.31.0       # HTTP requests

# Build Tools
pyinstaller>=6.0.0     # Empaquetado
```

### Dependencias PRO (Utilizadas en post-procesamiento)
- `agno>=2.0.0` - Framework de agentes AI (opcional, para features avanzadas)
- `openai>=1.0.0` - OpenAI API (opcional, para post-procesamiento LLM)

---

## 📜 DECISIONES TÉCNICAS HISTÓRICAS

### 1. Cambio de Licencia: MIT → Apache 2.0
**Fecha:** v0.9.3
**Motivo:** Estandar enterprise con protección de patentes y marca.

### 2. Sistema de Ofuscación de API Keys
**Implementación:** XOR + Base64 con clave "CENF_SECRET"
**Archivo:** `backend/config_manager.py`
**Nota:** No es criptografía fuerte, solo ofuscación básica.

### 3. Overlay Reactivado (FASE 4)
**Ubicación:** `ui/app.py` líneas 74-76
**Estado:** Reactivado en v0.10.0
**Descripción:**
```python
# Crear overlay de grabación - REACTIVADO
from ui.recording_overlay import RecordingOverlay
self.recording_overlay = RecordingOverlay(self)
```
El overlay muestra estado de grabación con LED de colores y temporizador.

### 4. UTF-8 Monkey Patch
**Ubicación:** `main.py` líneas 49-79
**Propósito:** Fix para CustomTkinter en Windows (error de TclError)

### 5. Build con Múltiples Variantes
**Implementación:** Scripts en `scripts/`
**Propósito:** Builds personalizados por cliente (GENERAL, CONTRERAS, CUTIGNOLA)

### 6. Integración de faster-whisper como Alternativa Local
**Fecha:** v0.12.0
**Archivos:** `backend/faster_whisper_asr.py`, `backend/transcriber.py`
**Motivo:**
- Proveer alternativa offline que no requiera API key
- faster-whisper es 4x más rápido que Whisper original
- Soporta 5 modelos (tiny, base, small, medium, large-v3)
- VAD (Voice Activity Detection) integrado con Silero
**Decisión de UI:**
- Groq y faster-whisper visibles en UI
- NVIDIA Riva ASR oculto pero funcional en config.json
- faster-whisper configurado por defecto en build distribuido

---

## 🚀 MEJORAS PLANIFICADAS

### Prioridad ALTA (Críticas)

#### 1. Sistema de Post-Procesamiento de Transcripciones
**Archivo:** `docs/MEJORAS_PABLO.md` líneas 60-152
**Propósito:**
- Transformar habla espontánea en texto escrito natural
- Restaurar puntuación y capitalización
- Normalizar vocabulario técnico (Prompt, ChatGPT, Gemini, etc.)
- Eliminar muletillas y repeticiones

**Implementación:**
- Prompt de sistema dedicado para post-procesamiento
- Vocabulario técnico pre-cargado
- Soporte para español rioplatense

#### 2. Migración a Flet
**Estado:** CustomTkinter → Flet
**Objetivo:**
- UI moderna basada en Flutter
- Mejor rendimiento
- Cross-platform futuro
- Mantener separación frontend/backend

#### 3. Corrección UTF-8
**Problema:** Bloqueos con tildes y ñ
**Causa:** Posible issue con Groq API
**Soluciones:**
- Implementar post-procesamiento
- Cambiar a modelo Gemini
- Usar API OpenAI directamente

#### 4. Reactivar Overlay de Grabación
**Ubicación:** `ui/app.py` líneas 74-76
**Estado:** Deshabilitado temporalmente
**Acción:** Reactivar y debuggear

### Prioridad MEDIA (Importantes)

#### 5. Sistema de Bloques/Middles
**Descripción:**
- Bloques de contexto aplicables a transcripciones
- Ejemplo: Extractor de tareas
- Aplicable pre o post transcripción
- Mix de bloques permitido

#### 6. Agente Extractor de Vocabulario Específico
**Propósito:**
- Detectar palabras técnicas en charlas
- Marcar palabras particulares
- Armar vocabulario automáticamente
- Corrección manual permitida

#### 7. Actualización Automática Funcional
**Problema:** Botón de actualizar no funciona
**Ubicación:** `backend/updater.py`, `ui/update_tab.py`
**Acción:** Debuggear y arreglar

#### 8. Gestión de Archivos
**Problemas:**
- Aplicación se cuelga con muchas transcripciones
- Sin límite máximo de audios
- Sin limpieza automática

**Soluciones:**
- Límite máximo de archivos (configurable)
- Limpieza automática por tiempo/cantidad
- Optimización de carga de historial

#### 9. Solución SmartScreen Windows 11
**Problema:** Bloqueo de Windows Defender
**Soluciones:**
- Code signing certificate
- Mejores prácticas de build
- Documentación de instalación

### Prioridad BAJA (Deseables)

#### 10. Combinaciones de Hotkeys
**Actual:** F1-F12 individual
**Propuesto:** Ctrl+F1, Alt+F2, etc.

#### 11. Logo Renovado
**Estado:** Logo actual genérico
**Acción:** Diseñar logo profesional

#### 12. Selector de Emojis
**Propósito:** Renombrar chats con emojis
**Inspiración:** Selector de Windows 11 (Win+.)

#### 13. Skills de Audio2Text
**Propósito:** Hacer Audio2Text más potente y extensible

#### 14. Agente Audio2Text
**Propósito:**
- Conectar con fuentes de información
- Gestionar vocabulario
- Integración con otros servicios

---

## ⚠️ PROBLEMAS CONOCIDOS

### Críticos - Todos Resueltos en v0.12.0
1. ✅ **Overlay deshabilitado** - SOLUCIONADO en FASE 4: Reactivado en ui/app.py
2. ✅ **UTF-8 issues** - SOLUCIONADO en FASE 3: Implementado UTF8Validator en backend/utf8_validator.py
3. ✅ **Actualizaciones no funcionan** - SOLUCIONADO en FASE 5: URL corregida a config/version.json
4. ✅ **Cuelga con muchos archivos** - SOLUCIONADO en FASE 6: Límite de 100 archivos y limpieza automática
5. ✅ **Bloqueo Windows 11** - SOLUCIONADO en FASE 7: Documentación y mejores prácticas de build implementadas
6. ✅ **Sistema de Bloques/Middles** - SOLUCIONADO en v0.12.0: TaskExtractor, Summary, KeywordExtractor implementados
7. ✅ **Correcciones de Vocabulario** - SOLUCIONADO en v0.12.0: CustomVocabulary con UI visible

### Menores
6. 📝 **Dependencias PRO no usadas** - `agno`, `openai` en requirements (opcional para post-procesamiento)
7. 📝 **Código comentado** - Código de desarrollo en archivos
8. 📝 **Sin tests automatizados** - No hay tests visibles

---

## 🗺️ ROADMAP

### v0.11.0 (Completado - Mejoras Críticas)
- [x] Análisis completo del proyecto
- [x] FASE 1: Implementar post-procesamiento de transcripciones (COMPLETADO)
- [x] FASE 2: Migrar UI a Flet (COMPLETADO)
- [x] FASE 3: Corregir problemas UTF-8 (COMPLETADO)
- [x] FASE 4: Reactivar overlay (COMPLETADO)
- [x] FASE 5: Arreglar actualizaciones (COMPLETADO)
- [x] FASE 6: Implementar límite y limpieza de archivos (COMPLETADO)
- [x] FASE 7: Solucionar bloqueo SmartScreen (COMPLETADO - Documentación y mejores prácticas)

### v0.12.0 (Completado - faster-whisper + Bloques)
- [x] Integración de faster-whisper como alternativa local a Groq
- [x] Sistema de bloques POST-transcripción (TaskExtractor, Summary, KeywordExtractor)
- [x] Correcciones de vocabulario custom con UI visible
- [x] Tutorial actualizado con nuevas features
- [x] UI mejorada (Groq vs faster-whisper visibles, NVIDIA oculto)
- [x] PyInstaller assets packegeando VAD models

### v0.13.0 (Próximo - Extras y UX)
- [ ] Logo renovado
- [ ] Selector de emojis para renombrar chats
- [ ] Combinaciones de hotkeys (Ctrl+F1, Alt+F2, etc.)
- [ ] Skills de Audio2Text
- [ ] Agente Audio2Text

### v1.0.0 (Lanzamiento Mayor)
- [ ] Versión para Linux y macOS
- [ ] API REST para integración
- [ ] Modo batch para múltiples archivos
- [ ] Interfaz web opcional
- [ ] Tests automatizados completos

---

## 🔗 ENLACES RÁPIDOS

### Repositorio
- **GitHub:** https://github.com/CENFARG/Audio2TextCENF
- **Issues:** https://github.com/CENFARG/Audio2Text/issues

### Documentación Intercional
- **Guía de Instalación:** `docs/INSTALACION.md`
- **Solución SmartScreen:** `docs/GUIA_SMARTSCREEN.md`
- **Estructura del Proyecto:** `docs/README_ESTRUCTURA_PROFESIONAL.md`
- **Changelog:** `docs/guides/CHANGELOG.md`

### Memoria del Proyecto
- **Decisiones:** `memory-bank/decisionLog.md`
- **Contexto del Producto:** `memory-bank/productContext.md`
- **Progreso:** `memory-bank/progress.md`
- **Patrones del Sistema:** `memory-bank/systemPatterns.md`
- **Contexto Técnico:** `memory-bank/techContext.md`
- **Contexto Activo:** `memory-bank/activeContext.md`

### Sistema de Desarrollo CENF
- **Ubicación:** `C:\Dropbox\DOC.RECA\06-Software\equipo-programacion-cenf\`
- **Guía de Inicio:** `GUIA-INICIO.md`
- **README:** `README.md`

### Archivos de Configuración
- **Version Info:** `config/version_info.txt`
- **Requirements:** `requirements.txt`
- **Setup:** `setup.py`
- **PyProject:** `pyproject.toml`

---

## 📊 ESTADO DEL PROYECTO

### Git Status
```bash
M config.json.example
M lang/en.json
M lang/es.json
M requirements.txt
M ui/app.py
?? backend/startup_manager.py
```

### Branch Actuales
- `main` - Rama principal
- `feature/pro-version` - Funcionalidades PRO
- `public-release` - Release público
- `temp_fresh_start` - Rama actual de trabajo

### Commits Recientes
1. **6048094** - Cleanup junk files and update version to 0.9.4
2. **64fed65** - Official release 0.9.4: Fix API key decoding, update Repo URL
3. **8db52dd** - Fix build script path and finalize v0.9.4 release
4. **1d6514b** - Implement key obfuscation, fix process termination
5. **8c8cddd** - Release v0.9.4 - Configuration fixes and API key encoding

---

**Fin del documento de memoria.**

Para actualizar este archivo, consultar con el equipo de desarrollo o verificar los archivos en `memory-bank/`.
