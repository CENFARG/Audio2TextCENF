# HANDOFF PARA EL AGENTE DE PABLO — Estado de Ramas Audio2Text

> **Objetivo**: Ordenar las ramas sin perder el trabajo de nadie.
> **Fecha**: 2026-08-03
> **Repo**: https://github.com/CENFARG/Audio2TextCENF.git

---

## 1. MAPA DE RAMAS — Qué tiene cada una

```
origin/main (1e2d76e) ← LO QUE ESTÁ EN GITHUB, LIMPIO
    │
    ├── [17 commits locales NO pusheados — incluyen modelos .bin >100MB, NO SE PUEDEN PUSHEAR]
    │
local main (4a9fd43) ← INCLUYE mvp-integration v0.16 Flet + modelos gigantes
    │
    ├── feature/audio2text-v016-mvp-integration (94a139c)
    │   └── 4 commits: WIP Flet MVP + session reports
    │   └── NO USAR — superseded por Tauri migration
    │
    ├── feature/audio2text-v2-core-rearchitecture (archivada)
    │   └── Cambios que YA FUEON absorbidos por la rama Tauri
    │
    └── feature/audio2text-v0.16.0-tauri-migration (66bf5d9+) ← ⭐ RAMA ACTIVA, LA BUENA
        └── 34 commits: Re-arquitectura completa + UI Tauri + tests
        └── ESTA ES LA RAMA CANÓNICA
```

## 2. LO QUE CAMBIÓ — Pablo trabajó sobre v0.15.0, TODO movió

| Aspecto | v0.15.0 (Pablo conoce) | v0.16.0-tauri (actual) |
|---|---|---|
| **UI** | Flet (`ui_flet/main.py`, 1700 líneas) | **ELIMINADA**. Nueva: Svelte 5 + Tauri v2 (`src/`) |
| **Backend** | `backend/` (transcriber.py monolítico) | **ELIMINADO**. Nuevo: `audio2text/` (Clean Architecture) |
| **Entry point** | `main.py` (raíz) | **ELIMINADO**. Nuevo: `audio2text/main.py` (solo uvicorn) |
| **Imports** | `from backend.transcriber import ...` | `from audio2text.providers.adapters.groq_adapter import ...` |
| **Infra** | `cenf_core` (paquete viejo) | `core_infrastructure` (desde core-cenf-py local) |
| **Providers** | Hardcoded en transcriber.py | Ports & Adapters: `providers/ports/` + `providers/adapters/` |
| **Config** | `config.json` plano | `audio2text/config/schema.py` (Pydantic nested) |
| **Tests** | `tests/test_*.py` (raíz) | `tests/infrastructure/`, `tests/config/`, `tests/unit/` |
| **Frontend** | No existía | `src/` (Svelte 5 + Vite + Tailwind v4 + Tauri) |

## 3. LO QUE PABLO TIENE QUE HACER CON SUS CAMBIOS

### Paso 1: Identificar qué cambió Pablo

En la compu de Pablo, sobre la versión 0.15.0 que tiene local:

```bash
# En el repo de Pablo, ver qué archivos modificó:
git status
git diff --stat
git log --oneline -10

# Si tiene commits locales sin push:
git log origin/main..HEAD --oneline

# Si tiene cambios sin commitear:
git stash list
git diff --name-only
```

### Paso 2: Extraer los cambios como patches

```bash
# Crear patch de TODOS sus cambios:
git diff main > pablo-cambios-v015.patch

# O si tiene commits:
git format-patch origin/main --stdout > pablo-cambios-v015.patch

# Guardar lista de archivos tocados:
git diff --name-only origin/main > pablo-archivos-cambiados.txt
```

### Paso 3: Clonar la rama nueva y aplicar selectivamente

```bash
# Traer la rama buena:
git fetch origin
git checkout -b feature/audio2text-v0.16.0-tauri-migration origin/feature/audio2text-v0.16.0-tauri-migration

# NO aplicar el patch directo (va a fallar, cambió todo el código).
# En su lugar, revisar archivo por archivo:

# Para cada archivo en pablo-archivos-cambiados.txt:
#   1. ¿Existe en la rama nueva? → Migrar el cambio manualmente
#   2. ¿No existe? → El archivo fue eliminado o movido → buscar dónde fue
```

### Paso 4: Migración de imports (lo más común)

Si Pablo tiene código con imports viejos:

```python
# ❌ VIEJO (v0.15.0):
from backend.config_manager import ConfigManager
from backend.transcriber import Transcriber
from backend.file_manager import FileManager
from ui_flet.main import Audio2TextApp
import cenf_core

# ✅ NUEVO (v0.16.0):
from audio2text.config.schema import Audio2TextConfig
from audio2text.providers.adapters.groq_adapter import GroqProvider
from audio2text.services.transcription_service import TranscriptionService
from audio2text.api.app import create_app
from core_infrastructure.config import InMemoryConfigAdapter
```

## 4. ARQUITECTURA ACTUAL (para que Pablo entienda la nueva estructura)

```
Audio2Text/
├── src-tauri/                  ← Rust (Tauri v2 shell)
│   ├── Cargo.toml              ← tauri 2, serde, shell plugin, global-shortcut plugin
│   ├── tauri.conf.json         ← ventana 1100x760, sidecar config
│   ├── capabilities/default.json ← permisos scoped
│   └── src/lib.rs              ← 6 IPC commands + sidecar spawn/kill
├── src/                        ← Frontend Svelte 5 (NUEVO)
│   ├── index.html              ← entry point standalone (no SvelteKit)
│   ├── main.ts                 ← mount(App)
│   ├── app.svelte              ← root: Navigation + 5 views
│   ├── app.css                 ← Tailwind v4 @theme + design tokens CSS vars
│   ├── design-tokens/          ← 50 tokens Dark Goldenrod (los de Pablo)
│   └── lib/
│       ├── navigation/tabs.ts  ← tabs extensibles con feature flags + sub-tabs
│       ├── components/         ← AudioCapture, RecordingOverlay, StatusBar, etc.
│       ├── views/              ← TranscribeView, SettingsView, HistoryView, InfoView, UpdateView
│       ├── infrastructure/     ← APIClient (16 endpoints + WS + Zod), ws-reconnect, MockApiClient
│       └── state/              ← Svelte 5 runes ($state)
├── audio2text/                 ← Backend Python (Clean Architecture)
│   ├── api/                    ← FastAPI: 16 routes + WebSocket
│   │   ├── app.py              ← factory + CORS + logging
│   │   ├── routes/             ← transcribe, settings, history, vocabulary, enhance, etc.
│   │   └── dependencies.py     ← DI via ManagerRegistry
│   ├── infrastructure/         ← bootstrap (18 managers core_infrastructure)
│   │   ├── bootstrap.py        ← wiring: Config→Logger→Secrets→Errors→...→I18n
│   │   ├── registry.py         ← ManagerRegistry typed accessors
│   │   └── ports.py            ← Protocol re-exports
│   ├── providers/              ← Ports & Adapters
│   │   ├── ports/              ← TranscriptionProvider, PostProcessingBlock, MetadataProvider
│   │   ├── adapters/           ← groq_adapter, faster_whisper_adapter, nvidia_riva_adapter, mock_adapter
│   │   └── factory.py          ← TranscriptionProviderFactory
│   ├── services/               ← 13 services
│   ├── config/                 ← Pydantic schema + migration
│   ├── domain/                 ← entities: TranscriptionResult, AudioSegment, etc.
│   └── main.py                 ← SOLO uvicorn (sidecar-compatible, no UI)
├── tests/
│   ├── infrastructure/         ← 24 tests (bootstrap order, managers, smoke)
│   ├── config/                 ← 3 tests (migration idempotent)
│   ├── unit/                   ← provider tests (factory, protocols, mock)
│   └── e2e/                    ← Playwright smoke (5 tests)
└── pnpm-workspace.yaml         ← packages: ['src']
```

## 5. CÓMO CORRER EL PROYECTO AHORA

```bash
# Backend:
cd C:\Dropbox\DOC.RECA\06-Software\Audio2Text
.\.venv\Scripts\activate
python audio2text/main.py
# → Uvicorn en http://127.0.0.1:8765

# Frontend (terminal aparte):
cd src
pnpm install
pnpm dev
# → Vite en http://localhost:5173

# Tests backend:
pytest tests/infrastructure/ tests/config/ -v --no-cov

# Tests frontend:
cd src && npx vitest run          # unit
cd src && npx playwright test     # E2E
```

## 6. PROBLEMA CON LOCAL MAIN — NO PUSHEAR

**Local main tiene 17 commits que NO se pueden pushear** porque incluyen archivos de modelos `.bin` de faster-whisper que pesan 72MB y 138MB (GitHub rechaza >100MB).

**NUNCA hacer `git push origin main` desde la compu de Gonzalo.**

**Solución si hay que actualizar origin/main**: crear una rama nueva desde origin/main, hacer cherry-pick de los commits que SÍ son necesarios (sin los modelos), y hacer PR.

## 7. RESUMEN PARA EL AGENTE DE PABLO

1. **NO trabajar sobre v0.15.0** — está obsoleta
2. **Clonar `feature/audio2text-v0.16.0-tauri-migration`** — esta es la rama activa
3. **Los cambios de Pablo hay que migrarlos manualmente** — el código cambió demasiado para un merge automático
4. **Los imports cambiaron todos** — usar la tabla de migración (sección 3, paso 4)
5. **La UI ya no es Flet** — es Svelte 5 + Tauri v2, si Pablo tenía cambios de UI hay que rehacerlos en Svelte
6. **NO pushear a main desde la compu de Gonzalo** — hay modelos gigantes en el historial
7. **Preguntar a Gonzalo antes de borrar cualquier rama**

---

*Handoff generado el 2026-08-03 desde `feature/audio2text-v0.16.0-tauri-migration`.*