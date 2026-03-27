# #Grama: La Evolución del Contexto Agéntico
> *De "Grabadora" a "Sistema Operativo de Contexto"*

## 1. Visión Estratégica
**#Grama** no es solo una transcripción de audio; es una **plataforma de gestión de contexto y prompts**. Su misión es conectar la intención humana (voz/texto) con la ejecución agéntica precisa, utilizando una estructura modular que permite compartir y mejorar "recetas" de inteligencia (Workflows/Prompts).

## 2. Los 3 Pilares de Grama

### A. El Oído (Input Layer - Community)
*   **Lo que es hoy:** Audio2Text CENF.
*   **Función:** Captura de alta fidelidad, transcripción (Whisper), y limpieza básica.
*   **Licencia:** Apache 2.0 (Open Source).
*   **Filosofía:** Rápido, local, privado.

### B. El Cerebro (Graph Layer - PRO/SaaS)
*   **Frontend (La Cara):** **TypeScript + React**.
*   **Backend (El Motor):** **Python (FastAPI)**.
*   **El Puente (Rust/Tauri):** **Rust** se usará únicamente como un "pegamento" invisible de configuración para gestionar la ventana y lanzar el proceso de Python. **No necesitarás escribir ni aprender Rust**; yo (tu Agente) me encargaré de la configuración del `sidecar` de Tauri. El 99% de tu interacción será con Python y TypeScript.
    *   *Responsabilidad:* Gestión de Ventana, Hotkeys Globales, Lanzamiento de Python.
*   **Orquestador:** El agente "Project Manager" que decide qué workflow ejecutar basándose en el input.

### C. La Comunidad (Share Layer)
*   **Marketplace de Contexto:** Usuarios comparten "mejores prácticas" (ej: Prompt para Resumen Legal, Workflow para Diagnóstico Médico).
*   **Modelo de Negocio:** Freemium.
    *   *Free:* Uso de prompts locales y transcripción ilimitada.
    *   *Pro:* Sync en la nube, acceso al Grafo Global de CENF, orquestación avanzada.

## 3. Arquitectura Modular (JSON-Driven)
La UI (`app.py`) no debe tener pestañas "hardcoded". Debe renderizarse dinámicamente basándose en un `grammar_config.json`:
```json
{
  "modules": {
    "transcriber": { "enabled": true, "ui": "panel_left" },
    "graph_visualizer": { "enabled": false, "ui": "tab_graph" }, // Activo solo en PRO
    "prompt_editor": { "enabled": true, "ui": "tab_editor" }
  }
}
```
Esto permite que el mismo ejecutable sirva para usuarios Community (solo ven transcripción) y usuarios Enterprise (ven grafos y editores), activado por licencia.

## 4. El "Orquestador de Workflows" (Meta-Agente)
El usuario requiere un sistema que no solo ejecute, sino que **decida**.
*   **Input:** "Tengo una idea para el proyecto de Contreras pero estoy en el de Pampa."
*   **Orquestador:**
    1.  Detecta intención: "Guardar Idea" + "Contexto Cruzado".
    2.  Selecciona Workflow: `/idea-processor` (vs `/task-creator`).
    3.  Ejecuta: Guarda el nodo en el Grafo, etiqueta `#Contreras` y `#Pampa`, y avisa al PM.

## 5. Roadmap de Transición (Audio2Text -> Grama)
1.  **Fase 1 (Limpieza):** Release Audio2Text v0.9.4 (Estado actual).
2.  **Fase 2 (Cimientos):** Renombrar repo a `grama-core`. Separar lógica de UI.
3.  **Fase 3 (Conexión):** Integrar `knowledge_graph_v2.json` como backend nativo de la app (no solo del agente).
4.  **Fase 4 (Expansión):** Lanzar "Grama Studio" (Editor de Prompts/Workflows).
