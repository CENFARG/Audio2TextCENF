"""
Task Extractor Block - Extrae tareas de transcripciones

Analiza el texto transcrito y extrae tareas/action items usando patrones
y procesamiento de lenguaje natural.

Author: Audio2Text Development Team
Version: 0.11.0 (development)
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .base_block import BaseBlock, BlockType, ProcessingStage, BlockResult

logger = logging.getLogger(__name__)


class TaskExtractorBlock(BaseBlock):
    """
    Bloque para extraer tareas/action items de transcripciones.

    Patrones reconocidos:
    - "tengo que...", "necesito...", "hay que..."
    - "recordar...", "no olvidar...", "acordarse..."
    - Verbos de acción: hacer, crear, implementar, arreglar, etc.
    """

    # Patrones de detección de tareas (español)
    TASK_PATTERNS = [
        r'tengo que\s+(.+?)(?:\.|$)',
        r'necesito\s+(.+?)(?:\.|$)',
        r'hay que\s+(.+?)(?:\.|$)',
        r'recordar\s+(.+?)(?:\.|$)',
        r'no olvidar\s+(.+?)(?:\.|$)',
        r'acordarse de\s+(.+?)(?:\.|$)',
        r'(?:(?:después|luego)|entonces)\s+(?:tengo que|necesito|hay que)\s+(.+?)(?:\.|$)',
    ]

    # Verbos de acción comunes
    ACTION_VERBS = [
        'hacer', 'crear', 'implementar', 'arreglar', 'corregir', 'solucionar',
        'revisar', 'verificar', 'testear', 'probar', 'documentar', 'actualizar',
        'mejorar', 'optimizar', 'refactorizar', 'limpiar', 'organizar',
        'investigar', 'analizar', 'evaluar', 'considerar', 'pensar',
        'contactar', 'hablar con', 'reunirme con', 'llamar a',
        'comprar', 'adquirir', 'conseguir', 'buscar', 'encontrar',
        'eliminar', 'borrar', 'remover', 'sacar'
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializar bloque extractor de tareas.

        Configuración opcional:
            - min_priority (int): Prioridad mínima para extraer (1-5, default=3)
            - extract_due_dates (bool): Extraer fechas de vencimiento (default=True)
            - extract_assignees (bool): Extraer responsables (default=True)
            - max_tasks (int): Máximo número de tareas a extraer (default=10)
        """
        super().__init__(
            name="task_extractor",
            description="Extrae tareas/action items de transcripciones",
            block_type=BlockType.POST_TRANSCRIPTION,
            enabled=True,
            config=config or {}
        )

        # Configuración con defaults
        self.min_priority = self.get_config('min_priority', 3)
        self.extract_due_dates = self.get_config('extract_due_dates', True)
        self.extract_assignees = self.get_config('extract_assignees', True)
        self.max_tasks = self.get_config('max_tasks', 10)

    def validate_input(self, data: Any, stage: ProcessingStage) -> bool:
        """Validar que el input sea texto transcribible."""
        if not isinstance(data, str):
            logger.warning(f"TaskExtractor: Input debe ser string, got {type(data)}")
            return False

        if len(data.strip()) < 10:
            logger.warning("TaskExtractor: Input demasiado corto")
            return False

        return True

    def process(self, data: str, stage: ProcessingStage) -> BlockResult:
        """
        Procesar transcripción y extraer tareas.

        Args:
            data: Texto transcrito
            stage: Etapa de procesamiento (debe ser TRANSCRIBED_TEXT o PROCESSED_TEXT)

        Returns:
            BlockResult con lista de tareas extraídas
        """
        try:
            # Validar input
            if not self.validate_input(data, stage):
                return BlockResult(
                    success=False,
                    data=[],
                    error="Input inválido"
                )

            # Extraer tareas
            tasks = self._extract_tasks(data)

            # Ordenar por prioridad y limitar cantidad
            tasks = sorted(tasks, key=lambda t: t.get('priority', 0), reverse=True)
            tasks = tasks[:self.max_tasks]

            # Actualizar estadísticas
            self.stats['processed'] += 1

            logger.info(f"TaskExtractor: Extraídas {len(tasks)} tareas")

            return BlockResult(
                success=True,
                data=tasks,
                metadata={
                    'total_found': len(tasks),
                    'max_tasks': self.max_tasks,
                    'processing_time': 0.0  # TODO: Implementar timer
                }
            )

        except Exception as e:
            logger.error(f"TaskExtractor: Error procesando: {e}")
            self.stats['failed'] += 1

            return BlockResult(
                success=False,
                data=[],
                error=str(e)
            )

    def _extract_tasks(self, text: str) -> List[Dict[str, Any]]:
        """Extraer tareas del texto usando patrones y NLP."""
        tasks = []

        # Normalizar texto
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)

        # Buscar patrones explícitos
        for pattern in self.TASK_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                task_text = match.group(1).strip()
                task = self._create_task(task_text, priority=4)
                tasks.append(task)

        # Buscar verbos de acción
        for verb in self.ACTION_VERBS:
            pattern = rf'\b{verb}\s+(.+?)(?:\.|$)'
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                task_text = f"{verb} {match.group(1).strip()}"
                task = self._create_task(task_text, priority=3)
                tasks.append(task)

        # Eliminar duplicados
        seen = set()
        unique_tasks = []
        for task in tasks:
            task_key = task['text'].lower()
            if task_key not in seen:
                seen.add(task_key)
                unique_tasks.append(task)

        return unique_tasks

    def _create_task(
        self,
        text: str,
        priority: int = 3
    ) -> Dict[str, Any]:
        """
        Crear estructura de tarea.

        Args:
            text: Descripción de la tarea
            priority: Prioridad (1-5, donde 5 es más alta)

        Returns:
            Diccionario con la tarea
        """
        task = {
            'id': f"task_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            'text': text,
            'priority': priority,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'due_date': None,
            'assignee': None,
            'tags': []
        }

        # Extraer fecha de vencimiento si está configurado
        if self.extract_due_dates:
            due_date = self._extract_due_date(text)
            if due_date:
                task['due_date'] = due_date

        # Extraer responsable si está configurado
        if self.extract_assignees:
            assignee = self._extract_assignee(text)
            if assignee:
                task['assignee'] = assignee

        return task

    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extraer fecha de vencimiento del texto."""
        # Patrones de fecha simples
        patterns = [
            r'para\s+(hoy|mañana|el lunes|el martes|el miércoles|el jueves|el viernes)',
            r'(?:esta|próxima)\s+semana',
        ]

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                return match.group(0) if match else None

        return None

    def _extract_assignee(self, text: str) -> Optional[str]:
        """Extraer responsable del texto."""
        # Patrones: "Juan que haga...", "para Pedro..."
        patterns = [
            r'([A-Z][a-z]+)\s+que\s+haga',
            r'para\s+([A-Z][a-z]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None
