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

- [x] D5. ruff mechanical 179→103 findings (E712 25→0) + subset seguro de D9 en ui/app.py (bare excepts→except Exception, _safe_int para int() sin guard, late-binding `e` en lambdas de reproducción) (7e3bef4, 7cdae57). Restantes reportados: F541×44/F401×24/F841×16/E701×6 y F821 update_tab.py:198 — deuda menor
- [x] CI/CD: ci.yml py3.12 + pytest GATING con -m "not order_dependent"; build.yml windows-latest + build_GENERAL_v2.py, trigger solo workflow_dispatch (fin de los mails de failures por tags) (e4d2870)
- [x] Settings: campo context_blocks_dir con browse + i18n (7e3bef4)
- [x] Guía de pruebas manuales: docs/PRUEBAS_MANUALES_v0.16.md
- [x] D7. Strays raíz eliminados con justificación (test_fixes.py QA obsoleto 0.14.0; backend/test_utf8_validator.py demo sin asserts — cobertura real en tests/test_utf8_fixes.py) (2469655)
- [x] D10. scripts/ limpio: logs 0.10.0, _raw_*.json, _chunked/_original eliminados (2469655)
- [x] D11. Marker order_dependent registrado + aplicado a los 2 flakes conocidos (80e144a)
- [ ] D9. 91 findings legacy en ui/app.py: DESPUÉS de suite verde, por zona (bare excepts,
      int() sin guard); contratos primero
- [ ] D11. Triaje de 2 flakes order-dependent: test_12min_real_repro, test_429_retry_backoff
      (pasan en aislado; fallan por orden/carga — estabilizar o aislar con marker)
- [ ] D10. Limpieza scripts/ (logs de build 0.10.0, _raw_*.json, __pycache__, subcarpetas
      stray audio/backend dentro de scripts/)

## E — F2: Pestaña Supervisor de IAs (spec SDD completa antes de codear)

- [x] E1-E4. F2 Supervisor IMPLEMENTADA (cf1a28e, 13563c9): store 334l + context_blocks 179l + recorder 215l + mixin 400l; +73 tests; 23 i18n keys; spec b3ecd36. Live test GR pendiente

## F — F3: Hotkey global captura portapapeles

- [x] F1-F2. F3 hotkey capture IMPLEMENTADA (d5c4311): decide_capture_action + HotkeyCaptureHandler, re-copia reemplaza última ordinal, hotkey configurable ctrl+alt+v, +16 tests

## G — Consolidación — ✅ EJECUTADA (2026-09-25)

- [x] G1. Push + CI del PR verde (Test 3.12 gating pass · lint/bandit/mypy pass)
- [x] G2. PR #3 mergeada (a9e44d6) + bump 0.16.0 (482d10c) + tag v0.16.0 pusheado
- [x] G3. version.json 0.16.0 en main (updater actualizado)
- [x] G4. Aviso a Pablo: docs/AVISO_PABLO_CONSOLIDACION_v0.16.0.md (b4ea417, pusheado)
- [x] G5. Tauri ARCHIVADA (decisión por evaluación team-strategic: 3ª línea insostenible; absorbir diseño, no código). Revisitar solo si falla el spike RN. Detalle: docs/DECISION_RN_MULTIPLATAFORMA.md

### Notas de G
- fix/v0.15.1-ui-polish: commits consolidados en main; borrado remoto rechazado por hook (reintentar)
- Backup línea local vieja (17 commits v0.14/v0.15 no contenidos en main): branch local backup/main-4a9fd43; push remoto rechazado por pre-receive hook — renombrar (archive/...) y reintentar
- Venv repair: base python 3.12.10 desinstalado de la máquina; .venv repuntado a uv cpython-3.12.13
- Late-binding fix: lambda de error de reproducción capturaba `e` post-except (NameError diferido)

## Estado

- **v0.16.0 LIBERADA EN MAIN** (tag v0.16.0 · 482d10c) — suite 421+ tests 0F/0E, cov ~64.7%, mypy backend 0 issues
- Pendientes menores: live tests de GR (guía: docs/PRUEBAS_MANUALES_v0.16.md) · D5-residual (103 ruff) · D9-style · D11 hardening flakes · G5 Tauri · backup push remoto · release instalador (dispatch build.yml)
- Nuevo en roadmap (2026-09-25): A4 Prompter Gate + A5 Visual QA harness — alcance de A4 a definir (Supervisor vs TUI agentes vs ambos)
- A5 nivel 1 ✅: scripts/visual_qa_capture.py (captura a pedido → qa_screenshots/ → auditoría por el agente). A4 alcance: ambos (Supervisor + TUI agentes) — spec pendiente
- Hotfix post-release (4a88652): crash arranque en Python 3.12.13 (Tcl estricto rechaza pads flotantes de CTk) — monkeypatch en main.py fuerza enteros post-escalado; verificado con reproducción de la llamada exacta
- Locales: backup/main-4a9fd43 (línea v0.14/v0.15 preservada) · Tauri pausada con 2 stashes

## G — Checklist de consolidación (requiere GO de GR)

- [ ] G0. GR: live tests finales (F1 3 vías, F2 supervisor completo, F3 hotkey)
- [ ] G1. Push + revisión PR #3
- [ ] G2. Merge a main + bump 0.16.0 (bump_version.py) + tag v0.16.0
- [ ] G3. version.json en main con --release (updater deja de decir 0.10.0)
- [ ] G4. Aviso a Pablo: mapa final de ramas
- [ ] G5. Decisión rama Tauri (retomar/archivar) — post-merge


## H — RN multiplataforma (GO-CONDICIONAL — docs/DECISION_RN_MULTIPLATAFORMA.md)

- [ ] H0. Fase 0 estabilización: 103 ruff residuales + spec del protocolo de streaming en docs/ + decisión BYOK firmada (3-6 semanas)
- [ ] H1. Fase 1 spike RN kill-or-commit: Expo mínimo Android → Groq BYOK → transcript + prueba RN Web (2-3 semanas)
- [ ] H2. Fase 2 MVP móvil: historial + archivos + streaming TS + BYOK + EAS (6-10 semanas)
- [ ] H3. Fase 3: RN Web + Cafecito pasiva (4-6 semanas)
- [ ] H4. Fase 4: iOS + monetización (solo con ≥100 MAU)