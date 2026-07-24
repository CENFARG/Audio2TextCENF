# GRAMA — Síntesis Estratégica Post-Brainstorming

> **Contexto**: Sesión de ideas libre sobre la evolución de Audio2Text hacia Grama.
> **Rol**: Advisor — no se delega nada hasta definir el rumbo.
> **Documentos consumidos**: CES v0.1.0 (frontend standard), bloques de contexto (11 archivos), Grama (proyecto Tauri existente), current-ui-inventory.md, spec_SDD_TDD_desing.md
> **Fecha**: 2026-07-24

---

## 1. EL CAMBIO FUNDACIONAL: Audio2Text → Grama

Audio2Text empezó como **transcriptor**. Grama es una **plataforma de interacción con IA**.

```
Audio2Text (hoy)                     Grama (visión)
┌──────────────────────┐            ┌──────────────────────────────┐
│ Grabar → Transcribir │            │ Capa gratuita (open source):  │
│ ─> Historial         │            │   Grabar → Transcribir       │
│ ─> Metadatos         │    ──→     │   Historial + metadatos      │
│ ─> AI Enhancement    │            │   Bloques de contexto básico  │
└──────────────────────┘            ├──────────────────────────────┤
                                    │ Capa paga (Grama Pro):       │
                                    │   Corrección iterativa (1:)  │
                                    │   Bloques de contexto full    │
                                    │   Engram integration           │
                                    │   Git versioning               │
                                    │   Multi-provider agents        │
                                    │   Token counter                │
                                    │   Team collaboration           │
                                    └──────────────────────────────┘
```

---

## 2. STACK TECNOLÓGICO — CES v0.1.0

El estándar de frontend CENF ya define TODO el stack:

| Capa | Tecnología | Versión |
|---|---|---|
| Contenedor | **Tauri v2** | Mínimo Rust (~250 líneas) |
| UI Framework | **Svelte 5 (Runes)** | `$state`, `$derived`, `$effect` |
| Estilos | **Tailwind CSS v4** | Utility-first |
| Componentes | **shadcn-svelte** | Copia local, editable |
| Iconos | **Lucide-svelte** | Vectorial |
| Infraestructura | **core-cenf-ts** | 19 managers |
| Validación | **Zod** | Single source of truth |
| Monorepo | **pnpm + Turborepo** | Workspaces |
| Testing | **Vitest + Playwright** | Unit + E2E |
| Git | **Conventional Commits** | Trunk-based |
| CI/CD | **GitHub Actions** | tauri-action |

**Esto responde las 4 preguntas que había dejado pendientes**:
1. **Framework TS**: Svelte 5 (Runes) ✅
2. **State management**: Runes nativos ($state, $derived) + core-cenf-ts para estado global ✅
3. **Migración**: Cutover controlado (Grama coexiste hasta paridad) 
4. **Component library**: shadcn-svelte + Tailwind v4 ✅

---

## 3. LAS 7 CAPABILITIES DE GRAMA

### 3.1 Transcripción (Free)
Lo que ya funciona. Backend FastAPI listo, providers cableados, 18 managers bootstrapped.
- ✅ Grabar + transcribir
- ✅ 3 proveedores (Groq, faster-whisper, NVIDIA)
- ✅ Historial con metadatos
- ✅ AI Enhancement
- ✅ Bloques de contexto POST-transcripción

### 3.2 Sistema de Corrección Iterativa (1:2:) (Pro)
Tu metodología documentada en `boques_contexto/iterativo-acumulativo.md`:
- Seleccionar parte de una respuesta de IA (Ctrl+Shift+Click?)
- Se abre en Grama como "1: [texto seleccionado]"
- Botón de grabación para transcribir tu corrección oral
- 2: siguiente bloque
- Genera automáticamente bloques de contexto reutilizables

### 3.3 Bloques de Contexto (Free + Pro)
11 archivos ya existen en `boques_contexto/`:
- `iterativo-acumulativo.md`, `inferencia.md`, `supervision.md`, `parafrase.md`, etc.
- Panel lateral con checkboxes para seleccionar cuáles adjuntar
- Token counter por bloque + total
- "Copy all" button → clipboard con todos los bloques seleccionados
- **Nuevo**: generación automática de bloques desde interacciones previas

### 3.4 Engram Integration (Pro)
- Conexión nativa con base Engram local
- Buscar prompts previos
- Analizar patrones de corrección → generar nuevos bloques de contexto
- Versionado de prompts

### 3.5 Git Versioning (Pro)
- Transcripciones versionadas en git local
- Correcciones y bloques de contexto versionados
- Diff entre versiones
- Rollback de cualquier cambio

### 3.6 Token Counter (Free + Pro)
- Conteo por bloque de contexto
- Conteo total del payload completo
- Estimación de costo ($) antes de enviar

### 3.7 Multi-Agent Portability (Visión CENF)
El concepto más ambicioso:
- Abstracción de "cerebro digital"
- Workflows, skills, hooks, subagentes en un formato portable
- Compilable/transformable a: OpenCode, CloudCode, Goose, Cline, etc.
- Conexión con el P2 Installer

---

## 4. FREE vs PRO — ARQUITECTURA

Dijiste que no sabés cómo separarlo. Opciones:

| Opción | Pros | Contras |
|---|---|---|
| **A. Mismo repo + feature flags** | Un solo codebase, fácil mantener | core-cenf-ts tiene FeatureFlagManager justo para esto |
| **B. Repos separados** | Límite claro, seguridad por repo | Duplicación, más mantenimiento |
| **C. Mismo repo, builds separados** | Código compartido, binarios diferentes | Más complejo de configurar |

**Recomendación (para debatir con el equipo)**: Opción A + FeatureFlagManager de core-cenf-ts. Es exactamente para lo que fue diseñado. Misma base, features habilitadas por license/role. Ya tenemos LicenceManager y PermissionManager en core-cenf-py.

---

## 5. PROYECTO GRAMA EXISTENTE

Ya existe en `C:\Dropbox\DOC.RECA\06-Software\Grama/`:
- `src-tauri/` — Tauri v2 con Cargo.toml, tauri.conf.json
- `src/` — Frontend (vacío o en desarrollo)
- `backend/` — Python FastAPI (main.py, requirements.txt, src/)
- `assets/`, `config/`, `data/`, `docs/`, `logs/`

Tiene `.agent/`, `.context/`, `.memorybank/` — ya tiene estructura agéntica.

**Propuesta**: Grama NO es un proyecto nuevo — es la continuación de este proyecto existente retomando lo que ya se construyó.

---

## 6. LO QUE HAY QUE DISCUTIR CON LOS EQUIPOS

| Tópico | Equipo |
|---|---|
| Stack final (CES v0.1.0) | Arquitecto de Sistema |
| Free vs Pro (feature flags) | Estrategia + Infra |
| Token counting + costos | Financiero |
| Engram integration | Infra + Desarrollo |
| Git versioning | Desarrollo |
| Multi-agent portability | Estrategia + Desarrollo |
| UI/UX de bloques de contexto | Desarrollo Frontend |
| Corrección iterativa (1:2:) | Desarrollo + Prompting |

---

## 7. PRÓXIMO PASO INMEDIATO

Lo más urgente antes de arrancar:
1. **Validar CES v0.1.0** con el equipo — ¿Svelte 5 + shadcn-svelte es el camino?
2. **Decidir Free vs Pro** — ¿feature flags o repos separados?
3. **Revisar el Grama existente** — ¿qué tiene, qué falta?

Después de esas 3 definiciones, podemos arrancar SDD:
- `/sdd-new` → Grama v1: Tauri shell + Svelte skeleton + core-cenf-ts bootstrap
- Luego: transcripción (migrar Audio2Text) → bloques de contexto → corrección iterativa → Engram → Git → etc.

---

*Documento de síntesis — modo Advisor. No se ejecuta nada hasta alinear visión con equipos.*
