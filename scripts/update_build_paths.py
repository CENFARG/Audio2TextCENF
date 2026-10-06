# Script para actualizar rutas en archivos de build
# Adapta los scripts a la nueva estructura profesional

from pathlib import Path
import re

current_dir = Path(__file__).parent.parent  # Estamos en scripts/

print("\n" + "=" * 70)
print("🔄 Actualizador de Rutas en Scripts de Build")
print("=" * 70 + "\n")

# Mapeo de rutas antiguas a nuevas
path_mappings = {
    '"icono.ico"': '"assets/icons/icono.ico"',
    '"logo.png"': '"assets/logos/logo.png"',
    '"logo_contreras.png"': '"assets/logos/logo_contreras.png"',
    '"logo_cutignola.png"': '"assets/logos/logo_cutignola.png"',
    '"config.json"': '"config/config.json"',
    '"info_template.html"': '"templates/info_template.html"',
    'version_info_path = current_dir / f"version_info_{VARIANT}.txt"': 'version_info_path = current_dir / "config" / f"version_info_{VARIANT}.txt"',
}

# Archivos a actualizar
build_scripts = [
    "build_GENERAL_v2.py",
    "build_CONTRERAS_v2.py",
    "build_CUTIGNOLA_v2.py",
]

updated_count = 0

for script_name in build_scripts:
    script_path = current_dir / "scripts" / script_name

    if not script_path.exists():
        print(f"⚠️  {script_name} - No encontrado")
        continue

    print(f"📝 Actualizando {script_name}...")

    # Leer contenido
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Aplicar reemplazos
    for old_path, new_path in path_mappings.items():
        if old_path in content:
            content = content.replace(old_path, new_path)
            print(f"   ✅ {old_path} → {new_path}")

    # Guardar si hubo cambios
    if content != original_content:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(content)
        updated_count += 1
        print("   💾 Guardado\n")
    else:
        print("   ℹ️  Sin cambios necesarios\n")

# Actualizar main.py también
main_py_path = current_dir / "main.py"
if main_py_path.exists():
    print("📝 Actualizando main.py...")

    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Reemplazos comunes en main.py
    replacements = {
        "config.json": "config/config.json",
        "icono.ico": "assets/icons/icono.ico",
    }

    for old, new in replacements.items():
        # Solo reemplazar si no es parte de una ruta más larga
        content = re.sub(r'(?<!")' + re.escape(old) + r'(?!")', new, content)

    if content != original:
        with open(main_py_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("   💾 main.py actualizado\n")
        updated_count += 1
    else:
        print("   ℹ️  main.py sin cambios necesarios\n")

print("=" * 70)
print(f"✅ Actualización completada: {updated_count} archivos modificados")
print("=" * 70 + "\n")

print("📋 Próximos pasos:")
print("   1. Revisar que los builds funcionen: python scripts/build_all_v2.py")
print("   2. Si hay errores, verificar rutas manualmente")
print("   3. Probar compilación de cada variante\n")
