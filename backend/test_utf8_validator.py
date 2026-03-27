"""
Test simplificado del módulo UTF8Validator.

Author: Audio2Text Team
Version: 0.10.0
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utf8_validator import UTF8Validator, normalize_text, validate_text


def test_basic_validation():
    print("\n=== TEST 1: Validación básica ===\n")

    validator = UTF8Validator()

    test_texts = [
        "Hola mundo",
        "Mi nombre es Juan",
        "¿Cómo estás?",
        "¡Está listo!",
        "El niño tiene 5 años",
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"{i}. '{text}'")
        is_valid, problems = validate_text(text)
        print(f"   Válido: {is_valid}")
        if problems:
            print(f"   Problemas: {', '.join(problems)}")
        print()


def test_spanish_normalization():
    print("\n=== TEST 2: Normalización de caracteres españoles ===\n")

    test_cases = [
        ("Tildes", "tildes: á, é, í, ó, ú, ñ"),
        ("Signos", "signos: ¿ ¡"),
    ]

    for test_name, test_input in test_cases:
        print(f"{test_name}: {test_input}")
        normalized = normalize_text(test_input)
        print(f"  Salida: {normalized}")
        print()


def test_force_utf8():
    print("\n=== TEST 3: Forzar UTF-8 ===\n")

    validator = UTF8Validator()

    test_cases = [
        "Hola mundo",
        "El niño tiene 5 años",
        "Por favor, revisen el documento",
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"{i}. '{text}'")
        try:
            result = validator.force_utf8(text)
            print(f"   Resultado: {result}")
            print()
        except Exception as e:
            print(f"   Error: {e}")


def main():
    print("=== Iniciando tests de UTF8Validator ===\n")
    test_basic_validation()
    test_spanish_normalization()
    test_force_utf8()
    print("\n=== Tests completados ===\n")


if __name__ == "__main__":
    main()
