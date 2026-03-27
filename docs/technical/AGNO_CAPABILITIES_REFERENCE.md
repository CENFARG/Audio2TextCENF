# 🔧 Capacidades Configurables de Agno - Referencia Completa

## 📋 Resumen

Este documento lista **TODAS** las capacidades configurables del framework Agno que están disponibles para Audio2Text PRO, aunque no las definamos explícitamente en el JSON de configuración.

**Fuente:** Documentación oficial de Agno (https://docs.agno.com)

---

## 🤖 Parámetros del Agent

### 1. Modelo y Proveedor

```python
# Configurables en JSON
model: Optional[Union[Model, str]] = None  # "provider:model_id"
reasoning_model: Optional[Union[Model, str]] = None
parser_model: Optional[Union[Model, str]] = None
output_model: Optional[Union[Model, str]] = None
```

**Disponible pero no en JSON:**
- Cambio dinámico de modelo durante ejecución
- Modelos diferentes para parsing y output
- Reasoning models separados

---

### 2. Identidad y Metadata

```python
# Configurables en JSON
id: Optional[str] = None
name: Optional[str] = None
description: Optional[str] = None
role: Optional[str] = None

# Disponible automáticamente
user_id: Optional[str] = None
session_id: Optional[str] = None
metadata: Optional[Dict[str, Any]] = None
```

**Disponible pero no en JSON:**
- Tracking automático de user_id
- Metadata extensible para cualquier dato
- Roles personalizados

---

### 3. Sesiones y Estado

```python
# Configurables en JSON
session_state: Optional[Dict[str, Any]] = None
add_session_state_to_context: bool = False
enable_agentic_state: bool = False

# Disponible automáticamente
cache_session: bool = False
search_session_history: Optional[bool] = False
num_history_sessions: Optional[int] = None
overwrite_db_session_state: bool = False
```

**Disponible pero no en JSON:**
- **Estado persistente** entre runs
- **Búsqueda en historial** de sesiones
- **Cache de sesiones** para performance
- **Estado agéntico** (el agente decide qué guardar)

---

### 4. Memoria (Memory)

```python
# Configurables en JSON
memory_manager: Optional[MemoryManager] = None
enable_agentic_memory: bool = False
enable_user_memories: bool = False
add_memories_to_context: Optional[bool] = None

# Disponible automáticamente
enable_session_summaries: bool = False
add_session_summary_to_context: Optional[bool] = None
session_summary_manager: Optional[SessionSummaryManager] = None
```

**Disponible pero no en JSON:**
- **Memoria de usuario** (recordar preferencias)
- **Resúmenes de sesión** automáticos
- **Memoria agéntica** (el agente decide qué recordar)
- **Managers personalizados** de memoria

---

### 5. Conocimiento (Knowledge)

```python
# Configurables en JSON
knowledge: Optional[Knowledge] = None
knowledge_filters: Optional[Dict[str, Any]] = None
search_knowledge: bool = True
update_knowledge: bool = False

# Disponible automáticamente
enable_agentic_knowledge_filters: Optional[bool] = None
add_knowledge_to_context: bool = False
knowledge_retriever: Optional[Callable] = None
references_format: Literal["json", "yaml"] = "json"
```

**Disponible pero no en JSON:**
- **Filtros agénticos** (el agente decide qué buscar)
- **Retriever personalizado** (custom search logic)
- **Formato de referencias** (JSON o YAML)
- **Actualización de knowledge** en tiempo real

---

### 6. Historial (Chat History)

```python
# Configurables en JSON
add_history_to_context: bool = False
num_history_runs: Optional[int] = None
num_history_messages: Optional[int] = None

# Disponible automáticamente
read_chat_history: bool = False
read_tool_call_history: bool = False
max_tool_calls_from_history: Optional[int] = None
store_history_messages: bool = True
store_tool_messages: bool = True
```

**Disponible pero no en JSON:**
- **Historial de tool calls** (qué herramientas se usaron)
- **Límite de tool calls** del historial
- **Control de almacenamiento** (qué se guarda)

---

### 7. Compresión de Contexto

```python
# Configurables en JSON
compress_tool_results: bool = False
compression_manager: Optional[CompressionManager] = None
```

**Disponible pero no en JSON:**
- **Compresión automática** de resultados largos
- **Manager personalizado** de compresión
- **Ahorro de tokens** en contexto

---

### 8. Herramientas (Tools)

```python
# Configurables en JSON
tools: Optional[List[Union[Toolkit, Callable, Function, Dict]]] = None
tool_call_limit: Optional[int] = None
tool_choice: Optional[Union[str, Dict[str, Any]]] = None

# Disponible automáticamente
tool_hooks: Optional[List[Callable]] = None
```

**Disponible pero no en JSON:**
- **Tool hooks** (callbacks antes/después de tool)
- **Tool choice** (forzar uso de tool específica)
- **Límite de llamadas** por run

---

### 9. Hooks y Guardrails

```python
# Configurables en JSON
pre_hooks: Optional[List[Union[Callable, BaseGuardrail, BaseEval]]] = None
post_hooks: Optional[List[Union[Callable, BaseGuardrail, BaseEval]]] = None

# Disponible automáticamente
# - PIIDetectionGuardrail
# - PromptInjectionGuardrail
# - OpenAIModerationGuardrail
# - Custom guardrails
```

**Disponible pero no en JSON:**
- **Pre-hooks** (validación antes de run)
- **Post-hooks** (procesamiento después de run)
- **Evals** (evaluación de calidad)
- **Background execution** de hooks

---

### 10. Razonamiento (Reasoning)

```python
# Configurables en JSON
reasoning: bool = False
reasoning_model: Optional[Union[Model, str]] = None
reasoning_agent: Optional[Agent] = None

# Disponible automáticamente
reasoning_min_steps: int = 1
reasoning_max_steps: int = 10
```

**Disponible pero no en JSON:**
- **Reasoning mode** (chain-of-thought)
- **Modelo separado** para razonamiento
- **Agente de razonamiento** personalizado
- **Control de pasos** (min/max)

---

### 11. Contexto y Prompts

```python
# Configurables en JSON
system_message: Optional[Union[str, Callable, Message]] = None
instructions: Optional[Union[str, List[str], Callable]] = None
introduction: str = None
expected_output: Optional[str] = None
additional_context: Optional[str] = None

# Disponible automáticamente
build_context: bool = True
build_user_context: bool = True
resolve_in_context: bool = True
add_name_to_context: bool = False
add_datetime_to_context: bool = False
add_location_to_context: bool = False
timezone_identifier: Optional[str] = None
```

**Disponible pero no en JSON:**
- **System message dinámico** (callable)
- **Instrucciones dinámicas** (callable)
- **Contexto de usuario** automático
- **Fecha/hora** en contexto
- **Ubicación** en contexto (con timezone)

---

### 12. Input/Output

```python
# Configurables en JSON
input_schema: Optional[Type[BaseModel]] = None
output_schema: Optional[Union[Type[BaseModel], Dict[str, Any]]] = None
markdown: bool = False

# Disponible automáticamente
additional_input: Optional[List[Union[str, Dict, BaseModel, Message]]] = None
user_message_role: str = "user"
system_message_role: str = "system"
parse_response: bool = True
structured_outputs: Optional[bool] = None
use_json_mode: bool = False
save_response_to_file: Optional[str] = None
```

**Disponible pero no en JSON:**
- **Input schema** (validación Pydantic)
- **Output schema** (structured outputs)
- **JSON mode** (forzar JSON)
- **Guardar respuesta** a archivo
- **Inputs adicionales** (imágenes, etc.)

---

### 13. Streaming y Eventos

```python
# Configurables en JSON
stream: Optional[bool] = None
stream_events: bool = False

# Disponible automáticamente
store_events: bool = False
events_to_skip: Optional[List[RunEvent]] = None
```

**Disponible pero no en JSON:**
- **Streaming** de respuestas
- **Event streaming** (progreso en tiempo real)
- **Almacenamiento de eventos**
- **Filtrado de eventos**

---

### 14. Multimodal

```python
# Configurables en JSON
send_media_to_model: bool = True
store_media: bool = True
```

**Disponible pero no en JSON:**
- **Soporte de imágenes** automático
- **Soporte de audio** automático
- **Soporte de video** automático
- **Almacenamiento de media**

---

### 15. Reintentos y Error Handling

```python
# Configurables en JSON
retries: int = 0
delay_between_retries: int = 1
exponential_backoff: bool = False
```

**Disponible pero no en JSON:**
- **Reintentos automáticos** en caso de error
- **Backoff exponencial**
- **Delay configurable**

---

### 16. Base de Datos

```python
# Configurables en JSON
db: Optional[BaseDb] = None

# Disponible automáticamente
# - PostgresDb
# - SQLiteDb
# - MySQLDb
# - DynamoDb
# - etc.
```

**Disponible pero no en JSON:**
- **Persistencia automática** de sesiones
- **Múltiples backends** de DB
- **Tracking de métricas**
- **Almacenamiento de runs**

---

### 17. Dependencias (Dependency Injection)

```python
# Configurables en JSON
dependencies: Optional[Dict[str, Any]] = None
add_dependencies_to_context: bool = False
```

**Disponible pero no en JSON:**
- **Inyección de dependencias** (servicios, configs, etc.)
- **Acceso desde tools**
- **Contexto compartido**

---

### 18. Debug y Telemetría

```python
# Configurables en JSON
debug_mode: bool = False
debug_level: Literal[1, 2] = 1
telemetry: bool = True
```

**Disponible pero no en JSON:**
- **Modo debug** con logs detallados
- **Niveles de debug** (1 o 2)
- **Telemetría** (opt-out)

---

## 🎯 Capacidades Avanzadas (No en Parámetros)

### 1. Teams (Multi-Agent)

```python
from agno.team import Team

team = Team(
    agents=[agent1, agent2, agent3],
    mode="sequential"  # o "parallel"
)
```

**Disponible:**
- Múltiples agentes trabajando juntos
- Modos: sequential, parallel
- Coordinación automática

---

### 2. Workflows

```python
from agno.workflow import Workflow

workflow = Workflow(
    steps=[step1, step2, step3]
)
```

**Disponible:**
- Orquestación de agentes
- Pasos definidos
- Control de flujo

---

### 3. Evals (Evaluación)

```python
from agno.evals import BaseEval

class CustomEval(BaseEval):
    def evaluate(self, run_output):
        # Evaluar calidad
        pass
```

**Disponible:**
- Evaluación automática de calidad
- Métricas personalizadas
- A/B testing

---

### 4. Tracing (Observabilidad)

```python
# Integración con:
# - Langfuse
# - LangSmith
# - Arize Phoenix
```

**Disponible:**
- Trazabilidad completa
- Debugging avanzado
- Análisis de performance

---

### 5. MCP Tools

```python
# Model Context Protocol
# Herramientas estandarizadas
```

**Disponible:**
- Integración con MCP servers
- Herramientas estandarizadas
- Interoperabilidad

---

## 📊 Resumen para Audio2Text PRO

### Lo Que Usaremos en JSON:

```json
{
  "prompt_enhancer": {
    "model": {"provider": "openrouter", "id": "z-ai/glm-4.7"},
    "guardrails": {"enabled": true, "types": [...]},
    "templates": {...},
    "limits": {...}
  }
}
```

### Lo Que Está Disponible Automáticamente:

1. ✅ **Memoria de usuario** (recordar preferencias)
2. ✅ **Resúmenes de sesión** (contexto largo)
3. ✅ **Compresión de contexto** (ahorrar tokens)
4. ✅ **Streaming** (respuestas en tiempo real)
5. ✅ **Multimodal** (imágenes, audio)
6. ✅ **Reintentos** (manejo de errores)
7. ✅ **Persistencia** (PostgreSQL, SQLite)
8. ✅ **Dependency injection** (servicios compartidos)
9. ✅ **Debug mode** (troubleshooting)
10. ✅ **Telemetría** (analytics)
11. ✅ **Evals** (calidad de respuestas)
12. ✅ **Tracing** (observabilidad)
13. ✅ **Teams** (multi-agent)
14. ✅ **Workflows** (orquestación)
15. ✅ **MCP Tools** (estandarización)

---

## 🔧 Ejemplo de Uso Completo

```python
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.guardrails import PIIDetectionGuardrail
from agno.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.db.postgres import PostgresDb

agent = Agent(
    # Básico (en JSON)
    id="prompt-enhancer",
    name="Audio2Text Prompt Enhancer",
    model=OpenRouter(id="z-ai/glm-4.7"),
    
    # Guardrails (en JSON)
    pre_hooks=[PIIDetectionGuardrail(mask_pii=True)],
    
    # Memoria (disponible, no en JSON)
    enable_user_memories=True,
    enable_session_summaries=True,
    
    # Knowledge (disponible, no en JSON)
    knowledge=Knowledge(vector_db=PgVector(...)),
    search_knowledge=True,
    
    # Persistencia (disponible, no en JSON)
    db=PostgresDb(db_url="..."),
    
    # Contexto (disponible, no en JSON)
    add_datetime_to_context=True,
    add_session_state_to_context=True,
    
    # Output (disponible, no en JSON)
    output_schema=EnhancedTranscription,
    structured_outputs=True,
    
    # Streaming (disponible, no en JSON)
    stream=True,
    stream_events=True,
    
    # Debug (disponible, no en JSON)
    debug_mode=True,
    debug_level=2
)
```

---

## 💡 Recomendaciones

### Para Audio2Text PRO:

1. **Empezar simple** (solo lo del JSON)
2. **Agregar gradualmente:**
   - Sprint 2: Memoria de usuario
   - Sprint 3: Resúmenes de sesión
   - Sprint 4: Streaming
   - Sprint 5: Evals y tracing

3. **No reinventar:**
   - Usar guardrails de Agno
   - Usar memoria de Agno
   - Usar persistencia de Agno

4. **Configurar lo crítico:**
   - Modelo y provider
   - Guardrails
   - Templates
   - Límites

5. **Dejar disponible:**
   - Todo lo demás está ahí
   - Se puede activar sin cambiar código
   - Solo cambiar parámetros

---

## 📚 Referencias

- **Documentación:** https://docs.agno.com
- **MCP:** https://docs.agno.com/mcp
- **Agent Reference:** https://docs.agno.com/reference/agents/agent
- **Guardrails:** https://docs.agno.com/basics/guardrails
- **Memory:** https://docs.agno.com/basics/memory/agent/overview
- **Knowledge:** https://docs.agno.com/basics/knowledge
- **Tools:** https://docs.agno.com/basics/tools
- **Hooks:** https://docs.agno.com/basics/hooks/overview

---

**Fecha:** 2025-12-26  
**Versión:** 1.0  
**Fuente:** Agno Docs MCP
