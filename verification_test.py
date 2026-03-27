"""
Verificación de ConfigManager - Test de integridad.

Este script NO contiene API keys harcoded.
Usa variables de entorno o placeholders para testing.
"""
import sys
import os
from backend.config_manager import ConfigManager

def test_config_manager():
    print("Iniciando verificación de ConfigManager...")

    # Crear un config temporal para no ensuciar
    test_config_path = "test_config_v094.json"
    if os.path.exists(test_config_path):
        os.remove(test_config_path)

    cm = ConfigManager(config_file=test_config_path)

    # 1. Verificar Versión
    version = cm.get("app_version")
    print(f"Versión detectada: {version}")
    if version == "0.12.0":
        print("✅ Versión correcta.")
    else:
        print(f"⚠️ Versión: {version}")

    # 2. Verificar lógica de Gift Key
    import base64

    def encode(key):
        """Codificar una key usando XOR + Base64."""
        xor_key = "CENF_SECRET"
        xor_result = bytes([ord(key[i]) ^ ord(xor_key[i % len(xor_key)]) for i in range(len(key))])
        return base64.b64encode(xor_result).decode('utf-8')

    # Usar un placeholder, NO una API key real
    test_key = "gsk_PLACEHOLDER_TEST_KEY_DO_NOT_USE"
    encoded_test_key = encode(test_key)
    cm.set("gift_key_encoded", encoded_test_key)

    # Simular que no hay key en config ni env
    cm.config["groq_api_key"] = ""
    os.environ.pop("GROQ_API_KEY", None)

    # Probar recuperación de gift key
    retrieved_key = cm.get_groq_api_key_from_env()
    print(f"Key recuperada: {retrieved_key}")
    if retrieved_key == test_key:
        print("✅ Gift key decodificada correctamente.")
    else:
        print(f"⚠️ Key esperada: {test_key}")
        print(f"⚠️ Key obtenida: {retrieved_key}")

    # 3. Verificar faster-whisper config
    faster_whisper_enabled = cm.get("faster_whisper_enabled", False)
    print(f"faster-whisper habilitado: {faster_whisper_enabled}")

    faster_whisper_model = cm.get("faster_whisper_model", "base")
    print(f"Modelo faster-whisper: {faster_whisper_model}")

    # Limpieza
    if os.path.exists(test_config_path):
        os.remove(test_config_path)

    print("\n✅ Verificación finalizada.")
    print("NOTA: Este script usa placeholders. Para usar con API key real:")
    print("  export GROQ_API_KEY=gsk_tu_key_aqui")
    print("  python verification_test.py")

if __name__ == "__main__":
    test_config_manager()
