# Audio2Text - Memoria Central (Cloud Memory)

> **Última actualización:** 2026-03-20
> **Versión:** 0.10.0 (CustomTkinter)
> **Estado:** Producción estable

---

## 📋 ÍNDICE

1. [Decisiones Críticas](#decisiones-críticas)
2. [Lecciones Aprendidas](#lecciones-aprendidas)
3. [Cambios Recientes](#cambios-recientes)
4. [Próximos Pasos](#próximos-pasos)
5. [Referencias Rápidas](#referencias-rápidas)

---

## 🔴 DECISIONES CRÍTICAS

### Decisión #1: REVERTIR migración a Flet (2026-03-19)

**Tipo:** Arquitectura / Reversión

**Contexto:**
Se intentó migrar la UI de CustomTkinter a Flet para modernizar la interfaz.

**Problemas encontrados:**
1. API de Flet 0.82.2 inconsistente con documentación
2. Errores constantes: `TypeError: 'module' object is not callable` con ft.padding
3. Resultado estético pobre: "todo muy separado, no tiene diseño estético"
4. Demasiadas iteraciones para lograr paridad visual
5. Usuario frustrado: "se sorprende que sea tan complejo pasar de una interfaz a la otra"

**Decisión:**
VOLVER a CustomTkinter v0.10.0 y ABANDONAR migración a Flet temporalmente.

**Justificación:**
- CustomTkinter funciona perfectamente
- Todas las features operativas (transcripción, hotkey F9, overlay, actualizaciones, UTF-8, post-procesamiento)
- Diseño probado y estético
- Sin errores de API

**Commit:**
```
0d9877a revert: Volver a CustomTkinter v0.10.0 estable
```

**Impacto:**
- Código ui_flet/ se mantiene como referencia futura
- CustomTkinter es la solución pragmática actual
- Flet podría reconsiderarse para cross-platform en el futuro

**Tags:** architecture, decision, flet, customtkinter, revert, ui-framework

---

### Decisión #2: CustomTkinter vs Rust/Frameworks futuros (2026-03-19)

**Tipo:** Estrategia de tecnología

**Contexto:**
Usuario sugirió: "Pasémoslo a Rust no sé pero alguna interfaz que sea sostenible de calidad"

**Análisis:**
- Rust + interfaz nativa sería desarrollo desde cero
- Requiere rewrite completo de backend (Python → Rust)
- Time-to-market muy largo
- CustomTkinter funciona bien para el caso de uso actual

**Decisión:**
MANTENER CustomTkinter por ahora. Rust/Frameworks futuros solo si:
1. Requerimiento real de cross-platform (Linux/macOS)
2. Problemas de performance críticos
3. CustomTkinter depreca o deja de mantenerse

**Tags:** strategy, rust, future, customtkinter, technology-stack

---

## 💡 LECCIONES APRENDIDAS

### Lección #1: No refactorizar UI frameworks sin razón crítica

**Fecha:** 2026-03-19

**Qué pasó:**
Intentamos migrar de CustomTkinter a Flet sin un requerimiento crítico.

**Lección:**
- Si funciona, no lo arregles
- UI frameworks tienen APIs muy diferentes
- La paridad visual toma más tiempo que esperado
- Migraciones de UI son HIGH RISK, LOW VALUE si no hay business case

**Aplicar en futuro:**
- Solo migrar UI si hay problema real (performance, deprecación, cross-platform crítico)
- Hacer POC completo antes de commit
- Evaluar si vale la pena el esfuerzo

**Tags:** lesson, ui-migration, framework, risk-assessment

---

### Lección #2: Git workflow con ramas por feature

**Fecha:** 2026-03-20

**Instrucción del usuario:**
"generar ramas específicas para cada una de estas mejoras"

**Workflow a seguir:**
```bash
# Para cada feature del roadmap:
git checkout -b feature/nombre-feature
# Desarrollar
git commit -m "feat: descripción detallada"
# Push y PR si es necesario
git checkout main
```

**Beneficios:**
- Rollback fácil por feature
- Historial limpio
- Code review por feature
- Deploy selectivo

**Tags:** lesson, git-workflow, branches, feature-branches

---

### Lección #3: Trazabilidad completa en commits

**Fecha:** 2026-03-20

**Instrucción del usuario:**
"Mantener trazabilidad y rollback completo hacia atrás"

**Formato de commit requerido:**
```bash
git commit -m "tipo(scope): descripción corta

- Detalle 1
- Detalle 2

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**Tipos:**
- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `revert:` reversión de cambio
- `docs:` documentación
- `refactor:` refactorización
- `perf:` mejora de performance

**Tags:** lesson, git, commits, trazabilidad, rollback

---

## 📝 CAMBIOS RECIENTES

### 2026-03-20: Desarrollo v0.11.0 - Sistema de Bloques (EN PROGRESO)

**Rama:** feature/blocks-system
**Estado:** Activo

**Implementaciones:**
1. **Arquitectura de bloques:**
   - BaseBlock: Clase base abstracta
   - BlockType: PRE/POST/BOTH
   - ProcessingStage: RAW_AUDIO/TRANSCRIBED/PROCESSED
   - BlockResult: Resultado estructurado

2. **BlockManager:**
   - Registro y gestión de bloques
   - Ejecución secuencial de pipeline
   - Manejo robusto de errores
   - Estadísticas de procesamiento

3. **Bloques implementados:**
   - TaskExtractorBlock: Extrae tareas/action items
   - SummaryBlock: Genera resúmenes ejecutivos
   - KeywordExtractorBlock: Extrae palabras clave

**Características:**
- Activación/desactivación dinámica de bloques
- Configuración por bloque
- Integración con vocabulario técnico existente
- Clasificación de keywords
- Detección de entidades nombradas

**Documentación:**
- backend/blocks/README.md: Guía completa
- Ejemplos de uso
- Plantilla para crear bloques custom

**Próximos pasos:**
- [ ] Integrar bloques con transcriber.py
- [ ] Testing unitario de bloques
- [ ] UI para configurar bloques
- [ ] Agente extractor de vocabulario

---

### 2026-03-19: Reversión a CustomTkinter

**Cambios:**
- Revertido main.py a versión CustomTkinter (commit dd20430)
- Corregido requirements.txt (eliminado pywin32-tools inexistente)
- Instaladas dependencias correctamente

**Resultado:**
- Aplicación CustomTkinter funcionando correctamente
- v0.10.0 estable con todas las features

**Commits:**
- `0d9877a` revert: Volver a CustomTkinter v0.10.0 estable

---

### 2026-03-19: Intento de migración a Flet (ABANDONADO)

**Cambios (revertidos):**
- Múltiples commits intentando migrar UI a Flet
- Ajustes de padding, tabs, layout
- Corrección de APIs de Flet 0.82.2

**Problemas:**
- Demasiados errores de sintaxis
- Resultado estético pobre
- API inconsistente

**Commits (revertidos):**
- `475dc17` fix(flet): Correct padding API syntax
- `67626e9` feat(flet): Improve Updates tab
- `dbb3400` fix(flet): Correct info_template.html path
- `8b9c83d` fix(flet): Adjust padding
- `a226b9f` feat(flet): Implement dynamic transcription panel
- `28cf6f6` fix(flet): Adjust window size
- `ccdb3b1` fix(flet): Increase tab button width
- `cddfae0` feat(flet): Implement hotkey recording dialog
- `f08fe0c` feat(flet): Implement horizontal tabs
- `a3349df` docs: Add comprehensive UI comparison

---

## 🎯 PRÓXIMOS PASOS

### Roadmap v0.11.0 - Bloques y Vocabulario

**Prioridad:** MEDIA
**Estimado:** 1-2 semanas
**Estado:** EN PROGRESO

#### ✅ 1. Sistema de bloques/middles - COMPLETADO
- [x] Diseñar arquitectura de bloques
- [x] Implementar bloque "Extractor de Tareas"
- [x] Implementar bloque "Summary" (resúmenes ejecutivos)
- [x] Implementar bloque "KeywordExtractor" (palabras clave)
- [x] Documentar cómo crear bloques custom (backend/blocks/README.md)
- [x] BlockManager para pipeline de ejecución
- [ ] Testing de bloques

**Commits:**
- `efa35a2` feat(blocks): Implementar sistema de bloques/middles v0.11.0
- `97b4c79` feat(blocks): Implementar SummaryBlock y KeywordExtractorBlock

#### 🔄 2. Agente extractor de vocabulario
- [ ] Integrar con transcripciones
- [ ] Detectar palabras técnicas automáticamente
- [ ] Marcar palabras particulares
- [ ] Permitir corrección manual
- [ ] Guardar en backend/vocabulary/custom.json

#### ⏳ 3. Combinaciones de hotkeys
- [ ] Soportar Ctrl+F1, Alt+F2, etc.
- [ ] UI para configurar combinaciones
- [ ] Validación de combinaciones únicas

---

### v0.12.0 - Extras

**Prioridad:** BAJA

- [ ] Logo renovado
- [ ] Selector de emojis
- [ ] Skills de Audio2Text
- [ ] Agente Audio2Text

---

### v1.0.0 - Lanzamiento Mayor

**Prioridad:** FUTURO

- [ ] Versión para Linux y macOS
- [ ] API REST para integración
- [ ] Modo batch para múltiples archivos
- [ ] Interfaz web opcional
- [ ] Tests automatizados completos

---

## 🔗 REFERENCIAS RÁPIDAS

### Documentación del Proyecto

- **CLAUDE.md:** `CLAUDE.md` - Memoria completa del proyecto
- **Decisiones:** `memory-bank/decisionLog.md`
- **Progreso:** `memory-bank/progress.md`
- **Patrones:** `memory-bank/systemPatterns.md`
- **Contexto Técnico:** `memory-bank/techContext.md`
- **Contexto Activo:** `memory-bank/activeContext.md`
- **Changelog:** `docs/guides/CHANGELOG.md`

### Sistema de Desarrollo CENF

- **Ubicación:** `C:\Dropbox\DOC.RECA\06-Software\equipo-programacion-cenf\`
- **Guía de Inicio:** `GUIA-INICIO.md`
- **README:** `README.md`

### Engram (Sistema de Memoria)

- **Ubicación:** `C:\Dropbox\DOC.RECA\06-Software\engram`
- **Docs:** `engram/DOCS.md`
- **Data dir:** `.engram/memory/` (este proyecto)

### Repositorio

- **GitHub:** https://github.com/CENFARG/Audio2TextCENF
- **Issues:** https://github.com/CENFARG/Audio2Text/issues

---

## 📊 ESTADO DEL PROYECTO

**Versión actual:** 0.10.0
**Rama actual:** feature/utf8-fix (después de revert a CustomTkinter)
**Estado:** ✅ Producción estable

**Features principales:**
- ✅ Transcripción con Groq API (Whisper Large v3)
- ✅ Hotkey F9 global
- ✅ Overlay de grabación
- ✅ Actualizaciones automáticas
- ✅ Validación UTF-8
- ✅ Post-procesamiento de texto
- ✅ Sistema de vocabulario técnico
- ✅ Límite de archivos (100) y limpieza automática
- ✅ UI CustomTkinter estable

**Limitaciones actuales:**
- Windows only (CustomTkinter)
- Sin tests automatizados
- Dependencias PRO (agno, openai) opcionales

---

**Fin del documento de memoria central.**

**Actualizado por:** Claude Sonnet 4.6
**Fecha de actualización:** 2026-03-20
**Versión:** 1.0
