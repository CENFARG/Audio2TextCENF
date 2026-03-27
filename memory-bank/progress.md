# Progress

This file tracks the project's progress using a task list format.
2025-05-06 20:20:49 - Log of updates made.
2026-03-18 12:00:00 - Updated for v0.10.0 release.
2026-03-22 10:00:00 - Updated for v0.11.0 release.

*

## Completed Tasks

### v0.10.0 - Release Major (2026-03-18)

- ✅ **FASE 1: Post-Procesamiento con LLM**
  - ✅ `backend/post_processor.py` creado (450+ líneas)
  - ✅ Vocabularios técnicos implementados (ia_tech.json, general.json)
  - ✅ Normalización de vocabulario AI/tech
  - ✅ Restauración de puntuación y capitalización
  - ✅ Eliminación de muletillas y repeticiones
  - ✅ Soporte para español rioplatense

- ✅ **FASE 2: Migración a Flet**
  - ✅ `ui_flet/main.py` creado (~1,100 líneas)
  - ✅ `ui_flet/components/recording_overlay.py` creado
  - ✅ Interfaz completa con Flet implementada
  - ✅ CustomTkinter preservado como legacy
  - ✅ Componentes modulares creados

- ✅ **FASE 3: Corrección UTF-8**
  - ✅ `backend/utf8_validator.py` creado (337 líneas)
  - ✅ Validación de caracteres españoles
  - ✅ Corrección automática de á, é, í, ó, ú, ñ
  - ✅ Integración en transcriber.py
  - ✅ Configuración utf8_validation en config.json

- ✅ **FASE 4: Overlay Reactivado**
  - ✅ Overlay reactivado en ui/app.py
  - ✅ Estados LED implementados
  - ✅ Temporizador en tiempo real

- ✅ **FASE 5: Actualizaciones Corregidas**
  - ✅ URL corregida a config/version.json
  - ✅ Sistema de actualizaciones funcional
  - ✅ Verificación de versión desde GitHub

- ✅ **FASE 6: Gestión de Archivos**
  - ✅ Límite de 100 archivos implementado
  - ✅ Limpieza automática (30 días)
  - ✅ Métodos maintain_audio_file_limit() y clean_old_audio_files()
  - ✅ Optimización de carga de historial

- ✅ **FASE 7: SmartScreen**
  - ✅ Documentación GUIA_SMARTSCREEN.md creada
  - ✅ Build optimizado con --noupx
  - ✅ Metadatos de versión profesionales
  - ✅ Guía de instalación para usuarios

- ✅ **Limpieza y Actualización de Memoria**
  - ✅ Carpetas __pycache__ eliminadas
  - ✅ Logs antiguos eliminados
  - ✅ Carpeta dist/ raíz limpiada
  - ✅ CLAUDE.md actualizado a v0.10.0
  - ✅ CHANGELOG.md actualizado a v0.10.0
  - ✅ CHANGELOG_EN.md actualizado a v0.10.0
  - ✅ Todas las configuraciones actualizadas a v0.10.0

### v0.11.0 - Sistema de Bloques (2026-03-22)

- ✅ **Sistema de Bloques POST-transcripción**
  - ✅ `backend/blocks/` módulo creado
  - ✅ `backend/blocks/base_block.py` - Clase base para bloques
  - ✅ `backend/blocks/block_manager.py` - Gestor de bloques
  - ✅ `backend/blocks/task_extractor_block.py` - Extractor de tareas
  - ✅ `backend/blocks/summary_block.py` - Generador de resúmenes
  - ✅ `backend/blocks/keyword_extractor_block.py` - Extractor de palabras clave
  - ✅ Pipeline: Audio → Groq/Whisper → UTF-8 → CustomVocabulary → Blocks → Output
  - ✅ Bloques POST independientes (no encadenados)

- ✅ **CustomVocabulary**
  - ✅ `backend/custom_vocabulary.py` creado (180+ líneas)
  - ✅ 7 correcciones predefinidas (zenf/cemp/cemf/senf/enf → CENF, gro/grog → Groq)
  - ✅ UI para agregar/eliminar correcciones
  - ✅ Modal para ver/editar correcciones
  - ✅ Integración en pipeline de transcripción

- ✅ **Mejoras del Historial**
  - ✅ Botón Play/Stop con toggle (▶️/⏹️)
  - ✅ Tooltips con info de archivos (nombre, fecha, tamaño, path)
  - ✅ Tooltips con transcripciones (cache desde transcriptions_log.jsonl)
  - ✅ Nombres representativos (🎤 DD/MM/YYYY HH:MM:SS)
  - ✅ Auto-refresh inteligente (solo archivos nuevos)
  - ✅ Protección contra widgets destruidos (winfo_exists)
  - ✅ Reproducción de audio no bloqueante (winsound SND_ASYNC)

- ✅ **Documentación**
  - ✅ `.engram/ESTADISTICAS_BLOQUES.md` creado
  - ✅ `docs/NVIDIA_RIVA_SETUP_V012.md` creado (para v0.12.0)
  - ✅ `scripts/nvidia_local_v012.sh` creado (para v0.12.0)
  - ✅ `scripts/nvidia_local_v012.ps1` creado (para v0.12.0)
  - ✅ `backend/nvidia_v012/nvidia_asr.py` creado (para v0.12.0)

- ✅ **Build v0.11.0**
  - ✅ Ejecutable compilado: Audio2Text_CENF_0.11.0.exe (91 MB)
  - ✅ build.py actualizado para incluir tkinter y customtkinter
  - ✅ Todas las dependencias de v0.11.0 incluidas
  - ✅ Tests de ejecución exitosos

- ✅ **Correcciones de Bugs**
  - ✅ Fix: Import error BlockManager en __init__.py
  - ✅ Fix: Encadenado incorrecto de bloques POST (ahora independientes)
  - ✅ Fix: UnboundLocalError en play_btn
  - ✅ Fix: TclError con widgets destruidos
  - ✅ Fix: Duplicación de transcripciones en auto-paste
  - ✅ Revert: Prompt de Whisper causaba alucinaciones
  - ✅ Fix: CustomVocabulary no funcionaba (diccionario invertido)

- 🔄 **NVIDIA Riva ASR**
  - ✅ Infraestructura creada (backend/nvidia_v012/, docs, scripts)
  - ✅ Documentación completa
  - ⏳ Integración pendiente para v0.12.0
  - ⏳ UI de configuración pendiente para v0.12.0

### v0.12.0 - NVIDIA Riva ASR (2026-03-23)

- ✅ **NVIDIA Riva ASR Integrado**
  - ✅ `backend/nvidia_asr.py` integrado desde nvidia_v012/
  - ✅ Integración completa en `backend/transcriber.py`
  - ✅ Método `_init_nvidia_client()` para inicialización
  - ✅ Método `get_transcription_service()` para selección Groq/NVIDIA
  - ✅ Método `transcribe_with_nvidia()` para transcripción
  - ✅ Método genérico `transcribe()` para routing
  - ✅ `reload_client()` actualizado para ambos servicios
  - ✅ Pipeline: Audio → Groq/NVIDIA → UTF-8 → CustomVocabulary → Blocks → Output

- ✅ **Configuración NVIDIA**
  - ✅ `config.json.example` actualizado con opciones NVIDIA
  - ✅ `nvidia_api_key`: Clave API de NVIDIA
  - ✅ `asr_provider`: "groq" o "nvidia"
  - ✅ `nvidia_enabled`: true/false para habilitar
  - ✅ `nvidia_mode`: "cloud" (API key) o "local" (Docker)

- ✅ **Localización NVIDIA**
  - ✅ `lang/es.json` actualizado con strings NVIDIA
  - ✅ `nvidia_api_key_placeholder`: Instrucciones de API key
  - ✅ `asr_provider_label`: Selector de servicio
  - ✅ `asr_provider_groq`: "Groq (Whisper Large v3)"
  - ✅ `asr_provider_nvidia`: "NVIDIA Riva (parakeet-ctc-0.6b-es)"
  - ✅ `nvidia_mode_label`: Modo cloud/local
  - ✅ `nvidia_setup_guide`: Guía de instalación

- ✅ **Build v0.12.0**
  - ✅ Especificación actualizada a v0.12.0
  - ✅ Corrección: tkinter/customtkinter removidos de excludes
  - ✅ Ejecutable compilado: Audio2Text_CENF_0.12.0.exe (90 MB)
  - ✅ Ejecución exitosa con NVIDIA integrado
  - ✅ Todos los servicios cargando correctamente

### v0.9.x - Previous Releases

- ✅ Crear nueva versión del transcriptor llamada "audio2text CENF 0.7.3"
- ✅ Implementar sistema de almacenamiento de archivos de audio en carpeta 'audio'
- ✅ Crear sistema de almacenamiento de logs de transcripciones en formato JSON
- ✅ Diseñar interfaz de configuración con pestañas para rutas y opciones de guardado
- ✅ Implementar sistema de configuración de teclas de acceso rápido (F1-F12)
- ✅ Crear funcionalidad para mostrar tamaño total de archivos de audio guardados
- ✅ Implementar botón de borrado de archivos de audio con confirmación
- ✅ Crear indicador del tamaño actual del log de transcripciones
- ✅ Implementar configuración de rutas personalizadas para audio y logs
- ✅ Agregar opciones de configuración para habilitar/deshabilitar guardado de audio y logs
- ✅ Crear sistema de configuración de teclas personalizadas (teclado y mouse)
- ✅ Implementar funciones CRUD para gestión de configuraciones
- ✅ Crear sistema de gestión de archivos con funciones de limpieza y mantenimiento
- ✅ Actualizar interfaz de usuario para incluir nuevas funcionalidades
- ✅ Implementar sistema de persistencia de configuraciones
- ✅ Todas las mejoras de interfaz de configuración implementadas exitosamente
- ✅ Aplicación completamente funcional con todas las características solicitadas
- ✅ Script de PowerShell creado para solucionar problema de ejecución de GUI
- ✅ Documentación completa y detallada creada
- ✅ Archivo de especificación (.spec) para PyInstaller creado
- ✅ Sistema de sonidos y prioridades de audio implementado
- ✅ Tecla F12 seleccionada como opción menos conflictiva
- ✅ Todas las mejoras adicionales del usuario implementadas exitosamente
- ✅ Problema de audio latente solucionado (nueva instancia PyAudio por grabación)
- ✅ Configuración integrada como pestañas en ventana principal
- ✅ Sistema de configuración de teclas completamente funcional
- ✅ Manejo robusto de errores de audio con limpieza automática
- ✅ Sistema de sonidos optimizado y estable
- ✅ Error "'str' object has no attribute 'decode'" solucionado
- ✅ Ventana reducida de 450x400 a 380x320 píxeles
- ✅ Sonidos más rápidos y con mejor calidad (44100Hz)
- ✅ Tiempo máximo configurable con combobox (1, 2, 3, 5, 10, 15 minutos)
- ✅ Sistema de API key seguro implementado
- ✅ Soporte para variables de entorno (GROQ_API_KEY)
- ✅ Validación automática de API key al iniciar aplicación
- ✅ Sistema de modos DESARROLLO/PRODUCCIÓN implementado
- ✅ Sistema de diseño unificado con paleta de colores profesional
- ✅ Jerarquía tipográfica estandarizada aplicada
- ✅ Sistema de espaciado consistente usando múltiplos de 8px
- ✅ Componentes reutilizables diseñados según guía de patrones
- ✅ Barra superior rediseñada eliminando duplicación con Windows
- ✅ Layout reorganizado agrupando elementos lógicamente
- ✅ Indicadores visuales profesionales para estados de grabación/transcripción

## Current Tasks

  - ✅ **v0.10.0 COMPLETADO**: Todas las fases del roadmap implementadas exitosamente
  - ✅ **v0.11.0 COMPLETADO**: Sistema de Bloques, CustomVocabulary, Historial mejorado
  - ✅ **v0.12.0 COMPLETADO**: NVIDIA Riva ASR integrado y funcional
  - 🎯 **Próximos pasos**: Publicar releases en GitHub

## Next Steps

- 📦 **v0.13.0 (Roadmap)**:
  - [ ] Logo renovado
  - [ ] Selector de emojis
  - [ ] Skills de Audio2Text
  - [ ] Agente Audio2Text

- 🚀 **v1.0.0 (Roadmap)**:
  - [ ] Versión para Linux y macOS
  - [ ] API REST para integración
  - [ ] Modo batch para múltiples archivos
  - [ ] Interfaz web opcional
  - [ ] Tests automatizados completos