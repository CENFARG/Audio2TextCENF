# Sistema de Bloques/Middles - Audio2Text v0.11.0

> **Fecha:** 2026-03-20
> **Versión:** 0.11.0 (development)
> **Autor:** Audio2Text Development Team

---

## 📋 ÍNDICE

1. [Concepto](#concepto)
2. [Arquitectura](#arquitectura)
3. [Uso](#uso)
4. [Bloques Implementados](#bloques-implementados)
5. [Cómo Crear Bloques Custom](#cómo-crear-bloques-custom)
6. [Ejemplos](#ejemplos)

---

## 🎯 CONCEPTO

El **Sistema de Bloques** permite procesar transcripciones con módulos independientes que pueden aplicarse:

- **PRE-transcripción:** Antes de que el audio se transcriba (ej: filtros de audio, normalización)
- **POST-transcripción:** Después de tener el texto transcrito (ej: extractor de tareas, resumen, traducción)
- **BOTH:** En ambos momentos

### Ventajas

✅ **Modular:** Cada bloque es independiente y reusable
✅ **Configurable:** Bloques pueden activarse/desactivarse dinámicamente
✅ **Extensible:** Fácil agregar nuevos bloques sin modificar código existente
✅ **Escalable:** Múltiples bloques pueden ejecutarse en pipeline
✅ **Robusto:** Si un bloque falla, no afecta a los demás

---

## 🏗️ ARQUITECTURA

### Componentes Principales

```
backend/blocks/
├── __init__.py              # Exportaciones
├── base_block.py            # Clase base abstracta
├── block_manager.py         # Gestor de pipeline
├── task_extractor_block.py  # Bloque extractor de tareas
└── README.md                # Este archivo
```

### Diagrama de Flujo

```
Audio Raw → [PRE Blocks] → Transcripción → [POST Blocks] → Texto Final
                         ↓
                   TaskExtractor
                   SummaryBlock
                   TranslationBlock
```

---

## 🚀 USO

### Ejemplo Básico

```python
from backend.blocks import BlockManager, TaskExtractorBlock

# Crear manager
manager = BlockManager()

# Registrar bloques
task_extractor = TaskExtractorBlock(config={
    'min_priority': 3,
    'max_tasks': 10
})
manager.register_block(task_extractor)

# Procesar transcripción
results = manager.process(
    data="Tengo que hacer el reporte. Necesito revisar el código.",
    stage=ProcessingStage.TRANSCRIBED_TEXT
)

# Ver resultados
for result in results:
    if result.success:
        print(f"Tareas extraídas: {result.data}")
```

### Integración con Transcriber

```python
from backend.transcriber import Transcriber
from backend.blocks import BlockManager, TaskExtractorBlock

class Audio2TextApp:
    def __init__(self):
        self.transcriber = Transcriber(...)
        self.block_manager = BlockManager()

        # Registrar bloques POST-transcripción
        self.block_manager.register_block(TaskExtractorBlock())

    def transcribe_audio(self, audio_path: str) -> dict:
        # Transcribir audio
        result = self.transcriber.transcribe(audio_path)

        if result['success']:
            # Procesar con bloques POST
            block_results = self.block_manager.process(
                data=result['text'],
                stage=ProcessingStage.TRANSCRIBED_TEXT
            )

            # Agregar resultados de bloques
            result['block_results'] = block_results

        return result
```

---

## 📦 BLOQUES IMPLEMENTADOS

### 1. TaskExtractorBlock

**Descripción:** Extrae tareas/action items de transcripciones

**Tipo:** POST_TRANSCRIPTION

**Patrones reconocidos:**
- "tengo que...", "necesito...", "hay que..."
- "recordar...", "no olvidar..."
- Verbos de acción: hacer, crear, implementar, etc.

**Configuración:**
```python
config = {
    'min_priority': 3,          # Prioridad mínima (1-5)
    'extract_due_dates': True,  # Extraer fechas
    'extract_assignees': True,  # Extraer responsables
    'max_tasks': 10             # Máximo de tareas
}
```

**Ejemplo de salida:**
```python
{
    'id': 'task_20260320123456',
    'text': 'hacer el reporte',
    'priority': 4,
    'status': 'pending',
    'created_at': '2026-03-20T12:34:56',
    'due_date': 'para mañana',
    'assignee': None,
    'tags': []
}
```

---

## 🔧 CÓMO CREAR BLOQUES CUSTOM

### Plantilla Base

```python
from backend.blocks.base_block import BaseBlock, BlockType, ProcessingStage, BlockResult

class MiBloqueCustom(BaseBlock):
    """Descripción de lo que hace mi bloque."""

    def __init__(self, config: dict = None):
        super().__init__(
            name="mi_bloque",
            description="Descripción",
            block_type=BlockType.POST_TRANSCRIPTION,
            enabled=True,
            config=config or {}
        )

    def validate_input(self, data, stage):
        """Validar input."""
        return True

    def process(self, data, stage):
        """Procesar datos."""
        try:
            # Lógica de procesamiento aquí
            result_data = self._mi_logica(data)

            return BlockResult(
                success=True,
                data=result_data,
                metadata={'key': 'value'}
            )
        except Exception as e:
            return BlockResult(
                success=False,
                data=None,
                error=str(e)
            )

    def _mi_logica(self, data):
        """Lógica interna de procesamiento."""
        # Implementar lógica específica
        return processed_data
```

### Ejemplo: SummaryBlock

```python
class SummaryBlock(BaseBlock):
    """Genera resumen de transcripción."""

    def __init__(self, config: dict = None):
        super().__init__(
            name="summary",
            description="Genera resumen ejecutivo",
            block_type=BlockType.POST_TRANSCRIPTION,
            enabled=True,
            config=config
        )
        self.max_length = self.get_config('max_length', 100)

    def validate_input(self, data, stage):
        return isinstance(data, str) and len(data) > 50

    def process(self, data, stage):
        text = data[:self.max_length] + "..."
        return BlockResult(
            success=True,
            data=text,
            metadata={'original_length': len(data)}
        )
```

---

## 📚 EJEMPLOS

### Ejemplo 1: Activar/Desactivar Bloques

```python
manager = BlockManager()
task_block = TaskExtractorBlock()
manager.register_block(task_block)

# Desactivar bloque
manager.disable_block('task_extractor')

# Procesar (task_extractor NO se ejecutará)
results = manager.process(text, stage)

# Reactivar
manager.enable_block('task_extractor')
```

### Ejemplo 2: Múltiples Bloques en Pipeline

```python
manager = BlockManager()

# Registrar varios bloques
manager.register_block(TaskExtractorBlock())
manager.register_block(SummaryBlock())
manager.register_block(TranslationBlock())

# Se ejecutan en orden de registro
results = manager.process(text, ProcessingStage.TRANSCRIBED_TEXT)

# results[0] = TaskExtractor
# results[1] = Summary
# results[2] = Translation
```

### Ejemplo 3: Estadísticas

```python
stats = manager.get_stats()

print(json.dumps(stats, indent=2))
# {
#   "task_extractor": {
#     "enabled": true,
#     "block_type": "post",
#     "stats": {
#       "processed": 150,
#       "failed": 2,
#       "avg_processing_time": 0.15
#     }
#   },
#   ...
# }
```

---

## 🎨 PRÓXIMOS BLOQUES PLANIFICADOS

### v0.11.0
- [ ] SummaryBlock - Generar resúmenes ejecutivos
- [ ] TranslationBlock - Traducir transcripciones
- [ ] KeywordExtractorBlock - Extraer palabras clave
- [ ] SentimentBlock - Análisis de sentimiento

### v0.12.0
- [ ] AudioEnhancerBlock - Mejorar calidad de audio (PRE)
- [ ] NoiseReductionBlock - Reducir ruido ambiental (PRE)
- [ ] SpeakerDiarizationBlock - Detectar diferentes hablantes

---

**Versión:** 0.11.0-dev
**Última actualización:** 2026-03-20
