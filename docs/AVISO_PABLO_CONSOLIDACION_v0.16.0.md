# Aviso a Pablo — Consolidación v0.16.0 (2026-09-25)

## Qué pasó

Tu línea de trabajo (`fix/v0.15.1-ui-polish`, v0.15.1 → v0.15.12) fue **mergeada a `main`** vía PR #3 y liberada como **v0.16.0** (tag `v0.16.0`). La rama remota `fix/v0.15.1-ui-polish` fue eliminada post-merge (los commits viven en `main` — nada se perdió).

## Qué contiene v0.16.0

- Streaming Slices A/B/C completos (hardening, pool paralelo, snapshots 25s + merge ordenado)
- **Fix de la transcripción doble**: causa raíz era el snapshot-cola streameado durante grabación (re-corte post-stop solapaba ~1.8s). Ya no streamea la cola; las grabaciones de 25–50s fusionan por el camino normal
- Sección **Archivos** dentro de la pestaña Principal (cargar / arrastrar / pegar desde portapapeles), con rechazo temprano de formatos no legibles (OGG de WhatsApp) y motivo de error por archivo
- Pestaña **Supervisor**: respuestas numeradas a tus IAs (cita + `:` + corrección), selectbox de bloques de contexto, autosave, CRUD, grabar por fragmento, "Copiar todo"
- Hotkey global `Ctrl+Alt+V`: captura el portapapeles como entrada del Supervisor (re-capturar el mismo texto reemplaza la última)
- Suite de tests: 421+ tests, 0 fallas, cobertura 64.7% (antes: 19 fallas + 16 errores)
- CI/CD arreglado: Python 3.12, pytest como gate real, build de instaladores en workflow manual
- Versionado: fuente única (pyproject.toml) + `scripts/bump_version.py` + `scripts/check_version.py` (10 fuentes validadas)

## Qué significa para vos

1. `main` es ahora la única línea activa — tus fixes de v0.15.x están todos consolidados
2. La línea Tauri sigue pausada en `feature/audio2text-v0.16.0-tauri-migration` (2 stashes)
3. Para el próximo cambio: feature branch desde `main`, como siempre
4. El backup de la línea vieja local de Gonzalo está en la branch `backup/main-4a9fd43` (solo trazabilidad, no mergear)

## Cómo construir el instalador

El workflow "Build Release" ahora corre en Windows con tu build script: Actions → Build Release → Run workflow (dispatch manual). Genera el artefacto `dist/*.exe`.
