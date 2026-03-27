# Script de limpieza rápida para archivos .spec sueltos
# Mueve cualquier .spec de la raíz a _build_artifacts/specs/legacy/

from pathlib import Path
import shutil

current_dir = Path.cwd()
artifacts_dir = current_dir / "_build_artifacts"
legacy_specs_dir = artifacts_dir / "specs" / "legacy"

# Crear carpeta legacy
legacy_specs_dir.mkdir(parents=True, exist_ok=True)

# Buscar archivos .spec en la raíz
spec_files = list(current_dir.glob("*.spec"))

if spec_files:
    print(f"\n📦 Encontrados {len(spec_files)} archivos .spec sueltos en la raíz\n")
    
    for spec_file in spec_files:
        dest = legacy_specs_dir / spec_file.name
        shutil.move(str(spec_file), str(dest))
        print(f"   ✅ {spec_file.name} → _build_artifacts/specs/legacy/")
    
    print(f"\n✅ {len(spec_files)} archivos .spec organizados\n")
else:
    print("\n✅ No hay archivos .spec sueltos en la raíz\n")

print("ℹ️  Los nuevos builds generarán .spec en:")
print("   _build_artifacts/specs/GENERAL/")
print("   _build_artifacts/specs/CONTRERAS/")
print("   _build_artifacts/specs/CUTIGNOLA/\n")
