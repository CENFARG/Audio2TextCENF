# Strategic Decision: Grama Platform

> Evaluación completa del equipo Strategic Gestion Team (7 sub-roles)
> Fecha: 2026-07-27
> Versión: v1.0

---

## Executive Summary

**Grama** es la evolución de Audio2Text hacia una plataforma de escritorio multiplataforma para interactuar con IAs y agentes. El mercado de transcripción AI vale $4.5B (2024) y crece al 15.6% CAGR hacia $19.2B en 2034, con un subsegmento de herramientas de productividad para IA en expansión acelerada. Grama se diferencia radicalmente de competidores (Otter, Fireflies, Wispr Flow) al ofrecer: **bloques de contexto**, **corrección iterativa 1:2:** (metodología CENF patentable), **integración Engram nativa** y **operación local + cloud híbrida**. El riesgo principal es el bus factor = 1 (Gonzalo como único desarrollador), seguido de la dependencia de core-cenf-tenant (no existe aún) y la estrechez del budget de tokens ($400/mes). La recomendación es **GO con condiciones**: arrancar Fase 1 (Free MVP en Tauri) en paralelo con investigación profunda de core-cenf-tenant y onboarding de Pablo como desarrollador secundario. Break-even en ~20 usuarios Pro a $15/mes.

---

## 1. Análisis Fractal

### Compresiones Abusivas Identificadas

| Elemento | Frase compresora | Niveles ocultos estimados | Riesgo |
|----------|-----------------|---------------------------|--------|
| Migración a Tauri | "Solo migrar Audio2Text a Tauri" | 5 | 🔴 ALTO |
| core-cenf-tenant | "Mientras tanto usamos Supabase" | 4 | 🔴 ALTO |
| Pablo como dev | "Pablo puede encargarse" | 3 | 🟡 MEDIO |
| Bloques de contexto | "11 archivos existentes, solo UI" | 3 | 🟡 MEDIO |
| Pricing Free/Pro | "LicenseManager resuelve" | 4 | 🟡 MEDIO |
| Multi-agent portability | "Abstracción portable" | 6 | 🔴 ALTO |
| Voice Output (TTS) | "Local con Microsoft TTS" | 3 | 🟡 MEDIO |
| Repos / Git strategy | "Subárbol o feature flags" | 3 | 🟡 MEDIO |

### Descomposición de Compresiones

#### 1.1 Migración a Tauri — NO es "solo migrar"

- **Nivel 1**: Setup de proyecto Tauri v2 + Svelte 5
  - **Nivel 2**: Crear scaffold con create-tauri-app, configurar tauri.conf.json, capabilities, permisos
    - **Nivel 3**: Configurar IPC entre Rust y TypeScript (invoke, events)
    - **Nivel 3**: Configurar build multiplataforma (Windows .msi, macOS .dmg, Linux .AppImage)
      - **Tarea**: Script CI/CD para builds — ~8h
      - **Tarea**: Code signing Windows (certificado) — ~4h + $200-300/año
  - **Nivel 2**: Migrar UI de Flet/CustomTkinter a Svelte 5 + Tailwind v4 + shadcn-svelte
    - **Nivel 3**: Recrear 7 pantallas (transcripción, historial, settings, bloques, voice output, corrección, about)
      - **Tarea**: Pantalla de transcripción con recording overlay — ~12h
      - **Tarea**: Historial con búsqueda, filtros, exportación — ~8h
      - **Tarea**: Settings con tabs (audio, transcripción, hotkeys, actualizaciones) — ~6h
      - **Tarea**: Bloques de contexto (panel lateral con checkboxes + token counter) — ~8h
      - **Tarea**: Voice Output UI (control de reproducción, velocidad, voz, loops) — ~6h
      - **Tarea**: Corrección iterativa 1:2: UI — ~10h
- **Nivel 1**: Conectar backend Python existente (FastAPI) con frontend Tauri
  - **Nivel 2**: Decidir: ¿backend embebido en Tauri (sidecar) o proceso separado?
    - **Nivel 3**: Sidecar: empaquetar Python con PyInstaller, configurar tauri.conf.json > bundle > externalBin
      - **Tarea**: Script de empaquetado del backend Python — ~4h
      - **Tarea**: Manejo de ciclo de vida del sidecar (start/stop/health check) — ~4h
    - **Nivel 3**: Comunicación REST/WebSocket entre frontend Tauri y backend Python
      - **Tarea**: Definir API contract (endpoints, tipos, errores) — ~4h
      - **Tarea**: Implementar llamadas HTTP desde Rust/Tauri al backend local — ~3h
- **Nivel 1**: Migrar hotkeys globales, system tray, overlay
  - **Nivel 2**: Tauri v2 plugin system (global-shortcut, tray-icon, window)
    - **Nivel 3**: Configurar hotkeys (F1-F12) con tauri-plugin-global-shortcut — ~3h
    - **Nivel 3**: System tray con menú contextual — ~2h
    - **Nivel 3**: Overlay flotante de grabación como ventana siempre-encima — ~4h

**Total descomprimido**: ~80-100h de trabajo puro de migración

#### 1.2 core-cenf-tenant — NO es "Supabase resuelve"

- **Nivel 1**: Definir modelo de datos de tenant (organization, user, role, feature flag)
  - **Nivel 2**: Migrations y schema SQL
    - **Nivel 3**: Definir entidades: Organization, User, Membership, Role, Permission, FeatureFlag — ~4h
    - **Nivel 3**: Políticas RLS (Row Level Security) por tenant — ~6h
  - **Nivel 2**: Integración con Supabase Auth (o Auth0)
    - **Nivel 3**: Flujo de signup/login/logout con Supabase Auth — ~3h
    - **Nivel 3**: Manejo de sesión JWT + refresh token — ~2h
    - **Nivel 3**: Webhooks de user management — ~2h
- **Nivel 1**: Implementar Feature Flags (Free vs Pro)
  - **Nivel 2**: LicenceManager como adapter de core-cenf-tenant
    - **Nivel 3**: Cache de licencias local (TTL configurable) — ~3h
    - **Nivel 3**: Verificación offline con grace period — ~4h
    - **Nivel 3**: UI de upgrade/pricing — ~4h
  - **Nivel 2**: Integración con payment provider (Stripe)
    - **Nivel 3**: Webhook de suscripciones — ~4h
    - **Nivel 3**: Manejo de trials, cancellations, refunds — ~3h
- **Nivel 1**: Migrar usuarios existentes (si hay)
  - No aplica aún (no hay usuarios Grama)

**Total descomprimido**: ~35-45h para una versión funcional

#### 1.3 Pablo como desarrollador — NO es "Pablo toma el proyecto"

- **Nivel 1**: Definir qué puede hacer Pablo vs qué requiere Gonzalo
  - **Nivel 2**: CES v0.1.0 no está documentado para terceros
    - **Nivel 3**: Escribir guía de onboarding para desarrollador externo — ~4h
    - **Nivel 3**: Documentar convenciones (commits, PRs, SDD) — ~2h
  - **Nivel 2**: Pablo no conoce Tauri v2, Svelte 5, shadcn-svelte
    - **Nivel 3**: Estimación de curva de aprendizaje: 2-3 semanas
    - **Nivel 3**: Definir tareas iniciales de baja complejidad (CSS, componentización, traducciones) — ~4h
  - **Nivel 2**: Comunicación async entre devs sin daily
    - **Nivel 3**: Definir ritmo de PR review (Gonzalo review, Pablo merge) — ~1h
    - **Nivel 3**: Definir canal de comunicación (Discord? GitHub Issues?) — ~1h

**Total descomprimido**: ~12h de setup + 2-3 semanas de ramp-up

#### 1.4 Bloques de Contexto — NO es "solo UI"

- **Nivel 1**: Migrar 11 archivos .md de bloques_contexto/ a un formato estructurado
  - **Nivel 2**: Parsear contenido, extraer metadatos (título, descripción, tokens estimados, dependencias)
    - **Nivel 3**: Decidir formato: ¿JSON schema? ¿YAML? ¿Markdown frontmatter? — ~2h
    - **Nivel 3**: Script de migración de MD → JSON estructurado — ~3h
  - **Nivel 2**: Token counter: estimar tokens por bloque + total
    - **Nivel 3**: Usar tiktoken para conteo preciso — ~2h
    - **Nivel 3**: Mostrar advertencia si se excede el context window del modelo — ~1h
- **Nivel 1**: UI de selección y composición
  - **Nivel 2**: Panel lateral con checkboxes, drag to reorder, token counter
    - **Nivel 3**: Componente BlockSelector con search/filter — ~4h
    - **Nivel 3**: Componente TokenCounter con barra de progreso — ~2h
  - **Nivel 2**: Copy all → clipboard con formato optimizado para cada IA
    - **Nivel 3**: Template system (formato para ChatGPT, Claude, Gemini) — ~3h

**Total descomprimido**: ~17-20h

### Valores Intermedios Faltantes

| Desde | Hasta | Valores intermedios faltantes |
|-------|-------|-------------------------------|
| Audio2Text v0.16.0 | Grama Free MVP | Skeleton Tauri → Backend embebido → Pantalla Transcripción → Pantalla Historial → Bloques UI → Release v1.0 |
| Grama Free MVP | Grama Pro v1.0 | core-cenf-tenant → LicenceManager → Stripe → Corrección Iterativa UI → Engram Integration → Git Versioning |
| CES v0.1.0 | Grama implementado | Template CES → Shadcn-svelte components → Convenciones de layout → CSS tokens → Dark/light mode |
| core-cenf-py (Python) | core-cenf-ts (TypeScript) | No faltan — ambos existen. Faltan: core-cenf-tenant (auth) y core-cenf-agents (portabilidad) |
| Gonzalo solo | Equipo > 1 dev | Onboarding Pablo → Definición de tareas → Ritmo de PRs → Code review → Delegación real |

### Preguntas Sin Responder

| Pregunta | Por qué es relevante |
|----------|---------------------|
| ¿El backend Python va como sidecar Tauri o como proceso separado que el usuario instala? | Determina la experiencia de instalación y la complejidad del build. Sidecar es más user-friendly pero más complejo técnicamente. |
| ¿Cómo se maneja el upgrade de Audio2Text v0.16.0 a Grama? | Los usuarios existentes de Audio2Text van a perder su configuración/historial. ¿Migración automática? |
| ¿Grama comparte el mismo backend Python o se refactoriza a Rust puro? | Si se refactoriza a Rust puro, el esfuerzo es 3-5x mayor pero elimina la dependencia Python en el sidecar. |
| ¿Qué pasa si Pablo no puede dedicar tiempo consistente? | Plan de contingencia: ¿reducir scope o contratar freelancer? |
| ¿core-cenf-tenant se hace en Python (core-cenf-py) o TypeScript (core-cenf-ts)? | Determina quién puede implementarlo y el stack del auth. Grama necesita auth en frontend + backend. |

### Coeficiente de Confianza Fractal

**Score**: 58/100
**Veredicto**: Necesita iteración
**Justificación**: El plan general es sólido pero comprime agresivamente la migración a Tauri (~100h de trabajo real) y asume que Pablo puede tomar el proyecto sin un onboarding estructurado. core-cenf-tenant es el mayor riesgo técnico: no existe y es requisito para la versión Pro. La pregunta de sidecar vs proceso separado no está resuelta y cambia significativamente el esfuerzo de build. Se recomienda una iteración de descomposición en las áreas de migración Tauri, tenant y pricing antes de iniciar implementación.

---

## 2. Product-Market Fit

### Segmento Analizado

| Métrica | Valor | Fuente |
|---------|-------|--------|
| **TAM** (mercado total direccionable) | $4.5B (2024) → $19.2B (2034) | Market.us AI Transcription Report |
| **TAM Speech-to-Text API** | $5.63B (2026) → $25.28B (2034) | Fortune Business Insights |
| **CAGR** | 15.6% (transcripción) / 20.66% (STT API) | Múltiples fuentes |
| **SAM** (mercado accesible) | $280M — herramientas de productividad desktop para IA + transcription | Estimación: 5% de mercado transcription + nicho bloques de contexto |
| **SOM** (mercado obtenible, año 1) | $180K — 100 usuarios Pro + 500 Free activos | Cálculo interno basado en reach de GitHub + Product Hunt |
| **Crecimiento anual** | >65% observado en consumo de IA (2025-2026) | Datos internos CENF |

### JTBD Principal

> "Cuando estoy trabajando con IAs y necesito guardar, corregir y reutilizar mis interacciones de voz, quiero una herramienta que unifique transcripción, contexto y portabilidad para no perder tiempo reescribiendo prompts ni cambiar entre apps."

### Propuesta de Valor

**Grama es la interfaz de escritorio que conecta tu voz con cualquier IA — transcribe, contextualiza, corrige y portablea tus interacciones sin perder ni un byte de trabajo.**

### Mapeo Competitivo

| Competidor | Segmento | Precio | Fortaleza | Debilidad vs Grama |
|-----------|----------|--------|-----------|--------------------|
| **Otter.ai** | Reuniones/Enterprise | $8-17/mes | Marca establecida, 1.2M+ usuarios | Solo reuniones, sin bloques de contexto, sin corrección iterativa, cloud-only |
| **Fireflies.ai** | Reuniones/Sales | $10-19/mes | CRM integrations, 100+ lenguajes | Mismo problema que Otter: vertical reuniones, no cubre workflow IA |
| **Wispr Flow** | Dictado personal | $12-15/mes | UX pulido, dictado en cualquier app | Solo dictado cloud. Sin bloques. Sin corrección IA. Sin portabilidad multi-herramienta. Sin offline. |
| **WhisperDesk** | Transcripción archivos | Free (OSS) | Tauri v2 + Whisper.cpp, local | Solo transcripción de archivos. Sin grabación en vivo. Sin contexto. Sin corrección. |
| **TranscriptionSuite** | Transcripción local | Free (OSS) | Multi-backend, diarization, 616 stars | Solo transcripción. Sin corrección IA. Sin bloques. Stack Electron pesado. |
| **OpenWhispr** | Dictado local | Free (OSS) | Offline, privacy-first | Solo dictado. Sin bloques. Sin corrección. MVP temprano. |
| **OpenFlow** | Dictado local | Free (OSS) | faster-whisper, hotkeys | Solo dictado. Sin contexto. Sin corrección. 11 stars. |
| **Rev** | Transcripción profesional | $5-30/mes | Accuracy humana disponible, marca | Caro, no real-time, sin automatización IA |
| **Speed of Sound** | Dictado Linux | Free (OSS) | Offline, Linux native | Solo Linux, sin corrección, sin bloques |
| **Deepgram** | API Enterprise | $0.0043/min | API de alta calidad, Nova-2 | API pura, sin UI, sin producto desktop |
| **AssemblyAI** | API Enterprise | $0.015/min | Modelo Universal-2, speaker diarization | API pura, sin UI, sin producto desktop |

### Diferenciadores Clave de Grama

1. **Bloques de Contexto**: Ningún competidor ofrece "paquetes de contexto" seleccionables para enriquecer prompts de IA. Esto es una categoría nueva.
2. **Corrección Iterativa 1:2:** (Pro): Metodología única CENF — seleccionás parte de respuesta IA, grabás corrección oral, todo se estructura automáticamente.
3. **Engram Integration (Pro)**: Memoria persistente de interacciones. Ningún competidor tiene un sistema de memoria portable como Engram.
4. **Híbrido Local + Cloud**: Whisper local para privacidad, Groq cloud para velocidad. Tú elegís. Competidores (Otter, Fireflies, Wispr) son 100% cloud.
5. **Multi-agent Portability (Visión)**: Misma interfaz para OpenCode, Claude Code, Goose, ChatGPT. Esto no existe hoy en ningún producto.

### FODA Estratégico

| | Positivo | Negativo |
|---|---|---|
| **Interno** | ✅ Backend Audio2Text funcional (62 tests, 18 managers) | ❌ Bus factor = 1 (solo Gonzalo) |
| | ✅ Stack moderno (Tauri + Svelte 5 + CES) | ❌ Presupuesto tokens ajustado ($400/mes) |
| | ✅ Metodología CENF validada | ❌ core-cenf-tenant no existe |
| | ✅ Diferenciadores reales (nadie tiene bloques + corrección) | ❌ Sin equipo de marketing/ventas |
| **Externo** | 🌟 Mercado de transcripción AI creciendo 15-20% CAGR | 🛡️ Competidores con millones en funding (Otter: $50M Serie C) |
| | 🌟 Open source como ventaja para comunidad dev | 🛡️ Wispr Flow con UX superior |
| | 🌟 AI desktop tools es categoría emergente | 🛡️ Usuarios esperan experiencia pulida "tipo Wispr" |
| | 🌟 Privacidad/local-first como diferenciador creciente | 🛡️ Barrera de entrada baja (cualquiera puede hacer un wrapper de Whisper) |

### Pricing Recomendado

| Plan | Precio | Qué incluye | WTP estimado | Justificación |
|------|--------|-------------|-------------|---------------|
| Free | $0 | Transcripción (local + cloud), Voice Output, Bloques de Contexto básicos | $0 | Benchmark: Otter Free, Fireflies Free, todos tienen tier gratuito. Captura base de usuarios. |
| Pro | $15/mes | Todo Free + Corrección Iterativa 1:2:, Bloques avanzados, Engram Integration, Git Versioning, AI contexto ilimitado | $10-20/mes | Benchmark: Wispr Pro ($12-15), Otter Pro ($8.33-16.99), Fireflies Pro ($10). $15 es punto dulce. |
| Enterprise | Contactar | Todo Pro + SSO/SAML, HIPAA, audit logs, despliegue on-prem, soporte dedicado | $25-50/mes | Benchmark: Otter Business ($20-30), Fireflies Business ($19-29), Wispr Enterprise (contactar) |

**Elasticidad estimada**: Premium (WTP alta para power users de IA que ya pagan $20+/mes en herramientas). Usuarios de Otter/Fireflies ya pagan $10-30/mes.

### Riesgo de PMF

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Mercado no valida bloques de contexto (no hay demanda probada) | 40% | 🔴 Alto | Free MVP primero con solo transcripción + bloques básicos. Validar con users reales antes de construir Pro. |
| Wispr Flow agrega features similares | 30% | 🟡 Medio | Wispr tiene $12M+ funding pero está en dictado cloud. Diferenciar con local-first + Engram. |
| Otter.ai/Fireflies.ai copian concepto | 20% | 🟡 Medio | Son verticales reuniones, no tool de IA desktop. Copiar requeriría pivot. |
| Usuarios no quieren otra app de escritorio | 35% | 🟡 Medio | Posicionar como "interfaz de IA" no como "transcriptor". Diferenciación clara. |
| Open source alternatives maduran (TranscriptionSuite, WhisperDesk) | 50% | 🟢 Bajo | Son solo transcripción. Grama compite en CAPA DE CONTEXTO, no en transcripción. |

### Métricas de Salud Target

| Métrica | Target | Benchmark industria |
|---------|--------|-------------------|
| DAU/MAU (usuarios activos diarios/mensuales) | >30% | SaaS promedio: 20-25% |
| Retention semanal (Free) | >40% | Herramientas productividad: 35-50% |
| Retention semanal (Pro) | >70% | SaaS premium: 60-80% |
| Conversión Free → Pro | >5% | Benchmark SaaS: 3-7% |
| NPS | >40 | Herramientas desktop: 30-50 |
| Time-to-value (minutos hasta primera transcripción) | <5 min | Audio2Text actual: <2 min |
| Sean Ellis "muy decepcionado si no pudiera usar" | >40% | Benchmark PMF: >40% |

### Recomendación

- **Veredicto**: **Build** — CON CONDICIONES
- **Prioridad**: Alta
- **Timing**: Arrancar Free MVP ahora. Validar bloques de contexto con users reales antes de construir Pro completo.
- **Próximo paso**: Skeleton Tauri + migración de transcripción + bloques básicos (Fase 1, 2 meses). ==NO construir Pro sin validación de mercado Free.==

---

## 3. Matriz de Riesgos

### Risk Register Completo

| ID | Riesgo | Categoría | Prob | Impacto | Score | Dueño | Mitigación | Estado |
|----|--------|-----------|------|---------|-------|-------|------------|--------|
| R01 | **Bus factor = 1**: Solo Gonzalo conoce el proyecto completo | Operacional | 4 | 5 | **20** | Gonzalo | Onboarding Pablo con CES + guías + PRs. Documentar decisiones en Engram. Definir tareas delegables. | 🟡 Abierto |
| R02 | **core-cenf-tenant no existe** y es requisito para Pro | Técnico | 5 | 4 | **20** | Gonzalo | Usar Supabase Auth + RLS como interim. Implementar LicenceManager como adapter desacoplado. | 🟡 Abierto |
| R03 | **Tiempo de desarrollo vs cash flow**: 6+ meses de desarrollo sin ingresos | Financiero | 4 | 4 | **16** | Gonzalo | Free MVP en 2 meses para validación. Pro features diferidas. No construir sin validación. | 🟡 Abierto |
| R04 | **Costo de tokens IA**: $400/mes puede no ser suficiente para desarrollo + operación | Financiero | 3 | 4 | **12** | Cost Gov | DeepSeek Flash 80%, Pro 15%, otros 5%. Monitorear Tokscale. Alerta amarilla a $350. | 🟢 Mitigado |
| R05 | **Competidores con funding**: Otter ($50M), Wispr Flow ($12M+) | Mercado | 3 | 3 | **9** | PM | Diferenciar con bloques + local-first. No competir en features de reuniones. | 🟢 Aceptado |
| R06 | **Pablo no puede dedicar tiempo consistente** | Operacional | 3 | 4 | **12** | Gonzalo | Scope reducido si Pablo no está. Tareas pequeñas y bien definidas. Alternativa: freelancer. | 🟡 Abierto |
| R07 | **Complejidad build multiplataforma**: Tauri builds en 3 OS | Técnico | 3 | 3 | **9** | Gonzalo | CI/CD con GitHub Actions. Windows primero. Mac/Linux después. | 🟢 Mitigado |
| R08 | **Dependencia de Tauri v2 ecosystem**: plugins, bugs, breaking changes | Técnico | 3 | 3 | **9** | Gonzalo | CES v0.1.0 con versiones pinneadas. Monitorear changelog. | 🟢 Aceptado |
| R09 | **Sidecar Python no funciona en producción**: issues de empaquetado | Técnico | 3 | 4 | **12** | Gonzalo | POC de sidecar en semana 1. Si falla, proceso separado. | 🟡 Abierto |
| R10 | **Fuga de API keys en app distribuida** | Seguridad | 2 | 4 | **8** | Gonzalo | Ofuscación XOR (existente). Proxy server opcional para enterprise. | 🟢 Mitigado |
| R11 | **Mercado no valida bloques de contexto** | Mercado | 4 | 3 | **12** | PM | Free MVP primero con transcripción sola. Bloques como feature experimental. Validar con users reales. | 🟡 Abierto |
| R12 | **Crecimiento de consumo de tokens >65% trimestral** | Financiero | 3 | 3 | **9** | Cost Gov | Monitorear trimestral. Ajustar budget. Escalar cuentas según necesidad. | 🟢 Mitigado |
| R13 | **Licencia: ¿mismo repo o repos separados para Free/Pro?** | Legal | 2 | 3 | **6** | Legal | Repo único con feature flags (simpler). Si surgen conflictos, migrar a repos separados. | 🟡 Abierto |
| R14 | **Code signing Windows**: necesario para evitar SmartScreen | Operacional | 3 | 2 | **6** | Gonzalo | Certificado EV ~$300/año. O alternativa: documentar "cómo instalar" para usuarios técnicos. | 🟡 Abierto |
| R15 | **core-cenf-agents no existe** y es visión clave | Técnico | 5 | 2 | **10** | Gonzalo | No es requisito para Fase 1-2. Investigación profunda en Q4 2026. | 🟢 Aceptado |

### Riesgos Críticos (Score > 15)

#### R01 — Bus Factor = 1
- **Impacto al cliente**: Si Gonzalo se toma 2 semanas de vacaciones, el proyecto se detiene. Bugs críticos no se corrigen. Releases se atrasan.
- **Mitigación propuesta**: Onboarding estructurado de Pablo con CES v0.1.0. Documentar decisiones clave en Engram (ya se hace). Dividir proyecto en tareas atómicas delegables. Definir "modo mantenimiento": Pablo puede hacer PRs de bugs sin supervisión.
- **Costo de mitigación**: ~12h de setup de onboarding + 2-3 semanas de ramp-up de Pablo (pagado por contrato actual)
- **Decisión requerida**: Mitigar — inversión necesaria antes de Fase 2

#### R02 — core-cenf-tenant NO existe
- **Impacto al cliente**: Sin tenant, no hay multi-usuario, no hay Pro con feature flags, no hay suscripciones. Grama Pro no puede existir sin esto.
- **Mitigación propuesta**: Interim 1 (2-3 semanas): Supabase Auth + RLS + LicenceManager local. Interim 2 (migración posterior): Cuando core-cenf-tenant exista, LicenceManager apunta a él (ports & adapters).
- **Costo de mitigación**: ~35-45h para interim funcional
- **Decisión requerida**: Mitigar — bloquear para Pro. No afecta Free MVP.

#### R03 — Tiempo de desarrollo vs cash flow
- **Impacto al cliente**: Proyecto abandonado por falta de fondos antes de llegar a ingresos. O peor: Gonzalo abandona por fatiga.
- **Mitigación propuesta**: Free MVP en MES 2 (no 3). Pro features DIFERIDAS hasta validación Free. No construir nada Pro hasta tener al menos 100 usuarios Free activos. Scope ambicioso pero plan pragmático.
- **Costo de mitigación**: $0 — es decisión de scope
- **Decisión requerida**: Mitigar — disciplina de scope

### Compliance Checklist

| Área | Requisito | Estado | Acción necesaria | Timeline |
|------|-----------|--------|------------------|----------|
| Privacidad | Política de privacidad para app desktop | ❌ No existe | Redactar y publicar en GitHub + web | Antes de Free MVP |
| Términos de servicio | ToS para Free vs Pro | ❌ No existe | Redactar con disclaimer de "beta" | Antes de Free MVP |
| Open Source License | Apache 2.0 (heredado de Audio2Text) | ✅ OK | Mantener | — |
| Code signing | Firma de builds Windows | ❌ No implementado | Evaluar si SmartScreen es problema real | Si usuarios reportan bloqueo |
| GDPR / Data protection | Procesamiento de datos de usuario | 🟡 Parcial | Documentar qué datos se envían a cloud (Groq) vs local | Antes de Pro |
| Telemetry | ¿Qué métricas se recolectan? | ❌ No definido | Decidir: opt-in telemetry anónima vs zero telemetry | Antes de Free MVP |

### Recomendaciones Priorizadas

**Acciones inmediatas (antes de Fase 1)**:
1. ✅ Decidir: sidecar Python VS proceso separado para backend (POC en semana 1)
2. ✅ Definir onboarding de Pablo: CES v0.1.0 + guía de contribución + tareas iniciales
3. ✅ Documentar la decisión "repo único con feature flags" oficialmente
4. ✅ Escribir Privacy Policy + ToS para Grama

**Acciones a 30/60/90 días**:
1. Mitigar R01: Pablo debe tener al menos 1 tarea completada (merged) en las primeras 2 semanas
2. Mitigar R02: Implementar interim Supabase + LicenceManager para Fase 2
3. Validar R11: Release Free MVP con bloques como feature experimental, medir uso y feedback

**Decisiones de "aceptar riesgo"**:
1. R05 (Competidores con funding): Aceptado — Grama no compite en su terreno. Diferenciación clara vía bloques + local-first.
2. R08 (Tauri v2 ecosystem): Aceptado — riesgo manejable con CES. Si Tauri v2 no funciona, Electron es plan de contingencia (pero no queremos).
3. R15 (core-cenf-agents no existe): Aceptado — visión a 12+ meses. No afecta roadmap inmediato.

---

## 4. Proyección de Costos

### Costos Fijos Mensuales

| Concepto | Costo/mes | Fuente |
|----------|-----------|--------|
| OpenCode Go (DeepSeek Flash workhorse) | $10 | Pricing actual |
| OpenCode Zen API | $40 | Pricing actual |
| Z.AI Pro (uso moderado) | $72 | Pricing actual |
| Antigravity (Gemini, Claude) | $20 | Pricing actual |
| GitHub Free (repos privados + Actions) | $0 | Plan Free |
| Supabase Free tier (auth + db) | $0 | Plan Free (hasta 50K users) |
| **Total costos fijos** | **$142/mes** | |

### Costos Variables — Desarrollo

| Actividad | Tokens/mes | Costo estimado | Notas |
|-----------|-----------|----------------|-------|
| Desarrollo SDD (Fase 1: ~80h) | ~20M tokens | $100-150/mes | DeepSeek Flash 80%, Pro 15% |
| Debugging y PRs | ~5M tokens | $25-40/mes | |
| Investigación (core-cenf-tenant, etc.) | ~3M tokens | $15-25/mes | |
| Generación de assets (UI, icons) | ~1M tokens | $5-10/mes | |
| **Total variable desarrollo** | **~29M tokens** | **$145-225/mes** | |

### Costos Variables — Operación (por usuario)

| Componente | Free (costo/user/mes) | Pro (costo/user/mes) |
|-----------|----------------------|---------------------|
| Transcripción Groq cloud | $0.05 (100 min/mes) | $0.20 (500 min/mes) |
| Transcripción local (faster-whisper) | $0 | $0 |
| Voice Output (TTS local) | $0 | $0 |
| AI post-processing (bloques, corrección) | $0 | $0.50-1.00 |
| Engram storage (SQLite local) | $0 | $0 |
| Git versioning storage | $0 | $0 |
| **Costo variable por usuario** | **~$0.05/mes** | **~$0.70-1.20/mes** |

**Observación clave**: Grama es mayoritariamente LOCAL. Los costos variables son BAJÍSIMOS comparados con SaaS cloud (Otter, Fireflies, Wispr). Esto es una VENTAJA COMPETITIVA ESTRUCTURAL.

### Escenarios Económicos

#### Escenario Pesimista (50 Free + 10 Pro)

| Concepto | Free (50 users) | Pro (10 users) | Total |
|----------|----------------|----------------|-------|
| Ingresos | $0 | $150 | $150/mes |
| Costos fijos | — | — | $142/mes |
| Costos variables | $2.50 | $12 | $14.50/mes |
| **Margen** | **-$144.50** | **-$4** | **-$6.50/mes** |
| **Break-even usuarios Pro**: | | | **~11 Pro** |

#### Escenario Base (300 Free + 50 Pro)

| Concepto | Free (300 users) | Pro (50 users) | Total |
|----------|-----------------|----------------|-------|
| Ingresos | $0 | $750 | $750/mes |
| Costos fijos | — | — | $142/mes |
| Costos variables | $15 | $60 | $75/mes |
| **Margen** | **-$157** | **+$690** | **+$533/mes** |
| **Break-even usuarios Pro**: | | | **~11 Pro** |

#### Escenario Optimista (1,000 Free + 200 Pro)

| Concepto | Free (1000 users) | Pro (200 users) | Total |
|----------|------------------|-----------------|-------|
| Ingresos | $0 | $3,000 | $3,000/mes |
| Costos fijos | — | — | $142/mes |
| Costos variables | $50 | $240 | $290/mes |
| **Margen** | **-$192** | **+$2,760** | **+$2,568/mes** |

### Break-Even Analysis

| Escenario | Pro users necesarios | Free users | Ingreso total | Margen |
|-----------|---------------------|------------|---------------|--------|
| Solo Pro (sin Free) | ~10 | 0 | $150 | ~$4/mes |
| + Free básico | ~12 | 100 | $180 | ~$20/mes |
| + Salario simbólico ($1000/mes) | ~78 | 500 | $1,170 | ~$980/mes |
| + Pablo part-time ($500/mes) | ~112 | 500 | $1,680 | ~$1,430/mes |

### Proyección a 12 Meses (Escenario Base)

| Mes | Free users | Pro users | Ingresos | Costos | Margen acumulado |
|-----|-----------|-----------|----------|--------|-----------------|
| 1 | 0 | 0 | $0 | $300 | -$300 |
| 2 (Free MVP) | 50 | 0 | $0 | $350 | -$650 |
| 3 | 150 | 5 | $75 | $350 | -$925 |
| 4 (Pro launch) | 250 | 15 | $225 | $370 | -$1,070 |
| 5 | 300 | 25 | $375 | $370 | -$1,065 |
| 6 | 350 | 35 | $525 | $370 | -$910 |
| 7 | 400 | 45 | $675 | $370 | -$605 |
| 8 (BREAK-EVEN) | 450 | 55 | $825 | $380 | -$160 |
| 9 | 500 | 65 | $975 | $380 | +$435 |
| 10 | 550 | 75 | $1,125 | $390 | +$1,170 |
| 11 | 600 | 90 | $1,350 | $400 | +$2,120 |
| 12 | 700 | 100 | $1,500 | $410 | +$3,210 |

**Break-even**: Mes 8 (Free MVP en mes 2, Pro en mes 4). ~55 usuarios Pro.
**Inversión inicial**: ~$1,070 (primeros 4 meses de costos acumulados).

---

## 5. Roadmap

### Visión / North Star

> "Grama es la interfaz universal que cualquier persona usa para hablar con IAs — una app de escritorio que transcribe lo que decís, enriquece lo que responden, guarda todo con contexto, y lo lleva a cualquier herramienta agéntica."

### Timeline Global

**Inicio**: Julio 2026 | **Free MVP**: Septiembre 2026 | **Pro Launch**: Noviembre 2026 | **Visión 12 meses**: Julio 2027

### Roadmap Fractal

| Fase | Release | Features | Timeline | Tokens est. | Costo $ | Dependencias |
|------|---------|----------|----------|-------------|---------|--------------|
| **F1** | **Grama Free MVP** | Skeleton Tauri v2 + Svelte 5 + CES template. Migrar transcripción (Groq + faster-whisper). Historial básico. Hotkeys globales. Bloques de contexto (básico, read-only). | Jul-Sep 2026 (8 semanas) | 8M | $150-200 | Audio2Text v0.16.0 funcional. CES v0.1.0 definido. POC sidecar resuelto. |
| **F2** | **Grama Free+** | Voice Output (TTS local). Bloques de contexto completos (edición, reorden, token counter, Copy All). Mejoras UI/UX. CI/CD builds. | Sep-Oct 2026 (6 semanas) | 5M | $100-150 | Fase 1 completa. Microsoft TTS repo integrado. |
| **F3** | **Grama Pro v1** | core-cenf-tenant (interim Supabase). LicenceManager + Stripe. Corrección Iterativa 1:2:. Engram Integration básica. Git Versioning básico. | Oct-Dic 2026 (10 semanas) | 10M | $200-250 | Fase 2 completa. core-cenf-tenant interim funcional. Stripe account. |
| **F4** | **Grama Scale** | Multi-agent portability (core-cenf-agents investigación). Engram avanzado (análisis patrones, generación automática de bloques). Git avanzado (diff, rollback). core-cenf-tenant definitivo. Pricing final. | Ene-Jul 2027 (6 meses) | 12M+ | $250-400/mes | Fase 3 completa + validación de mercado. core-cenf-agents investigación. |

### Hitos Clave

| Hito | Fecha | Criterio de éxito |
|------|-------|-------------------|
| POC sidecar Tauri-Python funcional | Semana 1 (Jul 2026) | Backend Python arranca desde Tauri, responde a ping HTTP |
| Skeleton Tauri conutería de 3 pantallas | Semana 3 | Transcripción, historial, settings — todas conectadas al backend |
| **Free MVP Released** | **Semana 8 (Sep 2026)** | Grabación → transcripción → historial → bloques básicos. Build .exe descargable. |
| Voice Output funcional | Semana 10 | TTS local funcionando, controles de reproducción |
| Bloques completos + Copy All | Semana 14 | Panel lateral completo, token counter, templates por IA |
| **Pro v1 Released** | **Semana 22 (Dic 2026)** | Corrección iterativa, Engram integration, Git versioning, suscripciones Stripe |
| core-cenf-tenant definitivo (no interim) | Q1 2027 | Auth multi-tenant, RBAC, feature flags, API completa |
| **Break-even** | **Mes 8 (Feb 2027)** | 55+ usuarios Pro activos |
| Multi-agent portability v1 | Q2-Q3 2027 | Soporte para OpenCode, Claude Code, Goose plugins |

### OKRs

#### Fase 1 — Fundación (Q3 2026)
- **O1**: Establecer Grama como plataforma funcional de código abierto
  - KR1: Free MVP released en GitHub con build descargable (target: semana 8)
  - KR2: 50+ GitHub stars en las primeras 2 semanas post-release
  - KR3: 10+ usuarios únicos reportando primera transcripción exitosa
  - KR4: Backend tests siguen pasando (62+ tests)
- **O2**: Establecer ritmo de desarrollo sostenible
  - KR1: Pablo completa y mergea al menos 2 PRs en Fase 1
  - KR2: Costo de desarrollo < $200/mes en tokens
  - KR3: CI/CD builds funcionando para Windows

#### Fase 2 — Diferenciación (Q4 2026)
- **O3**: Diferenciar Grama de competidores de transcripción pura
  - KR1: Voice Output released y documentado
  - KR2: Bloques de contexto completos con token counter
  - KR3: NPS > 30 en encuesta a early adopters

#### Fase 3 — Monetización (Q4 2026 - Q1 2027)
- **O4**: Convertir usuarios Free en suscripciones Pro
  - KR1: 10+ usuarios Pro pagando en mes 1 de Pro launch
  - KR2: Conversión Free → Pro > 5%
  - KR3: Churn Pro < 5% mensual
  - KR4: core-cenf-tenant interim funcionando con Stripe

#### Fase 4 — Escala (2027)
- **O5**: Construir plataforma portable multi-herramienta
  - KR1: core-cenf-agents spec completa y en desarrollo
  - KR2: 3+ tool integrations (OpenCode, Claude Code, Goose)
  - KR3: 200+ usuarios Pro
  - KR4: Revenue > $3,000/mes

### Recursos Necesarios por Fase

| Fase | Gonzalo (h/sem) | Pablo (h/sem) | Tokens/mes | Costo_total | Riesgo si falta recurso |
|------|----------------|---------------|------------|-------------|------------------------|
| F1 | 15-20 | 5-10 | $150-200 | $150-200 | Pablo crítico para acelerar UI. Sin Pablo: +4 semanas. |
| F2 | 10-15 | 5-10 | $100-150 | $100-150 | Menos crítico. Gonzalo puede solo. |
| F3 | 15-20 | 10-15 | $200-250 | $200-250 | **Pablo crítico** — core-cenf-tenant es mucho trabajo. |
| F4 | 10-15 | 5-10 | $250-400 | $250-400 | Depende de validación de mercado. Ajustar según demanda. |

---

## 6. Go-to-Market

### Propuesta de Valor (una línea)

**Para usuarios de IA que trabajan con voz**, Grama es la interfaz de escritorio que conecta tu voz con cualquier herramienta de IA — transcribe, contextualiza, corrige y portabiliza todo tu trabajo con un solo atajo de teclado.

### Segmentos y Canales

| Segmento | Canal principal | Canal secundario | CAC estimado | Ciclo de venta |
|----------|----------------|-----------------|-------------|----------------|
| **Developers / Power users de IA** | GitHub (open source) + Product Hunt | Twitter/X + YouTube tutorials | $0 (orgánico) | 0 — autoservicio |
| **Transcriptores profesionales** | Reddit (r/transcription, r/whisper) + Discord | YouTube + blogs | $0-5 (orgánico) | 1-3 días |
| **Profesionales que usan IAs** (knowledge workers) | Product Hunt + Twitter/X + LinkedIn | Medium/Substack articles | $0.50-2 (orgánico) | 1-7 días |
| **Estudiantes / investigadores** | Reddit (r/MacOS, r/Windows) + GitHub | TikTok/IG Reels (vídeos cortos) | $0 (orgánico) | 0 — gratuito |

### Estrategia de Pricing

| Plan | Precio | Qué incluye | Target | Justificación competitiva |
|------|--------|-------------|--------|--------------------------|
| Free | $0/mes | Transcripción (limitada cloud, ilimitada local). Voice Output. Bloques básicos. | 100% de usuarios — construir base | Benchmark: Otter Free (300 min/mes), Fireflies Free (800 min almacenamiento). Grama Free es más generosa en local. |
| Pro | $15/mes | Todo ilimitado. Corrección Iterativa 1:2:. Bloques avanzados. Engram Integration. Git Versioning. AI contexto ilimitado. | Power users de IA (500K global) | Benchmark: Wispr Pro ($12-15), Otter Pro ($8-17), Fireflies Pro ($10). $15 es punto dulce. |
| Pro Annual | $12/mes ($144/año) | Mismo que Pro mensual pero 20% descuento | Usuarios comprometidos | Benchmark: todos ofrecen descuento anual. Estándar de industria. |
| Enterprise | Contactar | Todo Pro + SSO, on-prem deploy, audit logs | Empresas con compliance (health, legal) | Benchmark: Otter Business ($20-30), Fireflies Business ($19). Precio a definir. |

### Mensajes por Canal

| Canal | Mensaje principal | Objeción a abordar |
|-------|-------------------|--------------------|
| **GitHub README** | "Tu interfaz de escritorio para hablar con IAs. Open source, local-first, con bloques de contexto y corrección iterativa." | "¿Por qué no usar solo Whisper?" → Porque Grama no es solo transcripción, es CAPA DE CONTEXTO para tu IA. |
| **Product Hunt** | "Grama: la primera interfaz de escritorio que une transcripción, contexto de IA y portabilidad — todo en una app." | "Ya uso Otter/Fireflies" → Ellos son para reuniones. Grama es para tu workflow personal de IA. Diferencia clave. |
| **Twitter/X** | "Grabá. Transcribí. Corregí tu IA. Repetí. Todo con un hotkey." | "¿Otra app de transcripción?" → No es de transcripción. Es de contexto IA. |
| **YouTube (tutorial)** | "Cómo usar Grama para corregir respuestas de IA con tu voz en 3 pasos." | "Parece complicado" → Demostración visual de 2 minutos. Time-to-value < 5 min. |
| **Reddit** | "Construí una app open source para transcribir + agregar contexto a prompts de IA. Feedback welcome." | "Muy bonito pero ¿funciona?" → "62 tests, 18 managers de infraestructura, 2 años de desarrollo. Sí, funciona." |
| **Discord (CENF)** | Early adopters program: acceso temprano, feedback directo, features priorizadas. | "¿Me van a vender algo?" → Free primero. Pro después y con opción. |

### Timeline de Lanzamiento

#### Pre-lanzamiento (Jul-Ago 2026 — 8 semanas)
- Semana 1-2: Setup repositorio público Grama (repo separado o subárbol — decidir)
- Semana 1-2: GitHub Issues + Projects configurados
- Semana 3-4: Skeleton Tauri funcional en main branch
- Semana 5-6: Invitar 5-10 early adopters (Discord CENF) a testear versión alpha
- Semana 7-8: Freeze features, testing, build de release candidate
- Semana 7-8: Preparar assets de Product Hunt (logo, screenshots, description, maker comment)

#### Launch (Semana 8 — Sep 2026)
- **Día 0**: Release v1.0.0 en GitHub (tag, release notes, build .exe)
- **Día 0**: Post en Product Hunt "Grama — Open source desktop interface for AI"
- **Día 0**: Tweet thread en Twitter/X (Gonzalo personal account)
- **Día 0**: Post en Reddit r/programming, r/MachineLearning, r/whisper
- **Día 0-3**: Monitorear GitHub Issues, responder comments de Product Hunt
- **Día 7**: Post-launch retrospective: qué funcionó, qué no

#### Post-launch (Sep-Nov 2026)
- **Día 30**: Release v1.1.0 con bugs fixes + Voice Output (basado en feedback)
- **Día 30**: Primer YouTube tutorial (Gonzalo lo hace, 5-10 min)
- **Día 60**: Release v1.2.0 con bloques completos + mejora UX
- **Día 60**: Encuesta NPS a usuarios activos (target: NPS > 30)
- **Día 90**: Anunciar Pro pricing + features. Abrir espera para Pro.

### KPIs de GTM

| Métrica | Target (Día 30) | Target (Día 90) | Target (Día 180) |
|---------|----------------|-----------------|------------------|
| GitHub stars | 100+ | 500+ | 2,000+ |
| GitHub clones/downloads | 200+ | 1,000+ | 5,000+ |
| Usuarios activos (DAU) | 20+ | 100+ | 300+ |
| Product Hunt upvotes | 50+ | — | — |
| Usuarios Pro | — | 15+ | 55+ |
| Conversión Free → Pro | — | >3% | >5% |
| Community Discord | 50+ | 200+ | 500+ |
| Revenue Monthly | $0 | $225+ | $825+ |

### Objeción Principal por Segmento

| Segmento | Objeción | Respuesta |
|----------|----------|-----------|
| Developers | "Ya uso terminal + whisper" | "Grama no compite con terminal. Es capa de contexto + portabilidad. ¿Tu terminal te guarda el contexto de lo que le dijiste a ChatGPT ayer?" |
| Power users IA | "Ya pago ChatGPT Plus ($20)" | "ChatGPT Plus es una subscription aparte. Grama funciona CON ChatGPT, Claude, Gemini. No reemplaza, complementa." |
| Transcriptores | "Prefiero SaaS como Otter" | "Otter te cobra $17/mes por 20h de transcripción. Grama te da ILIMITADO local por $0. Y si querés cloud, $15/mes." |
| Empresas | "No confío en apps de escritorio open source" | "Código abierto auditáble. Local-first (datos no salen de tu máquina). Si querés on-prem enterprise, tenemos plan." |

### Partners Estratégicos

| Partner | Valor que aporta | Modelo |
|---------|-----------------|--------|
| **Hermes** (comunidad CENF) | Early adopters, feedback, alpha testers | Gratuito, comunidad |
| **GitHub** (open source program) | Visibilidad, discoverability | Gratuito, open source |
| **YouTube creators** (tutorials) | Content marketing, reach | Revenue share en links de afiliado |
| **Product Hunt** | Launch visibility | Gratuito |
| **Discord communities** (Whisper, AI, transcription) | Community growth | Gratuito, presencia activa |

---

## 7. Investigaciones Pendientes

### Hook Research — Investigaciones Profundas a Realizar

Basado en los análisis de los 6 roles anteriores, se identifican las siguientes investigaciones críticas:

| # | Investigación | Prioridad | Por qué | Qué resolvería | Costo est. |
|---|--------------|-----------|---------|----------------|------------|
| HR1 | **core-cenf-tenant: arquitectura auth+multitenant** | 🔴 ALTA | Es PRERREQUISITO para versión Pro. Decidir stack: Supabase Auth vs Auth0 vs Cognito. Definir modelo de datos de tenant. Feature flags design. | La pregunta abierta #3: ¿investigación primero o implementación paralela? | $20-30 tokens |
| HR2 | **Mercado de herramientas desktop IA: validación de demanda de bloques de contexto** | 🔴 ALTA | Riesgo R11: el feature estrella (bloques) no tiene demanda validada. Entrevistar a 10-20 power users de IA. | Si la demanda no existe, pivotear antes de construir. | $0 (entrevistas) |
| HR3 | **Competencia profunda: Wispr Flow + Otter + Fireflies feature matrix** | 🟡 MEDIA | Entender exactamente qué features tienen y cuáles no. Buscar gaps. Validar diferenciación. | Confirmar que los diferenciadores (bloques, corrección iterativa, Engram) no están en roadmap de nadie. | $10-15 tokens |
| HR4 | **Tauri v2 sidecar Python: viabilidad técnica y alternativas** | 🟡 MEDIA | Decidir sidecar vs proceso separado. Investigar: empaquetado PyInstaller, manejo de errores, performance. | La pregunta no resuelta más importante del stack técnico. | $10-15 tokens |
| HR5 | **Pricing elasticity: WTP para herramienta de contexto IA** | 🟡 MEDIA | $15/mes es estimación. Validar con Van Westendorp o Gabor-Granger con early adopters. | Confirmar o ajustar pricing antes de Pro launch. | $0 (encuesta) |
| HR6 | **core-cenf-agents: state of the art de portabilidad multi-herramienta** | 🟢 BAJA | Visión a 12+ meses. Investigar: MCP protocol, plugin systems de cada herramienta, integraciones existentes. | Roadmap de Fase 4. No bloquea nada ahora. | $15-20 tokens |
| HR7 | **Open source monetization models: cómo monetizar OSS sin alienar comunidad** | 🟢 BAJA | Lecciones de GitPod, VS Code, Sentry, N8n, Supabase. Qué modelo funciona para OSS desktop. | Evitar errores de monetización que matan comunidades OSS. | $10-15 tokens |
| HR8 | **Git strategy: repo único + feature flags vs repos separados para Free/Pro** | 🟡 MEDIA | La pregunta abierta #1. Impacta CI/CD, licencias, contribuciones de comunidad, complejidad de build. | Decisión fundacional de arquitectura de repositorios. | $5-10 tokens |

### Recomendación de Orden de Investigación

1. **Semana 1-2**: HR4 (sidecar Tauri POC) + HR1 (core-cenf-tenant research) — en paralelo
2. **Semana 3-4**: HR2 (validación de demanda con entrevistas) + HR8 (decisión de repos)
3. **Semana 5-8**: HR3 (competencia deep dive) + HR5 (pricing WTP)
4. **Q1 2027**: HR6 (core-cenf-agents) + HR7 (OSS monetization)

---

## 8. Decisión Estratégica

### Veredicto: **GO — CON CONDICIONES**

### Síntesis de Evaluación

| Factor | Score | Detalle |
|--------|-------|---------|
| **Viabilidad Técnica** | 🟡 70/100 | Backend funcional (62 tests, 18 managers). Stack definido (CES v0.1.0). Riesgo: sidecar Tauri-Python no validado. |
| **Product-Market Fit** | 🟡 65/100 | Mercado grande ($4.5B) y creciendo (15-20% CAGR). Diferenciadores reales pero NO validados con usuarios. Riesgo: nadie pidió bloques de contexto. |
| **Riesgos** | 🟡 60/100 | 2 riesgos críticos (bus factor=1, core-cenf-tenant). Ambos mitigables pero requieren acción inmediata. |
| **Costos** | 🟢 80/100 | Costos operativos muy bajos (local-first). Break-even en solo ~11 usuarios Pro. Modelo económico viable. |
| **Roadmap** | 🟡 70/100 | Plan de 4 fases realista. Free MVP en 8 semanas es alcanzable. Pro requiere core-cenf-tenant. |
| **Go-to-Market** | 🟡 65/100 | Canales orgánicos bien definidos. CAC=$0. Community-first como estrategia correcta. Falta: presencia en Product Hunt y contenido. |

**Score general**: 68/100 — Viable, con condiciones claras.

### Condiciones para GO

1. ✅ **Sidecar POC en Semana 1**: Si el sidecar Python-Tauri no funciona en 1 semana, replantear arquitectura (proceso separado).
2. ✅ **core-cenf-tenant research antes de Fase 3**: Investigación profunda en Q3 2026. Decisión de stack antes de Nov 2026.
3. ✅ **Pablo onboarded en Fase 1**: Mínimo 2 PRs merged por Pablo en Fase 1. Si no se logra, asumir bus factor = 1 y ajustar scope.
4. ✅ **Validación de bloques de contexto**: Entrevistar a 10+ power users de IA en Fase 1. Si no hay tracción, NO construir Pro.
5. ✅ **Disciplina de scope**: Free MVP primero. No construir Pro features hasta tener base de usuarios Free validada.

### Riesgos Aceptados

1. **Competidores con funding** (Otter $50M, Wispr $12M+): Aceptado. Grama no compite en su terreno. Diferenciación clara.
2. **Tauri v2 ecosystem inmaduro**: Aceptado. Riesgo manejable. Plan de contingencia: Electron (pero no querido).
3. **core-cenf-agents no existe**: Aceptado. Visión a 12+ meses. No bloquea roadmap inmediato.

### Próximos Pasos

1. **HOY**: Sidecar Tauri-Python POC (1 día de trabajo). Si funciona, la arquitectura está validada.
2. **ESTA SEMANA**: Decidir repo strategy (recomendación: repo único con feature flags, separar si hay conflictos).
3. **ESTA SEMANA**: Iniciar investigación core-cenf-tenant (HR1) — delegar con task a team-strategic o investigador.
4. **SEMANA 1-2**: Definir onboarding de Pablo con CES v0.1.0 y guía de contribución.
5. **SEMANA 1-8**: Implementar Fase 1 — Free MVP. TODO el equipo enfocado en esto.
6. **SEMANA 4**: Entrevistar a 10+ power users de IA para validar bloques de contexto.

### Criterios de NO-GO (si alguno se cumple, detener)

1. Sidecar Tauri-Python no funciona y no hay alternativa viable en 2 semanas.
2. Pablo no completa NINGÚN PR en Fase 1 (bus factor sigue siendo 1 y no hay mejora).
3. Después de entrevistar a 10+ power users, NINGUNO muestra interés en bloques de contexto.
4. core-cenf-tenant resulta ser 3x más complejo de lo estimado (>120h).
5. Grama consume >$350/mes en tokens de desarrollo y no hay señales de tracción.

---

> *Documento generado por Strategic Gestion Team (7 sub-roles) del ecosistema CENF.*
> *Topic key: strategic-decision/grama-platform*
> *Supersedes: Decisión estratégica previa del 2026-07-24*
