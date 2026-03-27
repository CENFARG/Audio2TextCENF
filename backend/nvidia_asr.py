"""
NVIDIA Riva ASR - Transcripción con NVIDIA NIM (gRPC)

Soporta dos modos:
1. Cloud (API key): grpc.nvcf.nvidia.com:443
2. Local (Docker): localhost:50051

Basado en: https://github.com/nvidia-riva/python-clients

Author: Audio2Text Development Team
Version: 0.12.0 (Fixed)
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NvidiaASR:
    """
    Cliente de transcripción automática con NVIDIA Riva gRPC.

    Modelo: parakeet-ctc-0.6b-es (español optimizado)
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

        self.auth = None
        self.asr_service = None
        self._init_client()

    def _init_client(self):
        """Inicializar cliente gRPC de NVIDIA Riva."""
        try:
            import riva.client

            logger.info(f"NvidiaASR: Iniciando cliente (mode={self.mode}, server={self.server})")

            # Configurar metadata para autenticación
            metadata = []
            if self.mode == "cloud" and self.api_key:
                metadata.append(("function-id", self.function_id))
                metadata.append(("authorization", f"Bearer {self.api_key}"))
                logger.info(f"NvidiaASR: Metadata configurada (function-id={self.function_id}, api_key={self.api_key[:20]}...)")

            # Crear autenticación
            logger.info(f"NvidiaASR: Creando Auth (use_ssl={self.use_ssl}, uri={self.server})")
            self.auth = riva.client.Auth(
                use_ssl=self.use_ssl,
                uri=self.server,
                metadata_args=metadata,
            )
            logger.info("NvidiaASR: Auth creada exitosamente")

            # Crear servicio ASR
            logger.info("NvidiaASR: Creando ASRService...")
            self.asr_service = riva.client.ASRService(self.auth)
            logger.info(f"NvidiaASR: ASRService creada - {type(self.asr_service)}")

            logger.info(f"NvidiaASR: Cliente inicializado correctamente (mode={self.mode}, server={self.server})")

        except ImportError as e:
            logger.error(f"NvidiaASR: ImportError - {e}")
            logger.error("Instala con: pip install nvidia-riva-client")
            self.auth = None
            self.asr_service = None
        except Exception as e:
            logger.error(f"NvidiaASR: Exception en _init_client - {type(e).__name__}: {e}")
            import traceback
            logger.error(f"NvidiaASR: Traceback:\n{traceback.format_exc()}")
            self.auth = None
            self.asr_service = None

    def is_available(self) -> bool:
        """Verificar si el cliente está disponible."""
        return self.asr_service is not None

    def transcribe(self, audio_path: str, language_code: str = "es-US") -> Optional[str]:
        """
        Transcribir archivo de audio usando NVIDIA Riva gRPC.

        Args:
            audio_path: Ruta al archivo WAV (16-bit Mono, 16kHz)
            language_code: Código de idioma (default: es-US)

        Returns:
            Texto transcrito o None si falló
        """
        if not self.asr_service:
            logger.error("NvidiaASR: Cliente no inicializado")
            return None

        if not os.path.exists(audio_path):
            logger.error(f"NvidiaASR: Archivo no encontrado: {audio_path}")
            return None

        try:
            import riva.client

            # Configurar reconocimiento
            config = riva.client.StreamingRecognitionConfig(
                config=riva.client.RecognitionConfig(
                    language_code=language_code,
                    enable_automatic_punctuation=True,
                    verbatim_transcripts=False,
                ),
                interim_results=False,
            )

            logger.info(f"NvidiaASR: Transcribiendo {audio_path} (modo {self.mode})")

            # Transcribir usando streaming
            # AudioChunkFileIterator requiere: input_file, chunk_size, delay_callback
            responses = self.asr_service.streaming_response_generator(
                audio_chunks=riva.client.AudioChunkFileIterator(
                    audio_path,
                    1600,  # chunk_size (frames)
                    None   # delay_callback (simular realtime)
                ),
                streaming_config=config,
            )

            # Recolectar transcripción
            transcript_parts = []
            for response in responses:
                if not response.results:
                    continue

                for result in response.results:
                    if not result.alternatives:
                        continue

                    alternative = result.alternatives[0]
                    if alternative.transcript:
                        transcript_parts.append(alternative.transcript)

            # Unir todas las partes
            full_transcript = " ".join(transcript_parts).strip()

            if full_transcript:
                logger.info(f"NvidiaASR: Transcripción exitosa ({len(full_transcript)} chars)")
                return full_transcript
            else:
                logger.warning("NvidiaASR: Transcripción vacía")
                return None

        except Exception as e:
            logger.error(f"NvidiaASR: Error transcribiendo: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def test_connection(self) -> bool:
        """Probar conexión con el servidor."""
        if not self.asr_service:
            return False

        try:
            import riva.client

            # Intentar obtener configuración del servidor
            config_response = self.asr_service.stub.GetRivaSpeechRecognitionConfig(
                riva.client.proto.riva_asr_pb2.RivaSpeechRecognitionConfigRequest()
            )

            logger.info(f"NvidiaASR: Servidor disponible - {len(config_response.model_config)} modelos")
            return True

        except Exception as e:
            logger.error(f"NvidiaASR: Error probando conexión: {e}")
            return False


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
    def auto() -> Optional[NvidiaASR]:
        """
        Crear cliente automáticamente.

        Prioridad:
        1. Local si está disponible (localhost:50051)
        2. Cloud si hay NVIDIA_API_KEY
        3. None si nada está disponible
        """
        # Probar local primero
        try:
            local_client = NvidiaASR(mode="local")
            if local_client.test_connection():
                logger.info("NvidiaASR: Usando modo local (detectado)")
                return local_client
        except:
            pass

        # Probar cloud
        if os.environ.get("NVIDIA_API_KEY"):
            logger.info("NvidiaASR: Usando modo cloud (NVIDIA_API_KEY detectada)")
            return NvidiaASR(mode="cloud")

        logger.error("NvidiaASR: No hay servidor local ni API key configurada")
        return None
