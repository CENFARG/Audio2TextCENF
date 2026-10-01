# Audio2Text CENF v.0.15.12 — Streaming 25s + estabilidad 12 min

> **Tag:** `v.0.15.12` (annotated) — commit `3b11fcc` sobre `c5e8864` (v.0.15.11) — rama `fix/v0.15.1-ui-polish`
> **Artefacto:** `Audio2Text_CENF_v.0.15.12.exe` — 38.25 MB (40,107,235 bytes) — `FileVersion 0.15.12.0` — SHA256 `1FEEE400E08748C3E5B65CDE486EB793C15921589327127B2453DFB26F28F6BA`

---

## Cambios

Bump display/canónico **0.15.11 → 0.15.12** — 9 archivos, sin cambios funcionales (Slice C ya en v.0.15.11). Sincronización HC-05 single-source:

- `pyproject.toml` `version = "0.15.12"` (canónica)
- `backend/config_manager.py` `app_version` `0.15.11 → 0.15.12`
- `lang/es.json` + `lang/en.json` `app_title` `v.0.15.11 → v.0.15.12`
- `config/version_info.txt` + `config/version_info_GENERAL.txt` `filevers (0,15,11,0)→(0,15,12,0)` `FileVersion/ProductVersion 0.15.11.0→0.15.12.0`
- `scripts/build_GENERAL_v2.py` `APP_VERSION` + header
- `scripts/check_version.py` `EXPECTED_FALLBACK 0.15.11→0.15.12` + docstring
- `README.md` badge `0.13.0 → 0.15.12`

```bash
git diff --stat c5e8864..3b11fcc  # 9 files changed, 23 insertions(+), 23 deletions(-)
```

---

## Slices A/B/C — resumen completo (desde v.0.15.9)

Release v.0.15.12 consolida **A+B+C** completos. Cambios funcionales ya incluidos desde v.0.15.11; esta versión solo actualiza display/versión para distribución:

### Slice A — Hardening (17e8c20)
- Timeout 30s por chunk, pre-check 413 >25 MB fail-fast
- 429 retry x3 backoff+jitter + `Retry-After` + circuit-breaker 3×429 → 60s open
- Progress `Chunk X/Y ETA` vía queue crítica (maxsize 64, ~28 chunks para 720s/25s)
- Checkpoint `.partial.txt` flush/fsync orden preservado, WAV conservado en fallo/parcial
- Logger determinístico `logs/transcription_debug.log` flush per record
- `audio_chunker` split_on_silence target 25s max 29s, `ui/app` timer_queue poll progress+limit+overlay crítico
- Tests: `tests/test_long_transcription_hardening.py` (652 líneas) + `tests/test_12min_real_repro.py` (355 líneas)

### Slice B — Parallel workers 3 (f6f46ef)
- `ThreadPoolExecutor` 3 workers (configurable 2–4 vía `groq_parallel_workers`, clamp [2,4])
- Orden preservado por índice, `as_completed` + checkpoint thread-safe, `latency+queue_depth` logging
- Timeout 30s por future, global deadline 700s, speedup ~2.5×
- `config_manager`: `max_recording_time` CAP 720s (12 min) + `groq_parallel_workers=3` + clamps
- CAP TRANSITORIO 720s — reevaluar post-B

### Slice C — Streaming incremental 25s (c5e8864) ⭐
- Snapshot cada **25s durante grabación** (`STREAM_INTERVAL_S`) con `ThreadPoolExecutor` 2 workers **separado** de Slice B
- `streaming_ordered dict` + `streaming_lock` + `pending set` + persistencia incremental `.partial_stream.txt`
- UI streaming event `En vivo Chunk cur/total` vía `status_label` + `timer_queue`
- Post-stop merge **<6s**: solo 1–2 chunks restantes (test sintético 720s mock), orden preservado aunque completions desordenadas
- 429/413/timeout handling sin bloquear grabación (log `STREAM`, no propaga)
- Tests: `tests/test_streaming_slice_c.py` 287 líneas (intervalo/pool/orden/errores)

---

## Corrección bloqueo 12 min — join deadlock

- **Fix:** `ca55f84 fix(audio2text): avoid recording thread self-join` — evita `thread.join()` desde el propio thread de grabación (deadlock que congelaba la app al llegar a 12 min / 720s).
- **Complemento:** Slice A+B+C + `TRANSIENT_CAP_S = 720` con deadline/guardas y handling robusto de `max_recording_time`.
- **Efecto:** grabaciones largas (hasta 12 min) no bloquean UI ni dejan hilos huérfanos; el límite es explícito y testeado.

---

## Validación — 7 PASS (HC-05)

Validado con `python scripts/check_version.py` — fuente canónica `pyproject.toml`:

```
pyproject.toml ............... PASS (0.15.12)
backend/config_manager.py .... PASS (app_version 0.15.12)
lang/es.json ................. PASS (app_title v.0.15.12)
lang/en.json ................. PASS (app_title v.0.15.12)
config/version_info.txt ...... PASS (0.15.12.0 / filevers 0,15,12,0)
config/version_info_GENERAL .. PASS (0.15.12.0 / filevers 0,15,12,0)
scripts/build_GENERAL_v2.py .. PASS (APP_VERSION 0.15.12)
README badge ................. PASS (0.15.12)
```

> HC-05 7 PASS — sin cambios funcionales respecto a v.0.15.11 validada. `docs/informes` históricos preservados intencionalmente sin bump (baseline v.0.15.11).

**Binario verificado:**
- `FileVersion: 0.15.12.0` / `ProductVersion: 0.15.12.0` — `CompanyName: CENF`, `OriginalFilename: Audio2Text_CENF_v.0.15.12.exe`

---

## Instalación

1. Descargar `Audio2Text_CENF_v.0.15.12.exe` desde **Assets** de este release (abajo).
2. Ejecutar directamente (portable, no requiere instalación). Windows puede mostrar SmartScreen — elegir "Más información" → Ejecutar.
3. Primera ejecución crea `%APPDATA%/Audio2TextCENF/` con config y `logs/transcription_debug.log`.

---

## Verificación versión

Tras ejecutar, confirmar `v.0.15.12` en tres lugares:

- **Título de ventana:** `Audio2Text CENF v.0.15.12`
- **Bandeja del sistema (tray):** tooltip / menú muestra `v.0.15.12`
- **Pestaña Info:** versión `0.15.12` dentro de la app
- **Propiedades del archivo:** clic derecho `Audio2Text_CENF_v.0.15.12.exe` → Propiedades → Detalles → Versión de archivo `0.15.12.0`

Si alguno muestra `0.15.11`, descargar nuevamente el asset de **este** release (no caché).

---

## Rollback

Para volver a v.0.15.11:

```bash
# Opción A — descargar binario anterior
gh release download v.0.15.11 --repo CENFARG/Audio2TextCENF --pattern "*.exe"

# Opción B — checkout tag
git fetch origin tag v.0.15.11 --force
git checkout v.0.15.11
```

Releases anteriores permanecen disponibles en https://github.com/CENFARG/Audio2TextCENF/releases

---

## Docs / Informes

- `docs/informes/ROADMAP_AUDIO2TEXT_MASTER.md` — roadmap maestro (estado estable, baseline `c5e8864`, límites explícitos Slice C)
- `docs/informes/APRENDIZAJE_AUDIO2TEXT_STREAMING_v0.15.11_20260828.md` (y `.html`) — aprendizaje streaming v0.15.11, decisiones, métricas sintéticas y deuda técnica

> Nota: informes preservados en `v.0.15.11` intencionalmente — esta release solo bump de versión.

---

## Links

- **Repositorio:** https://github.com/CENFARG/Audio2TextCENF
- **Este release:** https://github.com/CENFARG/Audio2TextCENF/releases/tag/v.0.15.12
- **Commits:** https://github.com/CENFARG/Audio2TextCENF/compare/v.0.15.11...v.0.15.12
- **Rama:** https://github.com/CENFARG/Audio2TextCENF/tree/fix/v0.15.1-ui-polish
- **Issues/PRs:** no PR — release directo sobre tag (ver `fix/v0.15.1-ui-polish`)

---

*Generado 2026-08-29 — CENFARG — `HEAD 3b11fcc` — `v.0.15.12` latest.*
