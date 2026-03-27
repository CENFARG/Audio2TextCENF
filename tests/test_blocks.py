"""
Tests para el sistema de bloques de Audio2Text

Author: Audio2Text Development Team
Version: 0.11.0 (development)
"""

import pytest
import sys
import os

# Agregar backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.blocks import (
    BlockManager,
    TaskExtractorBlock,
    SummaryBlock,
    KeywordExtractorBlock,
    ProcessingStage
)


class TestTaskExtractorBlock:
    """Tests para TaskExtractorBlock."""

    def test_initialization(self):
        """Test de inicialización del bloque."""
        block = TaskExtractorBlock()
        assert block.name == "task_extractor"
        assert block.enabled == True
        assert block.block_type.value == "post"

    def test_validate_input_valid(self):
        """Test de validación de input válido."""
        block = TaskExtractorBlock()
        text = "Tengo que hacer el reporte mañana por la mañana."
        assert block.validate_input(text, ProcessingStage.TRANSCRIBED_TEXT) == True

    def test_validate_input_invalid(self):
        """Test de validación de input inválido."""
        block = TaskExtractorBlock()
        assert block.validate_input("", ProcessingStage.TRANSCRIBED_TEXT) == False
        assert block.validate_input(123, ProcessingStage.TRANSCRIBED_TEXT) == False

    def test_extract_tasks_simple(self):
        """Test de extracción de tareas simples."""
        block = TaskExtractorBlock()
        text = "Tengo que hacer el reporte. Necesito revisar el código."
        result = block.process(text, ProcessingStage.TRANSCRIBED_TEXT)

        assert result.success == True
        assert len(result.data) > 0
        assert any('reporte' in task['text'].lower() for task in result.data)

    def test_extract_tasks_with_priority(self):
        """Test de extracción de tareas con prioridad."""
        block = TaskExtractorBlock(config={'min_priority': 4})
        text = "Tengo que hacer el reporte. Recordar llamar a Juan."
        result = block.process(text, ProcessingStage.TRANSCRIBED_TEXT)

        assert result.success == True
        # Todas las tareas deberían tener prioridad >= 4
        for task in result.data:
            assert task['priority'] >= 4

    def test_max_tasks_limit(self):
        """Test de límite máximo de tareas."""
        block = TaskExtractorBlock(config={'max_tasks': 2})
        text = "Tengo que hacer A. Necesito hacer B. Hay que hacer C. Recordar D."
        result = block.process(text, ProcessingStage.TRANSCRIBED_TEXT)

        assert result.success == True
        assert len(result.data) <= 2


class TestSummaryBlock:
    """Tests para SummaryBlock."""

    def test_initialization(self):
        """Test de inicialización del bloque."""
        block = SummaryBlock()
        assert block.name == "summary"
        assert block.enabled == True
        assert block.block_type.value == "post"

    def test_validate_input_valid(self):
        """Test de validación de input válido."""
        block = SummaryBlock()
        text = "Este es un texto suficientemente largo para ser resumido. " * 10
        assert block.validate_input(text, ProcessingStage.TRANSCRIBED_TEXT) == True

    def test_validate_input_invalid(self):
        """Test de validación de input inválido."""
        block = SummaryBlock()
        assert block.validate_input("Corto", ProcessingStage.TRANSCRIBED_TEXT) == False
        assert block.validate_input(123, ProcessingStage.TRANSCRIBED_TEXT) == False

    def test_generate_summary(self):
        """Test de generación de resumen."""
        block = SummaryBlock(config={'max_sentences': 2, 'max_length': 200})
        text = """
        Esta es la primera oración del texto. Es una oración importante que contiene
        información clave sobre el tema principal. Esta segunda oración es menos
        importante y solo contiene detalles secundarios. La tercera oración vuelve
        a ser importante y resume las conclusiones principales. Esta cuarta oración
        es solo un relleno sin mucha importancia.
        """
        result = block.process(text, ProcessingStage.TRANSCRIBED_TEXT)

        assert result.success == True
        assert len(result.data) > 0
        assert len(result.data) <= 200  # Respeta max_length

    def test_summary_compression(self):
        """Test de ratio de compresión."""
        block = SummaryBlock()
        long_text = "Esta es una oración de prueba. " * 50
        result = block.process(long_text, ProcessingStage.TRANSCRIBED_TEXT)

        assert result.success == True
        assert result.metadata['compression_ratio'] < 1.0
        assert len(result.data) < len(long_text)


class TestKeywordExtractorBlock:
    """Tests para KeywordExtractorBlock."""

    def test_initialization(self):
        """Test de inicialización del bloque."""
        block = KeywordExtractorBlock()
        assert block.name == "keyword_extractor"
        assert block.enabled == True
        assert block.block_type.value == "post"

    def test_extract_keywords(self):
        """Test de extracción de palabras clave."""
        block = KeywordExtractorBlock(config={'max_keywords': 5})
        text = "La inteligencia artificial y el machine learning están transformando la tecnología. Python es importante para data science."
        result = block.process(text, ProcessingStage.TRANSCRIBED_TEXT)

        assert result.success == True
        assert len(result.data) > 0
        assert len(result.data) <= 5

    def test_keyword_classification(self):
        """Test de clasificación de palabras clave."""
        block = KeywordExtractorBlock()
        text = "El proyecto tiene un presupuesto de 5000 dólares y debe completarse el 15 de diciembre de 2024."
        result = block.process(text, ProcessingStage.TRANSCRIBED_TEXT)

        assert result.success == True
        # Debería haber clasificado algunas keywords
        types = [kw['type'] for kw in result.data]
        assert len(types) > 0

    def test_min_length_filter(self):
        """Test de filtro de longitud mínima."""
        block = KeywordExtractorBlock(config={'min_length': 5})
        text = "AI y ML son importantes. Python es útil."
        result = block.process(text, ProcessingStage.TRANSCRIBED_TEXT)

        assert result.success == True
        # Todas las keywords deberían tener >= 5 caracteres
        for kw in result.data:
            assert len(kw['keyword']) >= 5


class TestBlockManager:
    """Tests para BlockManager."""

    def test_register_block(self):
        """Test de registro de bloques."""
        manager = BlockManager()
        block = TaskExtractorBlock()

        manager.register_block(block)
        assert 'task_extractor' in manager.list_blocks()

    def test_duplicate_block_raises_error(self):
        """Test de error al registrar bloque duplicado."""
        manager = BlockManager()
        block1 = TaskExtractorBlock()
        block2 = TaskExtractorBlock()

        manager.register_block(block1)
        with pytest.raises(ValueError):
            manager.register_block(block2)

    def test_enable_disable_block(self):
        """Test de activación/desactivación de bloques."""
        manager = BlockManager()
        block = TaskExtractorBlock()
        manager.register_block(block)

        # Desactivar
        assert manager.disable_block('task_extractor') == True
        assert 'task_extractor' not in manager.list_blocks(enabled_only=True)

        # Activar
        assert manager.enable_block('task_extractor') == True
        assert 'task_extractor' in manager.list_blocks(enabled_only=True)

    def test_process_pipeline(self):
        """Test de pipeline de procesamiento."""
        manager = BlockManager()
        manager.register_block(TaskExtractorBlock())
        manager.register_block(SummaryBlock())

        text = "Tengo que hacer el reporte. Este es un texto suficientemente largo para generar un resumen. " * 10
        results = manager.process(text, ProcessingStage.TRANSCRIBED_TEXT)

        assert len(results) == 2  # TaskExtractor + Summary
        assert all(r.success for r in results)  # Todos exitosos

    def test_get_stats(self):
        """Test de obtención de estadísticas."""
        manager = BlockManager()
        block = TaskExtractorBlock()
        manager.register_block(block)

        stats = manager.get_stats()
        assert 'task_extractor' in stats
        assert stats['task_extractor']['enabled'] == True


class TestIntegration:
    """Tests de integración del sistema de bloques."""

    def test_full_transcription_pipeline(self):
        """Test de pipeline completo de transcripción."""
        manager = BlockManager()
        manager.register_block(TaskExtractorBlock(config={'max_tasks': 5}))
        manager.register_block(SummaryBlock(config={'max_sentences': 2}))
        manager.register_block(KeywordExtractorBlock(config={'max_keywords': 5}))

        # Simular transcripción
        transcription = """
        En la reunión de hoy discutimos varios temas importantes.
        Tengo que preparar el informe financiero para el próximo lunes.
        Necesito contactar al cliente para confirmar los requisitos.
        La inteligencia artificial está transformando nuestra industria.
        Recordar agendar la reunión de seguimiento con el equipo de desarrollo.
        El presupuesto del proyecto es de 50000 dólares.
        """

        # Procesar con bloques
        results = manager.process(transcription, ProcessingStage.TRANSCRIBED_TEXT)

        # Verificar resultados
        assert len(results) == 3

        # TaskExtractor
        task_result = results[0]
        assert task_result.success == True
        assert len(task_result.data) > 0

        # Summary
        summary_result = results[1]
        assert summary_result.success == True
        assert len(summary_result.data) > 0
        assert len(summary_result.data) < len(transcription)

        # Keywords
        keyword_result = results[2]
        assert keyword_result.success == True
        assert len(keyword_result.data) > 0

    def test_error_handling(self):
        """Test de manejo de errores en bloques."""
        manager = BlockManager()
        manager.register_block(TaskExtractorBlock())

        # Input inválido
        results = manager.process("", ProcessingStage.TRANSCRIBED_TEXT)

        # Debería devolver resultados vacíos (no crash)
        assert isinstance(results, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
