# Build script para Audio2Text v0.9.2 - CONTRERAS
import subprocess
import sys
import os

APP_VERSION = "0.9.2"
VARIANT = "CONTRERAS"
APP_NAME = f"Audio2Text_CENF_{APP_VERSION}_{VARIANT}"
ICON_PATH = "icono.ico"
LOGO_PATH = "logo_contreras.png"

current_dir = os.path.dirname(os.path.abspath(__file__))
main_script_path = os.path.join(current_dir, "main.py")
version_info_path = os.path.join(current_dir, f"version_info_{VARIANT}.txt")

print(f"\n============================================================")
print(f"Building {APP_NAME}")
print(f"============================================================\n")

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
    "--add-data", f"{os.path.join(current_dir, 'lang')};lang",
    "--add-data", f"{os.path.join(current_dir, 'config.json')};.",
    "--add-data", f"{os.path.join(current_dir, ICON_PATH)};.",
    "--add-data", f"{os.path.join(current_dir, LOGO_PATH)};.",
    "--add-data", f"{os.path.join(current_dir, 'info_template.html')};.",
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
    "--exclude-module", "pandas",
    "--exclude-module", "yt_dlp",
    main_script_path
]

print(f"Ejecutando PyInstaller...\n")
result = subprocess.run(command, cwd=current_dir)

if result.returncode == 0:
    print(f"\n✅ Build exitoso: dist/{APP_NAME}.exe")
else:
    print(f"\n❌ Build falló con código: {result.returncode}")
    
sys.exit(result.returncode)
