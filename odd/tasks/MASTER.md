# Audio2Text — MASTER TASKLIST (punta a punta)

> Branch: `fix/v0.15.1-ui-polish` → PR #3 → `main`
> Reglas: reglas-cenf-maestro.yaml · SemVer 2.0.0 (GIT-007) · commits ≤250 líneas · SDD→TDD
> Detalle por track: audio2text-ux-track.md (UX), tech-debt-suite-green.md (deuda), openspec/changes/*

## A — Versionado (auditoría 2026-09-25)

Fuentes de versión detectadas: config.json `app_version` (canon runtime), pyproject.toml,
config/version_info.txt (+3 variantes), setup.py, config/version.json (manifest updater).

- [ ] A1. Inventariar TODAS las ocurrencias hardcodeadas de versión (grep 0.15/0.10/0.9) y
      eliminar duplicados: una sola fuente canónica + derivados generados
- [ ] A2. Corregir setup.py (0.9.2) o deprecarlo si pyproject es el canon del packaging
- [ ] A3. scripts/check_version.py: extender a validador de consistencia entre las 5 fuentes
- [ ] A4. Script de bump atómico (scripts/bump_version.py): actualiza las 5 fuentes en un
      commit + crea tag `vX.Y.Z` (formato sin punto: v0.16.0, NO v.0.16.0)
- [ ] A5. Taguear retroactivamente los hitos que falten (v0.15.12 en el commit de release)
- [ ] A6. CLAUDE.md: refrescar a estado real (v0.15.12, faster-whisper ERRADICADO en esta
      línea, arquitectura mixins, F1/F2)
- [ ] A7. version.json de main: se actualiza SOLO al publicar release (procedure en A4)

## B — Batch 2: bug fixes (aprobado GR 2026-09-25)

- [ ] B1. BUG-1 hotkey fail-open: parse_hotkey_string descarta modificadores desconocidos →
      "win+f5" aceptado. Fix: rechazar tokens desconocidos; test ya existe (rojo)
- [ ] B2. BUG-2 keyword min_length: _extract_by_frequency hardcodea {4,} ignorando config.
      Fix: regex desde min_length configurado; test ya existe (rojo)
- [ ] B3. LT-3 charset API key: validar key al guardar/check (ASCII imprimible, strip),
      error amigable en UI en vez de crash ascii codec repetido
- [ ] B4. TRANSCRIPCIÓN DOBLE (reporte Pablo): bajo alguna condición el texto sale pegado
      dos veces. Investigar: merge post-stop de Slice C (checkpoint + merge final),
      hash guard de display_transcription (v0.15.8), doble llamado a save/display.
      Reproducir con test → fix → test verde
- [ ] B5. test_transcriber (2F+13E): triage AttributeError drift vs bugs reales
      (mismo protocolo que batch 1: tests al contrato actual; bugs reales se reportan)
- [ ] B6. Commit granular por fix + bump patch 0.15.13 al cerrar el batch

## C — F1 seguimiento

- [ ] C1. LT-2: validar legibilidad del archivo AL IMPORTAR (soundfile probe) — WhatsApp
      OGG/Opus se rechaza con razón clara en la UI, no a mitad de transcripción
- [ ] C2. LT-4: estado por archivo en la cola debe mostrar la razón de error (no solo
      "1 succeeded" con 1 log)
- [ ] C3. (decisión GR) fallback ffmpeg para OGG/Opus: transcodificar o rechazar
- [ ] C4. F1.1 RESTRUCTURE: mover la sección Archivos DENTRO de la pestaña principal
      (debajo, separada del área de texto) — elimina la pestaña dedicada
- [ ] C5. Prueba en vivo final de GR (3 vías + OGG WhatsApp + cola multi-archivo)

## D — Deuda técnica (restante)

- [ ] D5. ruff 0 en backend/ + tests/ (línea activa)
- [ ] D6. mypy: corregir pyproject (python_version 3.8 no soportado) y pasar limpio en
      código nuevo
- [ ] D7. Strays raíz (TEST-006): test_fixes.py y backend/test_utf8_validator.py → mover a
      tests/ con markers o eliminar con justificación
- [ ] D8. (cubierto en A6)
- [ ] D9. 91 findings legacy en ui/app.py: DESPUÉS de suite verde, por zona (bare excepts,
      int() sin guard); contratos primero
- [ ] D10. Limpieza scripts/ (logs de build 0.10.0, _raw_*.json, __pycache__, subcarpetas
      stray audio/backend dentro de scripts/)

## E — F2: Pestaña Supervisor de IAs (spec SDD completa antes de codear)

- [ ] E1. Spec openspec: entradas numeradas, cita "..." + ":" + corrección, selectbox de
      12 bloques de contexto (.amBotHs/contextBlocks/*.md), nueva respuesta, CRUD historial,
      auto-save JSON, copiar N/todo, estado borrador/enviada, grabar por fragmento,
      máquina de estado (ARCH-009)
- [ ] E2. TDD módulo puro (prompt builder + persistencia) antes de UI
- [ ] E3. UI CustomTkinter + i18n es/en
- [ ] E4. Prueba en vivo GR

## F — F3: Hotkey global captura portapapeles

- [ ] F1. Captura clipboard → entrada nueva del Supervisor (depende de E)
- [ ] F2. Re-copia del mismo contenido → reemplaza última entrada ordinal (no duplica)

## G — Consolidación (fecha dura: merge a main)

- [ ] G1. Revisión PR #3 completa (scope: v0.15.1→0.16.0)
- [ ] G2. Merge a main + tag v0.16.0 (SemVer: features nuevas = MINOR)
- [ ] G3. Actualizar version.json en main (updater deja de decir 0.10.0)
- [ ] G4. Comunicar a Pablo: mapa final de ramas + rama Tauri pausada (posterior)
- [ ] G5. Decisión rama Tauri (retomar/archivar) — posterior, no bloquea

## Estado

- Batch 1 deuda: ✅ (18F→5F, cov 61.29%)
- F1: ✅ implementada y verificada en vivo (pendiente C1-C5)
- Batch 2 (B1-B5): 🔄 en curso
- F2/F3/G: ⏳ cola
