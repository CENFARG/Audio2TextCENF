# 📝 Cómo Funciona la Configuración del Agente

## ❓ Pregunta: ¿El archivo `enhancer_system_prompt.md` se usa?

**Respuesta:** ✅ **SÍ, se usa**, pero de manera **indirecta** a través del código Python.

---

## 🔄 Flujo de Carga de Configuración

### 1. **Archivo JSON** (`agents_config.json`)

Este archivo contiene la **configuración** del agente, incluyendo la **ruta** al system prompt:

```json
{
  "system_prompt": {
    "path": "pro/prompts/enhancer_system_prompt.md",
    "variables": {
      "agent_name": "Audio2Text Prompt Enhancer",
      "version": "1.0.0"
    }
  }
}
```

**Qué hace:**
- Define **dónde** está el system prompt (path)
- Define **variables** para reemplazar en el prompt (opcional)

---

### 2. **Código Python** (`prompt_enhancer.py`)

El código **lee** el JSON y **carga** el archivo `.md`:

```python
class PromptEnhancer(Agent):
    def __init__(self, config_path="pro/config/agents_config.json"):
        # 1. Cargar configuración JSON
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        agent_config = config["prompt_enhancer"]
        
        # 2. Obtener path del system prompt
        prompt_path = agent_config["system_prompt"]["path"]
        
        # 3. LEER el archivo .md
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        
        # 4. (Opcional) Reemplazar variables
        variables = agent_config["system_prompt"].get("variables", {})
        for key, value in variables.items():
            system_prompt = system_prompt.replace(f"{{{key}}}", str(value))
        
        # 5. Inicializar agente con el prompt cargado
        super().__init__(
            model=OpenRouter(id="z-ai/glm-4.7"),
            instructions=[system_prompt],  # ← Aquí se usa
            ...
        )
```

---

## 📊 Diagrama de Flujo

```
agents_config.json
    ↓
    ├─ Contiene: "path": "pro/prompts/enhancer_system_prompt.md"
    ↓
Python lee JSON
    ↓
    ├─ Extrae: prompt_path = "pro/prompts/enhancer_system_prompt.md"
    ↓
Python abre archivo .md
    ↓
    ├─ Lee contenido del archivo
    ↓
Python pasa contenido a Agent()
    ↓
    └─ Agent usa el prompt en cada run
```

---

## 🎯 Ventajas de Este Enfoque

### 1. **Separación de Configuración y Contenido**
- ✅ JSON: Configuración técnica (modelo, límites, etc.)
- ✅ Markdown: Contenido del prompt (fácil de editar)

### 2. **Edición Sin Recompilar**
- ✅ Puedes editar `enhancer_system_prompt.md`
- ✅ Sin tocar el código Python
- ✅ Sin recompilar el ejecutable

### 3. **Versionado Separado**
- ✅ Puedes versionar prompts independientemente
- ✅ A/B testing de prompts
- ✅ Rollback fácil

### 4. **Reutilización**
- ✅ Mismo patrón que agenteTutor
- ✅ Fácil agregar más agentes
- ✅ Consistencia en el proyecto

---

## 🔧 Ejemplo Completo

### Archivo: `agents_config.json`
```json
{
  "prompt_enhancer": {
    "system_prompt": {
      "path": "pro/prompts/enhancer_system_prompt.md",
      "variables": {
        "agent_name": "Audio2Text Prompt Enhancer",
        "version": "1.0.0"
      }
    }
  }
}
```

### Archivo: `enhancer_system_prompt.md`
```markdown
# {agent_name} - System Prompt

Versión: {version}

Eres un agente especializado en...
```

### Código: `prompt_enhancer.py`
```python
# Cargar config
config = load_config("agents_config.json")

# Leer archivo .md
prompt_path = config["system_prompt"]["path"]
with open(prompt_path) as f:
    system_prompt = f.read()

# Reemplazar variables
system_prompt = system_prompt.replace("{agent_name}", "Audio2Text Prompt Enhancer")
system_prompt = system_prompt.replace("{version}", "1.0.0")

# Usar en agente
agent = Agent(instructions=[system_prompt])
```

### Resultado Final:
```markdown
# Audio2Text Prompt Enhancer - System Prompt

Versión: 1.0.0

Eres un agente especializado en...
```

---

## 📝 Comparación con Alternativas

### ❌ **Opción 1: Todo en JSON**
```json
{
  "system_prompt": "Eres un agente especializado en mejorar transcripciones..."
}
```
**Problemas:**
- Difícil de editar (sin syntax highlighting)
- No se puede usar markdown
- JSON se vuelve enorme

### ❌ **Opción 2: Hardcodeado en Python**
```python
system_prompt = """
Eres un agente especializado en...
"""
```
**Problemas:**
- Hay que recompilar para cambiar
- No es configurable
- Difícil de versionar

### ✅ **Opción 3: JSON + Archivo .md (ELEGIDA)**
```json
{"system_prompt": {"path": "prompts/enhancer.md"}}
```
**Ventajas:**
- ✅ Fácil de editar (markdown)
- ✅ No requiere recompilar
- ✅ Versionable
- ✅ Configurable

---

## 🚀 Cómo Editar el Prompt

### 1. **Abrir el archivo**
```bash
code pro/prompts/enhancer_system_prompt.md
```

### 2. **Editar el contenido**
```markdown
# Audio2Text Prompt Enhancer - System Prompt

## Identidad
Eres un agente especializado en...

## Nuevas Reglas
- Regla 1
- Regla 2
```

### 3. **Guardar**
- No necesitas recompilar
- No necesitas cambiar el JSON
- Solo reiniciar la app

### 4. **El agente usará el nuevo prompt**
```python
# Al inicializar, lee el archivo actualizado
with open("pro/prompts/enhancer_system_prompt.md") as f:
    system_prompt = f.read()  # ← Lee la versión nueva
```

---

## 💡 Recomendación

**Para Audio2Text PRO:**

1. ✅ **Mantener** el archivo `.md` separado
2. ✅ **Usar** el patrón de agenteTutor
3. ✅ **Versionar** ambos archivos (JSON + MD)
4. ✅ **Documentar** cambios en CHANGELOG.md

**Beneficios:**
- Fácil de mantener
- Fácil de testear (cambiar prompt sin recompilar)
- Fácil de escalar (agregar más prompts)

---

## 📚 Referencias

- **Patrón usado:** agenteTutor
- **Archivo de ejemplo:** `.context/agenteTutor/app/agents/agente_tutor.py`
- **Configuración:** `.context/agenteTutor/config/agents_config.json`

---

**Fecha:** 2025-12-26  
**Versión:** 1.0
