"""
Gemini ASR - Transcripción por API de Google Gemini (gratuita).

Usa el modelo gemini-flash-lite-latest (tier gratuito de Google AI Studio)
para transcribir audio. Es una alternativa a Groq Whisper.

FIX v0.15.0: proveedor nuevo — el usuario pidió poder elegir entre
Groq (Whisper Large v3) y Gemini (gratuito).

Author: Audio2Text Development Team
Version: 0.15.0
"""

import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GeminiASR:
    """Cliente de transcripción con la API de Gemini (gratuita)."""

    # Modelo gratuito y liviano (verificado: transcribe audio WAV correctamente)
    DEFAULT_MODEL = "gemini-flash-lite-latest"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        self.logger = logging.getLogger(self.__class__.__name__)

    def is_available(self) -> bool:
        """Indicar si la key está configurada."""
        return bool(self.api_key)

    def get_model_info(self) -> dict:
        """Información del modelo para logging."""
        return {"model": self.model, "provider": "gemini", "tier": "free"}

    def transcribe(self, audio_path: str, language_code: str = "es") -> Optional[str]:
        """
        Transcribir un archivo de audio usando la API de Gemini.

        Args:
            audio_path: Ruta al archivo WAV
            language_code: Código de idioma (se usa en el prompt)

        Returns:
            Texto transcrito o None si falla
        """
        if not self.is_available():
            self.logger.warning("GeminiASR: no hay API key configurada")
            return None

        try:
            import json
            import urllib.request
            import urllib.error

            # Leer audio y codificar en base64
            with open(audio_path, 'rb') as f:
                audio_b64 = base64.b64encode(f.read()).decode()

            # Prompt de transcripción
            lang_hint = {
                "es": "Transcribe el audio al español.",
                "en": "Transcribe the audio to English.",
            }.get(language_code or "es", "Transcribe el audio al español.")

            body = {
                "contents": [{
                    "parts": [
                        {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}},
                        {"text": f"{lang_hint} Solo el texto transcrito, sin comentarios."}
                    ]
                }]
            }

            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{self.model}:generateContent?key={self.api_key}")
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            )

            self.logger.info(f"GeminiASR: transcribiendo {audio_path} con {self.model}")
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())

            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts).strip()

            if not text:
                self.logger.error("GeminiASR: respuesta vacía")
                return None
            return text

        except urllib.error.HTTPError as e:
            body_err = ""
            try:
                body_err = e.read().decode()[:200]
            except Exception:
                pass
            self.logger.error(f"GeminiASR: error HTTP {e.code}: {body_err}")
            return None
        except Exception as e:
            self.logger.error(f"GeminiASR: error transcribiendo: {e}")
            return None
