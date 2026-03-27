"""
NVIDIA Riva ASR - Transcripción con NVIDIA NIM

Soporta dos modos:
1. Cloud (API key): grpc.nvcf.nvidia.com:443
2. Local (Docker): localhost:50051

Author: Audio2Text Development Team
Version: 0.11.0 (development)
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NvidiaASR:
    """
    Cliente de transcripción automática con NVIDIA Riva.

    Modelo: parakeet-ctc-0.6b-es (español)
    """

    def __init__(self, api_key: Optional[str] = None, server: str = None, mode: str = "cloud"):
        """
        Inicializar cliente NVIDIA ASR.

        Args:
            api_key: API key de NVIDIA NGC (para modo cloud)
            server: Servidor gRPC (default: grpc.nvcf.nvidia.com:443 para cloud, localhost:50051 para local)
            mode: "cloud" o "local"
        """
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY")
        self.mode = mode

        if mode == "cloud":
            self.server = server or "grpc.nvcf.nvidia.com:443"
            self.use_ssl = True
            self.function_id = "a9eeee8f-b509-4712-b19d-194361fa5f31"  # parakeet-ctc-0.6b-es
        else:
            self.server = server or "localhost:50051"
            self.use_ssl = False
            self.function_id = None

        self.client = None
        self._init_client()

    def _init_client(self):
        """Inicializar cliente gRPC de NVIDIA Riva."""
        try:
            import riva.client
            self.client = riva.client
            logger.info(f"NvidiaASR: Cliente inicializado (mode={self.mode}, server={self.server})")
        except ImportError:
            logger.error("NvidiaASR: nvidia-riva-client no está instalado")
            logger.error("Instala con: pip install nvidia-riva-client")
            self.client = None
        except Exception as e:
            logger.error(f"NvidiaASR: Error inicializando cliente: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Verificar si el cliente está disponible."""
        return self.client is not None

    def transcribe(self, audio_path: str, language_code: str = "es-US") -> Optional[str]:
        """
        Transcribir archivo de audio.

        Args:
            audio_path: Ruta al archivo WAV/OGG/OPUS (16-bit Mono)
            language_code: Código de idioma (default: es-US)

        Returns:
            Texto transcrito o None si falló
        """
        if not self.client:
            logger.error("NvidiaASR: Cliente no inicializado")
            return None

        if not os.path.exists(audio_path):
            logger.error(f"NvidiaASR: Archivo no encontrado: {audio_path}")
            return None

        try:
            import riva.client

            # Configurar metadata
            metadata = []
            if self.mode == "cloud":
                if not self.api_key:
                    logger.error("NvidiaASR: API key no configurada (NVIDIA_API_KEY)")
                    return None
                metadata.append(("function-id", self.function_id))
                metadata.append(("authorization", f"Bearer {self.api_key}"))

            # Crear solicitud de transcripción
            config = riva.client.AudioEncoding(
                encoding = riva.client.AudioEncoding.ENCODING_WAV,
                sample_rate_hertz = 16000,
                audio_channel_count = 1
            )

            # Leer archivo de audio
            with open(audio_path, "rb") as audio_file:
                audio_content = audio_file.read()

            # Transcribir
            logger.info(f"NvidiaASR: Transcribiendo {audio_path} con {self.server}")

            # NOTA: Esta es una implementación simplificada
            # La implementación real requiere usar el protoc de Riva ASR
            # que define los mensajes gRPC específicos

            # Por ahora, retornamos un placeholder
            logger.warning("NvidiaASR: Implementación incompleta - requiere protoc compilado")
            return None

        except Exception as e:
            logger.error(f"NvidiaASR: Error transcribiendo: {e}")
            return None

    def test_connection(self) -> bool:
        """Probar conexión con el servidor."""
        if self.mode == "local":
            import requests
            try:
                response = requests.get(f"http://{self.server.split(':')[0]}:9000/v1/health/ready", timeout=5)
                is_ready = response.json().get("ready", False)
                logger.info(f"NvidiaASR: Servidor local ready={is_ready}")
                return is_ready
            except Exception as e:
                logger.error(f"NvidiaASR: Error probando conexión local: {e}")
                return False
        else:
            # Para cloud, no hay endpoint de health check simple
            logger.info(f"NvidiaASR: Modo cloud - no se puede probar conexión sin transcribir")
            return True


class NvidiaASRBuilder:
    """Builder para configurar NvidiaASR fácilmente."""

    @staticmethod
    def cloud(api_key: str) -> NvidiaASR:
        """Crear cliente para modo cloud (requiere API key)."""
        return NvidiaASR(api_key=api_key, mode="cloud")

    @staticmethod
    def local(server: str = "localhost:50051") -> NvidiaASR:
        """Crear cliente para modo local (requiere Docker NIM corriendo)."""
        return NvidiaASR(server=server, mode="local")

    @staticmethod
    def auto() -> NvidiaASR:
        """
        Crear cliente automáticamente.

        Prioridad:
        1. Local si está disponible (localhost:50051)
        2. Cloud si hay NVIDIA_API_KEY
        3. None si nada está disponible
        """
        import requests

        # Probar local primero
        try:
            response = requests.get("http://localhost:9000/v1/health/ready", timeout=2)
            if response.json().get("ready"):
                logger.info("NvidiaASR: Usando modo local (detectado)")
                return NvidiaASR(mode="local")
        except:
            pass

        # Probar cloud
        if os.environ.get("NVIDIA_API_KEY"):
            logger.info("NvidiaASR: Usando modo cloud (NVIDIA_API_KEY detectada)")
            return NvidiaASR(mode="cloud")

        logger.error("NvidiaASR: No hay servidor local ni API key configurada")
        return None
