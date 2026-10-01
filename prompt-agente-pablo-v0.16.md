# PROMPT PARA EL AGENTE DE PABLO — Audio2Text v0.16.0

Sos el agente de programación de Pablo. Tu base de trabajo es la rama **`main`** (v0.16.0) — la línea v0.15.x que conocés fue consolidada ahí vía PR #3. No se perdió nada.

## CONTEXTO — qué cambió desde tu última versión

1. Tu línea (v0.15.1 → v0.15.12) fue mergeada completa a `main`.
2. Features nuevas construidas encima de tu trabajo:
   - **Sección Archivos** (dentro de la pestaña Principal, abajo): transcribir archivos existentes por cargar / arrastrar / pegar desde portapapeles. Backend nuevo: `backend/file_import.py` — usa TU transcriber (`backend/transcriber.py`) intacto.
   - **Pestaña Supervisor**: respuestas numeradas a IAs (cita de la IA entre comillas + `:` + tu corrección), selectbox de bloques de contexto (`.amBotHs\contextBlocks\*.md`), autosave atómico, CRUD, grabar por fragmento, "Copiar respuesta N" / "Copiar todo". Backend nuevo: `backend/supervisor_store.py`, `backend/context_blocks.py`, `backend/supervisor_recorder.py`, `ui/views/supervisor_view.py`.
   - **Hotkey global `Ctrl+Alt+V`**: captura el portapapeles como entrada del Supervisor; re-capturar el mismo texto REEMPLAZA la última entrada (anti-duplicado). Backend: `backend/hotkey_capture.py`.
   - **Fix transcripción doble** (el bug que reportaste): la causa raíz era el snapshot-cola que se streameaba durante grabaciones de 25–50s — al cortar, el re-corte solapaba ~1.8s y el merge re-transcribía el solape. Ya no se streamea la cola. Test de regresión: `tests/test_double_transcription.py`.
3. **Versionado con fuente única**: `pyproject.toml` es el canon. Para subir versión: `python scripts/bump_version.py X.Y.Z` (bump atómico de 9 fuentes + commit + tag `vX.Y.Z` sin punto). Validar siempre: `python scripts/check_version.py` (10 fuentes).
4. **CI real**: pytest 3.12 gatea el pipeline (windows-latest). Los tests marcados `@pytest.mark.order_dependent` se excluyen del gate (flakes de orden documentados).
5. **faster-whisper**: ERRADICADO en esta línea. Solo Groq (NVIDIA Riva oculto). No lo reintroduzcas.

## TU MISIÓN — paso a paso

1. `git fetch origin && git checkout main && git pull`
2. Leer en este orden: `CLAUDE.md` (header corregido) → `docs/PRUEBAS_MANUALES_v0.16.md` → `docs/informes/ROADMAP_AUDIO2TEXT_MASTER.md`
3. Toda tarea nueva: feature branch desde `main` (`git checkout -b feature/<nombre>`) — **NUNCA commitear directo a main**
4. Antes de cada commit: `.venv\Scripts\python.exe -m pytest -m "not order_dependent" -q` → 0 fallas
5. Commits convencionales (feat:/fix:/docs:/test:), ≤250 líneas por archivo, SIN atribución de IA
6. Para subir versión: solo con `bump_version.py` (nunca a mano en 5 archivos)

## ADVERTENCIAS CRÍTICAS

- **NO mergear ni cherry-pickear ramas viejas** — v0.16.0 en `main` es canónica. La línea v0.14/v0.15 vieja local de Gonzalo está preservada en `backup/main-4a9fd43` (solo trazabilidad, no tocar).
- **NUNCA commitear API keys** — existe validación de charset ahora, pero la regla es: nunca.
- **NO usar el python global**: usá `.venv\Scripts\python.exe` (el global no tiene las deps).
- **Archivos ≤400 líneas, commits ≤250 líneas** — el linter te lo va a exigir.
- `backend/transcriber.py` es crítico y tiene suite de regresión: cualquier cambio ahí = test primero (RED→GREEN).
- La rama `feature/audio2text-v0.16.0-tauri-migration` está PAUSADA (Tauri + Svelte, 2 stashes) — no retomarla sin orden expresa de Gonzalo.
