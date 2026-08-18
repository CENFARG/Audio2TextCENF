"""
Keyword Extractor Block - Extrae palabras clave de transcripciones

Identifica términos importantes y relevantes del texto transcrito.

Author: Audio2Text Development Team
Version: 0.11.0 (development)
"""

import re
from typing import Dict, Any, Optional, List, Tuple
import logging

from .base_block import BaseBlock, BlockType, ProcessingStage, BlockResult

logger = logging.getLogger(__name__)


class KeywordExtractorBlock(BaseBlock):
    """
    Bloque para extraer palabras clave de transcripciones.

    Estrategias:
    - Frecuencia de términos
    - TF-IDF simplificado
    - Entidades nombradas (nombres propios, fechas, números)
    - Términos técnicos del vocabulario
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializar bloque extractor de palabras clave.

        Configuración opcional:
            - max_keywords (int): Máximo número de palabras clave (default=10)
            - min_length (int): Longitud mínima de palabra (default=4)
            - include_numbers (bool): Incluir números (default=True)
            - include_entities (bool): Incluir entidades nombradas (default=True)
            - use_vocabulary (bool): Usar vocabulario técnico (default=True)
        """
        super().__init__(
            name="keyword_extractor",
            description="Extrae palabras clave de transcripciones",
            block_type=BlockType.POST_TRANSCRIPTION,
            enabled=True,
            config=config or {}
        )

        # Configuración con defaults
        self.max_keywords = self.get_config('max_keywords', 10)
        self.min_length = self.get_config('min_length', 4)
        self.include_numbers = self.get_config('include_numbers', True)
        self.include_entities = self.get_config('include_entities', True)
        self.use_vocabulary = self.get_config('use_vocabulary', True)

    def validate_input(self, data: Any, stage: ProcessingStage) -> bool:
        """Validar que el input sea texto."""
        if not isinstance(data, str):
            logger.warning(f"KeywordExtractor: Input debe ser string, got {type(data)}")
            return False

        if len(data.strip()) < 20:
            logger.warning("KeywordExtractor: Input demasiado corto")
            return False

        return True

    def process(self, data: str, stage: ProcessingStage) -> BlockResult:
        """
        Procesar transcripción y extraer palabras clave.

        Args:
            data: Texto transcrito
            stage: Etapa de procesamiento

        Returns:
            BlockResult con lista de palabras clave y metadatos
        """
        try:
            # Validar input
            if not self.validate_input(data, stage):
                return BlockResult(
                    success=False,
                    data=[],
                    error="Input inválido"
                )

            # Extraer palabras clave
            keywords = self._extract_keywords(data)

            # Ordenar por score y limitar
            keywords = sorted(keywords, key=lambda k: k['score'], reverse=True)
            keywords = keywords[:self.max_keywords]

            # Actualizar estadísticas
            self.stats['processed'] += 1

            logger.info(f"KeywordExtractor: Extraídas {len(keywords)} palabras clave")

            return BlockResult(
                success=True,
                data=keywords,
                metadata={
                    'total_keywords': len(keywords),
                    'unique_terms': len(set(k['keyword'] for k in keywords)),
                    'max_score': keywords[0]['score'] if keywords else 0
                }
            )

        except Exception as e:
            logger.error(f"KeywordExtractor: Error procesando: {e}")
            self.stats['failed'] += 1

            return BlockResult(
                success=False,
                data=[],
                error=str(e)
            )

    def _extract_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Extraer palabras clave usando múltiples estrategias."""
        keywords = {}

        # 1. Extracción por frecuencia
        freq_keywords = self._extract_by_frequency(text)
        for kw, score in freq_keywords:
            keywords[kw] = keywords.get(kw, 0) + score

        # 2. Extracción de entidades nombradas
        if self.include_entities:
            entities = self._extract_entities(text)
            for entity, score in entities:
                keywords[entity] = keywords.get(entity, 0) + score

        # 3. Extracción de vocabulario técnico
        if self.use_vocabulary:
            vocab_keywords = self._extract_vocabulary_terms(text)
            for kw, score in vocab_keywords:
                keywords[kw] = keywords.get(kw, 0) + score

        # 4. Extracción de números
        if self.include_numbers:
            numbers = self._extract_numbers(text)
            for num, score in numbers:
                keywords[num] = keywords.get(num, 0) + score

        # Convertir a lista de diccionarios
        return [
            {
                'keyword': kw,
                'score': score,
                'type': self._classify_keyword(kw)
            }
            for kw, score in keywords.items()
        ]

    def _extract_by_frequency(self, text: str) -> List[Tuple[str, float]]:
        """Extraer palabras por frecuencia (TF simplificado)."""
        # Stopwords en español
        stopwords = {
            'el', 'la', 'de', 'en', 'que', 'y', 'a', 'los', 'se', 'del',
            'las', 'un', 'por', 'con', 'una', 'su', 'para', 'es', 'al',
            'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'fue',
            'este', 'esta', 'esto', 'estos', 'estas', 'ese', 'esa', 'eso'
        }

        # Tokenizar
        words = re.findall(
            rf'\b[a-záéíóúñ]{{{self.min_length},}}\b',
            text.lower()
        )

        # Contar frecuencia
        freq = {}
        for word in words:
            if word not in stopwords:
                freq[word] = freq.get(word, 0) + 1

        # Normalizar scores (0-1)
        max_freq = max(freq.values()) if freq else 1
        normalized = [(word, count / max_freq) for word, count in freq.items()]

        # Filtrar por score mínimo
        return [(word, score) for word, score in normalized if score > 0.2]

    def _extract_entities(self, text: str) -> List[Tuple[str, float]]:
        """Extraer entidades nombradas (nombres propios, fechas, etc.)."""
        entities = []

        # Nombres propios (palabras que empiezan con mayúscula)
        proper_nouns = re.findall(r'\b[A-Z][a-záéíóúñ]+\b', text)
        for noun in set(proper_nouns):
            if len(noun) >= self.min_length:
                entities.append((noun, 0.8))

        # Fechas
        dates = re.findall(
            r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)(?:\s+de\s+\d{4})?)\b',
            text,
            re.IGNORECASE
        )
        for date in set(dates):
            entities.append((date, 0.7))

        # Horas
        times = re.findall(r'\b\d{1,2}:\d{2}(?:\s*(?:AM|PM|am|pm))?\b', text)
        for time in set(times):
            entities.append((time, 0.6))

        return entities

    def _extract_vocabulary_terms(self, text: str) -> List[Tuple[str, float]]:
        """Extraer términos del vocabulario técnico."""
        import json
        import os

        terms = []

        # Cargar vocabularios
        vocab_paths = [
            'backend/vocabulary/ia_tech.json',
            'backend/vocabulary/general.json'
        ]

        for vocab_path in vocab_paths:
            if not os.path.exists(vocab_path):
                continue

            try:
                with open(vocab_path, 'r', encoding='utf-8') as f:
                    vocab = json.load(f)

                # Buscar términos en el texto
                for term in vocab.keys():
                    if term.lower() in text.lower():
                        terms.append((term, 0.9))  # Score alto para vocabulario

            except Exception as e:
                logger.warning(f"Error cargando vocabulario {vocab_path}: {e}")

        return terms

    def _extract_numbers(self, text: str) -> List[Tuple[str, float]]:
        """Extraer números significativos."""
        numbers = []

        # Porcentajes
        percentages = re.findall(r'\b\d+(?:\.\d+)?%\b', text)
        for pct in set(percentages):
            numbers.append((pct, 0.7))

        # Cantidades con unidades
        quantities = re.findall(
            r'\b\d+(?:\.\d+)?\s*(?:USD|euros|dólares|pesos|KB|MB|GB|km|hs|horas)\b',
            text,
            re.IGNORECASE
        )
        for qty in set(quantities):
            numbers.append((qty, 0.8))

        # Números grandes (más de 3 dígitos)
        large_numbers = re.findall(r'\b\d{4,}\b', text)
        for num in set(large_numbers):
            numbers.append((num, 0.5))

        return numbers

    def _classify_keyword(self, keyword: str) -> str:
        """Clasificar palabra clave por tipo."""
        # Número
        if re.match(r'^\d+(?:\.\d+)?%?$', keyword):
            return 'number'

        # Fecha
        if re.search(r'(?:\d{1,2}[-/]\d{1,2}|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)', keyword, re.IGNORECASE):
            return 'date'

        # Hora
        if re.search(r'\d{1,2}:\d{2}', keyword):
            return 'time'

        # Moneda
        if re.search(r'(?:USD|euros|dólares|pesos)', keyword, re.IGNORECASE):
            return 'currency'

        # Nombre propio (empieza con mayúscula)
        if keyword[0].isupper() and keyword[1:].islower():
            return 'proper_noun'

        # Término técnico (contiene mayúsculas en medio)
        if any(c.isupper() for c in keyword[1:-1]):
            return 'technical'

        # Palabra común
        return 'common'
