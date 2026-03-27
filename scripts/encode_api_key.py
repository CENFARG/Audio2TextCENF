import base64
import sys

def encode_key(api_key):
    xor_key = "CENF_SECRET"
    # XOR each character
    xor_result = bytes([ord(api_key[i]) ^ ord(xor_key[i % len(xor_key)]) for i in range(len(api_key))])
    # Base64 encode
    encoded_key = base64.b64encode(xor_result).decode('utf-8')
    return encoded_key

def decode_key(encoded_key):
    xor_key = "CENF_SECRET"
    decoded_bytes = base64.b64decode(encoded_key)
    result = "".join(chr(b ^ ord(xor_key[i % len(xor_key)])) for i, b in enumerate(decoded_bytes))
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python encode_api_key.py <TU_API_KEY>")
        sys.exit(1)
    
    key = sys.argv[1]
    encoded = encode_key(key)
    print(f"\nAPI Key Original: {key}")
    print(f"API Key Codificada: {encoded}")
    print(f"\nCopia este valor en tu config.json bajo la clave 'gift_key_encoded'")
    
    # Verificación
    decoded = decode_key(encoded)
    if decoded == key:
        print("\n✅ Verificación exitosa: La clave se decodifica correctamente.")
    else:
        print("\n❌ Error: La verificación de decodificación falló.")
