"""
Vocabulary Extractor - Agente para extracción automática de vocabulario

Detecta palabras técnicas y términos específicos en transcripciones
y permite agregarlas al vocabulario personalizado.

Author: Audio2Text Development Team
Version: 0.11.0 (development)
"""

import json
import re
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VocabularyExtractor:
    """
    Agente extractor de vocabulario técnico.

    Responsabilidades:
    - Detectar palabras técnicas en transcripciones
    - Marcar términos para agregar a vocabulario
    - Permitir corrección manual
    - Guardar en backend/vocabulary/custom.json
    """

    def __init__(self, custom_vocab_path: str = "backend/vocabulary/custom.json"):
        """
        Inicializar extractor de vocabulario.

        Args:
            custom_vocab_path: Ruta al vocabulario personalizado
        """
        self.custom_vocab_path = Path(custom_vocab_path)
        self.custom_vocab: Dict[str, Any] = {}
        self.detected_terms: Set[str] = set()

        self._load_custom_vocab()

    def _load_custom_vocab(self):
        """Cargar vocabulario personalizado existente."""
        if self.custom_vocab_path.exists():
            try:
                with open(self.custom_vocab_path, 'r', encoding='utf-8') as f:
                    self.custom_vocab = json.load(f)
                logger.info(f"Vocabulario personalizado cargado: {len(self.custom_vocab)} términos")
            except Exception as e:
                logger.error(f"Error cargando vocabulario personalizado: {e}")
                self.custom_vocab = {}
        else:
            # Crear archivo vacío si no existe
            self.custom_vocab = {}
            self._save_custom_vocab()

    def _save_custom_vocab(self):
        """Guardar vocabulario personalizado."""
        try:
            self.custom_vocab_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.custom_vocab_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_vocab, f, indent=4, ensure_ascii=False)
            logger.info(f"Vocabulario personalizado guardado: {len(self.custom_vocab)} términos")
        except Exception as e:
            logger.error(f"Error guardando vocabulario personalizado: {e}")

    def extract_technical_terms(self, text: str) -> List[Dict[str, Any]]:
        """
        Extraer términos técnicos del texto.

        Args:
            text: Transcripción a analizar

        Returns:
            Lista de términos detectados con metadatos
        """
        detected = []

        # 1. Cargar vocabularios de referencia
        existing_terms = self._get_existing_terms()

        # 2. Detectar patrones técnicos
        technical_patterns = [
            # Acrónimos en mayúsculas (2+ letras)
            r'\b[A-Z]{2,}\b',
            # Palabras con CamelCase
            r'\b[a-z]+[A-Z][a-z]+\b',
            # Términos con guiones
            r'\b[a-z]+-[a-z]+\b',
            # Palabras seguidas de números
            r'\b[a-z]+\d+\b',
        ]

        for pattern in technical_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                term = match.group(0)
                term_lower = term.lower()

                # Filtrar términos comunes
                if self._is_common_term(term):
                    continue

                # Si ya está en vocabulario, skip
                if term_lower in existing_terms:
                    continue

                # Agregar a detected si no está ya
                if term_lower not in self.detected_terms:
                    self.detected_terms.add(term_lower)

                    detected.append({
                        'term': term,
                        'context': self._get_context(text, match.start()),
                        'frequency': text.lower().count(term_lower),
                        'type': self._classify_term(term),
                        'suggested': True
                    })

        logger.info(f"Detectados {len(detected)} términos técnicos")
        return detected

    def _get_existing_terms(self) -> Set[str]:
        """Obtener todos los términos de vocabularios existentes."""
        existing = set()

        # Cargar vocabularios de referencia
        vocab_paths = [
            'backend/vocabulary/ia_tech.json',
            'backend/vocabulary/general.json',
            str(self.custom_vocab_path)
        ]

        for vocab_path in vocab_paths:
            if Path(vocab_path).exists():
                try:
                    with open(vocab_path, 'r', encoding='utf-8') as f:
                        vocab = json.load(f)
                        existing.update(vocab.keys())
                except Exception as e:
                    logger.warning(f"Error cargando {vocab_path}: {e}")

        return existing

    def _is_common_term(self, term: str) -> bool:
        """Verificar si es un término común (no técnico)."""
        common_terms = {
            'el', 'la', 'de', 'en', 'que', 'y', 'a', 'los', 'se',
            'del', 'las', 'un', 'por', 'con', 'una', 'su', 'para',
            'es', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le',
            'ya', 'o', 'fue', 'este', 'esta', 'esto', 'estos',
            'esta', 'ese', 'esa', 'eso', 'esos', 'esas'
        }

        return term.lower() in common_terms

    def _get_context(self, text: str, position: int, window: int = 30) -> str:
        """
        Obtener contexto alrededor de un término.

        Args:
            text: Texto completo
            position: Posición del término
            window: Ventana de caracteres alrededor

        Returns:
            Contexto del término
        """
        start = max(0, position - window)
        end = min(len(text), position + len(text) - position + window)
        return text[start:end]

    def _classify_term(self, term: str) -> str:
        """Clasificar término por tipo."""
        # Acrónimo (todo mayúsculas)
        if term.isupper() and len(term) >= 2:
            return 'acronym'

        # CamelCase
        if any(c.isupper() for c in term[1:-1]):
            return 'camel_case'

        # Con guiones
        if '-' in term:
            return 'hyphenated'

        # Con números
        if any(c.isdigit() for c in term):
            return 'with_number'

        # Palabra técnica (default)
        return 'technical'

    def add_to_custom_vocab(
        self,
        term: str,
        definition: str = "",
        category: str = "general"
    ) -> bool:
        """
        Agregar término al vocabulario personalizado.

        Args:
            term: Término a agregar
            definition: Definición del término
            category: Categoría del término

        Returns:
            True si se agregó exitosamente
        """
        try:
            term_lower = term.lower()

            self.custom_vocab[term_lower] = {
                'term': term,
                'definition': definition,
                'category': category,
                'added_at': None  # TODO: Agregar timestamp
            }

            self._save_custom_vocab()
            logger.info(f"Término agregado: {term}")

            return True

        except Exception as e:
            logger.error(f"Error agregando término '{term}': {e}")
            return False

    def remove_from_custom_vocab(self, term: str) -> bool:
        """
        Eliminar término del vocabulario personalizado.

        Args:
            term: Término a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        try:
            term_lower = term.lower()

            if term_lower in self.custom_vocab:
                del self.custom_vocab[term_lower]
                self._save_custom_vocab()
                logger.info(f"Término eliminado: {term}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error eliminando término '{term}': {e}")
            return False

    def get_custom_vocab(self) -> Dict[str, Any]:
        """Obtener vocabulario personalizado completo."""
        return self.custom_vocab.copy()

    def export_custom_vocab(self, export_path: str) -> bool:
        """
        Exportar vocabulario personalizado a archivo.

        Args:
            export_path: Ruta del archivo de exportación

        Returns:
            True si se exportó exitosamente
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_vocab, f, indent=4, ensure_ascii=False)
            logger.info(f"Vocabulario exportado a {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exportando vocabulario: {e}")
            return False

    def import_custom_vocab(self, import_path: str, merge: bool = True) -> bool:
        """
        Importar vocabulario desde archivo.

        Args:
            import_path: Ruta del archivo a importar
            merge: Si True, mezcla con vocabulario existente

        Returns:
            True si se importó exitosamente
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_vocab = json.load(f)

            if merge:
                self.custom_vocab.update(imported_vocab)
            else:
                self.custom_vocab = imported_vocab

            self._save_custom_vocab()
            logger.info(f"Vocabulario importado desde {import_path}")
            return True

        except Exception as e:
            logger.error(f"Error importando vocabulario: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del vocabulario.

        Returns:
            Diccionario con estadísticas
        """
        categories = {}
        for term_data in self.custom_vocab.values():
            cat = term_data.get('category', 'general')
            categories[cat] = categories.get(cat, 0) + 1

        return {
            'total_terms': len(self.custom_vocab),
            'categories': categories,
            'detected_in_session': len(self.detected_terms)
        }
