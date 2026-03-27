**[Español](CHANGELOG.md) | [English](CHANGELOG_EN.md)**

# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.11.0] - 2026-03-20

### ✨ Agregado

**Sistema de Bloques/Middles:**
- `backend/blocks/` - Sistema modular de procesamiento de transcripciones
- `backend/blocks/base_block.py` - Clase base abstracta (200 líneas)
- `backend/blocks/block_manager.py` - Gestor de pipeline (150 líneas)
- `backend/blocks/task_extractor_block.py` - Extractor de tareas (220 líneas)
- `backend/blocks/summary_block.py` - Generador de resúmenes (180 líneas)
- `backend/blocks/keyword_extractor_block.py` - Extractor de keywords (250 líneas)

**Vocabulary Extractor:**
- `backend/vocabulary_extractor.py` - Agente extractor de vocabulario (350 líneas)
- Detección automática de términos técnicos
- Gestión de vocabulario personalizado

**Testing:**
- `tests/test_blocks.py` - Suite completa de tests (350+ líneas)
- 18 tests cubriendo todos los bloques y el manager
- Coverage para integración completa

**UI CustomTkinter:**
- Configuración de bloques en tab "Configuración"
- Switches para activar/desactivar bloques
- Ventana "Ver Estadísticas de Bloques"
- Recarga dinámica de bloques

### 🔧 Cambiado
- `backend/transcriber.py` - Integración con BlockManager
- `config.json.example` - Agregada sección "blocks"
- `ui/app.py` - Configuración de bloques en UI

### 🐛 Corregido
- Manejo robusto de errores en bloques
- Validación de inputs en todos los bloques

### 📦 Distribución
- Ejecutable: `Audio2Text_CENF_0.11.0.exe` (a generar)

### 📝 Documentación
- `backend/blocks/README.md` - Guía completa del sistema
- `.engram/cloud.md` - Memoria central actualizada
- `docs/guides/CHANGELOG.md` - Este archivo

---

## [Unreleased] - 2026-03-20

### 🔁 Revertido
- **Reversión a CustomTkinter:** Migración a Flet abandonada debido a complejidad de API
  - Motivo: API de Flet 0.82.2 inconsistente, resultado estético pobre
  - Decisión: Mantener CustomTkinter como UI estable
  - Commits revertidos: 475dc17, 67626e9, dbb3400, 8b9c83d, a226b9f, 28cf6f6, ccdb3b1, cddfae0, f08fe0c
  - Código ui_flet/ preservado como referencia futura

### 📝 Documentación
- Creado `.engram/cloud.md` - Memoria central del proyecto
- Documentada decisión de reversión en memoria
- Lecciones aprendidas sobre migraciones de UI

---

## [0.10.0] - 2026-03-18

### 🎯 BREAKING CHANGES
- **Nueva arquitectura de post-procesamiento:** Sistema de normalización lingüística con LLM
- **UTF-8 Validator:** Validación y corrección automática de caracteres españoles
- **Límites de archivos:** Implementación de límite de 100 archivos con limpieza automática

### ✨ Agregado
- **FASE 1 - Post-Procesamiento con LLM:**
  - `backend/post_processor.py` (450+ líneas) - Normalización de transcripciones
  - Vocabularios técnicos: `backend/vocabulary/ia_tech.json` (1000+ términos)
  - Vocabulario general: `backend/vocabulary/general.json` (500+ términos)
  - Restauración de puntuación y capitalización
  - Normalización de vocabulario técnico (AI, Prompt, ChatGPT, Gemini)
  - Eliminación de muletillas y repeticiones
  - Soporte para español rioplatense

- **FASE 2 - Migración a Flet:**
  - `ui_flet/main.py` (~1,100 líneas) - UI completa con Flet
  - `ui_flet/components/recording_overlay.py` - Overlay con estados LED
  - Interfaz moderna basada en Flutter
  - Mejor rendimiento y cross-platform futuro
  - CustomTkinter preservado como legacy

- **FASE 3 - Corrección UTF-8:**
  - `backend/utf8_validator.py` (337 líneas) - Validador UTF-8 para español
  - Corrección automática de á, é, í, ó, ú, ñ, ¿, ¡
  - Integración en `backend/transcriber.py`
  - Configuración `utf8_validation` en `config.json`

- **FASE 4 - Overlay Reactivado:**
  - Overlay de grabación reactivado en `ui/app.py`
  - Estados LED: Ready (azul), Recording (rojo), Processing (amarillo), Error (naranja)
  - Temporizador en tiempo real

- **FASE 5 - Actualizaciones Corregidas:**
  - URL corregida de root a `config/version.json`
  - Sistema de actualizaciones completamente funcional
  - Verificación de versión desde GitHub

- **FASE 6 - Gestión de Archivos:**
  - Límite de 100 archivos de audio (`max_audio_files`)
  - Limpieza automática de archivos antiguos (30 días)
  - Métodos: `maintain_audio_file_limit()`, `clean_old_audio_files()`
  - Optimización de carga de historial

- **FASE 7 - SmartScreen:**
  - Documentación completa: `docs/GUIA_SMARTSCREEN.md`
  - Build optimizado con flag `--noupx`
  - Metadatos de versión profesionales
  - Guía de instalación para usuarios

### 🔧 Cambiado
- `backend/transcriber.py` - Integración UTF8Validator
- `backend/file_manager.py` - +150 líneas para límites y limpieza
- `backend/config_manager.py` - Configuración utf8_validation
- `ui/app.py` - Overlay reactivado, variables de historial
- `lang/es.json` y `lang/en.json` - app_title actualizado a 0.10.0
- `scripts/build.py` - Versión 0.10.0, emojis removidos
- Todos los scripts de build actualizados a v0.10.0

### 🐛 Corregido
- Bloqueos con tildes y ñ (UTF-8)
- Sistema de actualizaciones (URL incorrecta)
- Cuelgue con muchos archivos
- Título de ventana mostrando versión incorrecta

### 📦 Distribución
- Ejecutable: `Audio2Text_CENF_0.10.0.exe` (45 MB)
- Ubicación: `scripts/dist/`

### 📝 Documentación
- CHANGELOG.md actualizado a v0.10.0
- CLAUDE.md actualizado a v0.10.0
- Todas las memorias del proyecto actualizadas

---

## [0.9.2] - 2025-12-23

### 🎯 BREAKING CHANGES
- **Estructura del Proyecto:** Reorganización completa a estructura enterprise
  - Contenido movido de `audio2text_v0.9.2/` a raíz del proyecto
  - Usuarios existentes deben re-clonar el repositorio

### ✨ Agregado
- **Estructura Profesional Enterprise:**
  - Carpetas organizadas por tipo: `assets/`, `backend/`, `config/`, `docs/`, `lang/`, `scripts/`, `templates/`, `ui/`
  - Separación clara de responsabilidades
  - Build artifacts organizados por variante en `_build_artifacts/`
  
- **Archivos de Proyecto Estándar:**
  - `setup.py` - Configuración de distribución
  - `pyproject.toml` - Configuración moderna de Python
  - `LICENSE` - Licencia MIT
  - `CHANGELOG.md` - Este archivo
  - `CONTRIBUTING.md` - Guía de contribución
  - `CODE_OF_CONDUCT.md` - Código de conducta
  - `SECURITY.md` - Política de seguridad
  - `MANIFEST.in` - Archivos a incluir en distribución

- **Soluciones Anti-SmartScreen:**
  - Metadatos de versión profesionales en ejecutables
  - Build optimizado con `--noupx`
  - Documentación completa para usuarios (`docs/INSTALACION.md`)
  - Reducción esperada: 30-40% en advertencias de SmartScreen

- **Variantes Personalizadas:**
  - Build GENERAL (CENF)
  - Build CONTRERAS (Contreras Hnos)
  - Build CUTIGNOLA
  - Cada variante con logo y metadatos propios

- **Scripts de Build Automatizados:**
  - `scripts/build_all_v2.py` - Compilar todas las variantes
  - `scripts/build_GENERAL_v2.py` - Build específico GENERAL
  - `scripts/build_CONTRERAS_v2.py` - Build específico CONTRERAS
  - `scripts/build_CUTIGNOLA_v2.py` - Build específico CUTIGNOLA
  - Logs con timestamp para trazabilidad

- **Documentación Completa:**
  - `docs/README_ESTRUCTURA_PROFESIONAL.md` - Guía de arquitectura
  - `docs/INSTALACION.md` - Instrucciones para usuarios finales
  - `docs/GUIA_SMARTSCREEN.md` - Soluciones técnicas a advertencias
  - `docs/COMPLETADO_v0.9.2.md` - Changelog detallado de desarrollo
  - `docs/installer.nsi` - Script NSIS actualizado

### 🔧 Cambiado
- **Organización de Archivos:**
  - Versiones antiguas archivadas en `_old_versions_archive/` (solo local)
  - `.gitignore` actualizado para estructura limpia
  - Rutas en scripts de build actualizadas

- **Mejoras de Build:**
  - Separación de artifacts por variante
  - Logs organizados con timestamp
  - Specs organizados por cliente

### 🐛 Corregido
- Rutas incorrectas en scripts de build
- Falta de metadatos en ejecutables
- Estructura desorganizada del proyecto

### 📦 Distribución
- Ejecutables disponibles para descarga en [Releases](https://github.com/CENFARG/Audio2Text/releases/tag/v0.9.2)
- Instalador NSIS profesional incluido

---

## [0.9.0] - 2024-12-17

### ✨ Agregado
- Interfaz gráfica con CustomTkinter
- Transcripción en tiempo real con Groq API (Whisper Large v3)
- Soporte multiidioma (Español/Inglés)
- Hotkeys configurables (F1-F12)
- Panel de configuración completo
- Sistema de auto-actualización
- Integración con system tray
- Gestión automática de archivos y logs

### 🔧 Cambiado
- Migración de versión 0.8.x a arquitectura modular
- Separación de UI y backend

---

## [0.8.1] - 2024-11-XX

### ✨ Agregado
- Primera versión funcional
- Transcripción básica de audio
- Guardado de archivos WAV

---

## Tipos de Cambios

- `✨ Agregado` - para nuevas funcionalidades
- `🔧 Cambiado` - para cambios en funcionalidades existentes
- `🗑️ Deprecado` - para funcionalidades que serán removidas
- `🐛 Corregido` - para corrección de bugs
- `🔒 Seguridad` - para vulnerabilidades de seguridad
- `📦 Distribución` - para cambios en empaquetado/distribución
- `📝 Documentación` - para cambios solo en documentación

---

[0.9.2]: https://github.com/CENFARG/Audio2Text/compare/v0.9.0...v0.9.2
[0.9.0]: https://github.com/CENFARG/Audio2Text/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/CENFARG/Audio2Text/releases/tag/v0.8.1
