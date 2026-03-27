from pro.agents.prompt_enhancer import PromptMaestro
import os

# Ensure API Key is present for the test
if not os.getenv("OPENROUTER_API_KEY"):
    print("WARNING: OPENROUTER_API_KEY not found. Test might fail auth but should run.")

try:
    print("Instantiating PromptMaestro...")
    m = PromptMaestro()
    print("Enhancing...")
    res = m.enhance("Esto es una prueba de transcripción para ver si el agente responde.", output_format="text")
    print(f"Result: {res}")
except Exception as e:
    print(f"CRASH: {e}")
