# ISSUES y mejoras — v0.17.0

> **Fecha:** 2026-10-28 · **Rama:** `feature/v0.17.0-pablo-feedback` · **Base:** main 32f0611
> **Origen:** feedback de Pablo sobre v0.16.1 + dirección de GR (todo directo a 0.17.0, sin 0.16.2).
> **Gates:** 595 tests passed / 0 failed · mypy 0 (83 archivos) · ruff full-repo 0 (con exclusiones explícitas).

## 1. Correcciones del feedback de Pablo (v0.16.1)

| # | Problema reportado | Causa raíz | Corrección | Commit |
|---|---|---|---|---|
| P1 | La sección de audios WhatsApp acapara espacio y achica el panel de transcripción | Sección fija siempre visible (~180px) | Sección **colapsable**: arranca en una sola fila de cabecera, se expande sola al agregar archivos y colapsa al limpiar; contador en vivo | `e8395ef` |
| P2 | "Transcribir todo" parece transcribir solo el último | El worker sí transcribe todos y guarda cada uno en historial; lo que se pisa es panel + portapapeles (cada resultado reemplaza al anterior) | Al terminar la cola, panel/portapapeles/auto-paste reciben **UN bloque combinado** con separadores `=== archivo ===` en orden de cola; guardado individual por archivo intacto; archivo único queda sin rótulo | `6d10f9b` |
| P3 | Botón "Limpiar cola" invisible (fondo igual al fondo) | Estilo fantasma `fg_color="transparent"` + borde | Color estándar de botón (azul por defecto) | `ef97dee` |
| P4 | Botones "Marcar enviada" y "🗑" de Supervisión invisibles | Mismo estilo fantasma | Color azul como los demás botones de fila | `e539f2b` |
| P5 | Icono de la ventana ("cuadrado azul") distinto al de la pestaña principal | El ícono de la **bandeja** se dibujaba en código: círculo del color primario (#2563EB, azul). Además `icono.ico` era un frame único 192×193 NO cuadrado (Windows lo escala mal) | Tray ahora renderiza `logo.png` real (`ui/branding.py`, círculo solo como fallback explícito); `icono.ico` regenerado multi-tamaño cuadrado 16–256px desde el logo (`scripts/generate_icons.py`); resolución de logo unificada para tray/pestaña/ventana | `ff70b33` |
| P6 | El tutorial no explica el sector de WhatsApp | No existía el paso | Nuevo paso "Audios de WhatsApp" apuntando a la sección (explica carga, cola y salida `=== archivo ===`) | `2601f1e` |
| P7 | No queda claro el mejorador de prompt (Prompter) | Vive dentro de Supervisión, que en este release va oculta | Paso de tutorial **condicional**: solo aparece con `supervisor_tab_enabled: true` (dev). UX definitiva cuando Supervisión vuelva (roadmap) | `2601f1e` |

## 2. Desactivado en este release

- **Pestaña Supervisión** (incluye Prompter Gate A4 y bloques de contexto): desactivada por defecto — hay que trabajarla más y mejor antes de exponerla a clientes.
  - Reactivación dev: `"supervisor_tab_enabled": true` en `config.json` (documentado en `config.json.example`).
  - El código, el store y sus ~500 tests siguen intactos; el hotkey de captura se auto-desactiva cuando el store no existe.
  - Default en `backend/config_manager.py`: `supervisor_tab_enabled: False` (commit `5b5ccc0`).

## 3. Sistema de actualizaciones (end-to-end)

- **Verificado antes de tocar:** la detección funcionaba en vivo (`check_for_updates` correcto contra `config/version.json` en main).
- **Lo roto estaba al instalar:** `install_update()` llamaba `sys.exit(0)` dentro de un callback de Tk (no cierra la app limpio) y el batch no reintentaba si el exe estaba bloqueado.
- **Ahora:** `install_update` valida el payload, escribe un batch ASCII seguro (reintento a los 3s; si falla, conserva el instalador y deja la ruta en `%TEMP%\update_install.log`), lo lanza desacoplado y devuelve `InstallResult`; la UI cierra la app con limpieza completa (`quit_application`) 1s antes del primer intento de reemplazo. Estados de UI explícitos (verificando / al día / disponible con datos / descargando con % real / instalando / error con motivo) y `UpdaterError` tipado con una línea de log clara por fallo.
- Commit `66535ff` (delegado a worker, 25 tests headless). **Pendiente real:** el reemplazo del exe solo se puede probar con un build congelado → validarlo con el instalador de esta v0.17.0.

## 4. Bugs latentes encontrados y corregidos durante el ciclo

| Bug | Impacto si no se arregla | Fix | Commit |
|---|---|---|---|
| Cambiar el hotkey desde el selector-modal desenganchaba TODOS los hotkeys (`keyboard.unhook_all`) y luego crasheaba en símbolos muertos (`hotkey_display_button` nunca asignado, `_setup_hotkey_system` nunca definido) | Hotkeys muertos hasta reiniciar la app | `_reregister_hotkey` delega en `transcriber.update_hotkey` (misma API del selector inline que sí funcionaba) + 3 tests de regresión | `7c4dc74` |
| f-string con comillas externas reutilizadas en `files_view.py` (sintaxis exclusiva de Python 3.12) | `SyntaxError` en el piso declarado Python 3.8+ — la app no arrancaría | Comillas internas simples | `5bee55d` |
| Bare `except` en fallback de locale (`main.py`) y sondeo de micrófono (`check_mic.py`) | Podía tragarse `KeyboardInterrupt` | `except` específicos | `5bee55d` |
| Drift de formatter de la sesión rota (10 archivos) | Ruido en diffs | Verificado AST-idéntico y commiteado separado | `12ef081` |

## 5. Calidad

- Suite: **595 passed / 0 failed** (4 flakes `order_dependent` deseleccionados, pre-existentes) — eran 535.
- **mypy 0** en `ui/ backend/ tests/` (83 archivos).
- **ruff full-repo 0** con alcance explícito y documentado en `pyproject.toml`: `ui_flet/` (migración Flet pausada, superficie archivada) y `verification_test.py` (test legacy en raíz, viola regla TEST-006) excluidos con justificación; patrones intencionales de `main.py` (monkey-patch UTF-8/Tcl) y `simple_build.py` con per-file ignores.
- Pase de tipado D9 en `ui/app.py`: declaraciones de host para widgets creados en runtime, overrides alineados a protocolos de mixin, base DnD tipada.
- Deuda tipado diferida (fuera del gate mypy/ruff/pytest, pedantería pyright-strict): wrappers DnD y mutaciones de árbol legacy en `tests/test_double_paste.py` / `ui/views/history_view.py`; stubs de `sys._MEIPASS` y el rebind intencional de `Canvas.configure` en `main.py`.

## 6. Roadmap (registrado, no en este release)

| Ítem | Detalle | Origen |
|---|---|---|
| Restyling estética hacia el prototipo de Florencia | Analizar `audio2text_landing_prototipo.html` con ego-lite (SVG de audio animado incluido); evaluar con equipos de seguridad y calidad qué adoptar en la UI desktop; estimación previa en `docs/ESTIMACION_RESTYLING.md` | GR |
| Despliegue de la landing | Subir como HTML estático a Google Cloud Storage + Cloudflare → `audiototext.semph.org.ar` | GR |
| Repo open-source nivel SOTA | Auditoría completa del repo en GitHub antes de abrirlo al público; README, badges, CI visible, seguridad de secretos, plantillas de issues/PR | GR |
| GitHub Sponsors / Buy Me a Coffee | Configurar sponsorship (archivo `.github/FUNDING.yml` + cuenta) tras la apertura pública | GR |
| Spec del protocolo de streaming | Último ítem H0; desbloquea el spike de React Native | GR (ciclo anterior) |
| UX definitiva del Prompter | Rediseñar descubridibilidad cuando Supervisión vuelva (hoy: flag dev + paso de tutorial condicional) | P7 |
| Supervisión v2 | Trabajar la sección (Prompter Gate + bloques de contexto) hasta nivel release | GR |
| Rotar API keys expuestas | Resend y SkillsMP (pendiente de GR, externo al repo) | Auditoría previa |
| macOS / RN Fase 4 | Desktop Python no compila en macOS (5+ subsistemas Windows-only); llega por React Native según `docs/DECISION_RN_MULTIPLATAFORMA.md` | GR |
| A4-TUI | Flujo del prompt estructurado hacia TUIs | GR |
| G5: confirmación formal de archivado Tauri | Evaluación ya hecha; falta OK formal | GR |

## 7. Checklist de pruebas manuales (Pablo / GR)

Build: `dist/Audio2Text_CENF_v0.17.0.exe` (o `git pull && python main.py`).

1. **Panel de transcripción + WhatsApp:** al abrir la app, la sección de audios aparece colapsada (una fila con contador). El cuadro de transcripción ocupa el espacio. ▸
2. **Cargar varios audios de WhatsApp:** botón "Cargar" (o Ctrl+V con rutas, o arrastrar). La sección se expande sola. Pulsar "Transcribir todo": los archivos se procesan en fila (estado por fila) y al terminar el panel/portapapeles reciben TODO junto con `=== nombre ===` por audio. Verificar que el Historial muestra cada transcripción por separado.
3. **Limpiar cola:** el botón es visible sin hover y al usarlo la sección colapsa de vuelta.
4. **Icono:** la bandeja del sistema muestra el logo (no un círculo azul); el ícono de ventana/barra de tareas es el logo nítido a cualquier tamaño.
5. **Supervisión:** NO debe aparecer la pestaña. (Dev: `supervisor_tab_enabled: true` la devuelve, con su paso de tutorial del Prompter.)
6. **Tutorial:** el paso de "Audios de WhatsApp" existe y explica la sección.
7. **Actualizaciones (con el instalador de 0.17.0):** pestaña Actualizaciones → "Verificar" dice que estás al día; con una versión vieja simulada ofrece la nueva; "Descargar e Instalar" descarga con %, cierra la app limpio, reemplaza el exe y relanza. Si el exe está bloqueado, reintenta y deja la ruta del instalador en `%TEMP%\update_install.log`.
8. **Hotkey:** cambiar el hotkey desde el selector → sigue funcionando (antes moría hasta reiniciar), y los de pausa/captura no se pierden.
