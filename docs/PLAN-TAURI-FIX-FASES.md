# Plan de Fix — Audio2Text Tauri (por fases, con gestión de modelos)

> Creado: 2026-08-18 · Branch: `feat/tauri-modernization` · Working tree limpio al momento del diagnóstico.
> Este plan contiene el diagnóstico YA REALIZADO (Fase 0 completa). Las fases siguientes son ejecución.

---

## FASE 0 — Diagnóstico ✅ (COMPLETA, hecha con GLM-5.3 Max)

### Evidencia recopilada

1. **Smoke test del sidecar Python (standalone): FUNCIONA PERFECTO**
   ```
   cd D:\CENF\gentle-ai\audio2text-v0150\repo
   echo '{"command":"get_status"}' | .venv/Scripts/python.exe -m backend.sidecar_entry
   → {"status": "ok", "data": {"transcriber_ready": true, "is_recording": false}}
   → Exit code 0. Groq OK, FileManager OK, vocabulario OK.
   ```
   **Conclusión: el 100% del problema #1 está del lado Rust (resolución de rutas).**

### ROOT CAUSE del Problema #1 (sidecar no arranca)

Cuando `pnpm tauri dev` levanta la app, el proceso corre con `cwd = <repo>\src-tauri`
(el CLI de Tauri invoca cargo desde ahí). El código en `lib.rs` (~líneas 87-94) prueba
SOLO estos candidatos:

| Candidato | Ruta resuelta | ¿Existe? |
|---|---|---|
| `cwd/.venv` | `src-tauri\.venv` | ❌ |
| `exe_dir/.venv` | `src-tauri\target\debug\.venv` | ❌ |
| `exe_dir/../.venv` | `src-tauri\target\.venv` | ❌ |

El venv real está en `<repo>\.venv` = **`cwd/../.venv`, el único candidato que FALTA en la lista**.
Como ninguno existe, cae al fallback `cwd/.venv/...` (inexistente) → `Command::new()` →
`os error 3` (path not found). Exactamente el error reportado.

### BUGS LATENTES adicionales (encontrados en el mismo análisis)

- **#1b — Working dir del hijo incorrecto**: `lib.rs` línea ~111 pasa `Some(&cwd)` como
  working dir del proceso Python → hijo con cwd = `src-tauri` → `python -m backend.sidecar_entry`
  NO encuentra el paquete `backend` (Python `-m` resuelve módulos desde el cwd).
  El smoke test prueba que con cwd = repo root funciona. **Hay que pasar el repo root.**
- **#1c — Restart del health check pierde el working dir**: `sidecar.rs` línea ~321 llama
  `state.spawn(&python, "backend.sidecar_entry", None)` → el restart hereda el cwd del
  proceso Rust (src-tauri) → mismo fallo en cada auto-restart. **Guardar working_dir en el estado.**
- **#2 real del hotkey**: "HotKey already registered" es error a nivel OS → OTRO proceso
  retiene el shortcut. Causa casi segura: instancia zombie de la propia app (tiene system
  tray; si el cierre la manda a la bandeja, sobrevive). NO hay plugin single-instance
  (verificado en Cargo.toml). Además hay DOS sistemas de hotkey duplicados: Rust registra
  Ctrl+Alt+F10 hardcodeado Y el sidecar Python tiene su propio listener ("Escuchando hotkey: f9")
  — discrepancia de paridad con la legacy (f9 toggle). Decisión de diseño para Fase 4.

---

## FASE 1 — Fix del spawn del sidecar (RAÍZ de todo)

**Modelo recomendado: GLM-5-Turbo (Thought level Off) o GLM-5.3 Low.** Es aplicación
mecánica de este patch ya diseñado. **No requiere razonamiento adicional.**

### Patch 1a — `src-tauri/src/lib.rs` (reemplazar bloque líneas ~79-111)

```rust
// Repo root determinístico en dev: CARGO_MANIFEST_DIR = <repo>/src-tauri (compile-time)
let manifest_root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
    .parent()
    .map(|p| p.to_path_buf());

let cwd = std::env::current_dir().unwrap_or_else(|_| std::path::PathBuf::from("."));
let exe_dir = std::env::current_exe()
    .ok()
    .and_then(|p| p.parent().map(|p| p.to_path_buf()))
    .unwrap_or_else(|| cwd.clone());

// Candidatos de repo root en orden de prioridad
let mut roots: Vec<std::path::PathBuf> = Vec::new();
if let Some(r) = manifest_root {
    roots.push(r);
}
roots.push(cwd.clone());
if let Some(p) = cwd.parent() {
    roots.push(p.to_path_buf());              // <-- el candidato que faltaba (cwd/../.venv)
}
roots.push(exe_dir.join("..").join(".."));    // target/debug -> repo
roots.push(exe_dir.join(".."));

let script_path = if cfg!(target_os = "windows") {
    std::path::Path::new(".venv").join("Scripts").join("python.exe")
} else {
    std::path::Path::new(".venv").join("bin").join("python3")
};

let (repo_root, python) = roots
    .iter()
    .map(|r| (r.clone(), r.join(&script_path)))
    .find(|(_, p)| p.exists())
    .unwrap_or_else(|| (cwd.clone(), cwd.join(&script_path)));
```

Y en el spawn (~línea 107-112), cambiar `python_str`/`cwd` por:

```rust
log::info!(
    "Sidecar Python: {} (repo root: {})",
    python.display(),
    repo_root.display()
);
match sidecar_for_spawn.spawn(
    &python.to_string_lossy(),
    "backend.sidecar_entry",
    Some(&repo_root),   // <-- repo root, NO cwd
) {
```

### Patch 1b — `src-tauri/src/sidecar.rs`

1. En `struct SidecarInner` agregar campo: `working_dir: Option<std::path::PathBuf>,`
   (inicializar en `None` en `SidecarState::new()`).
2. En `spawn()`, junto con `inner.python_path = ...`, agregar:
   `inner.working_dir = working_dir.map(|d| d.to_path_buf());`
3. En `start_health_check()` (~líneas 310-321), cambiar el bloque de lectura de
   `python` para leer también `working_dir`, y llamar:
   `state.spawn(&python, "backend.sidecar_entry", working_dir.as_deref())`
   en lugar de `None`.

### Verificación Fase 1

```bash
cd src-tauri && cargo test          # deben pasar los 6 tests existentes de sidecar
cd .. && pnpm tauri dev             # buscar en logs:
# "Sidecar Python: ...repo root: D:\CENF\gentle-ai\audio2text-v0150\repo"
# "Sidecar spawned successfully"
# Sin "Failed to spawn sidecar"
```

**Commit atómico 1**: `fix(tauri): resolve sidecar python/repo root via manifest dir + candidates`
(sin co-author, sin push — el push a CENFARG/Audio2TextCENF solo si Pablo lo pide).

---

## FASE 2 — Hotkey: single-instance + no-fatal

**Modelo recomendado: GLM-5-Turbo (Thought Off).** Mecánico.

1. Agregar a `src-tauri/Cargo.toml`: `tauri-plugin-single-instance = "2"`
2. En `lib.rs`, PRIMER plugin del builder:
   ```rust
   .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
       if let Some(w) = app.get_webview_window("main") {
           let _ = w.show();
           let _ = w.set_focus();
       }
   }))
   ```
3. En `hotkeys.rs::register_default_hotkey`: si el error contiene
   "already registered" (case-insensitive) → `log::warn!` con mensaje claro
   ("otra instancia retiene el shortcut — cerrala desde el tray") y devolver `Ok(())`
   para que no se reporte como error fatal en UI.
4. Durante dev: antes de `pnpm tauri dev`, matar zombies si los hay
   (`taskkill /IM audio2text-tauri.exe /F` o el nombre del binario en target/debug).

**Verificación**: dos `pnpm tauri dev` simultáneos → el segundo enfoca la primer ventana
en vez de duplicar proceso. Logs sin error de hotkey.
**Commit atómico 2**: `fix(tauri): single-instance guard + non-fatal hotkey registration`

---

## FASE 3 — Verificación end-to-end

**Modelo recomendado: GLM-5.3 High.** Interactivo (micrófono, Groq API, UI). Si algo
rompe en la cadena hace falta criterio de debugging.

Checklist:
1. `pnpm tauri dev` → sidecar vivo (health_check events en frontend).
2. Grabar desde botón UI y desde hotkey → overlay aparece con timer.
3. Parar → esperar Groq → texto visible en el panel.
4. Historial → entradas leídas de `transcriptions_log.jsonl`.
5. Auto-paste (si está en config).
6. Matar el proceso python a mano → health check lo revive Y sigue funcional
   (valida fix #1c del working dir en restart).
7. Repetir grabación post-restart.

**Commit solo si hay micro-fixes**: uno por concepto.

---

## FASE 4 — Auditoría de paridad vs CustomTkinter legacy

**Modelo recomendado: GLM-5.3 High (Max solo si la matriz de discrepancias crece mucho).**

Leer `main.py` + UI CustomTkinter vs app Tauri y armar matriz de features:
qué falta, qué difiere, qué sobra. Ítems YA detectados para incluir:
- Hotkey: legacy usa **f9** (toggle, desde config.json) vs Tauri **Ctrl+Alt+F10** hardcodeado.
- Doble sistema de hotkey (Rust global-shortcut + listener propio del sidecar Python).
  Recomendación preliminar: Rust como única fuente de verdad, desactivar el listener
  de Python cuando corre en modo sidecar.
- Overlay/tray/comportamiento al cerrar (legacy cierra, Tauri va a tray).
- Idioma/UI strings, settings expuestos, historia/clear, auto-paste.

Output: matriz de discrepancias priorizada → insumo de Fase 5.

---

## FASE 5 — Fixes de paridad + pulido UI

**Modelo según ítem: GLM-5.3 Low o GLM-5-Turbo (Thought On) para items especificados;
High solo para los que requieran decisiones de arquitectura.**

Ejecutar la matriz de Fase 4 en orden de prioridad. Un commit por discrepancia resuelta.

---

## Reglas del repo (recordatorio)

- pnpm v11+ (NUNCA npm) · Python con el venv del repo.
- Commits atómicos, sin atribución de IA, historia lineal.
- Remote existe (CENFARG/Audio2TextCENF) pero NO pushear sin autorización explícita.
- No buildear release sin pedido explícito.
