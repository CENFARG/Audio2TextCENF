import logging
import os
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import requests


class UpdaterError(Exception):
    """Typed failure of an update operation (reason logged by the raiser)."""


@dataclass(frozen=True)
class InstallResult:
    """Outcome of staging an install; the UI layer owns the shutdown."""

    batch_path: str
    source_path: str
    target_path: str
    log_path: str


def _build_install_batch(source: Path, target: Path, log_path: Path) -> str:
    """Build the detached installer batch (ASCII only, cmd-safe)."""
    return (
        "@echo off\r\n"
        f'echo [%date% %time%] Audio2Text update install started > "{log_path}"\r\n'
        f'echo Target: "{target}" >> "{log_path}"\r\n'
        f'echo Source: "{source}" >> "{log_path}"\r\n'
        "timeout /t 2 /nobreak > nul\r\n"
        f'move /y "{source}" "{target}" >> "{log_path}" 2>&1\r\n'
        "if errorlevel 1 (\r\n"
        f'    echo [%date% %time%] Move failed, exe may be locked. Retrying in 3 seconds >> "{log_path}"\r\n'
        "    timeout /t 3 /nobreak > nul\r\n"
        f'    move /y "{source}" "{target}" >> "{log_path}" 2>&1\r\n'
        ")\r\n"
        "if errorlevel 1 (\r\n"
        f'    echo [%date% %time%] ERROR: could not replace executable. Downloaded installer kept at: {source} >> "{log_path}"\r\n'
        "    exit /b 1\r\n"
        ")\r\n"
        f'echo [%date% %time%] Update installed, relaunching >> "{log_path}"\r\n'
        f'start "" "{target}"\r\n'
        'del "%~f0"\r\n'
    )


def _temp_dir() -> Path:
    """Cross-platform temp dir (TEMP/TMP env, system temp as fallback)."""
    env_temp = os.environ.get("TEMP") or os.environ.get("TMP")
    return Path(env_temp) if env_temp else Path(tempfile.gettempdir())


class Updater:
    """Gestor de actualizaciones automáticas desde GitHub"""

    def __init__(self, current_version: str, github_repo: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_version = current_version
        self.github_repo = github_repo  # "CENFARG/Audio2Text"
        self.version_url = (
            f"https://raw.githubusercontent.com/{github_repo}/main/config/version.json"
        )
        self.logger.info(f"Updater inicializado - Versión actual: {current_version}")

    def check_for_updates(self) -> dict:
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
                        "file_size": version_info.get("file_size", 0),
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
            current = tuple(map(int, self.current_version.split(".")))
            latest_tuple = tuple(map(int, latest.split(".")))
            return latest_tuple > current
        except Exception as e:
            self.logger.error(f"Error comparando versiones: {e}")
            return False

    def download_update(
        self, download_url: str, progress_callback: Callable[..., None] | None = None
    ) -> str:
        """
        Descargar nueva versión

        Args:
            download_url: URL del ejecutable a descargar
            progress_callback: Función callback(downloaded, total) para progreso.
                total puede ser 0 si el servidor no informa content-length;
                en ese caso la UI debe mostrar progreso indeterminado.

        Returns:
            Ruta del archivo descargado (verificado no vacío)

        Raises:
            UpdaterError: Si falla la descarga o el archivo queda vacío
        """
        try:
            self.logger.info(f"Descargando actualización desde {download_url}")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length") or 0)
            if total_size > 0:
                self.logger.info(f"Tamaño del archivo: {total_size / (1024 * 1024):.2f} MB")
            else:
                self.logger.info(
                    "Tamaño del archivo desconocido (sin content-length); "
                    "la UI mostrará progreso indeterminado"
                )

            # Guardar en carpeta temporal
            temp_path = _temp_dir() / "audio2text_update.exe"

            downloaded = 0
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            if downloaded == 0:
                error_msg = "La descarga llegó vacía (0 bytes); se cancela la instalación"
                self.logger.error(error_msg)
                raise UpdaterError(error_msg)

            self.logger.info(
                f"Descarga completada: {temp_path} "
                f"({downloaded / (1024 * 1024):.2f} MB"
                + (" reales, tamaño esperado desconocido)" if total_size == 0 else ")")
            )
            return str(temp_path)

        except UpdaterError:
            raise
        except requests.exceptions.HTTPError as e:
            error_msg = f"Error HTTP al descargar: {e}"
            self.logger.error(error_msg)
            raise UpdaterError(error_msg) from e
        except Exception as e:
            error_msg = f"Error descargando actualización: {e}"
            self.logger.error(error_msg)
            raise UpdaterError(error_msg) from e

    def install_update(self, temp_path: str) -> InstallResult:
        """
        Preparar la instalación de la actualización descargada.

        Lanza un script batch desacoplado que reemplaza el ejecutable
        (con reintento si el exe sigue bloqueado) y reinicia la app.
        NO termina este proceso: el cierre limpio es responsabilidad de
        la capa UI, que recibe un InstallResult.

        Args:
            temp_path: Ruta del ejecutable descargado

        Returns:
            InstallResult con rutas del batch, origen, destino y log

        Raises:
            UpdaterError: Si no está en modo compilado, o el archivo
                descargado no existe o está vacío
        """
        import subprocess

        # Verificar que estamos en modo compilado
        if not getattr(sys, "frozen", False):
            error_msg = "La actualización automática solo funciona en modo compilado"
            self.logger.error(error_msg)
            raise UpdaterError(error_msg)

        source = Path(temp_path)
        if not source.exists() or source.stat().st_size == 0:
            error_msg = f"El archivo descargado no existe o está vacío: {temp_path}"
            self.logger.error(error_msg)
            raise UpdaterError(error_msg)

        current_exe = Path(sys.executable)
        self.logger.info(f"Instalando actualización: {temp_path} -> {current_exe}")

        log_path = _temp_dir() / "update_install.log"
        batch_path = _temp_dir() / "update_install.bat"
        batch_path.write_text(_build_install_batch(source, current_exe, log_path), encoding="ascii")

        self.logger.info(
            f"Lanzando instalador desacoplado (log: {log_path}); "
            "el cierre de la app lo maneja la UI"
        )
        subprocess.Popen(
            ["cmd", "/c", str(batch_path)] if os.name == "nt" else [str(batch_path)],
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        return InstallResult(
            batch_path=str(batch_path),
            source_path=str(source),
            target_path=str(current_exe),
            log_path=str(log_path),
        )
