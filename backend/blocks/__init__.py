"""
Audio2Text - Sistema de Bloques/Middles

Este módulo implementa un sistema de bloques procesables que pueden aplicarse
antes (pre) o después (post) de la transcripción.

Author: Audio2Text Development Team
Version: 0.11.0 (development)
"""

from .base_block import BaseBlock, BlockType, ProcessingStage
from .block_manager import BlockManager
from .task_extractor_block import TaskExtractorBlock
from .summary_block import SummaryBlock
from .keyword_extractor_block import KeywordExtractorBlock

__all__ = [
    'BaseBlock',
    'BlockType',
    'ProcessingStage',
    'BlockManager',
    'TaskExtractorBlock',
    'SummaryBlock',
    'KeywordExtractorBlock',
]
