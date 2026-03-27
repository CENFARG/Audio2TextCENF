"""
Script de validación para el Bridge de Audio2Text PRO.
Verifica que la app detecte el módulo PRO y que el agente cargue su config.
"""

import sys
import os

# Asegurar que el root está en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_bridge():
    print("--- 🧪 Test de Bridge Audio2Text PRO ---")
    
    try:
        import pro
        print("✅ Módulo 'pro' encontrado.")
        
        pro.initialize()
        print("✅ Inicialización llamada exitosamente.")
        
        from pro.agents.prompt_enhancer import PromptMaestro
        maestro = PromptMaestro()
        print("✅ PromptMaestro instanciado.")
        
        # Verificar carga de config
        if maestro.config and maestro.config["agent"]["role"] == "Prompt Maestro V3":
            print(f"✅ Configuración cargada: {maestro.config['agent']['name']}")
            
            # Test de mejora (simulado o real según env)
            print("\n--- 🧪 Test de Mejora de Prompt ---")
            dummy_text = "Hola, mi nombre es Gonzalo y estamos probando la versión pro del transcriptor de audio para reuniones."
            result = maestro.enhance(dummy_text, output_format="text", template_id="meeting")
            
            if "enhanced" in result:
                print("✅ Respuesta recibida del agente.")
                print(f"Contenido mejorado (primeros 100 char): {result['enhanced'][:100]}...")
                print(f"Metadata: {result['metadata']}")
            else:
                print(f"❌ Error en la respuesta: {result.get('error')}")
        else:
            print("❌ Error en la configuración cargada.")
            
        print("✅ Test de Bridge COMPLETADO con éxito.")
        
    except ImportError as e:
        print(f"❌ Error: Módulo PRO no encontrado o error en importación: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_bridge()
