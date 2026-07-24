# SPEC_07_DASHBOARD_ARCHITECTURE — Audio2Text v0.16.0 UI Inventory

> **Propósito**: Inventario exhaustivo de la interfaz actual de Audio2Text (v0.16.0)
> para fundamentar la especificación de la nueva UI Tauri v2 + TypeScript + core-cenf-ts.
> **Metodología**: spec_SDD_TDD_desing.md — Nivel 1 Macro-Arquitectura + Nivel 2 Puertos y Contratos.
> **Estado**: Inventario completo — sin decisiones de stack aún.
> 
> **NOTA**: Existen DOS interfaces implementadas:
> 1. **Flet** (`audio2text/ui/`) — UI actual, en desarrollo activo, ~1500 líneas
> 2. **CustomTkinter** (`ui/` — ELIMINADA en Slice 11, preservada en git history) — UI legacy más completa, ~1289 líneas + 6 módulos auxiliares. **La interfaz de referencia para features.**
> 
> Este documento cubre AMBAS y marca qué features existen en cuál.

---

## 1. MACRO-ARQUITECTURA ACTUAL

### 1.1 Arquitectura General

```
┌─────────────────────────────────────────────────────┐
│                   Audio2Text App                     │
├──────────────────────┬──────────────────────────────┤
│   UI Layer (Flet)    │   Backend (FastAPI)           │
│                      │                              │
│  audio2text/ui/      │  audio2text/api/             │
│  ├── app.py          │  ├── app.py                  │
│  ├── views/          │  ├── routes/ (16 endpoints)  │
│  ├── components/     │  ├── ws/ (WebSocket)         │
│  ├── state/store.py  │  ├── dependencies.py         │
│  ├── client/         │  └── lifespan.py             │
│  ├── theme/          │                              │
│  ├── hotkey_listener │  audio2text/services/ (13)   │
│  └── system_tray.py  │  audio2text/providers/ (4)   │
│                      │  audio2text/domain/ (4)      │
│  Comunicación:       │                              │
│  REST + WebSocket    │◄──── http://127.0.0.1:8765 ──┤
└──────────────────────┴──────────────────────────────┘
```

### 1.2 Ventana Principal

| Propiedad | Valor |
|---|---|
| **Tamaño** | 1100×760 (min: 800×600) |
| **Tema** | Dark/Light mode (persiste) |
| **Título** | "Audio2Text" (localizado) |
| **Idiomas** | Español (es_ES), Inglés (en_US) |
| **Framework** | Flet 0.85.0 |
| **Comunicación** | REST (httpx) + WebSocket (transcripción streaming) |
| **API URL** | http://127.0.0.1:8765 |

---

## 2. ESTRUCTURA DE VISTAS (TABS)

### 2.1 NavigationRail (Sidebar izquierda)

```
┌──────────────┐
│ [🎤]Transcribir│  ← Vista principal por defecto
│ [📋]Historial │
│ [⚙️]Ajustes  │
│ [ℹ️]Información│
│ [📦]Actualizar│
└──────────────┘
```

Toggle de idioma (ES/EN) en la parte inferior de la sidebar.

---

### 2.2 VISTA TRANSCRIBE — `TranscribeView`

**Propósito**: Captura y transcripción de audio en tiempo real.

| Componente | Función |
|---|---|
| **AudioCapture** | Botón de grabación (modo toggle o hold). LED rojo grabando, micrófono animado |
| **RecordingOverlay** | Overlay animado durante grabación con temporizador (00:00) |
| **TranscriptionPanel** | Área de texto donde aparece la transcripción en vivo |
| **StatusBar** | Barra inferior con estado del proveedor, idioma, estado de conexión, errores |
| **ContextBlocksSelector** | Panel lateral con checkboxes para seleccionar bloques de contexto pre/post |
| **AIEnhancementTrigger** | Botón para activar mejora por IA del texto transcrito |

**Estados de grabación**:
- `IDLE` → Botón de micrófono gris
- `RECORDING` → LED rojo, overlay animado, contador, chunks de audio enviados
- `PAUSED` → Pausado (no implementado, reservado)
- `PROCESSING` → Spinner, "Procesando..." (después de soltar)

**Modos de grabación**:
- `toggle` → Click para empezar, click para parar
- `hold` → Mantener presionado para grabar, soltar para parar

**Streaming**: Conexión WebSocket que envía chunks de audio WAV y recibe texto transcrito en vivo.

**Flujo**:
1. Usuario presiona grabar → POST /transcribe/start
2. Audio capturado via sounddevice → chunks WAV
3. Chunks enviados por WebSocket → respuesta con texto parcial
4. Texto aparece en TranscriptionPanel en tiempo real
5. Al parar → POST /transcribe/stop → procesamiento final
6. Bloques de contexto (si seleccionados) se ejecutan POST-transcripción
7. Opcional: AI Enhancement (corrección gramatical, puntuación)

---

### 2.3 VISTA SETTINGS — `SettingsView`

**Propósito**: Configuración completa de la aplicación.
**Auto-save**: 400ms debounce tras cualquier cambio → PUT /settings.

#### Sección Provider
| Campo | Tipo | Opciones |
|---|---|---|
| Provider activo | RadioGroup | Groq / faster-whisper / NVIDIA Riva |
| Groq API key | TextField (password) | — |
| Groq model | Dropdown | whisper-large-v3 |
| Groq base URL | TextField | https://api.groq.com |
| Groq timeout | Number | 60s |
| Groq max retries | Number | 3 |
| FW model size | Dropdown | tiny / base / small / medium / large-v3 |
| FW device | Dropdown | auto / cpu / cuda |
| FW compute type | Dropdown | auto / float16 / int8 |
| FW VAD filter | Switch | On/Off |
| NVIDIA API key | TextField (password) | — |
| NVIDIA mode | Dropdown | cloud / local |

#### Sección Audio
| Campo | Tipo | Opciones |
|---|---|---|
| Sample rate | Number | 16000 Hz |
| Channels | Number | 1 |
| Buffer seconds | Number | 600 |
| Save recordings | Switch | On/Off |
| Recordings dir | TextField | ./audio |
| Max audio files | Number | 100 |
| Auto cleanup | Switch | On/Off |

#### Sección Recording
| Campo | Tipo | Opciones |
|---|---|---|
| Mode | Dropdown | toggle / hold |
| Max recording time | Dropdown | 5min / 10min / 15min / 20min |

#### Sección Hotkeys
| Componente | Función |
|---|---|
| **HotkeyConfig** | Modifier (Ctrl/Alt/Shift) + Key (F1-F12) → graba hotkey |

#### Sección UI
| Campo | Tipo |
|---|---|
| Auto-paste transcription | Switch |
| Show transcription panel | Switch |
| Post-processing enabled | Switch |
| Context blocks enabled | Switch |
| Run on startup | Switch |
| Theme (dark/light) | Switch |
| Sounds enabled | Switch |

#### Sección Vocabulary
| Componente | Función |
|---|---|
| **VocabularyEditor** | CRUD de correcciones custom (original → corrección). |
| | Lista con toggle enabled. Agregar, editar, eliminar, guardar. |

#### Sección AI Enhancement
| Campo | Tipo | Opciones |
|---|---|---|
| Enhancement profile | Dropdown | light / medium / aggressive |
| Default provider | Dropdown | groq / openai |
| Groq model | Dropdown | llama-3.1-70b-versatile / etc. |
| OpenAI model | Dropdown | gpt-4o-mini / etc. |

---

### 2.4 VISTA HISTORY — `HistoryView`

**Propósito**: Historial de transcripciones con búsqueda y acciones.

| Componente | Función |
|---|---|
| **HistoryPanel** | Lista paginada de transcripciones (scroll infinito) |
| **EmojiPicker** | Selector de emojis para renombrar transcripciones |
| **DetailPanel** | Panel lateral con detalle de la transcripción seleccionada |

**Acciones por item**:
- Seleccionar → muestra detalle en panel derecho
- Renombrar con emoji (Win+.)
- Copiar texto al portapapeles
- Eliminar (con confirmación)
- Buscar/filtrar

**Columnas en lista**:
- Emoji (si tiene)
- Título (o fecha si no tiene)
- Idioma
- Proveedor
- Duración
- Fecha

---

### 2.5 VISTA INFO — `InfoView`

**Propósito**: Información de la aplicación y sistema.

| Sección | Contenido |
|---|---|
| Versión app | v0.16.0 |
| Versión API | (desde backend) |
| Créditos | CENF Development Team |
| Licencia | Apache 2.0 |
| Python | Versión actual |
| Plataforma | SO + arquitectura |
| Repositorio | Link a GitHub |
| Documentación | Link a docs |

---

### 2.6 VISTA UPDATE — `UpdateView`

**Propósito**: Gestión de actualizaciones.

| Componente | Función |
|---|---|
| Check button | "Buscar actualizaciones" |
| Status text | Mensaje de estado (actualizada / disponible) |
| Progress bar | Barra de descarga |
| Current version | Texto con versión actual |
| Loading spinner | Durante la verificación |

---

## 3. COMPONENTES COMPARTIDOS

| Componente | Archivo | Propósito |
|---|---|---|
| `LanguageSelect` | components/language_select.py | Toggle ES/EN en sidebar |
| `HotkeyConfig` | components/hotkey_config.py | Selector de hotkey (modifier + key) |
| `ProviderConfig` | components/provider_config.py | Radio group de proveedores |
| `VocabularyEditor` | components/vocabulary_editor.py | CRUD correcciones custom |
| `EmojiPicker` | components/emoji_picker.py | Grid de emojis para renombrar |
| `HistoryPanel` | components/history_panel.py | Lista paginada de historial |
| `RecordingOverlay` | components/recording_overlay.py | Overlay animado de grabación |
| `StatusBar` | components/status_bar.py | Barra de estado inferior |
| `TranscriptionPanel` | components/transcription_panel.py | Área de texto transcrito |
| `AudioCapture` | components/audio_capture.py | Botón de grabación + streaming |
| `ContextBlocksSelector` | components/context_blocks_selector.py | Checkboxes de bloques |
| `AIEnhancementTrigger` | components/ai_enhancement_trigger.py | Botón mejora IA |
| `SettingsPanel` | components/settings_panel.py | (Parece no usado activamente) |

---

## 4. STATE MANAGEMENT

### AppState (Observer Pattern) — `state/store.py`

| Propiedad | Tipo | Dispara callback |
|---|---|---|
| `current_view` | ViewName (enum) | `on_view_change` |
| `recording_state` | RecordingState (enum) | `on_recording_state_change` |
| `recording_elapsed_s` | float | `on_timer_tick` |
| `current_transcription_text` | str | `on_text_update` |
| `current_language` | str | `on_language_change` |
| `selected_provider` | str | `on_provider_change` |
| `is_dark_mode` | bool | `on_theme_change` |
| `error_message` | str\|None | `on_error` |
| `is_loading` | bool | `on_loading_change` |
| `selected_context_blocks` | set\[str\] | No |
| `enhancement_profile` | str | No |
| `settings` | dict | `on_settings_change` |
| `history` | list | `on_history_change` |
| `context_blocks` | list | `on_context_blocks_change` |

**Enums**:
- `ViewName`: TRANSCRIBE, HISTORY, SETTINGS, INFO, UPDATE
- `RecordingState`: IDLE, RECORDING, PAUSED, PROCESSING

---

## 5. SISTEMA DE HOTKEYS

**`hotkey_listener.py`** — Listener global vía librería `keyboard`.

| Funcionalidad |
|---|
| Registrar hotkey (F1-F12 + Ctrl/Alt/Shift) |
| Callback al presionar (inicia/para grabación) |
| Funciona con app en background |
| Hilo daemon background |
| Unregister/cleanup al cerrar |

---

## 6. SYSTEM TRAY

**`system_tray.py`** — Icono en bandeja del sistema vía librería `pystray`.

| Funcionalidad |
|---|
| Icono azul 64×64 en bandeja |
| Menú contextual: "Show", "Exit" |
| Minimizar a bandeja al cerrar ventana |
| Hilo daemon background |

---

## 7. API CLIENT

**`client/api_client.py`** — Cliente HTTP asíncrono (httpx).

| Método | Endpoint |
|---|---|
| `start()` | — (health check) |
| `get_health()` | GET /health |
| `get_settings()` | GET /settings |
| `update_settings(data)` | PUT /settings |
| `get_history(limit, offset)` | GET /history |
| `get_transcription(id)` | GET /transcription/{id} |
| `delete_transcription(id)` | DELETE /transcription/{id} |
| `update_transcription(id, data)` | PATCH /transcription/{id} |
| `get_vocabulary()` | GET /vocabulary |
| `update_vocabulary(data)` | PUT /vocabulary |
| `get_context_blocks()` | GET /context-blocks |
| `select_context_blocks(ids)` | POST /context-blocks/select |
| `enhance_text(text, profile)` | POST /enhance |
| `check_update()` | GET /update/check |
| `download_update()` | POST /update/download |
| `get_models()` | GET /models |
| `start_recording()` | POST /transcribe/start |
| `stop_recording()` | POST /transcribe/stop |
| **WebSocket** | WS /ws/transcribe (streaming) |

**Streaming client**: `client/streaming.py` — maneja WebSocket, recibe chunks de texto, actualiza store.

---

## 8. THEME

**`theme/theme.py`** — Sistema de diseño.

| Token | Detalle |
|---|---|
| Colors | Primary, secondary, background, surface, error |
| Spacing | xs, sm, md, lg, xl |
| Typography | Tamaños de fuente, pesos |
| Dark/Light | Temas completos para ambos modos |

---

## 9. MODO DE USO COMPLETO

### Flujo típico del usuario:

1. **Abrir app** → Flet window 1100×760, dark mode
2. **Hydration** → Health check → carga settings → carga context blocks → carga history
3. **Configurar** (Settings tab):
   - Seleccionar provider (Groq/faster-whisper/NVIDIA)
   - Ingresar API key (si aplica)
   - Configurar hotkey
   - Configurar vocabulario custom
4. **Transcribir** (Transcribe tab):
   - Seleccionar bloques de contexto (opcional)
   - Presionar grabar (botón o hotkey)
   - Hablar
   - Ver texto en vivo
   - Detener grabación
   - Opcional: AI Enhancement
   - Resultado final mostrado
5. **Historial** (History tab):
   - Ver transcripciones pasadas
   - Buscar/filtrar
   - Renombrar con emoji
   - Copiar texto
   - Eliminar
6. **Info** (Info tab):
   - Ver versión, créditos, licencia
7. **Actualizar** (Update tab):
   - Buscar actualizaciones
   - Descargar e instalar
8. **Cerrar** → minimiza a system tray (Show/Exit)

---

## 10. CAPABILITIES DEL FUTURO (Wishlist detectada)

Basado en el análisis del código actual y comments/documentación:

| Capability | Evidencia |
|---|---|
| Selector de emojis para renombrar | Implementado en `emoji_picker.py` |
| Skills/plugins extensibles | Mencionado en docs/MEJORAS_PABLO.md |
| Agente Audio2Text | Mencionado en roadmap |
| Modo batch (múltiples archivos) | Roadmap v1.0.0 |
| API REST para integración | Roadmap v1.0.0 |
| Interfaz web opcional | Roadmap v1.0.0 |
| Linux/macOS support | Roadmap v1.0.0 |
| Pausa durante grabación | RecordingState.PAUSED definido pero no implementado |
| Streaming bidireccional mejorado | `streaming.py` con marcas de partial/final |

---

*Documentación generada desde análisis del código fuente real de `audio2text/ui/` v0.16.0.*
*Ubicación: `openspec/changes/audio2text-v2-tauri-ui/current-ui-inventory.md`*

---

## 10. COMPARATIVA: Flet vs CustomTkinter

La UI CustomTkinter (recuperada de git history en `ui/`) tiene características que la Flet no implementa:

| Feature | Flet | CustomTkinter |
|---|---|---|
| **Tutorial interactivo de onboarding** | ❌ | ✅ 6 pasos (tooltips in-app) |
| **Reproducir audio desde historial** | ❌ | ✅ Botón play/stop por item |
| **Cache de transcripciones (JSONL)** | ❌ | ✅ Carga diferida de transcripciones |
| **Auto-refresh inteligente de historial** | ❌ | ✅ Solo refresca si hay cambios (15s) |
| **Estadísticas de bloques** | ❌ | ✅ Ventana con métricas de procesamiento |
| **Tooltips flotantes custom** | ❌ | ✅ Ventanas emergentes con diseño propio |
| **Selector de hotkeys con modifier** | ❌ | ✅ Ctrl+Alt+Shift+F1-F12 |
| **Branding link inferior** | ❌ | ✅ "CENF" link al sitio web |
| **Mostrar/ocultar transcripciones** | ❌ | ✅ Toggle por item |
| **Editar transcripción inline** | ❌ | ✅ Doble click para editar |
| **Copy rápido al portapapeles** | ✅ | ✅ Ambos |
| **Emoji picker** | ✅ | ✅ |
| **Overlay de grabación con LED+Timer** | ✅ | ✅ Ambos (Flet más moderno) |
| **Dark/Light mode** | ✅ | ✅ |
| **System tray** | ✅ | ✅ |
| **Hotkeys globales** | ✅ | ✅ |
| **Tabs (5 vistas)** | ✅ | ✅ |
| **Settings con auto-save** | ✅ | ✅ |
| **Vocabulario custom CRUD** | ✅ | ✅ |
| **Bloques de contexto** | ✅ | ✅ |
| **AI Enhancement** | ✅ | ✅ |
| **Proveedores (Groq, FW, NVIDIA)** | ✅ | ✅ |
| **Update manager** | ✅ | ✅ |
| **Streaming WebSocket** | ✅ | ❌ (usa POST sincrónico) |

**Conclusión**: La CustomTkinter tiene ~8 features que la Flet NO implementa. La UI definitiva debe combinar lo mejor de ambas: la modernidad visual de Flet + las features completas de CustomTkinter.
