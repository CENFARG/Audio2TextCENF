# 01. Project Charter - Audio2Text

> **Versión:** 1.0.0
> **Fecha:** 2026-03-13
> **Estado:** Activo
> **Última actualización:** 2026-03-13

---

## 📋 IDENTIDAD DEL PROYECTO

### Nombre
**Audio2Text CENF**

### Versión Actual
**0.9.4**

### Sponsor
**CENF (Centro de Excelencia en Negocios del Futuro)**

### Team Lead
**Equipo de Desarrollo CENF**

---

## 🎯 PROPÓSITO (POR QUÉ EXISTE)

### Misión
Desarrollar una aplicación profesional de transcripción de audio en tiempo real que utilice inteligencia artificial para convertir voz a texto de manera rápida, precisa y segura.

### Visión
Ser la herramienta líder en transcripción de audio para profesionales y empresas en Latinoamérica, reconocida por su precisión, facilidad de uso y calidad enterprise.

### Problema que Resuelve
Los profesionales necesitan transcribir audio a texto de manera rápida y precisa, pero las opciones actuales son:
- Costosas (suscripciones caras)
- Complicadas de usar
- Imprécisas con español rioplatense
- Sin soporte para vocabulario técnico

### Solución
Una aplicación que:
- Transcribe en tiempo real con IA
- Soporta español e inglés
- Permite vocabulario técnico personalizado
- Es fácil de usar con hotkeys globales
- Es asequible y sin suscripciones

---

## 🎯 OBJETIVOS DEL PROYECTO

### Objetivos Principales (SMART)

#### 1. Calidad de Transcripción
- **Métrica:** Precisión del 95%+ en español rioplatense
- **Plazo:** v0.10.0 (Q2 2026)
- **Medición:** Tests de precisión con audio de muestra

#### 2. Experiencia de Usuario
- **Métrica:** Tiempo de transcripción < 10 segundos
- **Plazo:** v0.10.0 (Q2 2026)
- **Medición:** Benchmarks de rendimiento

#### 3. Adopción
- **Métrica:** 100 usuarios activos mensuales
- **Plazo:** v1.0.0 (Q4 2026)
- **Medición:** Analytics de uso

#### 4. Estabilidad
- **Métrica:** < 1% de crashes en uso normal
- **Plazo:** v0.10.0 (Q2 2026)
- **Medición:** Logs de errores

### Objetivos Secundarios

- Soportar múltiples idiomas (v0.11.0)
- Exportar a múltiples formatos (v0.11.0)
- Versión para Linux y macOS (v1.0.0)
- API REST para integración (v1.0.0)

---

## 🎯 ALCANCE (IN SCOPE)

### Funcionalidades Incluidas

#### v0.9.4 (Actual)
- ✅ Transcripción de audio en tiempo real
- ✅ Soporte para español e inglés
- ✅ Hotkeys globales configurables
- ✅ Sistema de actualizaciones automáticas
- ✅ Gestión de archivos de audio y transcripciones
- ✅ Interfaz gráfica moderna
- ✅ Soporte multiidioma (ES/EN)
- ✅ System tray integration
- ✅ Variantes personalizadas por cliente

#### v0.10.0 (Planificado)
- ⏳ Post-procesamiento de transcripciones
- ⏳ Migración a Flet
- ⏳ Corrección de problemas UTF-8
- ⏳ Reactivación de overlay
- ⏳ Arreglo de actualizaciones automáticas
- ⏳ Gestión de archivos y limpieza

#### v0.11.0 (Futuro)
- ⏳ Sistema de bloques/middles
- ⏳ Agente extractor de vocabulario
- ⏳ Combinaciones de hotkeys

### Variantes del Producto
1. **GENERAL** (CENF)
2. **CONTRERAS** (Contreras Hnos)
3. **CUTIGNOLA**

---

## 🚫 ALCANCE (OUT OF SCOPE)

### Funcionalidades NO Incluidas

#### v1.0.0
- ❌ Transcripción de video (solo audio)
- ❌ Reconocimiento de múltiples hablantes
- ❌ Traducción en tiempo real
- ❌ Edición de audio
- ❌ Streaming de audio en vivo

#### v1.0.0+
- ❌ Interfaz web (solo desktop)
- ❌ Versión mobile
- ❌ Servidor on-premise

### Limitaciones Conocidas
- Solo funciona en Windows (hasta v1.0.0)
- Requiere conexión a internet (API de Groq)
- No soporta audio en tiempo real desde otras apps

---

## 👥 STAKEHOLDERS

### Stakeholders Primarios

| Rol | Nombre | Responsabilidad | Contacto |
|-----|--------|-----------------|----------|
| Sponsor | CENF | Financiación y dirección | cenf.arg@gmail.com |
| Product Owner | Pablo | Definición de requisitos | - |
| Tech Lead | Gonza | Arquitectura y desarrollo | - |
| Usuario Final | Profesionales | Testing y feedback | GitHub Issues |

### Stakeholders Secundarios

| Rol | Nombre | Responsabilidad |
|-----|--------|-----------------|
| Cliente CONTRERAS | Contreras Hnos | Requisitos específicos |
| Cliente CUTIGNOLA | Cutignola | Requisitos específicos |
| Comunidad | Open Source | Contribuciones y feedback |

---

## 🎯 ÉXITO DEL PROYECTO

### Criterios de Éxito

#### Técnicos
- ✅ Precisión de transcripción ≥ 95%
- ✅ Tiempo de transcripción < 10 segundos
- ✅ Estabilidad (crashes < 1%)
- ✅ Cobertura de tests ≥ 80%

#### de Negocio
- ✅ 100 usuarios activos mensuales
- ✅ Satisfacción de usuarios ≥ 4.5/5
- ✅ Retención de usuarios ≥ 60%
- ✅ Churn rate ≤ 10%

#### de Producto
- ✅ Lanzamiento de v1.0.0 en Q4 2026
- ✅ 3 variantes del producto
- ✅ Documentación completa
- ✅ Roadmap claro

### KPIs (Key Performance Indicators)

| KPI | Objetivo | Actual | Tendencia |
|-----|----------|--------|-----------|
| Precisión de transcripción | ≥ 95% | ~85% | ↗️ |
| Tiempo de transcripción | < 10s | ~5s | ✅ |
| Usuarios activos mensuales | 100 | ~20 | ↗️ |
| Satisfacción de usuarios | ≥ 4.5/5 | N/A | - |
| Crashes | < 1% | ~5% | ↘️ |

---

## 🚀 HITOS MILESTONES

### Milestone 1: v0.9.4 (Completado)
- ✅ Release inicial
- ✅ 3 variantes del producto
- ✅ Sistema de build automatizado

### Milestone 2: v0.10.0 (Q2 2026)
- ⏳ Post-procesamiento de transcripciones
- ⏳ Migración a Flet
- ⏳ Corrección UTF-8
- ⏳ Arreglo de actualizaciones

### Milestone 3: v0.11.0 (Q3 2026)
- ⏳ Sistema de bloques/middles
- ⏳ Agente extractor de vocabulario
- ⏳ Combinaciones de hotkeys

### Milestone 4: v1.0.0 (Q4 2026)
- ⏳ Versión para Linux y macOS
- ⏳ API REST
- ⏳ Modo batch
- ⏳ 100 usuarios activos

---

## 🎯 RESTRICCIONES Y LIMITACIONES

### Restricciones Técnicas
- Python 3.8+ required
- Windows-only (hasta v1.0.0)
- Requiere conexión a internet
- API de Groq tiene límites de速率

### Restricciones de Negocio
- Presupuesto limitado
- Equipo pequeño
- Tiempo de desarrollo limitado
- Sin financiación externa

### Restricciones Legales
- Licencia Apache 2.0
- GDPR compliance si se lanza en Europa
- Privacy policy requerida

---

## 🎯 SUPUESTOS (ASSUMPTIONS)

### Supuestos Técnicos
- ✅ API de Groq será estable
- ✅ Whisper Large v3 mantendrá calidad
- ✅ Flet será estable para producción
- ✅ Python seguirá siendo soportado

### Supuestos de Negocio
- ✅ Demanda de transcripción de audio crecerá
- ✅ Usuarios están dispuestos a usar API keys
- ✅ Competencia no se moverá rápido
- ✅ Open Source será un ventaja

---

## 🎯 RIESGOS

### Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| API de Groq falle | Media | Alto | Tener backup (OpenAI, Gemini) |
| Flet no esté listo | Baja | Alto | Quedarse en CustomTkinter |
| Problemas UTF-8 | Alta | Medio | Post-procesamiento |
| Performance issues | Media | Medio | Optimización |

### Riesgos de Negocio

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Competencia free | Alta | Alto | Diferenciación por vocabulario |
| Usuarios no usen API keys | Media | Alto | Documentación clara |
| Churn rate alto | Media | Medio | Mejorar onboarding |
| Sin monetización | Alta | Bajo | Versión PRO futura |

---

## 🎯 PRESUPUESTO

### Costos de Desarrollo

| Item | Costo Mensual | Costo Total |
|------|--------------|-------------|
| Desarrollo (equipo) | $0 (voluntario) | $0 |
| API de Groq | $0 (gratis) | $0 |
| Hosting (GitHub) | $0 (gratis) | $0 |
| Code Signing (opcional) | $100-500 (único) | $100-500 |
| **Total** | **$0** | **$100-500** |

### Costos Operacionales

| Item | Costo Mensual |
|------|--------------|
| API de Groq (producción) | $0-50 (depende uso) |
| Hosting (futuro) | $0-20 |
| **Total** | **$0-70** |

---

## 🎯 APROBACIÓN

### Sponsor Approval
- **Nombre:** CENF
- **Fecha:** 2026-03-13
- **Firma:** _Aprobado_

### Tech Lead Approval
- **Nombre:** Gonza
- **Fecha:** 2026-03-13
- **Firma:** _Pendiente_

---

## 🎯 HISTORIAL DE CAMBIOS

| Versión | Fecha | Cambio | Autor |
|---------|-------|--------|-------|
| 1.0.0 | 2026-03-13 | Creación inicial | Claude |

---

**Fin del Project Charter.**

Este documento es VIVO y debe actualizarse con cada cambio significativo en el proyecto.
