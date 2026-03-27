# 🧠 Protocolo Operativo del Agente CENF (#amBotHs)

Este documento define las reglas de comportamiento, comunicación y desarrollo técnico que el agente debe seguir estrictamente.

---

## 1. Protocolo de Comunicación: "Respuesta Primero" (Answer First)

**Contexto:**
El usuario frecuentemente utiliza prompts híbridos que mezclan preguntas retóricas/estratégicas con directivas de tareas.

**Regla de Oro:**
> **JAMÁS** iniciar la ejecución de tareas sin antes haber respondido exhaustivamente a todas las preguntas planteadas.

**Procedimiento:**
1.  **Detectar:** Escanear el prompt en busca de signos de interrogación o planteos teóricos.
2.  **Priorizar:** La respuesta intelectual tiene prioridad absoluta sobre la acción técnica.
3.  **Responder:** Elaborar la respuesta estratégica/teórica.
4.  **Validar:** Preguntar: *"¿Esta respuesta modifica las tareas que me pediste?"*.
5.  **Ejecutar:** Solo proceder a la acción técnica tras la confirmación implícita o explícita de que la estrategia se mantiene.

**Justificación:**
Minimiza el desperdicio de tokens y retrabajo por cambios de dirección estratégica en mitad de un vuelo.

---

## 2. Protocolo de Desarrollo: Higiene de Entornos (Virtual Env)

**Contexto:**
La instalación de librerías en el entorno global del sistema es una mala práctica crítica.

**Regla de Oro:**
> **SIEMPRE** verificar y activar el entorno virtual (`.venv`) antes de cualquier operación de instalación o ejecución de Python.

**Procedimiento:**
1.  **Verificar Existencia:**
    ```bash
    if Test-Path .venv { ... }
    ```
2.  **Verificar Activación:**
    Antes de correr `pip install`, verificar si el path de python apunta al `.venv`.
3.  **Acción Correctiva:**
    Si no está activo, activarlo explícitamente:
    - Windows: `.venv\Scripts\activate` es para humanos. Para agentes/scripts, usar la ruta directa al ejecutable: `.venv\Scripts\python.exe -m pip ...` o `.venv\Scripts\pip.exe ...`.

**Justificación:**
Garantiza la portabilidad, evita conflictos de dependencias y mantiene limpio el sistema host del usuario.

---

## 3. Filosofía de Diseño PRO: "Interfaz de Slots" (No Ad-ware)

**Contexto:**
La integración de features PRO en la versión Community/Free no debe degradar la UX.

**Regla de Oro:**
> **NO** a los botones deshabilitados ("grisados") que sirvan solo como publicidad. La UI debe ser reactiva a las capacidades (Capabilities-Driven UI).

**Procedimiento:**
1.  **Slots Vacíos:** Diseñar la UI con "huecos" o contenedores invisibles donde irían los componentes PRO.
2.  **Inyección Dinámica:**
    - Si `config.has_pro_license == True` -> Renderizar el botón.
    - Si `config.has_pro_license == False` -> El slot permanece vacío o colapsado (no ocupa espacio).
3.  **Cero Fricción:** El usuario Free debe sentir que tiene un producto completo, no una "demo capada".

**Justificación:**
Respeto al usuario. La conversión a PRO debe ser por *necesidad de potencia* (pull), no por *molestia visual* (push).

---

## 4. Estrategia de Código: Fair Code + Cloud Brain

**Concepto:**
Compatibilidad entre Transparencia (Auditabilidad) y Seguridad (Negocio).

- **Capa 1: Cliente Local (La Puerta)**
  - Licencia: Apache 2.0 / Fair Code.
  - Rol: Interfaz, I/O, Orquestación básica.
  - Código: Visible, Auditable.
- **Capa 2: Agente Remoto (El Cerebro)**
  - Licencia: Propietaria / SaaS.
  - Rol: Lógica de negocio pesada, #Grama, Integración con Grafo.
  - Código: Oculto en servidor.
  - Acceso: Via API Key.

**Nota:** Este modelo permite auditar "qué se envía" (privacidad) sin exponer "cómo se procesa" (IP).
