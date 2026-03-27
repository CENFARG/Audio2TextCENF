# Organizador Profesional de Proyecto - Audio2Text v0.9.2
# Reorganiza todos los archivos en una estructura profesional

import shutil
from pathlib import Path

current_dir = Path(__file__).parent

print("\n" + "="*70)
print("🏗️  Organizador Profesional de Proyecto - Audio2Text v0.9.2")
print("="*70 + "\n")

# Definir estructura profesional
structure = {
    "assets": {
        "icons": ["icono.ico"],
        "logos": ["logo.png", "logo_contreras.png", "logo_cutignola.png"]
    },
    "config": [
        "config.json",
        "version.json",
        "version_info.txt",
        "version_info_GENERAL.txt",
        "version_info_CONTRERAS.txt",
        "version_info_CUTIGNOLA.txt"
    ],
    "templates": ["info_template.html"],
    "scripts": [
        "build.py",
        "build_GENERAL.py",
        "build_CONTRERAS.py",
        "build_CUTIGNOLA.py",
        "build_all.py",
        "build_GENERAL_v2.py",
        "build_CONTRERAS_v2.py",
        "build_CUTIGNOLA_v2.py",
        "build_all_v2.py",
        "cleanup_build_artifacts.py"
    ],
    "docs": [
        "INSTALACION.md",
        "GUIA_SMARTSCREEN.md",
        "RESUMEN_SOLUCIONES.md",
        "README_v0.9.2.md",
        "GENERACION_COMPLETA.md",
        "installer.nsi"
    ]
}

# Crear carpetas
print("📁 Creando estructura de carpetas...\n")

for folder, content in structure.items():
    folder_path = current_dir / folder
    folder_path.mkdir(exist_ok=True)
    print(f"   ✅ {folder}/")
    
    # Si tiene subcarpetas (como assets)
    if isinstance(content, dict):
        for subfolder in content.keys():
            subfolder_path = folder_path / subfolder
            subfolder_path.mkdir(exist_ok=True)
            print(f"      ├── {subfolder}/")

# Mover archivos
print("\n📦 Organizando archivos...\n")

moved_count = 0
skipped_count = 0

# Assets - Icons
print("🖼️  Assets - Icons:")
for filename in structure["assets"]["icons"]:
    src = current_dir / filename
    dest = current_dir / "assets" / "icons" / filename
    if src.exists() and src != dest:
        shutil.move(str(src), str(dest))
        print(f"   ✅ {filename} → assets/icons/")
        moved_count += 1
    elif not src.exists():
        print(f"   ⚠️  {filename} - No encontrado")
        skipped_count += 1

# Assets - Logos
print("\n🖼️  Assets - Logos:")
for filename in structure["assets"]["logos"]:
    src = current_dir / filename
    dest = current_dir / "assets" / "logos" / filename
    if src.exists() and src != dest:
        shutil.move(str(src), str(dest))
        print(f"   ✅ {filename} → assets/logos/")
        moved_count += 1
    elif not src.exists():
        print(f"   ⚠️  {filename} - No encontrado")
        skipped_count += 1

# Config
print("\n⚙️  Config:")
for filename in structure["config"]:
    src = current_dir / filename
    dest = current_dir / "config" / filename
    if src.exists() and src != dest:
        shutil.copy2(str(src), str(dest))  # Copy para mantener original
        print(f"   ✅ {filename} → config/")
        moved_count += 1
    elif not src.exists():
        print(f"   ⚠️  {filename} - No encontrado")
        skipped_count += 1

# Templates
print("\n📄 Templates:")
for filename in structure["templates"]:
    src = current_dir / filename
    dest = current_dir / "templates" / filename
    if src.exists() and src != dest:
        shutil.move(str(src), str(dest))
        print(f"   ✅ {filename} → templates/")
        moved_count += 1
    elif not src.exists():
        print(f"   ⚠️  {filename} - No encontrado")
        skipped_count += 1

# Scripts
print("\n🔧 Scripts:")
for filename in structure["scripts"]:
    src = current_dir / filename
    dest = current_dir / "scripts" / filename
    if src.exists() and src != dest:
        shutil.move(str(src), str(dest))
        print(f"   ✅ {filename} → scripts/")
        moved_count += 1
    elif not src.exists():
        # No es error, algunos scripts pueden no existir aún
        skipped_count += 1

# Docs
print("\n📚 Documentación:")
for filename in structure["docs"]:
    src = current_dir / filename
    dest = current_dir / "docs" / filename
    if src.exists() and src != dest:
        shutil.move(str(src), str(dest))
        print(f"   ✅ {filename} → docs/")
        moved_count += 1
    elif not src.exists():
        print(f"   ⚠️  {filename} - No encontrado")
        skipped_count += 1

print("\n" + "="*70)
print("📊 Resumen de Organización")
print("="*70)
print(f"✅ Archivos movidos: {moved_count}")
print(f"⚠️  Archivos no encontrados: {skipped_count}")

print("\n📁 Estructura Final del Proyecto:")
print("""
audio2text_v0.9.2/
├── assets/              ← Recursos visuales
│   ├── icons/           (iconos .ico)
│   └── logos/           (logos .png)
├── config/              ← Configuraciones
│   ├── config.json
│   ├── version.json
│   └── version_info_*.txt
├── templates/           ← Templates HTML
│   └── info_template.html
├── scripts/             ← Scripts de build
│   ├── build_*_v2.py
│   ├── build_all_v2.py
│   └── cleanup_*.py
├── docs/                ← Documentación
│   ├── INSTALACION.md
│   ├── GUIA_SMARTSCREEN.md
│   └── *.md
├── backend/             ← Código backend
├── ui/                  ← Código UI
├── lang/                ← Traducciones
├── _build_artifacts/    ← Artefactos de compilación
│   ├── build/
│   │   ├── GENERAL/
│   │   ├── CONTRERAS/
│   │   └── CUTIGNOLA/
│   ├── logs/
│   │   ├── GENERAL/
│   │   ├── CONTRERAS/
│   │   └── CUTIGNOLA/
│   └── specs/
│       ├── GENERAL/
│       ├── CONTRERAS/
│       └── CUTIGNOLA/
├── dist/                ← Ejecutables finales
├── main.py              ← Script principal
└── requirements.txt     ← Dependencias
""")

print("="*70)
print("✅ ¡Proyecto organizado profesionalmente!")
print("="*70 + "\n")

print("⚠️  IMPORTANTE: Ahora debes actualizar las rutas en los scripts de build")
print("   para que apunten a las nuevas ubicaciones (assets/, config/, templates/)")
print("\n   Usa: python scripts/update_build_paths.py\n")
