# PROMPT PARA EL AGENTE DE PABLO — Ordenar Ramas Audio2Text

Sos el agente de programación de Pablo. Tu trabajo es ORDENAR las ramas del proyecto Audio2Text sin perder ningún cambio que Pablo haya hecho localmente sobre la versión 0.15.0.

## CONTEXTO

El proyecto Audio2Text sufrió una re-arquitectura COMPLETA entre la v0.15.0 (que Pablo conoce) y la v0.16.0 actual. El equipo de Gonzalo reescribió todo: eliminó el backend monolítico (`backend/`), eliminó la UI Flet (`ui_flet/`), y construyó una nueva arquitectura Clean Architecture (`audio2text/`) con frontend Tauri v2 + Svelte 5 (`src/`).

**El repo NO está roto.** Lo que pasa es que Pablo tiene cambios locales sobre una versión que ya no existe en la rama activa.

## ARCHIVO DE REFERENCIA OBLIGATORIO

Antes de hacer CUALQUIER cosa, leé este archivo completo:

```
handoff-pablo-ramas-20260803.md
```

Está en la raíz del repo, en la rama `feature/audio2text-v0.16.0-tauri-migration`. Contiene:
- Mapa de todas las ramas y qué tiene cada una
- Tabla de migración de imports (v0.15.0 → v0.16.0)
- Árbol de la nueva arquitectura
- Comandos para correr el proyecto
- Advertencias críticas

Si no lo tenés, hacé:
```bash
git fetch origin
git show origin/feature/audio2text-v0.16.0-tauri-migration:handoff-pablo-ramas-20260803.md
```

## TU MISIÓN — Paso a Paso

### PASO 1: Inventario de cambios de Pablo

```bash
# En el repo local de Pablo, identificá TODO lo que cambió:
git status
git stash list
git log --oneline -20
git log origin/main..HEAD --oneline 2>/dev/null
git diff --name-only origin/main 2>/dev/null
git diff --name-only --cached 2>/dev/null
```

Guardá la lista de archivos modificados/creados por Pablo. Si hay cambios sin commitear, commitealos en una rama temporal:

```bash
git checkout -b pablo-wip-backup
git add -A
git commit -m "wip: backup de cambios de Pablo antes de reorganización"
```

### PASO 2: Identificar qué tipo de cambio es cada archivo

Para cada archivo que Pablo tocó, clasificalo:

| Tipo | Qué hacer |
|---|---|
| **Archivo nuevo** (Pablo lo creó) | Se puede copiar directo, ajustando imports |
| **Archivo de `backend/`** modificado | El archivo ya NO EXISTE. Hay que portar el cambio a `audio2text/` equivalente |
| **Archivo de `ui_flet/`** modificado | La UI Flet fue ELIMINADA. Hay que rehacer el cambio en Svelte 5 (`src/`) |
| **Config** (`config.json`, etc.) | Migrar al nuevo formato nested (`audio2text/config/schema.py`) |
| **Tests** | Migrar a la nueva estructura (`tests/unit/`, `tests/infrastructure/`) |

### PASO 3: Traer la rama buena

```bash
git fetch origin
git checkout -b feature/audio2text-v0.16.0-tauri-migration origin/feature/audio2text-v0.16.0-tauri-migration
```

### PASO 4: Migrar cambio por cambio

**NO intentes `git merge` o `git cherry-pick` de la rama vieja a la nueva.** El código cambió demasiado (>12,000 líneas eliminadas, >15,000 agregadas). Va a generar conflictos imposibles.

En su lugar, para cada cambio de Pablo:

1. Leé el archivo viejo (desde `pablo-wip-backup`)
2. Buscá el equivalente en la nueva estructura
3. Aplicá el cambio manualmente con los imports nuevos
4. Commiteá cada migración con mensaje descriptivo

### PASO 5: Reglas de imports

```python
# ❌ VIEJO — NO VA A FUNCIONAR:
from backend.config_manager import ConfigManager
from backend.transcriber import Transcriber
from backend.file_manager import FileManager
from backend.blocks import BlockManager
from ui_flet.main import Audio2TextApp
import cenf_core

# ✅ NUEVO — Equivalencias:
from audio2text.config.schema import Audio2TextConfig        # era backend.config_manager
from audio2text.services.transcription_service import TranscriptionService  # era backend.transcriber
from audio2text.services.history_service import HistoryService  # era backend.file_manager
from audio2text.services.block_processing_service import BlockProcessingService  # era backend.blocks
from audio2text.api.app import create_app                    # era el entry point de ui_flet
from core_infrastructure.config import InMemoryConfigAdapter  # era cenf_core
```

### PASO 6: Verificar que nada se perdió

```bash
# Comparar lista de archivos de Pablo vs lo migrado:
# Cada archivo en pablo-archivos-cambiados.txt debe tener:
#   (a) su equivalente migrado, o
#   (b) una justificación de por qué no aplica (ej: "UI Flet eliminada, rehacer en Svelte")

# Correr tests para verificar que no rompiste nada:
pytest tests/infrastructure/ tests/config/ -v --no-cov
```

### PASO 7: Push y PR

```bash
# NUNCA pushear a main directamente
git push origin feature/audio2text-v0.16.0-tauri-migration
# O mejor: crear una rama propia para los cambios de Pablo:
git checkout -b feature/pablo-migration-fixes
git push origin feature/pablo-migration-fixes
# Y hacer PR a feature/audio2text-v0.16.0-tauri-migration
```

## REGLAS INVIOLABLES

1. **NUNCA** hacer `git push origin main` — hay archivos de modelos >100MB en el historial local que GitHub rechaza
2. **NUNCA** hacer `git push --force` a ninguna rama compartida
3. **NUNCA** borrar ramas sin confirmar con Gonzalo primero
4. **SIEMPRE** respaldar los cambios de Pablo en `pablo-wip-backup` antes de tocar nada
5. **SIEMPRE** verificar con tests después de cada migración
6. Si un cambio de Pablo no tiene equivalente claro en la nueva arquitectura, **preguntá** antes de descartarlo
7. Los cambios de UI que Pablo hizo en Flet hay que **rehacerlos en Svelte 5**, no portarlos directo

## REGLAS DE WORKSPACE

- Trabajar SOLO dentro del repo de Audio2Text
- No ejecutar comandos fuera de la carpeta del proyecto
- "No ejecutes comandos en C:/, no DEBES HACER NADA EN C:/ TE DEBES HABER EQUIVOCADO EN EL PATH QUE INTENTAS USAR"

## CÓMO CORRER EL PROYECTO NUEVO

```bash
# Backend:
cd <repo>
.\.venv\Scripts\activate
python audio2text/main.py
# → http://127.0.0.1:8765

# Frontend (terminal aparte):
cd src
pnpm install
pnpm dev
# → http://localhost:5173

# Tests:
pytest tests/infrastructure/ tests/config/ -v --no-cov
cd src && npx vitest run
```

## RESULTADO ESPERADO

Al terminar, deberías tener:
1. Rama `pablo-wip-backup` con el respaldo de todos los cambios originales de Pablo
2. Rama `feature/pablo-migration-fixes` con los cambios migrados a la nueva arquitectura
3. PR de `feature/pablo-migration-fixes` → `feature/audio2text-v0.16.0-tauri-migration`
4. Tests pasando
5. Un informe de qué se migró, qué se descartó y por qué

Si algo no cierra o hay dudas, pará y preguntale a Gonzalo antes de continuar.
