# Script de Limpieza Final - Organizar archivos sueltos en raíz
# Prepara el proyecto para commit a GitHub

from pathlib import Path
import shutil

current_dir = Path.cwd()

print("\n" + "="*70)
print("🧹 Limpieza Final del Proyecto - Preparación para Commit")
print("="*70 + "\n")

# Archivos a mover o eliminar
actions = {
    "docs": [
        "COMPLETADO_v0.9.2.md",
        "INSTRUCCIONES_SIGUIENTES_PASOS.md",
        "README_ESTRUCTURA_PROFESIONAL.md",
        "RESUMEN_FINAL_v0.9.2.md"
    ],
    "scripts": [
        "organize_project.py",
        "cleanup_specs.py",
        "update_build_paths.py"
    ],
    "delete_duplicates": [
        "config.json",  # Ya está en config/
        "version.json",  # Ya está en config/
        "version_info.txt",  # Ya está en config/
        "version_info_GENERAL.txt",  # Ya está en config/
        "version_info_CONTRERAS.txt",  # Ya está en config/
        "version_info_CUTIGNOLA.txt"  # Ya está en config/
    ]
}

moved_count = 0
deleted_count = 0

# Mover READMEs y docs a docs/
print("📚 Moviendo documentación a docs/...")
docs_dir = current_dir / "docs"
for doc_file in actions["docs"]:
    src = current_dir / doc_file
    if src.exists():
        dest = docs_dir / doc_file
        shutil.move(str(src), str(dest))
        print(f"   ✅ {doc_file} → docs/")
        moved_count += 1

# Mover scripts a scripts/
print("\n🔧 Moviendo scripts a scripts/...")
scripts_dir = current_dir / "scripts"
for script_file in actions["scripts"]:
    src = current_dir / script_file
    if src.exists():
        dest = scripts_dir / script_file  
        shutil.move(str(src), str(dest))
        print(f"   ✅ {script_file} → scripts/")
        moved_count += 1

# Eliminar duplicados (ya están en config/)
print("\n🗑️  Eliminando archivos duplicados (ya están en config/)...")
for dup_file in actions["delete_duplicates"]:
    file_path = current_dir / dup_file
    if file_path.exists():
        file_path.unlink()
        print(f"   ✅ {dup_file} eliminado (duplicado)")
        deleted_count += 1

# Limpiar carpeta build/ antigua si existe
build_dir = current_dir / "build"
if build_dir.exists() and build_dir.is_dir():
    # Verificar si está vacía o tiene contenido antiguo
    build_contents = list(build_dir.iterdir())
    if build_contents:
        print(f"\n📦 Carpeta build/ detectada con {len(build_contents)} items")
        print("   ⚠️  Esta carpeta se eliminará en futuras ejecuciones")
        print("   ℹ️  Usar _build_artifacts/ en su lugar")
        print("   💡 Ejecuta: rmdir /s /q build (si no hay compilaciones activas)")
    else:
        try:
            build_dir.rmdir()
            print(f"\n📦 Carpeta build/ vacía eliminada")
            deleted_count += 1
        except Exception as e:
            print(f"\n⚠️  No se pudo eliminar build/: {e}")

print("\n" + "="*70)
print("📊 Resumen de Limpieza")
print("="*70)
print(f"✅ Archivos movidos: {moved_count}")
print(f"🗑️  Archivos/carpetas eliminados: {deleted_count}")

print("\n📁 Estructura Final (solo raíz):")
root_items = [
    item.name for item in current_dir.iterdir() 
    if not item.name.startswith('.') and not item.name.startswith('_')
]
for item in sorted(root_items):
    item_path = current_dir / item
    if item_path.is_dir():
        print(f"   📁 {item}/")
    else:
        print(f"   📄 {item}")

print("\n" + "="*70)
print("✅ Limpieza completada - Proyecto listo para commit")
print("="*70 + "\n")

print("📋 Próximos pasos:")
print("   1. Verificar que todo esté correcto: ls")
print("   2. Ver estado de Git: git status")
print("   3. Agregar cambios: git add .")
print("   4. Commit: git commit -m \"v0.9.2: Estructura profesional + SmartScreen fixes\"")
print("   5. Push: git push origin main\n")
