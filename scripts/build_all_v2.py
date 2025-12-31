# Master Build Script v2 - Audio2Text v0.9.2 (Organizado)
# Compila todas las variantes con estructura organizada de logs y specs

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Determinar rutas correctas
current_dir = Path(__file__).parent.parent  # Estamos en scripts/, subir a raíz
scripts_dir = Path(__file__).parent  # Carpeta scripts/

print("\n" + "="*70)
print(f"Audio2Text v0.9.2 - Master Build (Organizado)")
print(f"="*70 + "\n")

print("📁 Nueva estructura de carpetas:")
print("   _build_artifacts/")
print("   ├── logs/")
print("   │   ├── GENERAL/")
print("   │   ├── CONTRERAS/")
print("   │   └── CUTIGNOLA/")
print("   └── specs/")
print("       ├── GENERAL/")
print("       ├── CONTRERAS /")
print("       └── CUTIGNOLA/\n")

variants = ["GENERAL", "CONTRERAS", "CUTIGNOLA"]
results = {}
start_time = datetime.now()

for variant in variants:
    print(f"\n{'─'*70}")
    print(f"Compilando variante: {variant}")
    print(f"{'─'*70}")
    
    # Ejecutar desde scripts/
    build_script = scripts_dir / f"build_{variant}_v2.py"
    result = subprocess.run([sys.executable, str(build_script)], cwd=current_dir)
    results[variant] = result.returncode == 0

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print(f"\n{'='*70}")
print("RESUMEN DE COMPILACIONES")
print(f"{'='*70}\n")

for variant, success in results.items():
    status = "✅ EXITOSO" if success else "❌ FALLIDO"
    print(f"  {variant:15} : {status}")

print(f"\n{'─'*70}")
print(f"⏱️  Tiempo total: {duration:.1f} segundos ({duration/60:.1f} minutos)")
print(f"{'─'*70}\n")

all_success = all(results.values())

if all_success:
    print("🎉 ¡Todas las variantes compiladas exitosamente!")
    print(f"\n📦 Ejecutables en: dist/")
    print(f"  - Audio2Text_CENF_0.9.2_GENERAL.exe")
    print(f"  - Audio2Text_CENF_0.9.2_CONTRERAS.exe")
    print(f"  - Audio2Text_CENF_0.9.2_CUTIGNOLA.exe")
    print(f"\n📄 Logs organizados en: _build_artifacts/logs/[VARIANTE]/")
    print(f"📄 Specs organizados en: _build_artifacts/specs/[VARIANTE]/")
else:
    print("⚠️  Algunas compilaciones fallaron. Revisa los logs:")
    for variant, success in results.items():
        if not success:
            print(f"  - _build_artifacts/logs/{variant}/")

print(f"{'─'*70}\n")

sys.exit(0 if all_success else 1)
