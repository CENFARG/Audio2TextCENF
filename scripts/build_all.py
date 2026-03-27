# Master Build Script - Audio2Text v0.10.0
# Compila todas las variantes: GENERAL, CONTRERAS, CUTIGNOLA

import subprocess
import sys
from pathlib import Path

print("\n======================================================================")
print(f"Audio2Text v0.10.0 - Master Build")
print(f"======================================================================\n")

variants = ["GENERAL", "CONTRERAS", "CUTIGNOLA"]
results = {}

for variant in variants:
    print(f"\n──────────────────────────────────────────────────────────────────────")
    print(f"Compilando variante: {variant}")
    print(f"──────────────────────────────────────────────────────────────────────")
    
    result = subprocess.run([sys.executable, f"build_{variant}.py"])
    results[variant] = result.returncode == 0

print(f"\n======================================================================")
print("RESUMEN DE COMPILACIONES")
print(f"======================================================================\n")

for variant, success in results.items():
    status = "✅ EXITOSO" if success else "❌ FALLIDO"
    print(f"  {variant:15} : {status}")

all_success = all(results.values())
print(f"\n──────────────────────────────────────────────────────────────────────")
if all_success:
    print("🎉 ¡Todas las variantes compiladas exitosamente!")
    print(f"\nEjecutables en: dist/")
    print(f"  - Audio2Text_CENF_0.10.0_GENERAL.exe")
    print(f"  - Audio2Text_CENF_0.10.0_CONTRERAS.exe")
    print(f"  - Audio2Text_CENF_0.10.0_CUTIGNOLA.exe")
else:
    print("⚠️  Algunas compilaciones fallaron. Revisa los logs.")
print(f"──────────────────────────────────────────────────────────────────────\n")

sys.exit(0 if all_success else 1)
