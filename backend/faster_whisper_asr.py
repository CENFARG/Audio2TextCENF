"""
faster-whisper ASR - Transcripción local optimizada

Ventajas sobre Whisper estándar:
- 4x más rápido que Whisper original
- Menor uso de memoria
- Mismos modelos Whisper (base, small, medium, large)
- NO requiere Docker
- Soporta GPU automáticamente (CUDA)

Modelos disponibles:
- tiny: 39M, más rápido (~1GB RAM)
- base: 74M, rápido (~1GB RAM)
- small: 244M, balanceado (~2GB RAM)
- medium: 769M, preciso (~5GB RAM)
- large-v3: 1550M, más preciso (~10GB RAM)

Author: Audio2Text Development Team
Version: 0.12.0
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FasterWhisperASR:
    """
    Cliente de transcripción automática con faster-whisper.

    Usa WhisperModel con CTranslate2 para optimización.
    """

    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "default"):
        """
        Inicializar cliente faster-whisper.

        Args:
            model_size: Tamaño del modelo ("tiny", "base", "small", "medium", "large-v3")
            device: "cpu", "cuda", "auto" (auto detecta GPU si disponible)
            compute_type: "int8", "float16", "float32", "default" (elige el mejor)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._init_model()

    def _init_model(self):
        """Inicializar modelo WhisperModel."""
        try:
            from faster_whisper import WhisperModel

            logger.info(f"FasterWhisperASR: Inicializando modelo {self.model_size} (device={self.device}, compute_type={self.compute_type})")

            # Auto-detectar GPU si device es "auto"
            if self.device == "auto":
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"FasterWhisperASR: Dispositivo auto-detectado: {self.device}")

            # Ajustar compute_type según dispositivo
            if self.compute_type == "default":
                self.compute_type = "float16" if self.device == "cuda" else "int8"
                logger.info(f"FasterWhisperASR: Compute_type auto-ajustado: {self.compute_type}")

            # Crear modelo
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )

            logger.info(f"FasterWhisperASR: Modelo {self.model_size} cargado exitosamente")

        except ImportError as e:
            logger.error(f"FasterWhisperASR: ImportError - {e}")
            logger.error("Instala con: pip install faster-whisper")
            self.model = None
        except Exception as e:
            logger.error(f"FasterWhisperASR: Exception en _init_model - {type(e).__name__}: {e}")
            import traceback
            logger.error(f"FasterWhisperASR: Traceback:\n{traceback.format_exc()}")
            self.model = None

    def is_available(self) -> bool:
        """Verificar si el modelo está disponible."""
        return self.model is not None

    def transcribe(self, audio_path: str, language_code: str = "es") -> Optional[str]:
        """
        Transcribir archivo de audio usando faster-whisper.

        Args:
            audio_path: Ruta al archivo WAV (cualquier formato soportado por ffmpeg)
            language_code: Código de idioma (default: "es" para español)

        Returns:
            Texto transcrito o None si falló
        """
        if not self.model:
            logger.error("FasterWhisperASR: Modelo no inicializado")
            return None

        if not os.path.exists(audio_path):
            logger.error(f"FasterWhisperASR: Archivo no encontrado: {audio_path}")
            return None

        try:
            logger.info(f"FasterWhisperASR: Transcribiendo {audio_path} (modelo={self.model_size}, device={self.device})")

            # Transcribir
            segments, info = self.model.transcribe(
                audio_path,
                language=language_code,
                beam_size=5,  # Beam search size (mayor = más preciso pero más lento)
                vad_filter=True,  # Voice Activity Detection para eliminar silencios
                word_timestamps=False  # No necesitamos timestamps por palabra
            )

            # Recolectar transcripción
            transcript_parts = []
            total_duration = info.duration

            for segment in segments:
                if segment.text:
                    transcript_parts.append(segment.text.strip())

            # Unir todas las partes
            full_transcript = " ".join(transcript_parts).strip()

            if full_transcript:
                logger.info(f"FasterWhisperASR: Transcripción exitosa ({len(full_transcript)} chars, {total_duration:.1f}s audio)")
                return full_transcript
            else:
                logger.warning("FasterWhisperASR: Transcripción vacía")
                return None

        except Exception as e:
            logger.error(f"FasterWhisperASR: Error transcribiendo: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def get_model_info(self) -> dict:
        """Obtener información del modelo."""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "is_available": self.is_available()
        }


class FasterWhisperASRBuilder:
    """Builder para configurar FasterWhisperASR fácilmente."""

    @staticmethod
    def tiny(device: str = "auto") -> FasterWhisperASR:
        """Crear cliente con modelo tiny (más rápido, menos preciso)."""
        return FasterWhisperASR(model_size="tiny", device=device)

    @staticmethod
    def base(device: str = "auto") -> FasterWhisperASR:
        """Crear cliente con modelo base (balanceado)."""
        return FasterWhisperASR(model_size="base", device=device)

    @staticmethod
    def small(device: str = "auto") -> FasterWhisperASR:
        """Crear cliente con modelo small (más preciso)."""
        return FasterWhisperASR(model_size="small", device=device)

    @staticmethod
    def medium(device: str = "auto") -> FasterWhisperASR:
        """Crear cliente con modelo medium (muy preciso)."""
        return FasterWhisperASR(model_size="medium", device=device)

    @staticmethod
    def large_v3(device: str = "auto") -> FasterWhisperASR:
        """Crear cliente con modelo large-v3 (máxima precisión, mismo que Groq)."""
        return FasterWhisperASR(model_size="large-v3", device=device)

    @staticmethod
    def auto() -> Optional[FasterWhisperASR]:
        """
        Crear cliente automáticamente según hardware disponible.

        Prioridad:
        1. Si hay CUDA GPU → large-v3 con GPU
        2. Si hay 16GB+ RAM → medium con CPU
        3. Si hay 8GB+ RAM → small con CPU
        4. Si hay 4GB+ RAM → base con CPU
        5. Sino → tiny con CPU
        """
        import psutil
        import torch

        # Detectar GPU
        has_cuda = torch.cuda.is_available()

        # Detectar RAM
        ram_gb = psutil.virtual_memory().total / (1024**3)

        if has_cuda:
            logger.info("FasterWhisperASR: CUDA detectada, usando large-v3 con GPU")
            return FasterWhisperASR(model_size="large-v3", device="cuda")
        elif ram_gb >= 16:
            logger.info(f"FasterWhisperASR: {ram_gb:.1f}GB RAM detectados, usando medium con CPU")
            return FasterWhisperASR(model_size="medium", device="cpu")
        elif ram_gb >= 8:
            logger.info(f"FasterWhisperASR: {ram_gb:.1f}GB RAM detectados, usando small con CPU")
            return FasterWhisperASR(model_size="small", device="cpu")
        elif ram_gb >= 4:
            logger.info(f"FasterWhisperASR: {ram_gb:.1f}GB RAM detectados, usando base con CPU")
            return FasterWhisperASR(model_size="base", device="cpu")
        else:
            logger.info(f"FasterWhisperASR: {ram_gb:.1f}GB RAM detectados, usando tiny con CPU")
            return FasterWhisperASR(model_size="tiny", device="cpu")
