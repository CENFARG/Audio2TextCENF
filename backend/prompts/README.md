# backend/prompts — Prompts de sistema canónicos y versionados

Artefactos de prompt de sistema versionados, separados del código. Cada archivo
`*_vN.md` es la fuente canónica de un pass de LLM; el código solo lo carga.

## Archivos

| Archivo | id | Versión | Consumidor |
|---|---|---|---|
| `prompter_system_v1.md` | `prompter_system` | 1.0.0 | `backend/prompter_gate.py` → `build_prompter_messages` (pass Prompter del Supervisor) |

## Contrato de versionado (SemVer)

- **MAJOR** (v1→v2): cambia el contrato observable — formato de salida, idioma,
  invariantes (p. ej. "no inventar"), o los marcadores de sección
  (`BORRADOR A REESTRUCTURAR:`, `BLOQUES DE CONTEXTO…`, `NOTA DESTINO:`).
  Requiere re-evaluar contra el golden set antes de mergear.
- **MINOR**: aclaraciones aditivas que no cambian las salidas esperadas
  (nuevas reglas que solo acotan casos borde, ejemplos ilustrativos).
- **PATCH**: redacción, typos, formato del propio archivo.

## Promoción v1 → v2

1. Crear `prompter_system_v2.md` como archivo NUEVO (v1 queda congelado como
   histórico; nunca editar in-place una versión publicada).
2. Cambiar el loader en `build_prompter_messages` para apuntar a v2
   (nombre de archivo o campo `active` en la tabla de arriba).
3. Re-evaluar: correr el golden set de borradores (es/en, 1–8+ puntos, con y
   sin bloques/nota) y verificar los `quality_criteria` del frontmatter.
4. Aprobación: **team-prompting** (autor del artefacto) + owner del repo
   (merge a la línea activa). Nadie cambia un prompt canónico sin estos dos.
5. Actualizar la tabla de archivos de este README en el mismo commit.

## Nota de integración (desarrollo)

- El frontmatter YAML es metadatos del artefacto: **nunca se envía al modelo**.
  El loader debe separar el bloque `--- … ---` inicial y usar solo el cuerpo.
- Los marcadores de sección del mensaje de usuario los produce
  `build_prompter_messages` y están acoplados a las secciones del prompt:
  cambiarlos es bump MINOR/MAJOR coordinado (prompt + código en el mismo PR).
- PyInstaller: agregar `--add-data backend/prompts;backend/prompts` en
  `scripts/build.py` (y variantes por cliente) para que el archivo viaje en los
  builds empaquetados. Alternativa sin empaquetado: mantener la constante
  actual como fallback si el archivo no existe en runtime.
