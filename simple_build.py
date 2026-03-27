#!/usr/bin/env python
"""Simple build script for Audio2Text v0.11.0"""
import subprocess
import sys

print("=== Starting Audio2Text v0.11.0 Build ===")

# Change to project root
import os
os.chdir(r"C:\Dropbox\DOC.RECA\06-Software\Audio2Text")

# Run PyInstaller directly
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--clean",
    "--noconfirm",
    "--name=Audio2Text_CENF_0.11.0",
    "--noupx",
    "--add-data", "lang;lang",
    "--add-data", "config.json;.",
    "--add-data", "assets/icons/icono.ico;assets/icons",
    "--add-data", "assets/logos/logo.png;assets/logos",
    "--add-data", "templates/info_template.html;templates",
    "--hidden-import", "flet",
    "--hidden-import", "flet.runtime",
    "--collect-all", "flet",
    "--hidden-import", "PIL",
    "--hidden-import", "PIL._imagingtk",
    "--hidden-import", "sounddevice",
    "--hidden-import", "soundfile",
    "--hidden-import", "mouse",
    "--hidden-import", "keyboard",
    "--hidden-import", "pyautogui",
    "--hidden-import", "pyperclip",
    "--hidden-import", "psutil",
    "--hidden-import", "groq",
    "--hidden-import", "requests",
    "--hidden-import", "backend.blocks",
    "--hidden-import", "backend.blocks.base_block",
    "--hidden-import", "backend.blocks.block_manager",
    "--hidden-import", "backend.blocks.task_extractor_block",
    "--hidden-import", "backend.blocks.summary_block",
    "--hidden-import", "backend.blocks.keyword_extractor_block",
    "--hidden-import", "backend.custom_vocabulary",
    "--exclude-module", "pandas",
    "--exclude-module", "yt_dlp",
    "--exclude-module", "tkinter",
    "--exclude-module", "customtkinter",
    "--distpath", "scripts/dist",
    "--workpath", "scripts/build",
    "--icon", "assets/icons/icono.ico",
    "--version-file", "config/version_info.txt",
    "main.py"
]

print(f"Running: {' '.join(cmd[:3])}...")
print()

# Run WITHOUT capturing output so we see it in real-time
result = subprocess.run(cmd, cwd=os.getcwd())

print()
print(f"=== Build Complete (exit code: {result.returncode}) ===")

if result.returncode == 0:
    print("SUCCESS! Checking for executable...")
    exe_path = "scripts/dist/Audio2Text_CENF_0.11.0.exe"
    if os.path.exists(exe_path):
        size = os.path.getsize(exe_path)
        print(f"Executable: {exe_path}")
        print(f"Size: {size / (1024*1024):.2f} MB")
    else:
        print("WARNING: Executable not found!")
else:
    print("FAILED!")

sys.exit(result.returncode)
