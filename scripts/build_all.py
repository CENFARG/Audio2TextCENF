# Master Build Script - Audio2Text v0.10.0
# Compila todas las variantes: GENERAL, CONTRERAS, CUTIGNOLA

import subprocess
import sys

print("\n======================================================================")
print("Audio2Text v0.10.0 - Master Build")
print("======================================================================\n")

variants = ["GENERAL", "CONTRERAS", "CUTIGNOLA"]
results = {}

for variant in variants:
    print("\n──────────────────────────────────────────────────────────────────────")
    print(f"Compilando variante: {variant}")
    print("──────────────────────────────────────────────────────────────────────")

    result = subprocess.run([sys.executable, f"build_{variant}.py"])
    results[variant] = result.returncode == 0

print("\n======================================================================")
print("RESUMEN DE COMPILACIONES")
print("======================================================================\n")

for variant, success in results.items():
    status = "✅ EXITOSO" if success else "❌ FALLIDO"
    print(f"  {variant:15} : {status}")

all_success = all(results.values())
print("\n──────────────────────────────────────────────────────────────────────")
if all_success:
    print("🎉 ¡Todas las variantes compiladas exitosamente!")
    print("\nEjecutables en: dist/")
    print("  - Audio2Text_CENF_0.10.0_GENERAL.exe")
    print("  - Audio2Text_CENF_0.10.0_CONTRERAS.exe")
    print("  - Audio2Text_CENF_0.10.0_CUTIGNOLA.exe")
else:
    print("⚠️  Algunas compilaciones fallaron. Revisa los logs.")
print("──────────────────────────────────────────────────────────────────────\n")

sys.exit(0 if all_success else 1)
