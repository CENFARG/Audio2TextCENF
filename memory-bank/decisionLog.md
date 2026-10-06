# Decision Log

This file records architectural and implementation decisions using a list format.
2025-05-06 20:21:00 - Log of updates made.

*

## Decision

*

## Rationale

*

## Implementation Details

*

## 2026-09-25 — React Native multiplataforma: GO-CONDICIONAL (evaluación team-strategic + team-risk)

**Decisión**: migrar la interfaz a React Native (Expo) es GO-CONDICIONAL — no arranca hasta cerrar Fase 0 (estabilización + spec del protocolo de streaming + decisión BYOK) y pasar un spike kill-or-commit en Android físico.
**Arquitectura**: BYOK (key del usuario en SecureStore, jamás embebida); sin backend propio en fase 1; desktop Python pasa a maintenance mode; proxy FastAPI solo con capa gratuita y demanda.
**Tauri**: ARCHIVADA con stashes documentados — se absorben las ideas de diseño, no el código. Revisitar solo si falla el spike.
**Cafecito**: link pasivo desde el MVP; gating de features solo con ≥100 MAU + retention 4 semanas. Dictado core siempre gratis.
**Detalle completo**: docs/DECISION_RN_MULTIPLATAFORMA.md
