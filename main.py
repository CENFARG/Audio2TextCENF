# -*- coding: utf-8 -*-
import sys
import io
import os

# CRITICAL: Forzar UTF-8 en Windows ANTES de cualquier import de librerías externas
if sys.platform.startswith('win'):
    # Método 1: Variables de entorno (debe estar PRIMERO)
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    # Método 2: Configurar locale para Windows
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except locale.Error:
        try:
            # Fallback a configuración genérica UTF-8
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            # Si todo falla, al menos configurar LC_CTYPE
            try:
                locale.setlocale(locale.LC_CTYPE, 'UTF-8')
            except:
                pass  # Continuamos sin locale específico

    # Método 3: Reconfigurar stdout/stderr para UTF-8
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Add the project root to the Python path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    base_path = sys._MEIPASS
    external_path = os.path.dirname(sys.executable)
else:
    # Running from source
    base_path = os.path.dirname(os.path.abspath(__file__))
    external_path = base_path

sys.path.insert(0, base_path)

# --- MONKEY PATCH: Fix CustomTkinter float geometry error (TclError: bad screen distance) ---
# Cause: CTkTabview passes float 300.0 to Canvas, which this Tcl version rejects.
try:
    import tkinter
    import customtkinter # Return this import to ensure correct load order

    def patch_canvas_methods():
        original_configure = tkinter.Canvas.configure
        original_init = tkinter.Canvas.__init__

        def patched_configure(self, cnf=None, **kwargs):
            if 'width' in kwargs and isinstance(kwargs['width'], float):
                kwargs['width'] = int(kwargs['width'])
            if 'height' in kwargs and isinstance(kwargs['height'], float):
                kwargs['height'] = int(kwargs['height'])
            return original_configure(self, cnf, **kwargs)

        def patched_init(self, master=None, cnf={}, **kwargs):
            if 'width' in kwargs and isinstance(kwargs['width'], float):
                kwargs['width'] = int(kwargs['width'])
            if 'height' in kwargs and isinstance(kwargs['height'], float):
                kwargs['height'] = int(kwargs['height'])
            original_init(self, master, cnf, **kwargs)

        tkinter.Canvas.configure = patched_configure
        tkinter.Canvas.__init__ = patched_init
    
    patch_canvas_methods()
except Exception as e:
    print(f"Warning: Could not apply tkinter.Canvas monkeypatch: {e}")
# --- END MONKEY PATCH ---

from ui.app import App
from backend.config_manager import ConfigManager

# --- Logging Configuration ---
# Config and logs should be in the external path (next to executable)
config_manager = ConfigManager(config_file=os.path.join(external_path, "config.json"))
logs_path = os.path.join(external_path, config_manager.get("logs_path", "logs"))

if not os.path.exists(logs_path):
    os.makedirs(logs_path)

log_file_name = datetime.now().strftime("app_%Y%m%d_%H%M%S.log")
log_file_path = os.path.join(logs_path, log_file_name)

# Check if running as frozen executable
is_frozen = getattr(sys, 'frozen', False)

# Use RotatingFileHandler for log rotation
file_handler = RotatingFileHandler(
    log_file_path,
    maxBytes=10*1024*1024, # 10 MB
    backupCount=5,
    encoding='utf-8'
)

# Configurar StreamHandler con UTF-8 explícito para la consola
stream_handler = logging.StreamHandler(sys.stdout)
if hasattr(stream_handler.stream, "buffer"):
    try:
        stream_handler.stream = io.TextIOWrapper(stream_handler.stream.buffer, encoding='utf-8', errors='replace')
    except:
        pass

handlers = [file_handler, stream_handler] if not is_frozen else [file_handler]

logging.basicConfig(
    level=logging.DEBUG, # Mantener DEBUG pero silenciar específicos
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

# Silenciar logs ruidosos de la UI y librerías
logging.getLogger("App").setLevel(logging.INFO)
logging.getLogger("Transcriber").setLevel(logging.INFO)
logging.getLogger("ConfigManager").setLevel(logging.INFO)
for lib in ["httpcore", "httpx", "groq", "PIL", "agno", "openai", "urllib3"]:
    logging.getLogger(lib).setLevel(logging.ERROR)

# Suppress verbose logs from specific libraries
for lib in ["httpcore", "httpx", "groq", "PIL", "agno", "openai"]:
    logging.getLogger(lib).setLevel(logging.ERROR)



if __name__ == "__main__":
    app = App()
    app.mainloop()