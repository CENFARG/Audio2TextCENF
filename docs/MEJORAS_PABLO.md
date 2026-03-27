# Mejoras y Correcciones Propuestas por Pablo

> **Fecha:** 2026-03-13
> **Versión objetivo:** 0.10.0+
> **Estado:** Planificación

---

## 📋 ÍNDICE DE MEJORAS

### CRÍTICAS (Prioridad 1)
1. [Sistema de Post-Procesamiento de Transcripciones](#1-sistema-de-post-procesamiento-de-transcripciones)
2. [Migración de CustomTkinter a Flet](#2-migración-de-customtkinter-a-flet)
3. [Corrección de Problemas UTF-8](#3-corrección-de-problemas-utf-8)
4. [Reactivar Overlay de Grabación](#4-reactivar-overlay-de-grabación)

### IMPORTANTES (Prioridad 2)
5. [Sistema de Bloques/Middles](#5-sistema-de-bloquesmiddles)
6. [Agente Extractor de Vocabulario Específico](#6-agente-extractor-de-vocabulario-específico)
7. [Arreglar Actualizaciones Automáticas](#7-arreglar-actualizaciones-automáticas)
8. [Gestión de Archivos y Limpieza](#8-gestión-de-archivos-y-limpieza)
9. [Solución SmartScreen Windows 11](#9-solución-smartscreen-windows-11)

### DESEABLES (Prioridad 3)
10. [Combinaciones de Hotkeys](#10-combinaciones-de-hotkeys)
11. [Logo Renovado](#11-logo-renovado)
12. [Selector de Emojis](#12-selector-de-emojis)
13. [Skills de Audio2Text](#13-skills-de-audio2text)
14. [Agente Audio2Text](#14-agente-audio2text)

---

## 1. SISTEMA DE POST-PROCESAMIENTO DE TRANSIPCIONES

### Problema Actual
La transcripción actual es "mala" y necesita parecerse más a lo que hace ChatGPT.

### Solución Propuesta

#### 1A. Mejorar Nivel de Transcripción
- Añadir prompt de sistema especializado
- Que ya traiga vocabulario técnico adentro:
  - "Prompt"
  - "ChatGPT"
  - "Gemini"
  - Otros términos de IA

#### 1B. Limitar Tiempo de Transcripción
- Probar hasta 90 o 60 segundos máximo por transcripción
- Objetivo: Mayor estabilidad

### Implementación Técnica

**Sistema de Post-Procesamiento:**

Crear un prompt de sistema especializado que:

```python
SYSTEM_PROMPT = """
Eres un sistema profesional de normalización lingüística y reconstrucción cognitiva
especializado en postprocesar transcripciones provenientes de sistemas speech-to-text.

ROL:
Transformar habla espontánea continua en texto escrito natural, claro, coherente y
correctamente estructurado, manteniendo fidelidad total al contenido original del hablante.

OBJETIVO PRINCIPAL:
Convertir lenguaje oral en lenguaje escrito legible sin alterar significado, intención,
tono ni estilo comunicativo.

PRIORIDADES (en orden estricto):
1. Preservar significado exacto.
2. Mejorar legibilidad.
3. Restaurar estructura escrita natural.
4. Mantener autenticidad del habla.
5. Corregir errores de reconocimiento automático.

--------------------------------------------------
PROCESAMIENTO LINGÜÍSTICO
--------------------------------------------------

1. Restauración de puntuación:
- Inserta puntos, comas y signos según unidades completas de sentido.
- NO determines límites de oración únicamente por silencios del audio.
- Introduce punto solo cuando exista cierre semántico real.
- Usa comas para organizar ideas largas sin fragmentarlas innecesariamente.

2. Capitalización:
- Corrige mayúsculas iniciales correctamente.
- Evita comenzar nuevas oraciones debido a pausas respiratorias.
- Mantén nombres propios y términos técnicos correctamente capitalizados.

3. Segmentación discursiva:
- Detecta continuidad temática.
- Divide en oraciones coherentes.
- Crea nuevos párrafos únicamente ante cambio conceptual real.

4. Normalización del habla espontánea:
- Elimina repeticiones accidentales.
- Reduce muletillas ("eh", "mmm", "bueno", "digamos") solo si no aportan significado.
- Conserva énfasis cuando tenga valor expresivo.

5. Reconstrucción sintáctica mínima:
- Ajusta estructuras solo cuando la comprensión escrita lo requiera.
- NO reformules ideas.
- NO resumas contenido.

6. Inferencia prosódica:
- Interpreta cierres reales de pensamiento.
- Ignora pausas técnicas o silencios del hablante.
- Mantén continuidad cuando la idea siga activa.

--------------------------------------------------
CONVERSIÓN HABLA → ESCRITURA
--------------------------------------------------

Transforma estructuras propias del lenguaje oral en equivalentes escritos naturales:
- Corrige frases inconclusas cuando el sentido sea evidente.
- Reconstruye conectores implícitos.
- Reduce redundancias propias del habla.
- Mantén estilo conversacional sin volverlo académico.

--------------------------------------------------
VOCABULARIO TÉCNICO PRIORITARIO (IA Y TECNOLOGÍA)
--------------------------------------------------

Corrige automáticamente errores fonéticos frecuentes y normaliza:
prompt / prompts
ChatGPT
OpenAI
Gemini
Gemini CLI
CLI
API
LLM / LLMs
ASR
Whisper
Faster-Whisper
Groq
GPU
Python
Jupyter
VSCode
LangChain
RAG
token / tokens
fine-tuning
speech-to-text
text-to-speech
machine learning
deep learning

Si aparecen variantes mal reconocidas (PROM, promp, geminy, chat gp t, etc.),
corrígelas automáticamente.

--------------------------------------------------
ADAPTACIÓN REGIONAL (ESPAÑOL LATINO / RIOPLATENSE)
--------------------------------------------------

- Interpreta correctamente pronunciaciones regionales.
- Resuelve ambigüedad entre B/V según contexto léxico.
- Corrige préstamos del inglés usados en español técnico.
- Mantiene modismos naturales sin neutralizar identidad lingüística.

--------------------------------------------------
REGLAS CONDICIONALES DE DECISIÓN
--------------------------------------------------

SI una oración es excesivamente larga → dividir en límites semánticos naturales.
SI existe pausa sin cambio conceptual → continuar misma oración.
SI cambia el tema → iniciar nuevo párrafo.
SI una expresión oral genera ambigüedad escrita → aclarar mínimamente sin agregar información.
SI detectas listado implícito → estructurarlo correctamente.
SI aparece autocorrección del hablante → conservar solo la versión final.

--------------------------------------------------
RESTRICCIONES ABSOLUTAS
--------------------------------------------------

NO agregar información.
NO interpretar intenciones.
NO resumir.
NO cambiar registro lingüístico.
NO formalizar artificialmente.
NO inventar puntuación dramática.
NO modificar significado.

--------------------------------------------------
FORMATO DE SALIDA
--------------------------------------------------

Devuelve únicamente el texto final normalizado, fluido y listo para lectura humana profesional.
Sin explicaciones adicionales.
"""
```

### Archivos a Modificar
- `backend/transcriber.py` - Añadir post-procesamiento
- `lang/es.json` - Añadir strings para UI
- `lang/en.json` - Añadir strings para UI

### Archivos a Crear
- `backend/post_processor.py` - Módulo de post-procesamiento

---

## 2. MIGRACIÓN DE CUSTOMTKINTER A FLET

### Problema Actual
- CustomTkinter tiene limitaciones
- UTF-8 issues
- Difícil mantenimiento

### Solución Propuesta
Migrar a **Flet** (framework basado en Flutter)

### Beneficios
- UI moderna y responsive
- Mejor rendimiento
- Cross-platform (Windows, Linux, macOS, web)
- Componentes modernos pre-construidos
- Mejor manejo de UTF-8

### Plan de Migración

#### Fase 1: Preparación
1. Crear rama `feature/flet-migration`
2. Instalar dependencias de Flet
3. Estudiar documentación de Flet
4. Crear mockup de nueva UI

#### Fase 2: Backend (Sin cambios)
- Backend se mantiene igual
- Solo adaptar interfaces si es necesario

#### Fase 3: Frontend
1. Crear nueva estructura en `ui_flet/`
2. Migrar componente por componente:
   - Main app
   - Recording overlay
   - Configuration panel
   - Transcription history
   - Update tab
   - Tutorial

#### Fase 4: Testing
1. Probar cada componente
2. Integración con backend
3. Testing completo de UI

#### Fase 5: Build
1. Actualizar scripts de build
2. Probar compilación
3. Verificar tamaño de ejecutable

### Archivos a Modificar
- `requirements.txt` - Añadir `flet`
- `scripts/build_*_v2.py` - Actualizar para Flet
- `ui/app.py` - Reescribir en Flet

### Archivos a Crear
- `ui_flet/` - Nueva estructura de UI en Flet
- `docs/flet-migration-guide.md` - Guía de migración

---

## 3. CORRECCIÓN DE PROBLEMAS UTF-8

### Problema Actual
Bloqueos con tildes y letras ñ del español.

### Causas Posibles
1. Problema con Groq API
2. Problema con Whisper model
3. Problema con encoding de Python/Windows

### Soluciones Propuestas

#### Opción A: Mantener Groq + Post-Procesamiento
- Implementar post-procesamiento que corrija UTF-8
- Añadir validación de encoding
- Manejar excepciones de encoding

#### Opción B: Cambiar a Gemini
- Usar Gemini API para transcripción
- Verificar cuotas y costos
- Probar calidad de transcripción

#### Opción C: Usar OpenAI Directamente
- Usar Whisper API de OpenAI directamente
- API Key de OpenAI (requeriría pago)
- Mejor manejo de UTF-8

### Implementación Recomendada
**Opción A primero** (más económico)
- Si no funciona, pasar a **Opción C** (OpenAI)

### Archivos a Modificar
- `backend/transcriber.py` - Añadir corrección UTF-8
- `backend/config_manager.py` - Añadir configuración de proveedor
- `ui/app.py` - Añadir selector de proveedor

---

## 4. REACTIVAR OVERLAY DE GRABACIÓN

### Problema Actual
**RESUELTO EN FASE 4**: Overlay estaba deshabilitado temporalmente en `ui/app.py:74-76`

### Solución Implementada
1. ✅ Investigado el código del overlay (`ui/recording_overlay.py`)
2. ✅ Reactivado el overlay en `ui/app.py`
3. ✅ Verificado que el código está bien implementado
4. ✅ Actualizada documentación

### Resultado
El overlay muestra:
- LED de colores (verde=grabando, amarillo=procesando, gris=listo, rojo=error)
- Temporizador en formato MM:SS
- Ventana flotante arrastrable
- Posicionamiento en esquina superior derecha
- Always-on-top para visibilidad constante

### Archivos a Modificar
- `ui/app.py` - Reactivar overlay
- `ui/recording_overlay.py` - Debuggear si es necesario

---

## 5. SISTEMA DE BLOQUES/MIDDLES

### Descripción
Sistema de bloques de contexto aplicables a transcripciones.

### Casos de Uso
- **Extractor de tareas:** Extrae tareas de una charla
- **Vocabulario técnico:** Añade vocabulario específico
- **Resumen:** Genera resumen de la transcripción
- **Formato:** Formatea salida (markdown, bullets, etc.)

### Funcionalidades
1. **Pre-transcripción:** Aplicar bloque antes de transcribir
2. **Post-transcripción:** Aplicar bloque después de transcribir
3. **Mix de bloques:** Permitir combinación de múltiples bloques
4. **Bloques personalizables:** Usuario puede crear sus propios bloques

### Implementación

#### Estructura de Datos
```json
{
  "blocks": [
    {
      "id": "task_extractor",
      "name": "Extractor de Tareas",
      "description": "Extrae tareas de una charla",
      "type": "post",
      "prompt": "...",
      "enabled": true
    },
    {
      "id": "tech_vocabulary",
      "name": "Vocabulario Técnico",
      "description": "Añade vocabulario técnico de IA",
      "type": "pre",
      "prompt": "...",
      "enabled": true
    }
  ]
}
```

#### UI
- Panel de gestión de bloques
- Checkbox para habilitar/deshabilitar
- Botón para crear bloques personalizados
- Selector de orden de aplicación

### Archivos a Crear
- `backend/block_manager.py` - Gestión de bloques
- `backend/blocks/` - Bloques predefinidos
- `ui/blocks_panel.py` - UI de gestión de bloques

### Archivos a Modificar
- `backend/transcriber.py` - Integrar bloques
- `ui/app.py` - Añadir panel de bloques
- `lang/es.json` - Strings para bloques
- `lang/en.json` - Strings para bloques

---

## 6. AGENTE EXTRACTOR DE VOCABULARIO ESPECÍFICO

### Descripción
Agente que detecta y extrae vocabulario técnico de charlas.

### Funcionalidades
1. **Detección automática:** Detecta palabras técnicas en charlas
2. **Marcado:** Marca palabras particulares
3. **Armado de vocabulario:** Construye vocabulario automáticamente
4. **Corrección manual:** Permite corrección manual de vocabulario

### Implementación
- Usar NLP para detectar palabras técnicas
- Base de datos de vocabulario por dominio
- Interfaz para corrección manual
- Exportación de vocabulario

### Archivos a Crear
- `backend/vocabulary_extractor.py` - Extractor de vocabulario
- `backend/vocabulary_db.py` - Base de datos de vocabulario
- `ui/vocabulary_panel.py` - UI de vocabulario

---

## 7. ARREGLAR ACTUALIZACIONES AUTOMÁTICAS

### Problema Actual
Botón de actualizar no funciona.

### Solución
1. Debuggear `backend/updater.py`
2. Debuggear `ui/update_tab.py`
3. Verificar conexión con GitHub
4. Implementar solución

### Archivos a Modificar
- `backend/updater.py`
- `ui/update_tab.py`

---

## 8. GESTIÓN DE ARCHIVOS Y LIMPIEZA

### Problemas Actuales
**RESUELTOS EN FASE 6**:
- ✅ Aplicación se cuelga con muchas transcripciones - SOLUCIONADO
- ✅ Sin límite máximo de audios - SOLUCIONADO
- ✅ Sin limpieza automática - SOLUCIONADO

### Soluciones Implementadas

#### Límite Máximo de Archivos
- ✅ Límite configurable: `max_audio_files` (default: 100)
- ✅ Método `maintain_audio_file_limit()` elimina archivos más antiguos automáticamente
- ✅ Se llama automáticamente después de guardar cada audio

#### Limpieza Automática
- ✅ Método `clean_old_audio_files()` elimina archivos por antigüedad
- ✅ Configuración: `max_transcription_age_days` (default: 30 días)
- ✅ Configuración: `auto_cleanup_enabled` (default: True)
- ✅ Se ejecuta automáticamente después de cada transcripción si está activado

#### Optimización de Carga
- ✅ Método `get_audio_files_list(limit, offset)` con paginación
- ✅ `refresh_history_list()` limitado a 100 archivos máximos
- ✅ Auto-refresh optimizado: solo actualiza si hay cambios
- ✅ Detección de cambios por conteo de archivos y mtime

### Archivos Modificados
- ✅ `backend/file_manager.py` - Añadidos límites y limpieza (100+ líneas nuevas)
- ✅ `backend/config_manager.py` - Añadidas configuraciones: `max_transcription_age_days`, `auto_cleanup_enabled`
- ✅ `ui/app.py` - Optimizada carga de historial con límite de 100 archivos
- ✅ Variables de seguimiento: `last_history_file_count`, `last_history_mtime`

### Resultados
- Ya no se cuelga con muchos archivos (limiteado a 100 en UI)
- Limpieza automática de archivos antiguos (30 días por defecto)
- Auto-refresh optimizado que solo actualiza cuando hay cambios
- Historial carga máximo 100 archivos para prevenir cuelgues

---

## 9. SOLUCIÓN SMARTSCREEN WINDOWS 11

### Problema Actual
**RESUELTO EN FASE 7**:
- Windows 11 bloquea el ejecutable con SmartScreen
- ✅ SOLUCIONADO con documentación y mejores prácticas

### Soluciones Implementadas

#### ✅ Opción B: Mejores Prácticas de Build (IMPLEMENTADO)
- ✅ `--noupx` ya está en todos los scripts de build
- ✅ Metadatos de versión profesionales actualizados a v0.10.0
- ✅ Scripts de build actualizados en:
  * `scripts/build.py` (v0.10.0)
  * `scripts/build_all_v2.py` (v0.10.0)
  * `scripts/build_GENERAL_v2.py` (v0.10.0)
  * `scripts/build_CONTRERAS_v2.py` (v0.10.0)
  * `scripts/build_CUTIGNOLA_v2.py` (v0.10.0)

#### ✅ Opción C: Documentación de Instalación (IMPLEMENTADO)
- ✅ `docs/GUIA_SMARTSCREEN.md` actualizada a v0.10.0
- Guía detallada con:
  * Explicación de qué es SmartScreen
  * Por qué aparece el bloqueo (sin certificado)
  * 3 opciones para instalar correctamente
  * Verificación de seguridad con SHA-256
  * Exclusiones permanentes de Windows Security
  * Preguntas frecuentes
  * Comparación de soluciones
  * Recomendaciones por escenario

### Resultados
- Usuarios tienen guía clara para superar SmartScreen
- Builds con metadatos profesionales reducen advertencias ~30-40%
- `--noupx` reduce falsos positivos de antivirus
- Documentación completa disponible en `docs/GUIA_SMARTSCREEN.md`

### Opción A: Code Signing Certificate (FUTURO - OPCIONAL)
- Comprar certificate de code signing
- Firmar ejecutables
- Costo: ~$100-500/año
- **Nota:** Solo implementar si hay distribución masiva planificada

### Archivos Modificados
- ✅ `scripts/build.py` - Versión 0.10.0
- ✅ `scripts/build_all_v2.py` - Versión 0.10.0
- ✅ `scripts/build_*_v2.py` - Versión 0.10.0 (GENERAL, CONTRERAS, CUTIGNOLA)
- ✅ `docs/GUIA_SMARTSCREEN.md` - Actualizada a v0.10.0

---

## 10. COMBINACIONES DE HOTKEYS

### Estado Actual
Solo F1-F12 individual.

### Propuesta
Permitir combinaciones:
- Ctrl+F1, Ctrl+F2, etc.
- Alt+F1, Alt+F2, etc.
- Shift+F1, Shift+F2, etc.
- Ctrl+Shift+F1, etc.

### Archivos a Modificar
- `backend/config_manager.py` - Guardar combinaciones
- `ui/app.py` - UI para seleccionar combinaciones
- `lang/es.json` - Strings
- `lang/en.json` - Strings

---

## 11. LOGO RENOVADO

### Estado Actual
Logo genérico de CENF.

### Propuesta
Diseñar logo profesional y moderno para Audio2Text.

### Opciones
1. Contratar diseñador
2. Usar herramienta de IA (Midjourney, DALL-E)
3. Diseñarlo in-house

---

## 12. SELECTOR DE EMOJIS

### Propuesta
Insertar herramienta para levantar emojis (tipo Windows 11 con Win+.)

### Funcionalidades
- Todos los emojis disponibles
- Búsqueda de emojis
- Categorización
- No ocupar mucho espacio
- Fácil acceso y uso

### Caso de Uso
Renombrar chats con emojis

### Archivos a Crear
- `ui/emoji_picker.py` - Selector de emojis

---

## 13. SKILLS DE AUDIO2TEXT

### Propuesta
Crear skills de Audio2Text potentes.

### Ideas
- Skill para integración con otras apps
- Skill para exportación en diferentes formatos
- Skill para análisis de transcripciones
- Skill para resumen automático

---

## 14. AGENTE AUDIO2TEXT

### Propuesta
Crear agente Audio2Text avanzado.

### Funcionalidades
- Conectar con fuentes de información
- Gestionar vocabulario
- Integración con otros servicios
- Aprendizaje automático

---

## 📊 PRIORIDAD DE IMPLEMENTACIÓN

### Fase 1: Críticas (v0.10.0)
1. Sistema de post-procesamiento
2. Migración a Flet
3. Corrección UTF-8
4. Reactivar overlay

### Fase 2: Importantes (v0.11.0)
5. Sistema de bloques/middles
6. Agente extractor de vocabulario
7. Arreglar actualizaciones
8. Gestión de archivos

### Fase 3: Deseables (v0.12.0)
9. Solución SmartScreen
10. Combinaciones de hotkeys
11. Logo renovado
12. Selector de emojis
13. Skills de Audio2Text
14. Agente Audio2Text

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### Git Flow
1. Crear rama `feature/v0.10.0-mejoras` desde `main`
2. Crear sub-ramas por feature:
   - `feature/post-procesamiento`
   - `feature/flet-migration`
   - `feature/utf8-fix`
   - `feature/overlay-fix`
3. Commits frecuentes con CONTEXT
4. Pull requests con code review
5. Merge a `main` cuando esté listo

### Commits con CONTEXT
```bash
<type>(<scope>): <descripción corta>

CONTEXT:
- ESTADO: Qué se acaba de hacer
- ARCHIVOS: Lista de archivos modificados
- NEXT: Qué viene después

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>
```

### Testing
1. Unit tests para cada módulo
2. Integration tests para features
3. Manual testing de UI
4. Beta testing con usuarios

---

**Fin del documento de mejoras.**

Para más información, consultar con Pablo o revisar los archivos en `memory-bank/`.
