"""
Summary Block - Genera resúmenes ejecutivos de transcripciones

Crea resúmenes concisos manteniendo los puntos clave de la transcripción.

Author: Audio2Text Development Team
Version: 0.11.0 (development)
"""

import re
from typing import Dict, Any, Optional, List
import logging

from .base_block import BaseBlock, BlockType, ProcessingStage, BlockResult

logger = logging.getLogger(__name__)


class SummaryBlock(BaseBlock):
    """
    Bloque para generar resúmenes ejecutivos de transcripciones.

    Estrategias:
    - Extracción de oraciones clave
    - Eliminación de redundancias
    - Mantener contexto y coherencia
    - Limitar longitud objetivo
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializar bloque generador de resúmenes.

        Configuración opcional:
            - max_sentences (int): Máximo número de oraciones (default=3)
            - max_length (int): Longitud máxima en caracteres (default=300)
            - include_keywords (bool): Incluir palabras clave (default=True)
            - strategy (str): 'extractive' o 'abstractive' (default='extractive')
        """
        super().__init__(
            name="summary",
            description="Genera resúmenes ejecutivos de transcripciones",
            block_type=BlockType.POST_TRANSCRIPTION,
            enabled=True,
            config=config or {}
        )

        # Configuración con defaults
        self.max_sentences = self.get_config('max_sentences', 3)
        self.max_length = self.get_config('max_length', 300)
        self.include_keywords = self.get_config('include_keywords', True)
        self.strategy = self.get_config('strategy', 'extractive')

    def validate_input(self, data: Any, stage: ProcessingStage) -> bool:
        """Validar que el input sea texto transcriptible."""
        if not isinstance(data, str):
            logger.warning(f"SummaryBlock: Input debe ser string, got {type(data)}")
            return False

        if len(data.strip()) < 50:
            logger.warning("SummaryBlock: Input demasiado corto para resumir")
            return False

        return True

    def process(self, data: str, stage: ProcessingStage) -> BlockResult:
        """
        Procesar transcripción y generar resumen.

        Args:
            data: Texto transcrito
            stage: Etapa de procesamiento

        Returns:
            BlockResult con resumen generado
        """
        try:
            # Validar input
            if not self.validate_input(data, stage):
                return BlockResult(
                    success=False,
                    data="",
                    error="Input inválido o demasiado corto"
                )

            # Generar resumen según estrategia
            if self.strategy == 'extractive':
                summary = self._extractive_summary(data)
            else:
                # Por ahora, usar extractive como fallback
                summary = self._extractive_summary(data)

            # Extraer palabras clave si está configurado
            keywords = []
            if self.include_keywords:
                keywords = self._extract_keywords(data)

            # Actualizar estadísticas
            self.stats['processed'] += 1

            logger.info(f"SummaryBlock: Resumen generado ({len(summary)} chars, {len(keywords)} keywords)")

            return BlockResult(
                success=True,
                data=summary,
                metadata={
                    'original_length': len(data),
                    'summary_length': len(summary),
                    'compression_ratio': len(summary) / len(data),
                    'keywords': keywords,
                    'strategy': self.strategy
                }
            )

        except Exception as e:
            logger.error(f"SummaryBlock: Error procesando: {e}")
            self.stats['failed'] += 1

            return BlockResult(
                success=False,
                data="",
                error=str(e)
            )

    def _extractive_summary(self, text: str) -> str:
        """
        Generar resumen extractivo (selecciona oraciones importantes).

        Args:
            text: Texto original

        Returns:
            Resumen generado
        """
        # Dividir en oraciones
        sentences = self._split_sentences(text)

        if len(sentences) <= self.max_sentences:
            # Texto ya es corto, devolver completo
            return self._truncate(text, self.max_length)

        # Puntuar oraciones por importancia
        scored_sentences = []
        for sentence in sentences:
            score = self._score_sentence(sentence, text)
            scored_sentences.append((sentence, score))

        # Ordenar por score y tomar top N
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:self.max_sentences]]

        # Mantener orden original
        summary = ' '.join(top_sentences)

        # Truncar si excede longitud máxima
        return self._truncate(summary, self.max_length)

    def _split_sentences(self, text: str) -> List[str]:
        """Dividir texto en oraciones."""
        # Reemplazar saltos de línea por espacios
        text = text.replace('\n', ' ')

        # Dividir por puntos, signos de interrogación/exclamación
        sentences = re.split(r'[.!?]+', text)

        # Limpiar y filtrar
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        return sentences

    def _score_sentence(self, sentence: str, full_text: str) -> float:
        """
        Calcular importancia de una oración.

        Factores:
        - Longitud (oraciones muy cortas o muy largas penalizan)
        - Posición (primeras oraciones más importantes)
        - Palabras clave (términos importantes aumentan score)
        """
        score = 0.0

        # Longitud óptima: 10-30 palabras
        word_count = len(sentence.split())
        if 10 <= word_count <= 30:
            score += 1.0
        elif word_count < 10:
            score -= 0.5
        else:
            score -= 0.2 * (word_count - 30) / 10

        # Posición en el texto (primeras oraciones más importantes)
        position = full_text.find(sentence) / len(full_text)
        if position < 0.3:  # Primer 30% del texto
            score += 1.0
        elif position < 0.6:  # Primer 60% del texto
            score += 0.5

        # Palabras clave importantes
        important_words = [
            'importante', 'crítico', 'clave', 'principal', 'fundamental',
            'conclusión', 'resumen', 'por lo tanto', 'en conclusión',
            'decisión', 'acordó', 'definió', 'estableció'
        ]

        sentence_lower = sentence.lower()
        for word in important_words:
            if word in sentence_lower:
                score += 0.5

        return score

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncar texto manteniendo palabras completas."""
        if len(text) <= max_length:
            return text

        # Buscar último espacio completo antes del límite
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')

        if last_space > max_length * 0.8:  # Si el espacio está en el 80%+
            truncated = truncated[:last_space]

        return truncated + '...'

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extraer palabras clave del texto."""
        # Palabras vacías a ignorar
        stopwords = {
            'el', 'la', 'de', 'en', 'que', 'y', 'a', 'los', 'se', 'del',
            'las', 'un', 'por', 'con', 'una', 'su', 'para', 'es', 'al',
            'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'fue'
        }

        # Tokenizar y contar frecuencias
        words = re.findall(r'\b[a-záéíóúñ]{4,}\b', text.lower())

        # Filtrar stopwords y contar
        word_freq = {}
        for word in words:
            if word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Ordenar por frecuencia y tomar top N
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]

        return keywords
