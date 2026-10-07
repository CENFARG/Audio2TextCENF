# Backlog de Issues — v0.16.0 post-release interna

> Fuentes: live test GR (2026-10-06) · auditoría visual (9 capturas qa_screenshots/) · QA consola punta a punta (subagente, real API)
> Estado: pendientes de fix — priorizar antes del build del instalador
> Reglas: commits ≤250 líneas, conventional commits, tests primero donde aplique

## UX / Visual

| ID | Sev | Descripción | Evidencia |
|---|---|---|---|
| UX-1 | major | Área de transcripción comprimida: la sección Archivos (altura fija + label) consume el espacio vertical en la ventana de 590px; al agrandar a mano se ve. Redistribuir alturas (transcripción expandible, archivos con altura mínima/scroll). | GR + shots 05/08 |
| UX-2 | major | Supervisor: las entradas muestran solo la fila de botones (#1 · borrador + acciones) — los campos cita/respuesta NO son visibles. El workbench es inutilizable tal cual. | GR + shots 03/07/09 |
| UX-3 | minor | Botón "Copiar todo" cortado en el borde derecho del toolbar del Supervisor (ventana 590px). | shots 03/07/09 |
| UX-4 | minor | "Fallo en la transcripción" queda en rojo indefinidamente (sin auto-limpieza ni botón descartar). | shots 06/08 |
| UX-5 | minor | Indicador "Chunk X/X ETA 0s" persiste después de completar la transcripción (no se limpia). | shot 05 |
| UX-6 | minor | Overlay de grabación del Supervisor flota desconectado (timer 01:39) + estado "Transcribiendo..." en el borde inferior. Relacionado con C-1. | shot 09 |

## Funcionales (confirmados por QA consola)

| ID | Sev | Descripción | Evidencia |
|---|---|---|---|
| C-1 | major | SupervisorRecorder: si la captura falla (InputStream raise, 0 frames, mic ocupado/desconectado), `_capture_loop` retorna SIN llamar `on_text` → UI colgada en "Transcribiendo..." para siempre (reproducido: start=True, stop=True, sin callback en 8s+). Fix: en early-return de captura, invocar on_text con error para que la UI lo muestre. | QA F3 repro |
| C-2 | minor | Números de entrada del Supervisor se reutilizan al borrar la entrada máxima (create #1,#2 → delete #2 → next = #2). Contradice "históricos, nunca reasignados". `_next_number` = max+1. | QA A5/A7 |
| C-3 | minor | "Copiar respuesta N" con cita y respuesta vacías copia `"1. "` (solo número). Fix: si no hay contenido, copiar placeholder o bloquear copia con mensaje. | QA H |
| C-4 | minor | `transcribe_with_groq` sobre path inexistente devuelve None (no raise); UI solo muestra "Fallo en la transcripción" sin causa. Reintento del MISMO path sí funciona (bug #1 de GR refutado a nivel API) — el fallo real ocurre cuando la fuente de la cola ya no existe. Fix: mensaje de causa específica (archivo no encontrado vs API). | QA E/E2a |
| C-5 | minor | Comillas del quote sin escapar en `assemble_entry`: quote `dijo "hola"` → `"dijo "hola""` (anidado ambiguo). | QA H |
| C-6 | minor | "Insertar bloque" sin entrada seleccionada → mensaje "Sin bloques de contexto" aunque haya 12 — engañoso. `ui/views/supervisor_view.py:349-353`. | QA C-6 |
| C-7 | minor | `iterativo-acumulativo.md` malformado (sin frontmatter válido) se omite silenciosamente del menú de bloques — su contenido no es usable. Fix: cargar con id derivado del filename + warning visible. | QA B |


## Ronda 2 (live test 2, capturas 10-18)

| ID | Sev | Descripción | Evidencia |
|---|---|---|---|
| UX-2b | major | CONFIRMADA causa visible de UX-2: los dos textareas de cada entrada (cita + respuesta) se renderizan como tiras verticales de ~30px — pack sin fill/expand dentro de la fila. Fix: pack(fill="both", expand=True) o grid con pesos de columna. | shots 11/17/18 |
| UX-7 | minor | Indicador "Chunk X/X ETA 0s" es INTERMITENTE: a veces pasa a "Transcripción completada" (shots 15/16), a veces queda pegado (shots 05/14). La limpieza del estado depende de la ruta de finalización. | shots 05/14/15/16 |
| UX-8 | minor | El texto de transcripción previo convive con "Fallo en la transcripción" en el header sin indicar qué es válido. | shots 06/08 |
| OK-1 | info | Campo "Carpeta de bloques de contexto" EXISTE y funciona en Configuración → Gestión de Archivos (GR no lo había visto). | shot 12 |
| OK-2 | info | Grabación: header "Grabando... 00:05" y "Transcripción completada" funcionan correctamente. | shots 13/15 |

## De GR a investigar

| ID | Sev | Descripción |
|---|---|---|
| GR-1 | major | Transcripción doble vía F8 (ocurrió una vez): posiblemente auto-pegado duplicado u otra ruta de streaming (la grabación era de otra duración que la del fix B4). Reproducir antes de release. |
| GR-2 | minor | Hotkey de captura: GR probó Ctrl+Alt+C (la configurada es Ctrl+Alt+V) — validar registro del hotkey + considerar feedback visible cuando captura (la msg ya existe, confirmar que aparece). |

## Features solicitadas (roadmap)

| ID | Feature | Notas |
|---|---|---|
| REQ-1 | **Pausa/reanudación de grabación**: tecla configurable (ej: F9 pausa, F8 inicia/termina) — pausar, leer la transcripción del modelo, continuar en la MISMA sesión de transcripción. Pausa y reanudación dentro de un mismo recording. | Máquina de estados: recording → paused → recording → stopped |
| REQ-2 | **Sesiones de Supervisor**: identificar a qué agente/sesión se responde; acumulado de respuestas/correcciones por sesión; seleccionar qué copiar del acumulado (sistema acumulativo para agentes que olvidan contexto) + bloques de contexto encima. | Extiende SupervisorStore: session_id/agente por entrada, vista agrupada |
| REQ-3 | **Bloques de contexto multi-select**: elegir VARIOS bloques a la vez (hoy es uno por inserción). | UI: checkboxes o multiselect + orden de inserción |
| A4 | Prompter Gate (alcance: Supervisor + TUI agentes) — ver roadmap Track A. | Spec pendiente |
| REQ-4 | **Notificación de no-grabación**: detectar rápido cuando se habla sin grabar (health-check de frames al iniciar captura: si 0 frames en ~2s → notificar "no hay audio entrante") + notificación proactiva si el recorder muere en silencio. Complementa C-1. | Spec pendiente |
