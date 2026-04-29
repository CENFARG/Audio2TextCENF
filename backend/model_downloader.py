"""
Model Downloader - Descarga on-demand de modelos desde HuggingFace

Permite descargar modelos de faster-whisper solo cuando se necesitan,
reduciendo el tamaño del ejecutable compilado.

Author: Audio2Text Development Team
Version: 0.15.0
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Callable
import threading
import requests

logger = logging.getLogger(__name__)


class ModelDownloader:
    """
    Gestor de descarga de modelos desde HuggingFace.

    Descarga modelos de faster-whisper en una carpeta específica
    para no incluirlos en el ejecutable compilado.
    """

    # Modelos disponibles y sus tamaños aproximados
    MODELS = {
        "tiny": {"size_mb": 39, "url": "guillaumekln/faster-whisper-tiny"},
        "base": {"size_mb": 74, "url": "guillaumekln/faster-whisper-base"},
        "small": {"size_mb": 244, "url": "guillaumekln/faster-whisper-small"},
        "medium": {"size_mb": 769, "url": "guillaumekln/faster-whisper-medium"},
        "large-v3": {"size_mb": 1550, "url": "guillaumekln/faster-whisper-large-v3"}
    }

    def __init__(self, models_dir: str = None):
        """
        Inicializar gestor de descarga de modelos.

        Args:
            models_dir: Directorio donde guardar los modelos (default: ./models)
        """
        if models_dir is None:
            # Usar carpeta models/ en el directorio raíz
            if getattr(sys, 'frozen', False):
                # Ejecutándose como .exe compilado
                base_dir = os.getcwd()
            else:
                # Ejecutándose como script Python
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            models_dir = os.path.join(base_dir, "models")

        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ModelDownloader inicializado - Directorio de modelos: {self.models_dir}")

    def is_model_downloaded(self, model_size: str) -> bool:
        """
        Verificar si un modelo ya está descargado.

        Args:
            model_size: Tamaño del modelo ("tiny", "base", "small", "medium", "large-v3")

        Returns:
            True si el modelo existe localmente
        """
        if model_size not in self.MODELS:
            logger.warning(f"Modelo desconocido: {model_size}")
            return False

        # faster-whisper guarda modelos en una subcarpeta con el nombre del modelo
        model_path = self.models_dir / model_size
        return model_path.exists() and any(model_path.iterdir())

    def get_model_path(self, model_size: str) -> Path:
        """
        Obtener la ruta local del modelo.

        Args:
            model_size: Tamaño del modelo

        Returns:
            Path al directorio del modelo
        """
        return self.models_dir / model_size

    def download_model(
        self,
        model_size: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Descargar modelo desde HuggingFace.

        Args:
            model_size: Tamaño del modelo a descargar
            progress_callback: Función callback(downloaded_bytes, total_bytes) para progreso

        Returns:
            True si la descarga fue exitosa
        """
        if model_size not in self.MODELS:
            logger.error(f"Modelo desconocido: {model_size}")
            return False

        if self.is_model_downloaded(model_size):
            logger.info(f"Modelo {model_size} ya descargado")
            return True

        try:
            logger.info(f"Descargando modelo {model_size} desde HuggingFace...")

            # Importar huggingface_hub para la descarga
            from huggingface_hub import snapshot_download

            # Descargar modelo
            model_path = snapshot_download(
                repo_id=self.MODELS[model_size]["url"],
                local_dir=str(self.get_model_path(model_size)),
                local_dir_use_symlinks=False,
                progress_callback=progress_callback
            )

            logger.info(f"Modelo {model_size} descargado exitosamente en: {model_path}")
            return True

        except ImportError:
            logger.error("huggingface_hub no está instalado. Instala con: pip install huggingface_hub")
            return False
        except Exception as e:
            logger.error(f"Error descargando modelo {model_size}: {e}")
            return False

    def download_model_async(
        self,
        model_size: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        completion_callback: Optional[Callable[[bool], None]] = None
    ) -> threading.Thread:
        """
        Descargar modelo en un thread separado.

        Args:
            model_size: Tamaño del modelo a descargar
            progress_callback: Función callback(downloaded_bytes, total_bytes) para progreso
            completion_callback: Función callback(success) cuando termine

        Returns:
            Thread de descarga
        """
        def download_thread():
            success = self.download_model(model_size, progress_callback)
            if completion_callback:
                completion_callback(success)

        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
        return thread

    def get_model_info(self, model_size: str) -> Optional[dict]:
        """
        Obtener información de un modelo.

        Args:
            model_size: Tamaño del modelo

        Returns:
            Dict con información del modelo o None si no existe
        """
        if model_size not in self.MODELS:
            return None

        info = self.MODELS[model_size].copy()
        info["downloaded"] = self.is_model_downloaded(model_size)
        info["path"] = str(self.get_model_path(model_size))
        return info

    def get_all_models_info(self) -> dict:
        """Obtener información de todos los modelos."""
        return {
            model_size: self.get_model_info(model_size)
            for model_size in self.MODELS
        }

    def delete_model(self, model_size: str) -> bool:
        """
        Eliminar un modelo descargado.

        Args:
            model_size: Tamaño del modelo a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        if not self.is_model_downloaded(model_size):
            logger.warning(f"Modelo {model_size} no está descargado")
            return False

        try:
            import shutil
            model_path = self.get_model_path(model_size)
            shutil.rmtree(model_path)
            logger.info(f"Modelo {model_size} eliminado")
            return True
        except Exception as e:
            logger.error(f"Error eliminando modelo {model_size}: {e}")
            return False

    def get_downloaded_size(self) -> int:
        """
        Obtener el tamaño total de modelos descargados en MB.

        Returns:
            Tamaño en MB
        """
        total_size = 0
        for model_size in self.MODELS:
            model_path = self.get_model_path(model_size)
            if model_path.exists():
                for file in model_path.rglob("*"):
                    if file.is_file():
                        total_size += file.stat().st_size

        return total_size // (1024 * 1024)  # Convertir a MB
