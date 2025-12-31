# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

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
