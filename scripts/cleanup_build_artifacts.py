# Script de limpieza para Audio2Text v0.9.2
# Organiza archivos .log y .spec antiguos en la nueva estructura

import shutil
from pathlib import Path

current_dir = Path(__file__).parent
artifacts_dir = current_dir / "_build_artifacts"
legacy_dir = artifacts_dir / "legacy"

print("\n" + "=" * 60)
print("Organizador de Artefactos de Build")
print("=" * 60 + "\n")

# Crear estructura
legacy_dir.mkdir(parents=True, exist_ok=True)

# Buscar archivos antiguos .log y .spec en la raíz
old_logs = list(current_dir.glob("build_*.log"))
old_specs = list(current_dir.glob("*.spec"))

if old_logs or old_specs:
    print(f"📦 Encontrados {len(old_logs)} logs y {len(old_specs)} specs antiguos\n")

    # Mover logs
    if old_logs:
        logs_legacy_dir = legacy_dir / "logs"
        logs_legacy_dir.mkdir(exist_ok=True)
        print(f"📄 Moviendo {len(old_logs)} archivos .log...")
        for log_file in old_logs:
            dest = logs_legacy_dir / log_file.name
            shutil.move(str(log_file), str(dest))
            print(f"   ✅ {log_file.name}")

    # Mover specs
    if old_specs:
        specs_legacy_dir = legacy_dir / "specs"
        specs_legacy_dir.mkdir(exist_ok=True)
        print(f"\n📄 Moviendo {len(old_specs)} archivos .spec...")
        for spec_file in old_specs:
            dest = specs_legacy_dir / spec_file.name
            shutil.move(str(spec_file), str(dest))
            print(f"   ✅ {spec_file.name}")

    print("\n✅ Archivos organizados en: _build_artifacts/legacy/")
else:
    print("✅ No hay archivos antiguos para organizar\n")

print("\n📁 Nueva estructura en futuras compilaciones:")
print("   _build_artifacts/")
print("   ├── logs/")
print("   │   ├── GENERAL/")
print("   │   ├── CONTRERAS/")
print("   │   └── CUTIGNOLA/")
print("   ├── specs/")
print("   │   ├── GENERAL/")
print("   │   ├── CONTRERAS/")
print("   │   └── CUTIGNOLA/")
print("   └── legacy/")
print("       ├── logs/  (archivos antiguos)")
print("       └── specs/ (archivos antiguos)")

print("\n" + "=" * 60)
print("✅ Organización completada")
print("=" * 60 + "\n")
