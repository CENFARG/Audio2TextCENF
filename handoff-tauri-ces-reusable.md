# Audio2Text → Tauri v2 Migration — Reusable Components & Patterns

> **Handoff para el agente que está empezando un nuevo proyecto Tauri v2 + CES**
> **Proyecto fuente**: `C:\Dropbox\DOC.RECA\06-Software\Audio2Text`
> **Branch**: `feature/audio2text-v0.16.0-tauri-migration`
> **CES standard**: `C:\Dropbox\DOC.RECA\03-CENF\05-Recursos\25-db_Prompt\development\CES`

---

## 1. ESTRUCTURA DEL PROYECTO TAURI v2

```
proyecto/
├── src-tauri/                  ← Rust (Tauri v2 shell)
│   ├── Cargo.toml              ← Dependencias Rust
│   ├── tauri.conf.json         ← Config ventana, sidecar, bundle
│   ├── capabilities/default.json ← Permisos scoped (shell, global-shortcut, window)
│   ├── src/
│   │   ├── lib.rs              ← IPC commands + plugin setup
│   │   └── main.rs             ← Entry point
│   └── build.rs
├── src/                        ← Frontend Svelte 5
│   ├── index.html              ← Entry point (IMPORTANTE: standalone, no SvelteKit)
│   ├── main.ts                 ← Mount Svelte app
│   ├── app.svelte              ← Root component + routing
│   ├── app.css                 ← Tailwind v4 @theme + design tokens CSS vars
│   ├── vite.config.ts          ← Vite + Svelte plugin + $lib alias + cache
│   ├── tsconfig.json
│   ├── svelte.config.js
│   ├── package.json
│   ├── design-tokens/          ← Tokens de diseño (Pablo)
│   │   ├── tokens.json         ← Fuente única de verdad (50 tokens)
│   │   └── tokens.css          ← CSS custom properties
│   └── lib/
│       ├── navigation/tabs.ts  ← Config extensible de tabs (con feature flags)
│       ├── components/         ← Componentes reutilizables Svelte 5
│       ├── views/              ← Vistas de la app
│       ├── infrastructure/     ← API client + WebSocket + MockApiClient
│       └── state/              ← Svelte 5 runes ($state)
├── pnpm-workspace.yaml         ← Monorepo: solo src/
├── audio2text/                 ← Backend Python (sidecar)
│   ├── api/                    ← FastAPI
│   ├── infrastructure/         ← core_infrastructure bootstrap + registry
│   └── providers/              ← Ports & Adapters (3 ports, 4 adapters)
└── tests/
    ├── e2e/smoke.spec.ts       ← Playwright E2E
    └── infrastructure/          ← Backend tests
```

---

## 2. ARCHIVOS PARA COPIAR DIRECTAMENTE A UN NUEVO PROYECTO

### 2.1 Rust shell (src-tauri/)

| Archivo | ¿Copiable? | Notas |
|---|---|---|
| `Cargo.toml` | ✅ | Cambiar `name`, `version`. Las dependencias (tauri v2, serde, tauri-plugin-shell, tauri-plugin-global-shortcut) son estándar |
| `tauri.conf.json` | ✅ | Cambiar `productName`, `identifier`, `frontendDist` |
| `capabilities/default.json` | ✅ | Los permisos son genéricos. El scoped `shell:allow-execute` con sidecar binary name es el patrón a seguir |
| `src/lib.rs` | ✅ | Las 6 IPC commands (toggle_recording, start/stop_backend, get_backend_status, get/set_hotkeys) son template. Cambiar nombres según proyecto |
| `src/main.rs` | ✅ | Siempre igual |
| `build.rs` | ✅ | Siempre igual |

### 2.2 Frontend (src/)

| Archivo | ¿Copiable? | Notas |
|---|---|---|
| `index.html` | ✅ | `<div id="app">` + `<script type="module" src="/main.ts">` |
| `vite.config.ts` | ✅ | **IMPORTANTE**: `$lib` alias, `cacheDir: '.vite-cache'` (evita locks de Windows Defender), `fileURLToPath` shim para ESM |
| `svelte.config.js` | ✅ | `vitePreprocess()` para Svelte 5 |
| `tsconfig.json` | ✅ | Básico |
| `package.json` | ⚠️ | Copiar devDependencies (svelte, vite, tailwindcss, typescript, @playwright/test, zod). Cambiar `name` |
| `pnpm-workspace.yaml` | ⚠️ | Solo si es monorepo. `packages: ['src']` |
| `app.css` | ⚠️ | Template de Tailwind v4 @theme. Reemplazar tokens si el proyecto tiene paleta diferente |
| `design-tokens/*` | ⚠️ | Específico del proyecto. Copiar `tokens.json` + `tokens.css` si usás la misma paleta Dark Goldenrod. Si no, reemplazar valores |
| `lib/navigation/tabs.ts` | ✅ | **MUY REUTILIZABLE**. El `TabConfig` interface + `defaultTabs` array con `enabled` (feature flags) + `children` (sub-tabs) |
| `lib/infrastructure/api-client.ts` | ⚠️ | Template de APIClient con Zod. Cambiar endpoints y schemas |
| `lib/infrastructure/mock-api-client.ts` | ✅ | **MUY REUTILIZABLE**. Template de MockApiClient para desarrollo sin backend |
| `lib/infrastructure/ws-reconnect.ts` | ✅ | **MUY REUTILIZABLE**. Exponential backoff (max 3 retries, doubling delay) |

---

## 3. PATRONES SVELTE 5 (Runes) — COSAS QUE APRENDIMOS

### 3.1 NO usar SvelteKit
Usamos **Svelte standalone** con `@sveltejs/vite-plugin-svelte`. No instalamos SvelteKit. El entry point es `index.html` + `main.ts`.

### 3.2 $props() en vez de export let
```svelte
<!-- ❌ Svelte 4 -->
<script>export let currentView: string;</script>

<!-- ✅ Svelte 5 Runes -->
<script>
  let { currentView = $bindable('') }: { currentView: string } = $props();
</script>
```

### 3.3 $state, $derived, $effect
```svelte
<script>
  let count = $state(0);
  let doubled = $derived(count * 2);
  $effect(() => console.log(count));
</script>
```

### 3.4 Archivos .svelte.ts para estado compartido
```ts
// lib/state/transcription.svelte.ts
export const transcriptionState = $state({
  text: '',
  recordingStatus: 'idle' as 'idle' | 'recording' | 'processing',
  elapsedSeconds: 0,
});
```
Se importa en componentes: `import { transcriptionState } from '$lib/state/transcription.svelte';`

### 3.5 Navegación extensible con feature flags
```ts
// lib/navigation/tabs.ts
export interface TabConfig {
  id: string;
  label: string;
  icon: string;
  enabled: boolean;       // ← feature flag
  children?: TabConfig[];  // ← sub-tabs
}
```
Agregar/remover tabs es una línea:
```ts
defaultTabs.push({ id: 'nuevo', label: 'Nuevo', icon: '✨', enabled: userHasPro });
```

### 3.6 Vite config para Windows
```ts
// vite.config.ts
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  resolve: {
    alias: { '$lib': path.resolve(__dirname, 'lib') },
  },
  cacheDir: '.vite-cache',  // ← FUERA de node_modules (evita Windows Defender locks)
  server: { port: 5173 },
});
```

---

## 4. CORRECCIONES DE BUGS DURANTE LA MIGRACIÓN

| Bug | Causa | Fix |
|---|---|---|
| Blank page | `export let` en Svelte 5 runes no funciona | → `$props()` + `$bindable` |
| Blank page | `__dirname` undefined en ESM | → `fileURLToPath(import.meta.url)` |
| Blank page | Vite cache en node_modules (Windows Defender EBUSY) | → `cacheDir: '.vite-cache'` |
| 404 /main.ts | `index.html` referenciaba `/src/main.ts` | → `/main.ts` |
| CORS bloqueado | `allow_origin_regex` no agrega header | → `allow_origins: ["http://localhost:5173"]` |
| History 500 | Stub retornaba None | → Instanciar `MetadataService()` real |
| Settings 422 | Schema mismatch flat vs nested | → Alinear frontend/backend |

---

## 5. CORE-CENF-TS — ESTADO DE INTEGRACIÓN

**NO INSTALADO**. El bootstrap.ts intenta cargarlo dinámicamente y falla silenciosamente:

```ts
// lib/infrastructure/bootstrap.ts
export async function bootstrap() {
  try {
    const { BootstrapOrchestrator } = await import('@cenf/core-cenf-ts');
    const orchestrator = new BootstrapOrchestrator();
    await orchestrator.startup();
  } catch {
    console.warn('core-cenf-ts not available — using mock bootstrap');
  }
}
```

**Para integrar core-cenf-ts en un nuevo proyecto**:
1. `pnpm add` desde path relativo: `../../core-cenf-ts` (o `C:\Dropbox\DOC.RECA\06-Software\core-cenf-ts`)
2. Cambiar el import dinámico por uno estático: `import { BootstrapOrchestrator } from '@cenf/core-cenf-ts'`
3. Wirear managers: ConfigManager, LoggerManager, I18nManager, CacheManager
4. Usar `BootstraOrchestrator` en `main.ts` antes de `mount(App, ...)`

---

## 6. PARA EL AGENTE DEL NUEVO PROYECTO

### Paso 0: Leer el estándar CES
```
C:\Dropbox\DOC.RECA\03-CENF\05-Recursos\25-db_Prompt\development\CES\AGENTS.md
C:\Dropbox\DOC.RECA\03-CENF\05-Recursos\25-db_Prompt\development\CES\llms.txt
C:\Dropbox\DOC.RECA\03-CENF\05-Recursos\25-db_Prompt\development\CES\CES-v0.1.0.md
```

### Paso 1: Copiar estructura base
```bash
# Copiar Rust shell
cp -r audio2text/src-tauri/ nuevo-proyecto/src-tauri/

# Copiar frontend scaffold
cp audio2text/src/index.html nuevo-proyecto/src/
cp audio2text/src/main.ts nuevo-proyecto/src/
cp audio2text/src/vite.config.ts nuevo-proyecto/src/
cp audio2text/src/svelte.config.js nuevo-proyecto/src/
cp audio2text/src/tsconfig.json nuevo-proyecto/src/
cp audio2text/src/package.json nuevo-proyecto/src/
cp audio2text/src/app.css nuevo-proyecto/src/

# Copiar componentes reutilizables
cp -r audio2text/src/lib/navigation/ nuevo-proyecto/src/lib/navigation/
cp -r audio2text/src/lib/infrastructure/ nuevo-proyecto/src/lib/infrastructure/
cp audio2text/src/lib/state/ nuevo-proyecto/src/lib/state/

# Copiar design tokens (si usás la paleta de Pablo)
cp -r audio2text/src/design-tokens/ nuevo-proyecto/src/design-tokens/
```

### Paso 2: Instalar dependencias
```bash
cd nuevo-proyecto
pnpm install
# Instalar Rust toolchain si no está
# rustup default stable
```

### Paso 3: Personalizar
- `tauri.conf.json`: cambiar `productName`, `identifier`
- `Cargo.toml`: cambiar `name`, `version`
- `lib/navigation/tabs.ts`: cambiar tabs según proyecto
- `app.css`: cambiar tokens si usás paleta diferente

### Paso 4: Arrancar
```bash
# Terminal 1 — Backend
python backend/main.py

# Terminal 2 — Frontend
cd src && pnpm dev
```

---

## 7. QUÉ FALTA PARA COMPLETAR EL ESTÁNDAR CES

Estas cosas ya implementadas deberían extraerse al CES como templates:

- [ ] Template de `vite.config.ts` con alias + cacheDir
- [ ] Template de TabConfig extensible con feature flags
- [ ] Template de MockApiClient
- [ ] Template de WebSocket reconnect con exponential backoff
- [ ] Checklist de "cosas que rompen en Svelte 5 Runes" (sección 3 de este doc)
- [ ] Checklist de "cosas que rompen en Windows" (Vite cache, ESM, pnpm)
- [ ] Template de Rust lib.rs con IPC commands genéricos
- [ ] Template de capabilities/default.json con scoped permissions

---

*Documento generado desde `feature/audio2text-v0.16.0-tauri-migration` el 2026-07-31.*
*Para el agente: este es EL handoff. Leélo entero, copiá la estructura, y personalizá.*