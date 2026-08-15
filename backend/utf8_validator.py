# -*- coding: utf-8 -*-
"""
Módulo de Validación y Corrección de Encoding UTF-8.

Este módulo se encarga de validar y corregir problemas de encoding
que causan bloqueos o caracteres incorrectos en transcripciones de audio.

Author: Audio2Text Team
Version: 0.15.0
"""

import logging
import re
from typing import Optional, Tuple, List

# Caracteres problemáticos comunes
MALFORMED_CHARS = {
    "´": "á",
    "`": "é",
    "ã": "ã",
    "õ": "õ",
    "ñ": "ñ",
}

# Caracteres españoles correctos (mapa para corrección)
SPANISH_CHARS = {
    "a": "á",
    "e": "é",
    "i": "í",
    "o": "ó",
    "u": "ú",
    "n": "ñ",
    "A": "Á",
    "E": "É",
    "I": "Í",
    "O": "Ó",
    "U": "Ú",
    "N": "Ñ",
    "¿": "¿",
    "¡": "¡",
    "«": "«",
    "»": "»",
}

# FIX Bug B: patrones reales de mojibake (doble-encoding UTF-8 → latin-1)
# Texto con acentos leído como latin-1 produce estos pares de caracteres.
MOJIBAKE_MAP = {
    "Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú",
    "Ã": "Á", "Ã‰": "É", "Ã": "Í", "Ã“": "Ó", "Ãš": "Ú",
    "Ã±": "ñ", "Ã‘": "Ñ",
    "Â¿": "¿", "Â¡": "¡",
    "Ã¼": "ü", "Ã¶": "ö", "Ã¤": "ä", "Ã«": "ë", "Ã¯": "ï", "Ã¶": "ö",
    "Â«": "«", "Â»": "»", "â€": "€", "â€œ": "“", "â€�": "”", "â€˜": "‘", "â€™": "’",
    "â€“": "–", "â€”": "—", "â€¦": "…",
}


class UTF8Validator:
    """
    Validador y corrector de encoding UTF-8.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializar validador.

        Args:
            logger: Logger opcional para logging
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def validate_encoding(self, text: str) -> Tuple[bool, List[str]]:
        """
        Validar encoding de un texto.

        FIX Bug B: la versión anterior era una TAUTOLOGÍA — codificar y
        decodificar en UTF-8 siempre devuelve el mismo string (round-trip
        sin pérdida), por lo que NUNCA detectaba mojibake y el texto
        quedaba corrupto. Ahora se detectan patrones reales de doble-encoding.

        Args:
            text: Texto a validar

        Returns:
            Tuple con (es_valido, lista de problemas encontrados)
        """
        problems = []

        # FIX: detección real de mojibake (patrones de doble-encoding)
        for bad in MOJIBAKE_MAP:
            if bad in text:
                problems.append(f"mojibake: {bad} -> {MOJIBAKE_MAP[bad]}")

        # BOM al inicio
        if text.startswith('\ufeff'):
            problems.append("bom_present")

        # Caracteres de control problemáticos
        if '\x00' in text:
            problems.append("null_bytes")

        return (len(problems) == 0, problems)

    def normalize_spanish_chars(self, text: str) -> str:
        """
        Normalizar caracteres españoles (tildes, ñ, signos).

        Args:
            text: Texto a normalizar

        Returns:
            Texto con caracteres normalizados
        """
        result = text

        # FIX Bug B: corregir mojibake REAL (doble-encoding UTF-8 → latin-1)
        # Debe ir ANTES de la corrección de caracteres individuales
        for bad, correct in MOJIBAKE_MAP.items():
            result = result.replace(bad, correct)

        # Corregir combinaciones incorrectas
        for malformed, correct in MALFORMED_CHARS.items():
            result = result.replace(malformed, correct)

        # Corregir signos interrogación/exclamación
        result = result.replace("¿¿", "¿")
        # Corregir signos exclamación
        result = result.replace("¡¡", "¡")

        # Corregir comillas simples por dobles o curvas
        result = result.replace("simple", "simple")
        # Corregir "curly" por "curly"
        result = result.replace("angled", "angled")

        self.logger.debug(f"Caracteres normalizados: {text[:50]}")

        return result

    def force_utf8(self, text: str, encoding: str = 'utf-8') -> str:
        """
        Forzar encoding UTF-8 de un texto.

        Args:
            text: Texto a codificar
            encoding: Encoding a usar (default: utf-8)

        Returns:
            Texto codificado en UTF-8
        """
        try:
            # Codificar texto
            encoded = text.encode(encoding)

            # Decodificar para obtener string limpio
            result = encoded.decode(encoding)

            self.logger.debug(f"Texto forzado a UTF-8: {text[:50]}")

            return result

        except UnicodeEncodeError as e:
            self.logger.error(f"Error codificando a {encoding}: {e}")
            # Fallback: limpiar artefactos
            return self.clean_encoding_artifacts(text)

        except UnicodeDecodeError as e:
            self.logger.error(f"Error decodificando de {encoding}: {e}")
            # Fallback: limpiar artefactos
            return self.clean_encoding_artifacts(text)

    def clean_encoding_artifacts(self, text: str) -> str:
        """
        Limpiar artefactos de encoding (BOM, caracteres nulos, etc.).

        Args:
            text: Texto a limpiar

        Returns:
            Texto limpio sin artefactos
        """
        result = text

        # FIX Bug C: el BOM es UN carácter (\ufeff = U+FEFF), no 3.
        # La versión anterior hacía result[3:] que se comía 3 caracteres REALES del texto.
        if result.startswith('\ufeff'):
            result = result[1:]
            self.logger.debug("BOM removido del inicio")

        # Remover caracteres nulos y otros caracteres de control
        control_chars = ['\\x00', '\\x01', '\\x02', '\\x03', '\\x04', '\\x05', '\\x06',
                        '\\x07', '\\x08', '\\x09', '\\x0b', '\\x0c',
                        '\\x0d', '\\x0e', '\\x0f',
                        '\\u200b', '\\u200c', '\\u200d', '\\u200e',
                        '\\u200f', '\\u202a', '\\u202c', '\\u202d', '\\u202e',
                        '\\u202f', '\\u203a', '\\u203c', '\\u203d',
                        '\\u203e', '\\u203f', '\\u204a', '\\u204c',
                        '\\u204d', '\\u204e', '\\u204e', '\\u204f',
                        '\\u205a', '\\u205c', '\\u205d', '\\u205e',
                        '\\u205e', '\\u205f', '\\u206a', '\\u206c',
                        '\\u206d', '\\u206e', '\\u206e', '\\u206e',
                        '\\u207a', '\\u207c', '\\u207d', '\\u207e',
                        '\\u207e', '\\u207f', '\\u208a', '\\u208c',
                        '\\u208d', '\\u208e', '\\u208f',
                        '\\u209a', '\\u209a', '\\u209c',
                        '\\u209d', '\\u209e', '\\u209e',
                        '\\u209f', '\\u20a', '\\u20c', '\\u20d',
                        '\\u20e', '\\u20f', '\\u210a',
                        '\\u210a', '\\u210c', '\\u210d', '\\u210e',
                        '\\u210e', '\\u210e', '\\u210f',
                        '\\u211a', '\\u211c', '\\u211d', '\\u211e',
                        '\\u211e', '\\u211f', '\\u212a', '\\u212a',
                        '\\u212d', '\\u212e', '\\u212f']

        for char in control_chars:
            result = result.replace(char, '')

        # Limpiar espacios múltiples consecutivos
        result = re.sub(r' {2,}', ' ', result)

        # Limpiar saltos de línea innecesarios
        result = result.rstrip()

        self.logger.debug("Artefactos de encoding limpiados")

        return result

    def normalize_transcription(self, text: str, normalize: bool = True) -> str:
        """
        Normalizar una transcripción de audio para español.

        Proceso:
        1. Limpiar artefactos de encoding
        2. Normalizar caracteres españoles si está activado
        3. Forzar UTF-8

        Args:
            text: Texto de transcripción a normalizar
            normalize: Si True, aplica normalización de caracteres

        Returns:
            Texto normalizado
        """
        if not text or not text.strip():
            return text

        # Paso 1: Limpiar artefactos
        result = self.clean_encoding_artifacts(text)

        # Paso 2: Normalizar caracteres españoles si está activado
        if normalize:
            result = self.normalize_spanish_chars(result)

        # Paso 3: Forzar UTF-8
        is_valid, problems = self.validate_encoding(result)
        if not is_valid:
            self.logger.warning(f"Texto no válido como UTF-8: {problems}")
            result = self.force_utf8(result)
        else:
            # Aplicar force_utf8 para asegurar consistencia
            result = self.force_utf8(result)

        return result

    def validate_transcription(self, text: str) -> Tuple[bool, List[str]]:
        """
        Validar que una transcripción no tenga problemas de encoding.

        Args:
            text: Texto de transcripción a validar

        Returns:
            Tuple con (es_válido, lista de problemas)
        """
        is_valid, problems = self.validate_encoding(text)

        if is_valid:
            # Validar caracteres problemáticos adicionales
            for malformed in MALFORMED_CHARS.keys():
                if malformed in text:
                    problems.append(f"caracter_malformado: {malformed}")

            if is_valid and len(problems) == 0:
                self.logger.debug("Transcripción válida")
            else:
                self.logger.warning(f"Problemas de validación: {problems}")

        return (is_valid, problems)

    def get_encoding_report(self, text: str) -> dict:
        """
        Generar reporte de encoding de un texto.

        Args:
            text: Texto a analizar

        Returns:
            Diccionario con información de encoding
        """
        is_valid, problems = self.validate_encoding(text)

        return {
            "valid": is_valid,
            "encoding": "utf-8",
            "problems": problems,
            "length": len(text),
            "preview": text[:100] + "..." if len(text) > 100 else text
        }


# Funciones de conveniencia para uso rápido

def create_validator(logger: Optional[logging.Logger] = None) -> UTF8Validator:
    """
    Crear instancia de UTF8Validator.

    Args:
        logger: Logger opcional

    Returns:
        Instancia de UTF8Validator
    """
    return UTF8Validator(logger=logger)


def normalize_text(text: str, normalize: bool = True) -> str:
    """
    Normalizar texto para español.

    Args:
        text: Texto a normalizar
        normalize: Si True, aplica normalización de caracteres

    Returns:
        Texto normalizado
    """
    validator = create_validator()
    return validator.normalize_transcription(text, normalize=normalize)


def validate_text(text: str) -> Tuple[bool, List[str]]:
    """
    Validar texto de transcripción.

    Args:
        text: Texto a validar

    Returns:
        Tuple con (es_válido, lista de problemas)
    """
    validator = create_validator()
    return validator.validate_transcription(text)
