# Audio2Text — MASTER TASKLIST (punta a punta)

> Branch: `fix/v0.15.1-ui-polish` → PR #3 → `main`
> Reglas: reglas-cenf-maestro.yaml · SemVer 2.0.0 (GIT-007) · commits ≤250 líneas · SDD→TDD
> Detalle por track: audio2text-ux-track.md (UX), tech-debt-suite-green.md (deuda), openspec/changes/*

## A — Versionado (auditoría 2026-09-25)

Fuentes de versión detectadas: config.json `app_version` (canon runtime), pyproject.toml,
config/version_info.txt (+3 variantes), setup.py, config/version.json (manifest updater).

- [x] A1-A4. Inventario + setup.py dinámico + check_version 10 fuentes + scripts/bump_version.py atómico (8d4700d; dry-run 0.16.0 verificado; --release para version.json documentado)
- [x] A5. Tag v0.15.12 retroactivo en 3b11fcc (formato vX.Y.Z sin punto)
- [x] A6. CLAUDE.md refrescado a estado real (6270dce)
- [x] A7. Procedimiento version.json documentado en bump_version.py (solo con --release al publicar)

## B — Batch 2: bug fixes (aprobado GR 2026-09-25)

- [x] B1. BUG-1 hotkey fail-open — fail closed vía Hotkey.invalid_modifiers (c56ff0f)
- [x] B2. BUG-2 keyword min_length — regex desde config + filtro a nivel ensamblado (168d6ca)
- [x] B3. LT-3 charset API key — validación en save + check, error localizado es/en (99d6fb6)
- [x] B4. TRANSCRIPCIÓN DOBLE — RAÍZ: excepción total==1 streameaba el snapshot-cola con borde
      inestable (re-corte post-stop solapa ~1.8s) → merge re-transcribía el solape. Fix: no
      streamear la cola durante grabación (8e8f9c2; repro determinista + 2 invariantes)
- [x] B5. test_transcriber — 24/24 alineados al contrato verificado, sin bugs nuevos (f5d4090)
- [x] B6. Suite: 307 passed / 0 failed / 0 errors, cov 61.93% (2 flakes preexistentes
      order-dependent: test_12min_real_repro, test_429_retry_backoff)

## C — F1 seguimiento

- [x] C1. LT-2: probe_audio_readable (soundfile.info) rechaza no-legibles al importar con razón localizada (3db3af8; C3: sin ffmpeg, rechazo-only)
- [x] C2. LT-4: estado por archivo es (estado, razón) con choke point _mark_file_error — un solo ERROR por archivo, razón visible en UI (8fbdcff)
- [x] C4. F1.1: sección Archivos dentro de pestaña principal (fila 4, bajo transcripción); pestaña dedicada eliminada (8fbdcff)
- [ ] C5. Prueba en vivo final de GR (3 vías + OGG WhatsApp rechazado con razón + cola multi-archivo)
- [ ] C6. (futuro, decisión GR) fallback ffmpeg OGG/Opus como transcodificación opcional

## D — Deuda técnica (restante)

- [ ] D5. ruff 0 en backend/ + tests/ (línea activa)
- [ ] D6. mypy: corregir pyproject (python_version 3.8 no soportado) y pasar limpio en
      código nuevo
- [ ] D7. Strays raíz (TEST-006): test_fixes.py y backend/test_utf8_validator.py → mover a
      tests/ con markers o eliminar con justificación
- [ ] D8. (cubierto en A6)
- [ ] D9. 91 findings legacy en ui/app.py: DESPUÉS de suite verde, por zona (bare excepts,
      int() sin guard); contratos primero
- [ ] D11. Triaje de 2 flakes order-dependent: test_12min_real_repro, test_429_retry_backoff
      (pasan en aislado; fallan por orden/carga — estabilizar o aislar con marker)
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
- F1: ✅ implementada y verificada en vivo; C1/C2/C4 ✅ (3db3af8, 8fbdcff); C5 pendiente GR
- Batch 2 (B1-B6): ✅ suite 100% verde (307P/0F/0E)
- Track A versionado: ✅ (8d4700d, 6270dce, tag v0.15.12; 10 fuentes PASS)
- Batch C: ✅ (3db3af8, 8fbdcff) — 330P, cov 62.12%
- style: transcriber.py formateado con AST idéntico (a3de9e7) — fin del churn
- Siguiente: E (F2 Supervisor spec SDD) → F3 → G consolidación (v0.16.0)
