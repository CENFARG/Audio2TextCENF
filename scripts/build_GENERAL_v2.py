# Build script para Audio2Text v.0.15.10 - (Unificado) | HC-05: pyproject.toml es fuente canónica
import subprocess
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

APP_VERSION = "0.15.10"
VARIANT = ""
APP_NAME = f"Audio2Text_CENF_v.{APP_VERSION}"

# ── HC-05 version single-source check (fail fast if sources diverge) ──
try:
    import importlib.util as _ilu
    _check_path = Path(__file__).parent / "check_version.py"
    if _check_path.exists():
        _spec = _ilu.spec_from_file_location("check_version", _check_path)
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)  # type: ignore
        if hasattr(_mod, "check_all"):
            _ok = _mod.check_all(verbose=True)
            if not _ok:
                print("[!] Version check FAILED — aborting build. Ejecuta: python scripts/check_version.py")
                sys.exit(1)
            else:
                print(f"[✓] Version check PASS — canonical pyproject.toml = {APP_VERSION}")
        else:
            print("[!] check_version.py missing check_all — skipping version gate")
    else:
        print(f"[!] check_version.py not found at {_check_path} — skipping version gate")
except SystemExit:
    raise
except Exception as _e:
    print(f"[!] Version check error (continuing with warning): {_e}")

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

# Comando PyInstaller — base sin datas (se agregan condicionalmente abajo)
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
]

# ── Fix v0.15.7: datas solo si el archivo existe (config/config.json está gitignored) ──
def _add_data(src: Path, dst: str):
    if src.exists():
        command.extend(["--add-data", f"{src};{dst}"])
        print(f"[+] datas: {src.relative_to(current_dir)} -> {dst}")
    else:
        print(f"[!] datas skip (no existe): {src} -> {dst}")

# lang es directorio — requerido
_add_data(current_dir / "lang", "lang")
# config: preferir config/config.json si existe, sino fallback a config.json en root, sino omitir
_config_src = current_dir / "config" / "config.json"
if not _config_src.exists():
    _fallback = current_dir / "config.json"
    if _fallback.exists():
        print(f"[!] config/config.json no existe — usando fallback { _fallback.relative_to(current_dir) }")
        _config_src = _fallback
    else:
        _example = current_dir / "config.json.example"
        if _example.exists():
            print(f"[!] config/config.json y config.json no existen — usando {_example.relative_to(current_dir)}")
            _config_src = _example
        else:
            _config_src = None  # type: ignore
            print("[!] Ningún config.json encontrado — omitiendo datas de config")
if _config_src is not None:
    _add_data(_config_src, ".")
_add_data(ICON_PATH, ".")
_add_data(LOGO_PATH, ".")
_add_data(current_dir / "templates" / "info_template.html", ".")

# hidden-imports / excludes siguen a continuación — se agregan al command existente
command.extend([
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
    # FIX v0.15.0: ERRADICADO faster-whisper + modelo local (ctranslate2/transformers/
    # tokenizers/huggingface_hub) — la app usa SOLO API cloud Groq.
    # FIX v0.15.0: ERRADICADO stack flet/ui_flet/flet_view (código muerto, no se importa)
    "--exclude-module", "pandas",
    "--exclude-module", "yt_dlp",
    "--exclude-module", "faster_whisper",
    "--exclude-module", "ctranslate2",
    "--exclude-module", "transformers",
    "--exclude-module", "tokenizers",
    "--exclude-module", "huggingface_hub",
    "--exclude-module", "flet",
    "--exclude-module", "flet_view",
    str(main_script_path)
])

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
