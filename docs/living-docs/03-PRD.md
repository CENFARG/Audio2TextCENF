# 03. Product Requirements Document (PRD) - Audio2Text

> **Versión:** 1.0.0
> **Fecha:** 2026-03-13
> **Estado:** Activo
> **Última actualización:** 2026-03-13

---

## 📋 RESUMEN EJECUTIVO

**Audio2Text** es una aplicación de escritorio para Windows que transcribe audio a texto en tiempo real usando IA, específicamente optimizada para español rioplatense y vocabulario técnico.

### Versión Actual
**0.9.4** (Producción)

### Próxima Versión
**0.10.0** (En desarrollo)

---

## 🎯 DEFINICIÓN DEL PRODUCTO

### Qué es Audio2Text

Una aplicación de escritorio que:
1. Captura audio del micrófono del usuario
2. Lo envía a la API de Groq (Whisper Large v3)
3. Post-procesa el texto para que sea legible
4. Muestra el resultado en una interfaz moderna
5. Guarda el audio y la transcripción

### Para Quién es

#### Usuario Primario (Persona)

**María, Contadora (35 años)**
- Trabaja en una PYME argentina
- Necesita transcribir reuniones con clientes
- No sabe mucho de tecnología
- Quiere algo rápido y preciso
- No quiere pagar suscripciones

#### Usuario Secundario (Persona)

**Juan, Desarrollador (28 años)**
- Trabaja en remoto
- Necesita transcribir reuniones técnicas
- Conoce de tecnología
- Quiere algo customisable
- Valora el open source

### Para Quién NO es

- ❌ Usuarios que quieren transcribir video (solo audio)
- ❌ Usuarios que quieren transcribir múltiples hablantes
- ❌ Usuarios sin conexión a internet
- ❌ Usuarios de Mac/Linux (hasta v1.0.0)

---

## 🎯 REQUISITOS FUNCIONALES

### Epic 1: Transcripción de Audio

#### User Story 1.1: Grabar Audio
**Como** usuario
**Quiero** grabar audio con un hotkey
**Para** transcribirlo rápidamente

**Criterios de Aceptación:**
- [ ] Usuario puede configurar hotkey (F1-F12)
- [ ] Al presionar hotkey, comienza grabación
- [ ] Overlay muestra que está grabando
- [ ] Timer muestra tiempo transcurrido
- [ ] Al presionar nuevamente, detiene grabación
- [ ] Audio se guarda en formato WAV

**Prioridad:** P0 (Crítico)
**Versión:** 0.9.4 (Completado)

#### User Story 1.2: Transcribir Audio
**Como** usuario
**Quiero** que el audio se transcriba automáticamente
**Para** obtener texto sin esfuerzo

**Criterios de Aceptación:**
- [ ] Al detener grabación, se transcribe automáticamente
- [ ] Transcripción se muestra en menos de 10 segundos
- [ ] Precisión del 95%+ en español rioplatense
- [ ] Soporte para español e inglés
- [ ] Vocabulario técnico reconocido correctamente

**Prioridad:** P0 (Crítico)
**Versión:** 0.10.0 (En desarrollo)

#### User Story 1.3: Post-Procesar Transcripción
**Como** usuario
**Quiero** que la transcripción se vea como texto escrito
**Para** no tener que editarla

**Criterios de Aceptación:**
- [ ] Puntuación correcta (puntos, comas)
- [ ] Mayúsculas correctas
- [ ] Muletillas eliminadas
- [ ] Vocabulario técnico normalizado
- [ ] Español rioplatense respetado

**Prioridad:** P0 (Crítico)
**Versión:** 0.10.0 (En desarrollo)

### Epic 2: Gestión de Transcripciones

#### User Story 2.1: Ver Historial
**Como** usuario
**Quiero** ver mis transcripciones anteriores
**Para** encontrarlas fácilmente

**Criterios de Aceptación:**
- [ ] Historial muestra últimas 100 transcripciones
- [ ] Se puede buscar por texto
- [ ] Se puede filtrar por fecha
- [ ] Se puede abrir transcripción completa
- [ ] Se puede copiar al portapapeles

**Prioridad:** P1 (Alta)
**Versión:** 0.9.4 (Completado)

#### User Story 2.2: Exportar Transcripción
**Como** usuario
**Quiero** exportar mis transcripciones
**Para** usarlas en otras apps

**Criterios de Aceptación:**
- [ ] Exportar a TXT
- [ ] Exportar a JSON
- [ ] Exportar a PDF (futuro)
- [ ] Exportar a DOCX (futuro)

**Prioridad:** P1 (Alta)
**Versión:** 0.11.0 (Planificado)

#### User Story 2.3: Renombrar con Emojis
**Como** usuario
**Quiero** renombrar transcripciones con emojis
**Para** identificarlas visualmente

**Criterios de Aceptación:**
- [ ] Selector de emojis disponible
- [ ] Búsqueda de emojis
- [ ] Categorización de emojis
- [ ] Emoji se guarda con nombre

**Prioridad:** P2 (Media)
**Versión:** 0.12.0 (Planificado)

### Epic 3: Configuración

#### User Story 3.1: Configurar API Key
**Como** usuario
**Quiero** configurar mi API key
**Para** usar la aplicación

**Criterios de Aceptación:**
- [ ] Campo para ingresar API key
- [ ] API key se ofusca al guardar
- [ ] Validación de API key
- [ ] Instrucciones de cómo obtenerla

**Prioridad:** P0 (Crítico)
**Versión:** 0.9.4 (Completado)

#### User Story 3.2: Configurar Hotkey
**Como** usuario
**Quiero** configurar mi hotkey
**Para** usar la tecla que prefiera

**Criterios de Aceptación:**
- [ ] Selector de hotkey (F1-F12)
- [ ] Combinaciones permitidas (Ctrl+F1, Alt+F2, etc.)
- [ ] Vista previa de hotkey seleccionado
- [ ] Conflicto con otras apps detectado

**Prioridad:** P1 (Alta)
**Versión:** 0.12.0 (Planificado)

#### User Story 3.3: Configurar Idioma
**Como** usuario
**Quiero** configurar el idioma de la app
**Para** usarla en mi idioma

**Criterios de Aceptación:**
- [ ] Selector de idioma (Español/Inglés)
- [ ] Cambio de idioma en tiempo real
- [ ] Strings traducidos correctamente

**Prioridad:** P1 (Alta)
**Versión:** 0.9.4 (Completado)

### Epic 4: Bloques y Middles

#### User Story 4.1: Crear Bloque
**Como** usuario
**Quiero** crear bloques personalizados
**Para** procesar transcripciones

**Criterios de Aceptación:**
- [ ] Editor de bloques disponible
- [ ] Bloque tiene nombre y descripción
- [ ] Bloque tiene prompt de sistema
- [ ] Bloque se guarda y reutiliza

**Prioridad:** P1 (Alta)
**Versión:** 0.11.0 (Planificado)

#### User Story 4.2: Aplicar Bloque
**Como** usuario
**Quiero** aplicar bloques a transcripciones
**Para** procesarlas

**Criterios de Aceptación:**
- [ ] Checkbox para habilitar bloque
- [ ] Bloque se aplica en orden
- [ ] Bloque pre-transcripción modifica prompt
- [ ] Bloque post-transcripción modifica resultado

**Prioridad:** P1 (Alta)
**Versión:** 0.11.0 (Planificado)

### Epic 5: Vocabulario

#### User Story 5.1: Extraer Vocabulario
**Como** usuario
**Quiero** extraer vocabulario de charlas
**Para** construir mi diccionario

**Criterios de Aceptación:**
- [ ] Agente detecta palabras técnicas
- [ ] Palabras se marcan en texto
- [ ] Vocabulario se guarda
- [ ] Vocabulario se puede exportar

**Prioridad:** P2 (Media)
**Versión:** 0.11.0 (Planificado)

#### User Story 5.2: Editar Vocabulario
**Como** usuario
**Quiero** editar mi vocabulario
**Para** corregir errores

**Criterios de Aceptación:**
- [ ] Editor de vocabulario disponible
- [ ] Palabras se pueden añadir/editar/borrar
- [ ] Vocabulario se puede importar
- [ ] Vocabulario se usa en transcripciones

**Prioridad:** P2 (Media)
**Versión:** 0.11.0 (Planificado)

### Epic 6: Actualizaciones

#### User Story 6.1: Ver Actualizaciones
**Como** usuario
**Quiero** saber si hay actualizaciones
**Para** tener la última versión

**Criterios de Aceptación:**
- [ ] App verifica actualizaciones al inicio
- [ ] Notificación si hay actualización
- [ ] Changelog de actualización
- [ ] Botón para actualizar

**Prioridad:** P1 (Alta)
**Versión:** 0.10.0 (En desarrollo - BUG FIX)

#### User Story 6.2: Actualizar App
**Como** usuario
**Quiero** actualizar con un click
**Para** no tener que descargar manualmente

**Criterios de Aceptación:**
- [ ] Descarga automática de actualización
- [ ] Barra de progreso de descarga
- [ ] Instalación silenciosa
- [ ] App se reinicia automáticamente

**Prioridad:** P1 (Alta)
**Versión:** 0.10.0 (En desarrollo - BUG FIX)

---

## 🎯 REQUISITOS NO FUNCIONALES

### RNF1: Performance

| Requisito | Métrica | Actual | Objetivo |
|-----------|---------|--------|----------|
| Tiempo de transcripción | < 10s | ~5s | ✅ | | Tiempo de inicio | < 5s | ~3s | ✅ | | Tamaño de ejecutable | < 100MB | ~80MB | ✅ | | Uso de memoria | < 500MB | ~200MB | ✅ | | Uso de CPU | < 20% | ~10% | ✅ |

### RNF2: Confiabilidad

| Requisito | Métrica | Actual | Objetivo |
|-----------|---------|--------|----------|
| Uptime (sin crashes) | > 99% | ~95% | ⏳ |
| Pérdida de datos | 0% | 0% | ✅ |
| Recuperación de errores | 100% | ~80% | ⏳ |

### RNF3: Usabilidad

| Requisito | Métrica | Actual | Objetivo |
|-----------|---------|--------|----------|
| Tiempo de aprendizaje | < 5 min | ~10 min | ⏳ |
| Satisfacción de usuario | > 4.5/5 | N/A | ⏳ |
| Soporte de help | Completo | ~70% | ⏳ |

### RNF4: Seguridad

| Requisito | Métrica | Actual | Objetivo |
|-----------|---------|--------|----------|
| Encriptación de API keys | Sí | XOR+Base64 | ⏳ |
| Sin telemetría | Sí | ✅ | ✅ |
| Datos locales | Sí | ✅ | ✅ |
| Privacidad | 100% | ✅ | ✅ |

### RNF5: Compatibilidad

| Requisito | Versión | Estado |
|-----------|---------|--------|
| Windows | 10+ | ✅ |
| Windows | 11 | ✅ |
| Python | 3.8+ | ✅ |
| Linux | - | ❌ (v1.0.0) |
| macOS | - | ❌ (v1.0.0) |

---

## 🎯 MAQUETAS Y WIREFRAMES

### Pantalla Principal

```
┌─────────────────────────────────────────────┐
│ Audio2Text v0.9.4              [−][□][×]    │
├─────────────────────────────────────────────┤
│ [Transcripción] [Historial] [Config]        │
├─────────────────────────────────────────────┤
│                                             │
│  Última transcripción:                      │
│  ┌─────────────────────────────────────┐   │
│  │ [Texto de transcripción aquí...]    │   │
│  │                                     │   │
│  │                                     │   │
│  └─────────────────────────────────────┘   │
│  [Copiar] [Editar] [Exportar]               │
│                                             │
│  Hotkey: F12 (toggle)                       │
│                                             │
│  Estado: 🟢 Listo para grabar               │
└─────────────────────────────────────────────┘
```

### Pantalla de Configuración

```
┌─────────────────────────────────────────────┐
│ Configuración                   [−][□][×]    │
├─────────────────────────────────────────────┤
│                                             │
│  API Key de Groq:                           │
│  [gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx]         │
│  [¿Cómo obtener API key?]                   │
│                                             │
│  Hotkey:                                    │
│  [F12 ▼]                                    │
│                                             │
│  Modo de grabación:                         │
│  ○ Toggle  ○ Hold                           │
│                                             │
│  Idioma:                                    │
│  [Español ▼]                                │
│                                             │
│  Guardar audio: [✓]                         │
│  Guardar logs: [✓]                          │
│                                             │
│  [Guardar] [Cancelar]                       │
└─────────────────────────────────────────────┘
```

---

## 🎯 FLUJOS DE USUARIO

### Flujo Principal: Transcribir Audio

```
1. Usuario abre app
2. App verifica API key
3. Si no hay API key:
   3.1. Usuario va a Configuración
   3.2. Usuario ingresa API key
   3.3. Usuario guarda
4. Usuario presiona hotkey (F12)
5. App verifica apps de audio prioritarias
6. Si hay app prioritaria:
   6.1. App muestra advertencia
   6.2. Usuario confirma o cancela
7. App comienza grabación
8. Overlay muestra "🔴 Grabando..."
9. Usuario presiona hotkey nuevamente
10. App detiene grabación
11. App transcribe audio
12. App post-procesa transcripción
13. App muestra resultado
14. App copia al portapapeles (si está activado)
15. App guarda audio y transcripción
```

### Flujo Alternativo: Primera Vez

```
1. Usuario abre app por primera vez
2. App muestra tutorial
3. Usuario sigue pasos del tutorial
4. Usuario termina tutorial
5. App pide API key
6. Usuario ingresa API key
7. App va a pantalla principal
```

---

## 🎯 CRITERIOS DE ÉXITO

### Métricas de Éxito

| Métrica | Objetivo | Actual | Estado |
|---------|----------|--------|--------|
| Precisión de transcripción | ≥ 95% | ~85% | ⏳ |
| Tiempo de transcripción | < 10s | ~5s | ✅ |
| Usuarios activos mensuales | 100 | ~20 | ⏳ |
| Satisfacción de usuarios | ≥ 4.5/5 | N/A | ⏳ |
| Crashes | < 1% | ~5% | ⏳ |
| Retención (día 7) | ≥ 60% | N/A | ⏳ |

### KPIs por Release

**v0.10.0:**
- Precisión de transcripción ≥ 95%
- Tiempo de transcripción < 10s
- Crashes < 2%

**v0.11.0:**
- Usuarios activos = 50
- Satisfacción ≥ 4.0/5
- Retención (día 7) ≥ 50%

**v1.0.0:**
- Usuarios activos = 100
- Satisfacción ≥ 4.5/5
- Retención (día 7) ≥ 60%

---

## 🎯 ROADMAP DE FEATURES

### v0.10.0 (Q2 2026) - Transcripción Mejorada

| Feature | Prioridad | Estado |
|---------|-----------|--------|
| Post-procesamiento de transcripciones | P0 | ⏳ |
| Migración a Flet | P0 | ⏳ |
| Corrección UTF-8 | P0 | ⏳ |
| Reactivar overlay | P0 | ⏳ |
| Arreglar actualizaciones | P1 | ⏳ |
| Gestión de archivos | P1 | ⏳ |

### v0.11.0 (Q3 2026) - Bloques y Vocabulario

| Feature | Prioridad | Estado |
|---------|-----------|--------|
| Sistema de bloques/middles | P1 | ⏳ |
| Agente extractor de vocabulario | P2 | ⏳ |
| Combinaciones de hotkeys | P2 | ⏳ |
| Selector de emojis | P2 | ⏳ |

### v1.0.0 (Q4 2026) - Lanzamiento Mayor

| Feature | Prioridad | Estado |
|---------|-----------|--------|
| Multi-platform (Linux, macOS) | P0 | ⏳ |
| API REST | P1 | ⏳ |
| Modo batch | P1 | ⏳ |
| Interfaz web (opcional) | P2 | ⏳ |
| Tests completos (80%+) | P0 | ⏳ |

---

## 🎯 DEPENDENCIAS

### Dependencias Externas

| Dependencia | Versión | Propósito | Crítica |
|-------------|---------|-----------|---------|
| Groq API | Latest | Transcripción | ✅ |
| Python | 3.8+ | Runtime | ✅ |
| Flet | Latest | UI | ⏳ |
| Whisper Large v3 | - | Modelo | ✅ |

### Dependencias Internas

| Dependencia | Versión | Propósito |
|-------------|---------|-----------|
| backend/transcriber.py | 0.9.4 | Motor de transcripción |
| backend/config_manager.py | 0.9.4 | Configuración |
| backend/file_manager.py | 0.9.4 | Archivos |
| ui/app.py | 0.9.4 | UI principal |

---

## 🎯 RIESGOS DEL PRODUCTO

### Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| API de Groq falle | Media | Alto | Backup (OpenAI, Gemini) |
| Flet no esté listo | Baja | Alto | Quedarse en CustomTkinter |
| Problemas UTF-8 | Alta | Medio | Post-procesamiento |
| Performance issues | Media | Medio | Optimización |

### Riesgos de Usuario

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Usuario no tenga API key | Alta | Medio | Documentación clara |
| Usuario no sepa cómo usar | Media | Medio | Tutorial interactivo |
| Usuario abandone | Media | Alto | Onboarding mejorado |

---

## 🎯 HISTORIAL DE CAMBIOS

| Versión | Fecha | Cambio | Autor |
|---------|-------|--------|-------|
| 1.0.0 | 2026-03-13 | Creación inicial | Claude |

---

**Fin del PRD.**

Este documento es VIVO y debe actualizarse con cada cambio en los requisitos del producto.
