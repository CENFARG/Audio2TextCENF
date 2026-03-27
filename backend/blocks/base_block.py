"""
Base Block - Clase base para todos los bloques procesables

Define la interfaz y comportamiento común que todos los bloques deben implementar.

Author: Audio2Text Development Team
Version: 0.11.0 (development)
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BlockType(Enum):
    """Tipo de bloque procesable."""

    PRE_TRANSCRIPTION = "pre"  # Se ejecuta ANTES de transcribir
    POST_TRANSCRIPTION = "post"  # Se ejecuta DESPUÉS de transcribir
    BOTH = "both"  # Se ejecuta en ambos momentos


class ProcessingStage(Enum):
    """Etapa de procesamiento."""

    RAW_AUDIO = "raw_audio"  # Audio sin procesar
    TRANSCRIBED_TEXT = "transcribed_text"  # Texto transcrito
    PROCESSED_TEXT = "processed_text"  # Texto post-procesado


class BlockResult:
    """Resultado del procesamiento de un bloque."""

    def __init__(
        self,
        success: bool,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.data = data
        self.metadata = metadata or {}
        self.error = error
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            'success': self.success,
            'data': self.data,
            'metadata': self.metadata,
            'error': self.error,
            'timestamp': self.timestamp.isoformat()
        }


class BaseBlock(ABC):
    """
    Clase base abstracta para todos los bloques procesables.

    Todos los bloques deben heredar de esta clase e implementar los métodos
    abstractos `process()` y `validate_input()`.
    """

    def __init__(
        self,
        name: str,
        description: str,
        block_type: BlockType,
        enabled: bool = True,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializar bloque.

        Args:
            name: Nombre único del bloque
            description: Descripción de lo que hace el bloque
            block_type: Tipo de bloque (PRE_TRANSCRIPTION, POST_TRANSCRIPTION, BOTH)
            enabled: Si el bloque está activo
            config: Configuración específica del bloque
        """
        self.name = name
        self.description = description
        self.block_type = block_type
        self.enabled = enabled
        self.config = config or {}
        self.stats = {
            'processed': 0,
            'failed': 0,
            'avg_processing_time': 0.0
        }

    @abstractmethod
    def process(self, data: Any, stage: ProcessingStage) -> BlockResult:
        """
        Procesar datos con este bloque.

        Args:
            data: Datos a procesar (audio o texto dependiendo del stage)
            stage: Etapa actual de procesamiento

        Returns:
            BlockResult con resultado del procesamiento
        """
        pass

    @abstractmethod
    def validate_input(self, data: Any, stage: ProcessingStage) -> bool:
        """
        Validar que los datos de entrada sean correctos para este bloque.

        Args:
            data: Datos a validar
            stage: Etapa de procesamiento

        Returns:
            True si los datos son válidos, False otherwise
        """
        pass

    def should_process(self, stage: ProcessingStage) -> bool:
        """
        Determinar si este bloque debe procesar en la etapa dada.

        Args:
            stage: Etapa de procesamiento actual

        Returns:
            True si el bloque debe procesar, False otherwise
        """
        if not self.enabled:
            return False

        if self.block_type == BlockType.BOTH:
            return True

        if stage == ProcessingStage.RAW_AUDIO:
            return self.block_type == BlockType.PRE_TRANSCRIPTION

        if stage in [ProcessingStage.TRANSCRIBED_TEXT, ProcessingStage.PROCESSED_TEXT]:
            return self.block_type == BlockType.POST_TRANSCRIPTION

        return False

    def get_config(self, key: str, default: Any = None) -> Any:
        """Obtener valor de configuración."""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Establecer valor de configuración."""
        self.config[key] = value

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de procesamiento."""
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Resetear estadísticas."""
        self.stats = {
            'processed': 0,
            'failed': 0,
            'avg_processing_time': 0.0
        }

    def __repr__(self) -> str:
        """Representación del bloque."""
        return f"<{self.__class__.__name__} name={self.name} type={self.block_type.value} enabled={self.enabled}>"
