"""
Block Manager - Gestiona el pipeline de bloques procesables

Coordina la ejecución de bloques en el orden correcto y maneja el flujo
de datos entre ellos.

Author: Audio2Text Development Team
Version: 0.11.0 (development)
"""

from typing import List, Dict, Any, Optional
import logging

from .base_block import BaseBlock, BlockType, ProcessingStage, BlockResult

logger = logging.getLogger(__name__)


class BlockManager:
    """
    Gestiona el pipeline de bloques procesables.

    Responsabilidades:
    - Registrar bloques
    - Ejecutar bloques en el orden correcto
    - Manejar errores y fallbacks
    - Proveer estadísticas de ejecución
    """

    def __init__(self):
        """Inicializar manager de bloques."""
        self.blocks: List[BaseBlock] = []
        self.enabled_blocks: List[BaseBlock] = []

    def register_block(self, block: BaseBlock) -> None:
        """
        Registrar un bloque en el pipeline.

        Args:
            block: Instancia de bloque a registrar
        """
        if not isinstance(block, BaseBlock):
            raise TypeError(f"Expected BaseBlock, got {type(block)}")

        # Verificar duplicados
        if any(b.name == block.name for b in self.blocks):
            raise ValueError(f"Block '{block.name}' already registered")

        self.blocks.append(block)
        self._update_enabled_blocks()

        logger.info(f"BlockManager: Registrado bloque '{block.name}' (type={block.block_type.value})")

    def unregister_block(self, block_name: str) -> bool:
        """
        Desregistrar un bloque del pipeline.

        Args:
            block_name: Nombre del bloque a desregistrar

        Returns:
            True si se desregistró correctamente, False si no existía
        """
        for i, block in enumerate(self.blocks):
            if block.name == block_name:
                self.blocks.pop(i)
                self._update_enabled_blocks()
                logger.info(f"BlockManager: Desregistrado bloque '{block_name}'")
                return True

        return False

    def enable_block(self, block_name: str) -> bool:
        """Activar un bloque."""
        for block in self.blocks:
            if block.name == block_name:
                block.enabled = True
                self._update_enabled_blocks()
                logger.info(f"BlockManager: Activado bloque '{block_name}'")
                return True
        return False

    def disable_block(self, block_name: str) -> bool:
        """Desactivar un bloque."""
        for block in self.blocks:
            if block.name == block_name:
                block.enabled = False
                self._update_enabled_blocks()
                logger.info(f"BlockManager: Desactivado bloque '{block_name}'")
                return True
        return False

    def _update_enabled_blocks(self) -> None:
        """Actualizar lista de bloques activos."""
        self.enabled_blocks = [b for b in self.blocks if b.enabled]

    def process(
        self,
        data: Any,
        stage: ProcessingStage
    ) -> List[BlockResult]:
        """
        Ejecutar todos los bloques activos para la etapa dada.

        Args:
            data: Datos a procesar
            stage: Etapa de procesamiento actual

        Returns:
            Lista de resultados de cada bloque ejecutado
        """
        results = []

        # Filtrar bloques que deben procesar en esta etapa
        blocks_to_process = [
            block for block in self.enabled_blocks
            if block.should_process(stage)
        ]

        if not blocks_to_process:
            logger.debug(f"BlockManager: No hay bloques para etapa {stage.value}")
            return results

        logger.info(f"BlockManager: Procesando {len(blocks_to_process)} bloques en etapa {stage.value}")

        # Ejecutar bloques
        # Para POST-transcripción: cada bloque procesa el input original independientemente
        # Para PRE-transcripción: los bloques se encadenan (output → input del siguiente)
        current_data = data
        for block in blocks_to_process:
            try:
                logger.debug(f"BlockManager: Ejecutando bloque '{block.name}'")
                result = block.process(current_data, stage)
                results.append(result)

                # Si el bloque falló, loguear pero continuar con siguiente
                if not result.success:
                    logger.warning(f"BlockManager: Bloque '{block.name}' falló: {result.error}")

                # Encadenar SOLO para bloques PRE-transcripción
                # Los bloques POST-transcripción siempre procesan el input original
                if block.block_type == BlockType.PRE_TRANSCRIPTION:
                    if result.success and result.data is not None:
                        current_data = result.data
                else:
                    # POST-transcripción: resetear al input original para cada bloque
                    current_data = data

            except Exception as e:
                logger.error(f"BlockManager: Excepción en bloque '{block.name}': {e}")
                results.append(BlockResult(
                    success=False,
                    data=None,
                    error=str(e)
                ))

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de todos los bloques.

        Returns:
            Diccionario con stats de cada bloque
        """
        stats = {}
        for block in self.blocks:
            stats[block.name] = {
                'enabled': block.enabled,
                'block_type': block.block_type.value,
                'stats': block.get_stats()
            }
        return stats

    def get_block(self, block_name: str) -> Optional[BaseBlock]:
        """Obtener bloque por nombre."""
        for block in self.blocks:
            if block.name == block_name:
                return block
        return None

    def list_blocks(self, enabled_only: bool = False) -> List[str]:
        """
        Listar nombres de bloques registrados.

        Args:
            enabled_only: Si True, solo listar bloques activos

        Returns:
            Lista de nombres de bloques
        """
        blocks = self.enabled_blocks if enabled_only else self.blocks
        return [block.name for block in blocks]
