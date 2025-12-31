# C:\Users\gonza\Dropbox\DOC. RECA\06-Software\Audio2Text\audio2text_v0.8.1\build.py
import subprocess
import os
import shutil
import sys
import logging
from datetime import datetime

# --- Configuración ---
APP_VERSION = "0.9.3"
MAIN_SCRIPT = "main.py"
APP_NAME = f"Audio2Text_CENF_{APP_VERSION}"
ICON_PATH = "assets/icons/icono.ico"
REQUIREMENTS_FILE = "requirements.txt"

# --- Configuración de Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"build_{APP_VERSION}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- Rutas ---
# Ruta del directorio del script de build
current_dir = os.path.dirname(os.path.abspath(__file__))
# Ruta raíz del proyecto (un nivel arriba)
project_root = os.path.dirname(current_dir)

DIST_PATH = os.path.join(current_dir, "dist")
BUILD_PATH = os.path.join(current_dir, "build")
REQUIREMENTS_PATH = os.path.join(project_root, REQUIREMENTS_FILE)

def check_dependencies():
    """Verifica e instala dependencias necesarias."""
    logger.info("Verificando dependencias...")

    # Verificar si PyInstaller está instalado
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], check=True, capture_output=True)
        logger.info("PyInstaller ya está instalado.")
    except subprocess.CalledProcessError:
        logger.warning("PyInstaller no está instalado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        logger.info("PyInstaller instalado exitosamente.")

    # Instalar dependencias del proyecto si existe requirements.txt
    if os.path.exists(REQUIREMENTS_PATH):
        logger.info(f"Instalando dependencias desde {REQUIREMENTS_FILE}...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_PATH], check=True)
        logger.info("Dependencias instaladas exitosamente.")
    else:
        logger.warning(f"No se encontró {REQUIREMENTS_FILE}. Asegúrate de que las dependencias estén instaladas.")

def clean_previous_builds():
    """Limpia compilaciones anteriores."""
    logger.info("Limpiando compilaciones anteriores...")
    for path, name in [(DIST_PATH, "dist"), (BUILD_PATH, "build")]:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                logger.info(f"Directorio '{name}' eliminado.")
            except OSError as e:
                if e.winerror == 32:  # Archivo en uso
                    logger.warning(f"No se pudo eliminar '{name}' porque hay archivos en uso. Intentando forzar eliminación...")
                    # En Windows, podemos usar subprocess para forzar
                    try:
                        subprocess.run(["rmdir", "/s", "/q", path], check=True, shell=True)
                        logger.info(f"Directorio '{name}' eliminado forzosamente.")
                    except subprocess.CalledProcessError:
                        logger.error(f"No se pudo eliminar '{name}' incluso con fuerza. Continuando...")
                else:
                    logger.error(f"Error al eliminar '{name}': {e}")
    logger.info("Limpieza completada.")

def build_executable():
    """Construye el ejecutable con PyInstaller."""
    logger.info(f"Iniciando compilación para {APP_NAME}")

    # Verificar que el script principal existe
    main_script_path = os.path.join(project_root, MAIN_SCRIPT)
    if not os.path.exists(main_script_path):
        raise FileNotFoundError(f"No se encontró el script principal: {main_script_path}")

    # Verificar que el icono existe
    icon_path = os.path.join(project_root, ICON_PATH)
    if not os.path.exists(icon_path):
        logger.warning(f"No se encontró el icono: {icon_path}. Continuando sin icono.")
        icon_option = []
    else:
        icon_option = [f"--icon={icon_path}"]

    # Verificar si existe el archivo de versión
    version_info_path = os.path.join(project_root, "config", "version_info.txt")
    version_info_option = []
    if os.path.exists(version_info_path):
        version_info_option = [f"--version-file={version_info_path}"]
        logger.info(f"Usando archivo de versión: {version_info_path}")
    else:
        logger.warning("No se encontró version_info.txt. El ejecutable no tendrá metadatos de versión.")

    # Construir el comando de PyInstaller con opciones adicionales para profesionalismo
    command = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Ejecutable único
        "--windowed",  # Sin consola para apps GUI
        "--clean",  # Limpiar cache antes de construir
        "--noconfirm",  # No pedir confirmación
        f"--name={APP_NAME}",
        "--noupx",  # Desactivar UPX (reduce falsos positivos de antivirus)
        "--add-data", f"{os.path.join(project_root, 'lang')};lang",  # Incluir archivos de idioma
        "--add-data", f"{os.path.join(project_root, 'config.json')};.",  # Incluir config (como default interno)
        "--add-data", f"{os.path.join(project_root, 'assets', 'icons', 'icono.ico')};assets/icons", # Incluir icono
        "--add-data", f"{os.path.join(project_root, 'assets', 'logos', 'logo.png')};assets/logos", # Incluir logo
        "--add-data", f"{os.path.join(project_root, 'templates', 'info_template.html')};templates", # Incluir template HTML
        "--hidden-import", "tkinter",  # Asegurar que tkinter esté incluido
        "--hidden-import", "customtkinter",
        "--hidden-import", "sounddevice",
        "--hidden-import", "soundfile",
        "--hidden-import", "mouse",
        "--hidden-import", "keyboard",
        "--hidden-import", "pyautogui",
        "--hidden-import", "pyperclip",
        "--hidden-import", "psutil",
        "--hidden-import", "groq",
        "--exclude-module", "pandas",  # Excluir pandas
        "--exclude-module", "yt_dlp",  # Excluir yt_dlp
        f"--distpath={DIST_PATH}",
        f"--workpath={BUILD_PATH}",
    ] + icon_option + version_info_option + [main_script_path]

    logger.info("Ejecutando PyInstaller...")
    logger.info(f"Comando: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, cwd=current_dir)
        logger.info("Compilación completada exitosamente.")
        logger.info(f"Salida de PyInstaller: {result.stdout}")
        if result.stderr:
            logger.warning(f"Advertencias de PyInstaller: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Falló la compilación.")
        logger.error(f"Salida de PyInstaller: {e.stdout}")
        logger.error(f"Errores de PyInstaller: {e.stderr}")
        return False

def verify_build():
    """Verifica que el ejecutable se haya generado correctamente."""
    executable_path = os.path.join(DIST_PATH, f"{APP_NAME}.exe")
    if os.path.exists(executable_path):
        size = os.path.getsize(executable_path)
        logger.info(f"Ejecutable generado: {executable_path}")
        logger.info(f"Tamaño del ejecutable: {size / (1024*1024):.2f} MB")
        return True
    else:
        logger.error(f"No se encontró el ejecutable en: {executable_path}")
        return False

def main():
    """Función principal del script de build."""
    logger.info(f"=== Iniciando compilación profesional para {APP_NAME} ===")

    try:
        # Paso 1: Verificar e instalar dependencias
        # check_dependencies()

        # Paso 2: Limpiar builds anteriores
        clean_previous_builds()

        # Paso 3: Construir ejecutable
        if not build_executable():
            logger.error("La compilación falló. Abortando.")
            sys.exit(1)

        # Paso 4: Verificar build
        if verify_build():
            logger.info("✅ Compilación completada exitosamente.")
            logger.info(f"El ejecutable se encuentra en: {DIST_PATH}")
            logger.info(f"Nombre del ejecutable: {APP_NAME}.exe")
        else:
            logger.error("❌ Verificación fallida.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        sys.exit(1)

    logger.info("=== Compilación finalizada ===")

if __name__ == "__main__":
    main()