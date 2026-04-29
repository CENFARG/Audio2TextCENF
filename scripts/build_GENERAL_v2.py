# Build script para Audio2Text v0.14.0 - (Unificado)
import subprocess
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

APP_VERSION = "0.15.0"
VARIANT = ""
APP_NAME = f"Audio2Text_CENF_v{APP_VERSION}"

# Rutas - estamos en scripts/, el proyecto está un nivel arriba
current_dir = Path(__file__).parent.parent
ICON_PATH = current_dir / "assets" / "icons" / "icono.ico"
LOGO_PATH = current_dir / "assets" / "logos" / "logo.png"

main_script_path = current_dir / "main.py"
version_info_path = current_dir / "config" / f"version_info_{VARIANT or 'GENERAL'}.txt"

# Estructura de carpetas organizada por variante
artifacts_dir = current_dir / "_build_artifacts"
logs_dir = artifacts_dir / "logs" / (VARIANT or "GENERAL")
specs_dir = artifacts_dir / "specs" / (VARIANT or "GENERAL")
build_dir = artifacts_dir / "build" / (VARIANT or "GENERAL")
dist_dir = current_dir / "dist"

# Crear carpetas si no existen
logs_dir.mkdir(parents=True, exist_ok=True)
specs_dir.mkdir(parents=True, exist_ok=True)

# Timestamp para el log
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = logs_dir / f"build_{timestamp}.log"

print(f"\n{'='*60}")
print(f"Building {APP_NAME}")
print(f"{'='*60}\n")
print(f"[*] Organizando artefactos en:")
print(f"   Logs:  {logs_dir}")
print(f"   Specs: {specs_dir}\n")

# Comando PyInstaller
command = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--clean",
    "--noconfirm",
    "--noupx",
    f"--name={APP_NAME}",
    f"--icon={ICON_PATH}",
    f"--version-file={version_info_path}",
    f"--distpath={dist_dir}",
    f"--workpath={build_dir}",
    f"--specpath={specs_dir}",  # Guardar spec en carpeta organizada
    "--add-data", f"{current_dir / 'lang'};lang",
    "--add-data", f"{current_dir / 'config' / 'config.json'};.",
    "--add-data", f"{ICON_PATH};.",
    "--add-data", f"{LOGO_PATH};.",
    "--add-data", f"{current_dir / 'templates' / 'info_template.html'};.",
    "--hidden-import", "tkinter",
    "--hidden-import", "customtkinter",
    "--hidden-import", "sounddevice",
    "--hidden-import", "soundfile",
    "--hidden-import", "mouse",
    "--hidden-import", "keyboard",
    "--hidden-import", "pyautogui",
    "--hidden-import", "pyperclip",
    "--hidden-import", "psutil",
    "--hidden-import", "groq",
    "--hidden-import", "backend.transcription_metadata",
    "--hidden-import", "backend.transcription_metadata_generator",
    "--hidden-import", "backend.hotkey_manager",
    "--hidden-import", "backend.emoji_picker",
    "--hidden-import", "ui_flet.components.design_system",
    "--hidden-import", "ui_flet.components.history_tab",
    "--hidden-import", "flet",
    "--hidden-import", "flet.core",
    "--hidden-import", "flet.core.page",
    "--hidden-import", "flet.core.controls",
    "--hidden-import", "flet.URIDataReaderAtOrigin",
    "--hidden-import", "flet.pubsub",
    "--hidden-import", "flet.runtime",
    "--hidden-import", "flet.runtime.app",
    "--hidden-import", "flet.runtime.pubsub",
    "--hidden-import", "flet.runtime.web",
    "--hidden-import", "flet_view",
    "--hidden-import", "flet_view.adwaita",
    "--hidden-import", "flet_view.platform",
    "--hidden-import", "flet_view.platform.android",
    "--hidden-import", "flet_view.platform.ios",
    "--hidden-import", "flet_view.platform.linux",
    "--hidden-import", "flet_view.platform.mac",
    "--hidden-import", "flet_view.platform.windows",
    "--hidden-import", "flet_view.theme",
    "--hidden-import", "flet_view.utils",
    "--hidden-import", "flet_view.utils.logging",
    "--hidden-import", "flet_view.utils.tasks",
    "--hidden-import", "flet_view.utils.transform",
    "--hidden-import", "flet_view.utils.version",
    "--hidden-import", "faster_whisper",
    "--hidden-import", "ctranslate2",
    "--hidden-import", "transformers",
    "--hidden-import", "tokenizers",
    "--hidden-import", "huggingface_hub",
    "--exclude-module", "pandas",
    "--exclude-module", "yt_dlp",
    str(main_script_path)
]

# Ejecutar directamente
result = subprocess.run(
    command, 
    cwd=current_dir,
    text=True
)

# Guardar resultado
success = result.returncode == 0

# Crear archivo de resumen
summary_file = logs_dir / f"summary_{timestamp}.txt"
with open(summary_file, 'w', encoding='utf-8') as f:
    f.write(f"Build Summary - {APP_NAME}\n")
    f.write(f"{'='*60}\n")
    f.write(f"Timestamp: {timestamp}\n")
    f.write(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}\n")
    f.write(f"Return Code: {result.returncode}\n")
    f.write(f"Log File: {log_file.name}\n")
    f.write(f"Spec File: {specs_dir / f'{APP_NAME}.spec'}\n")
    if success:
        exe_path = dist_dir / f"{APP_NAME}.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024*1024)
            f.write(f"Executable: {exe_path}\n")
            f.write(f"Size: {size_mb:.2f} MB\n")

print(f"\n{'='*60}")
if success:
    print(f"[+] Build exitoso: dist/{APP_NAME}.exe")
    print(f"[*] Log guardado: {log_file.relative_to(current_dir)}")
    print(f"[*] Spec guardado: {(specs_dir / f'{APP_NAME}.spec').relative_to(current_dir)}")
else:
    print(f"[-] Build fallo con codigo: {result.returncode}")
    print(f"[*] Ver detalles en: {log_file.relative_to(current_dir)}")
print(f"{'='*60}\n")
    
sys.exit(result.returncode)
