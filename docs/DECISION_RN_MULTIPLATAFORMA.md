# Decisión estratégica: React Native multiplataforma — Audio2Text

> Fecha: 2026-09-25 (evaluación team-strategic + team-risk) · Estado: GO-CONDICIONAL
> Contexto: v0.16.0 liberada en main · Tauri v2 pausada (2 stashes) · dueño solo + agentes IA · monetización vía Cafecito

## Veredicto

**GO-CONDICIONAL** — no escribir una línea de RN hasta cerrar Fase 0 (estabilización + spec del protocolo + decisión BYOK), y pasar un spike validatorio (Fase 1) que puede matar el plan.

## 1. Comparativa de alternativas

| Alternativa | Costo | Riesgo | Tiempo a mercado | Mantenimiento (solo dev) |
|---|---|---|---|---|
| Mantener desktop (v0.16.x) | Mínimo | Bajo | 0 (ya está) | Bajo — CI maduro, línea única |
| PWA / web-first | Bajo ($0 infra) | Bajo-medio | 4-8 semanas | Bajo — 1 codebase browser |
| React Native (Expo) + RN Web | Medio: 3-6 meses de foco | Medio (audio nativo + web híbrido) | 8-12 semanas MVP Android | Medio-alto, viable con Expo/EAS |
| Flutter | Medio + aprender Dart | Medio | Similar a RN | 3er lenguaje (Python+TS ya) |
| Retomar Tauri v2 + Svelte 5 | Medio | Medio | Desktop multiplat. 6-10 semanas | Alto: 3ª línea paralela — no viable |

Lectura: PWA distribuye ya y barato, pero sin dictado por hotkey ni audio en background. RN es el pick correcto para móvil nativo serio. Flutter no aporta extra. Tauri compite con el propio desktop.

## 2. Top 8 riesgos

| # | Riesgo | Prob | Impacto | Mitigación |
|---|---|---|---|---|
| 1 | Groq key embebida en móvil → extracción y abuso | Media (si se bundea) | Crítico | **Nunca embeber.** BYOK en SecureStore/Keychain. Capa gratis futura → proxy con key server-side + rate limit |
| 2 | Políticas app stores audio/IA (Apple USD 99/año, revisión mic/privacy) | Alta (Apple) | Alto | Web primero (cero revisión); privacy policy desde día 1; Android antes que iOS |
| 3 | Costo API por usuario gratuito lo pagás vos | Alta | Alto | BYOK transfiere el costo. Free tier futuro: solo quota diaria + auth |
| 4 | Mantenimiento 3-4 plataformas solo | Alta | Alto | Expo managed + EAS; desktop a maintenance mode; iOS pospuesto; máx 2 líneas vivas |
| 5 | Fragmentación Android LATAM (low-end, ROMs que matan permisos de mic) | Alta | Medio | min SDK conservador, pruebas en gama baja real, checklist por fabricante |
| 6 | Reescritura TS: transcriber/slices/checkpoints Python NO corren en RN | Cierta | Medio | Documentar el protocolo (chunks, snapshots 25s, checkpoints) como spec; tests de contrato contra Groq compartidos |
| 7 | RN Web: captura de audio inestable (MediaRecorder + codecs que Groq acepta, iOS Safari) | Media | Medio | Spike obligatorio Fase 1; fallback: web = solo subida de archivos |
| 8 | Cafecito convierte bajo | Alta | Bajo (si no dependés) | Link pasivo desde el MVP; cero features gated hasta métricas reales |

## 3. Arquitectura recomendada

**BYOK (Bring Your Own Key), sin backend propio en fase 1.**

- Móvil/Web (RN): cliente TS directo a Groq con la key del usuario (SecureStore, jamás en el bundle). Reescribir en TS: captura → chunking → Groq → ensamblado con checkpoints (mismo protocolo, nueva implementación).
- Desktop (Python): sigue igual — ya es BYOK de facto. Maintenance mode.
- ¿API REST sobre el backend Python? No en fase 1 — la lógica crítica vive en el cliente igual. Proxy (fase opcional 2+): FastAPI mínimo en VPS (~USD 5-10/mes), key server-side, auth y quota — SOLO con capa gratuita.

**Sobre la separación backend/frontend:** la higiene es real (tests, mypy, módulos puros), pero el código Python no migra a RN — lo que migra es el conocimiento del protocolo. La herencia valiosa es la spec, no el código.

## 4. Roadmap por fases

- **Fase 0 — Estabilizar (3-6 semanas). NO arranca RN antes.** Limpiar 103 findings ruff, congelar scope desktop → maintenance mode, escribir spec del protocolo de streaming en docs/, firmar decisión BYOK. Salida: CI verde 2 semanas, 0 bugs críticos, spec publicada.
- **Fase 1 — Spike RN (2-3 semanas, kill-or-commit).** App Expo mínima: grabar en Android físico → Groq con key propia → transcript. Probar RN Web. Kill: si no funciona en Android o RN Web no sube archivos → pivotar a PWA Android-first y archivar RN.
- **Fase 2 — MVP móvil (6-10 semanas).** Historial, archivos (cargar/pegar), streaming con checkpoints en TS, pantalla BYOK, build EAS. Salida: APK que reemplace el uso real; distribución APK + Play Store.
- **Fase 3 — Web + Cafecito pasiva (4-6 semanas).** RN Web (subida sí o sí; dictado vivo si el spike lo permitió), link Cafecito en Settings.
- **Fase 4 — iOS + monetización** solo con métricas: ≥100 MAU o retention 4+ semanas.

## 5. Decisión Tauri

**ARCHIVAR.** Con RN en camino, Tauri es una 3ª línea insostenible para un solo dev; RN Web cubre "usar sin Windows". Acción: documentar los 2 stashes, no borrar nada. **Absorber** las ideas de layout de Svelte 5 como insumo de diseño para RN. Revisitar solo si Fase 1 falla.

## 5b. Design reference (nuevo, 2026-09-25)

Landing prototipo con la estética objetivo: `docs/design/landing_prototipo.html` (preview: `landing_preview.png`, factibilidad: `RN_UI_FEASIBILITY.md`). Veredicto: 100% reproducible en RN — el prototipo sirve doble: landing web publicable tal cual (GitHub Pages) y design system de referencia para la app RN (Fase 1/2).

## 6. Cafecito

Link pasivo desde Fase 2-3. Gating de features: NO antes de ~100 MAU + retention 4 semanas — un paywall temprano mata el boca-a-boca. Qué justifica pago después: bloques POST, historial en la nube, vocabularios por rubro. **El dictado core: siempre gratis** — es el diferenciador y el canal de adquisición. Cafecito es tips, no salario.
