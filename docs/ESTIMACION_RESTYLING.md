# Estimación de restyling desktop (CustomTkinter → estética del prototipo landing)

> Fecha: 2026-10-08 · Base: v0.16.1, 478+ tests verdes, dueño solo + agentes IA
> Referencias: `docs/design/landing_prototipo.html` (+ `landing_preview.png`), `RN_UI_FEASIBILITY.md`, `ISSUES_v0.16.1.md`, `DECISION_RN_MULTIPLATAFORMA.md`
> Target visual: el mockup `app-window` dentro de la landing (header + waveform + transcript + status pill) = diseño objetivo de la app.
> Punto de partida: `DesignSystem` en `ui/app.py:168` usa paleta vieja (#0F172A / #2563EB) ajena al prototipo; el resto de colores está hardcodeado en app.py (2.390 líneas) y `ui/views/` (1.776 líneas).

## 1. Estimación por componente (trabajo asistido por agentes)

| Componente | Alcance | Estimación |
|---|---|---|
| Tokens de color | Nuevo `ui/theme.py` con tokens exactos (bg #080d18, surfaces #101827/#141f32, cyan/blue/violet) + barrido de hardcodes en app.py y views. | 4–6 h |
| Tipografía | CTkFont Segoe UI Variable + jerarquía display/heading/body/caption; labels uppercase ("TRANSCRIPCIÓN EN VIVO") — sin letter-spacing nativo en Tcl. | 2–4 h |
| Cards | CTkFrame con border sutil + corner_radius en todas las superficies (6 pestañas). Nativo CTk, directo. | 6–10 h |
| Badges/chips/pills | Status pill "● Conectado", badges de estado por entrada del Supervisor, chips de atajos. Nativo CTk. | 3–5 h |
| Layout funcional | UX-1 (transcripción vs archivos), UX-2b (textareas de 30px), UX-3 (botón cortado), UX-4/5/7 (indicadores pegados). Es FIX, no restyling — la Fase 0 del plan RN ya lo exige. | 1–2 días |
| Restyle por pestaña | Principal según mockup (header de captura + área transcript + foot modelo/estado), Supervisor, Historial, Configuración, Información, Actualizaciones. | 2–3 días |
| Botón CTA con gradiente | PNG generado (Pillow) + estados hover manuales sobre CTkLabel. Frágil y de baja fidelidad. | 4–8 h |
| Waveform animada | Canvas custom + bucle `after()`. Decorativa pseudo-random: 8–16 h. Con amplitud real de mic: +8–16 h y acopla el recorder a la UI. | 8–16 h |
| Chrome de ventana | Titlebar dark vía DWM (ctypes). | 1–2 h |

**Totales:**
- Pulido mínimo (tokens + tipografía + cards/badges + fixes funcionales): **4–7 días**.
- Réplica completa (gradientes + waveform): **+1 semana**, con retorno decreciente.

## 2. Límite duro de CustomTkinter 5.2.2 — qué NO se puede replicar

- **Gradientes reales** (texto con clip, botones CTA): solo hacks PNG/Canvas que se rompen con hover/focus/escala DPI.
- **Glass/backdrop-blur** (topbar, chips flotantes): Tk no compone transparencias con blur.
- **Sombras suaves** (box-shadow de cards y chips): CTk solo ofrece borde sólido.
- **Letter-spacing/kerning**: el font engine de Tcl no lo soporta; los labels trackeados quedan aproximados.
- **Transiciones/motion CSS** (reveal, drift, pulse): solo bucles `after()` manuales, costo alto por efecto.
- **Stroke dashed animado** del waveform (SVG): hay que reescribirlo línea por línea en Canvas.

Fidelidad alcanzable en CTk: **~70% del prototipo**. El 30% que falta (gradientes, glass, sombras, motion) es justamente lo que da el carácter "premium" a la estética aprobada.

## 3. ¿Vale la pena ahora en CTk?

**La tensión**: el desktop es el producto que los clientes usan HOY, pero RN es GO-CONDICIONAL y su Fase 0 (3–6 semanas) ya exige estabilizar el desktop antes del spike. Toda la UI se reescribe en RN; el código CTk no migra.

**Lectura**:
- Los fixes funcionales (UX-1/2b/3/4/5/7) no son "restyle": son deuda que los usuarios sufren hoy y la Fase 0 ya los requiere. Se hacen siempre.
- Unificar tokens/tipografía/cards NO es esfuerzo tirado: los tokens se transfieren 1:1 a RN (ya están en `RN_UI_FEASIBILITY.md`); `ui/theme.py` se convierte en la fuente del design system RN y en criterio de aceptación visual.
- SÍ es tirado: gradientes, waveform real, glass y motion — CTk no llega ahí y RN sí; consumirían ~1 semana para conseguir el 30% que define la estética.

**Respuesta**: pulir mínimo en CTk (sin gradientes ni waveform real). Réplica completa NO — esperar a RN Fase 1/2.

## 4. Plan por fases (hitos verificables)

| Fase | Contenido | Hito verificable | Criterio de salida | Est. |
|---|---|---|---|---|
| R0 — Higiene | UX-1, UX-2b, UX-3, UX-4/5, UX-7 | Re-capturas de las 9 screenshots contra `ISSUES_v0.16.1.md` | Sin tiras de 30px ni texto cortado; indicadores se limpian; 478+ tests verdes | 1–2 d |
| R1 — Tokens | `ui/theme.py` con tokens exactos; barrido de hardcodes; tipografía jerarquizada | `grep -rE "#[0-9A-Fa-f]{6}" ui/` ≈ 0 fuera de theme.py (salvo tokens de estado) | App con paleta del prototipo; captura lado a lado vs mockup aprobada por el dueño | 1–2 d |
| R2 — Superficies | Cards/badges/pills por pestaña; Principal según mockup (label + transcript + status pill) | Screenshot antes/después de cada una de las 6 pestañas | Dueño aprueba capturas; tests verdes; cero regresión en hotkeys y flujo de grabación | 2–3 d |
| R3 — Opcional | Waveform decorativa + CTA plano acentuado | Demo grabada en video | Solo si hay demo/comercial antes de RN; si no, se archiva | 3–5 d |

R0–R2 se solapan con la Fase 0 del plan RN (es la misma estabilización). Total recomendado: **~1 semana asistida**.

## 5. Recomendación final

1. Hacer R0–R2 (~1 semana asistida): arregla lo que los clientes sufren HOY y cristaliza el design system que RN va a consumir — no es esfuerzo desperdiciado.
2. NO replicar gradientes/glass/waveform en CTk: es el 30% que define la estética y CTk no puede — se hace nativo en RN Fase 2.
3. El mockup de la landing es el criterio de aceptación: si una pantalla CTk no se parece al mockup con los tokens de R1, no está lista — y en RN ya nace parecida.
