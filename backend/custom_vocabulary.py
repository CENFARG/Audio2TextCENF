"""
Custom Vocabulary - Corrección de palabras mal entendidas

Permite agregar palabras que el modelo de transcripción tiende a entender mal,
como "CENF" que se transcribe como "zenf", "cemp", "cemf", etc.

Author: Audio2Text Development Team
Version: 0.11.0
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class CustomVocabulary:
    """
    Gestor de vocabulario personalizado para correcciones.

    Permite definir correcciones para palabras que el modelo entiende mal.
    """

    def __init__(self, vocab_path: str = "backend/vocabulary/custom_corrections.json"):
        """
        Inicializar gestor de vocabulario personalizado.

        Args:
            vocab_path: Ruta al archivo de correcciones
        """
        self.vocab_path = Path(vocab_path)
        self.corrections: Dict[str, str] = {}
        self._load_vocab()

    def _load_vocab(self):
        """Cargar correcciones desde archivo."""
        if self.vocab_path.exists():
            try:
                with open(self.vocab_path, 'r', encoding='utf-8') as f:
                    self.corrections = json.load(f)
                logger.info(f"Correcciones cargadas: {len(self.corrections)} términos")
            except Exception as e:
                logger.error(f"Error cargando correcciones: {e}")
                self.corrections = {}
        else:
            # Crear con ejemplos por defecto
            self.corrections = {
                "zenf": "CENF",
                "cemp": "CENF",
                "cemf": "CENF",
                "senf": "CENF",
                "gro": "Groq",
                "grog": "Groq"
            }
            self._save_vocab()

    def _save_vocab(self):
        """Guardar correcciones a archivo."""
        try:
            self.vocab_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.vocab_path, 'w', encoding='utf-8') as f:
                json.dump(self.corrections, f, indent=4, ensure_ascii=False)
            logger.info(f"Correcciones guardadas: {len(self.corrections)} términos")
        except Exception as e:
            logger.error(f"Error guardando correcciones: {e}")

    def add_correction(self, incorrect: str, correct: str) -> bool:
        """
        Agregar corrección al vocabulario.

        Args:
            incorrect: Palabra incorrecta que el modelo usa
            correct: Palabra correcta que debería ser

        Returns:
            True si se agregó exitosamente
        """
        try:
            self.corrections[incorrect.lower()] = correct
            self._save_vocab()
            logger.info(f"Corrección agregada: '{incorrect}' → '{correct}'")
            return True
        except Exception as e:
            logger.error(f"Error agregando corrección: {e}")
            return False

    def remove_correction(self, incorrect: str) -> bool:
        """
        Eliminar corrección del vocabulario.

        Args:
            incorrect: Palabra incorrecta a remover

        Returns:
            True si se eliminó exitosamente
        """
        try:
            if incorrect.lower() in self.corrections:
                del self.corrections[incorrect.lower()]
                self._save_vocab()
                logger.info(f"Corrección eliminada: '{incorrect}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando corrección: {e}")
            return False

    def get_corrections(self) -> Dict[str, str]:
        """Obtener todas las correcciones."""
        return self.corrections.copy()

    def apply_corrections(self, text: str) -> str:
        """
        Aplicar correcciones a un texto.

        Args:
            text: Texto a corregir

        Returns:
            Texto con correcciones aplicadas
        """
        if not text or not self.corrections:
            return text

        corrected_text = text
        corrections_applied = []

        for incorrect, correct in self.corrections.items():
            # Buscar y reemplazar la palabra incorrecta
            # Usamos word boundaries para no reemplazar dentro de otras palabras
            import re

            # Crear patrón con word boundary
            pattern = r'\b' + re.escape(incorrect) + r'\b'

            # Buscar todas las ocurrencias (case-insensitive)
            matches = list(re.finditer(pattern, corrected_text, re.IGNORECASE))

            if matches:
                # Procesar cada ocurrencia individualmente para preservar caso
                # Procesar de derecha a izquierda para no afectar los índices
                for match in reversed(matches):
                    matched_text = match.group()
                    start, end = match.span()

                    # Determinar el caso correcto
                    if matched_text.isupper():
                        replacement = correct.upper()
                    elif matched_text[0].isupper():
                        replacement = correct.capitalize()
                    else:
                        replacement = correct.lower()

                    # Reemplazar solo esta ocurrencia
                    corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
                    corrections_applied.append(f"{matched_text} → {replacement}")

        if corrections_applied:
            logger.info(f"Correcciones aplicadas: {corrections_applied}")

        return corrected_text

    def get_whisper_prompt(self) -> str:
        """
        Generar un prompt para Whisper con las palabras correctas.

        Whisper usa el prompt para mejorar la transcripción de palabras específicas.
        Incluimos las palabras CORRECTAS (no las incorrectas) para ayudar al modelo.

        Returns:
            String con palabras correctas separadas por comas
        """
        if not self.corrections:
            return ""

        # Obtener palabras únicas correctas
        correct_words = set(self.corrections.values())

        # Crear prompt contextual
        # Whisper funciona mejor con frases contextuales
        prompts = []
        for word in correct_words:
            if word == "CENF":
                prompts.append("CENF es una empresa de tecnología")
            elif word == "Groq":
                prompts.append("Groq es una plataforma de inferencia AI")
            else:
                prompts.append(word)

        return ". ".join(prompts) + "."

    def get_stats(self) -> Dict[str, any]:
        """Obtener estadísticas del vocabulario."""
        return {
            'total_corrections': len(self.corrections),
            'corrections': self.corrections.copy()
        }
