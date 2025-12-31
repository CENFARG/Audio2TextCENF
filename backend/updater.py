import requests
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Optional, Callable

class Updater:
    """Gestor de actualizaciones automáticas desde GitHub"""
    
    def __init__(self, current_version: str, github_repo: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_version = current_version
        self.github_repo = github_repo  # "CENFARG/Audio2Text"
        self.version_url = f"https://raw.githubusercontent.com/{github_repo}/main/version.json"
        self.logger.info(f"Updater inicializado - Versión actual: {current_version}")
    
    def check_for_updates(self) -> Dict:
        """
        Verificar si hay nueva versión disponible
        
        Returns:
            Dict con:
                - available (bool): Si hay actualización disponible
                - version (str): Versión disponible
                - download_url (str): URL de descarga
                - changelog (str): Notas de la versión
                - release_date (str): Fecha de lanzamiento
                - error (str): Mensaje de error si falló
        """
        try:
            self.logger.info(f"Verificando actualizaciones en {self.version_url}")
            response = requests.get(self.version_url, timeout=10)
            
            if response.status_code == 200:
                version_info = response.json()
                latest_version = version_info["version"]
                
                self.logger.info(f"Última versión disponible: {latest_version}")
                
                if self._is_newer_version(latest_version):
                    self.logger.info("Nueva versión disponible!")
                    return {
                        "available": True,
                        "version": latest_version,
                        "download_url": version_info.get("download_url", ""),
                        "changelog": version_info.get("changelog", "Sin información"),
                        "release_date": version_info.get("release_date", ""),
                        "file_size": version_info.get("file_size", 0)
                    }
                else:
                    self.logger.info("Ya estás usando la última versión")
                    return {"available": False}
            else:
                error_msg = f"Error HTTP {response.status_code}"
                self.logger.error(error_msg)
                return {"available": False, "error": error_msg}
                
        except requests.exceptions.Timeout:
            error_msg = "Timeout al verificar actualizaciones"
            self.logger.error(error_msg)
            return {"available": False, "error": error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = "Sin conexión a internet"
            self.logger.error(error_msg)
            return {"available": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            self.logger.error(error_msg)
            return {"available": False, "error": error_msg}
    
    def _is_newer_version(self, latest: str) -> bool:
        """
        Comparar versiones (formato: X.Y.Z)
        
        Args:
            latest: Versión más reciente
            
        Returns:
            True si latest es más nueva que current_version
        """
        try:
            current = tuple(map(int, self.current_version.split('.')))
            latest_tuple = tuple(map(int, latest.split('.')))
            return latest_tuple > current
        except Exception as e:
            self.logger.error(f"Error comparando versiones: {e}")
            return False
    
    def download_update(self, download_url: str, progress_callback: Optional[Callable] = None) -> str:
        """
        Descargar nueva versión
        
        Args:
            download_url: URL del ejecutable a descargar
            progress_callback: Función callback(downloaded, total) para progreso
            
        Returns:
            Ruta del archivo descargado
            
        Raises:
            Exception: Si falla la descarga
        """
        try:
            self.logger.info(f"Descargando actualización desde {download_url}")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            self.logger.info(f"Tamaño del archivo: {total_size / (1024*1024):.2f} MB")
            
            # Guardar en carpeta temporal
            temp_dir = Path(os.getenv('TEMP', '/tmp'))
            temp_path = temp_dir / "audio2text_update.exe"
            
            downloaded = 0
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)
            
            self.logger.info(f"Descarga completada: {temp_path}")
            return str(temp_path)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Error HTTP al descargar: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error descargando actualización: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def install_update(self, temp_path: str) -> None:
        """
        Instalar actualización y reiniciar aplicación
        
        Args:
            temp_path: Ruta del ejecutable descargado
            
        Raises:
            Exception: Si no está en modo compilado o falla la instalación
        """
        import subprocess
        
        # Verificar que estamos en modo compilado
        if not getattr(sys, 'frozen', False):
            raise Exception("La actualización automática solo funciona en modo compilado")
        
        current_exe = sys.executable
        self.logger.info(f"Instalando actualización: {temp_path} -> {current_exe}")
        
        # Crear script batch para reemplazar y reiniciar
        # El batch espera 2 segundos para que la app se cierre completamente
        batch_script = f"""@echo off
timeout /t 2 /nobreak > nul
move /y "{temp_path}" "{current_exe}"
if errorlevel 1 (
    echo Error al instalar actualización
    pause
    exit /b 1
)
start "" "{current_exe}"
del "%~f0"
"""
        
        batch_path = Path(os.getenv('TEMP', '/tmp')) / "update_install.bat"
        with open(batch_path, 'w') as f:
            f.write(batch_script)
        
        self.logger.info("Ejecutando script de instalación y cerrando aplicación")
        
        # Ejecutar batch y cerrar aplicación
        subprocess.Popen([str(batch_path)], shell=True, 
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        
        # Cerrar la aplicación actual
        sys.exit(0)
