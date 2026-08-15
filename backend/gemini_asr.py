"""
Gemini ASR - Transcripción por API de Google Gemini (gratuita).

Usa el modelo gemini-flash-lite-latest (tier gratuito de Google AI Studio)
para transcribir audio. Es una alternativa a Groq Whisper.

FIX v0.15.0: proveedor nuevo — el usuario pidió poder elegir entre
Groq (Whisper Large v3) y Gemini (gratuito).

Límites del tier free (para el contador):
- 15 peticiones por minuto
- 250 peticiones por día (se contabilizan localmente)
- ~20MB o ~9.5 min de audio por petición

Author: Audio2Text Development Team
Version: 0.15.0
"""

import base64
import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Límites del tier free de Google AI Studio
FREE_TIER_DAILY_LIMIT = 250
FREE_TIER_PER_MINUTE_LIMIT = 15
FREE_TIER_WARNING_THRESHOLD = 200  # Avisar cuando quedan < 50 peticiones hoy


class GeminiASR:
    """Cliente de transcripción con la API de Gemini (gratuita)."""

    # Modelo gratuito y liviano (verificado: transcribe audio WAV correctamente)
    DEFAULT_MODEL = "gemini-flash-lite-latest"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, usage_file: str = None):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
        self.logger = logging.getLogger(self.__class__.__name__)
        # Archivo de contador de uso diario (junto al config de la app)
        self.usage_file = usage_file or os.path.join(os.getcwd(), "gemini_usage.json")
        self._usage = self._load_usage()

    def _load_usage(self) -> dict:
        """Cargar contador de uso diario."""
        try:
            p = Path(self.usage_file)
            if p.exists():
                data = json.loads(p.read_text(encoding='utf-8'))
                # Resetear si cambió el día
                if data.get("date") != str(date.today()):
                    return {"date": str(date.today()), "count": 0, "per_minute": []}
                return data
        except Exception as e:
            self.logger.warning(f"GeminiASR: error cargando uso: {e}")
        return {"date": str(date.today()), "count": 0, "per_minute": []}

    def _save_usage(self):
        """Guardar contador de uso diario."""
        try:
            p = Path(self.usage_file)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(self._usage, indent=2), encoding='utf-8')
        except Exception as e:
            self.logger.warning(f"GeminiASR: error guardando uso: {e}")

    def get_usage_stats(self) -> dict:
        """Estado de uso diario del tier free."""
        today = str(date.today())
        if self._usage.get("date") != today:
            self._usage = {"date": today, "count": 0, "per_minute": []}
        return {
            "date": self._usage["date"],
            "used_today": self._usage.get("count", 0),
            "daily_limit": FREE_TIER_DAILY_LIMIT,
            "remaining": max(0, FREE_TIER_DAILY_LIMIT - self._usage.get("count", 0)),
            "near_limit": self._usage.get("count", 0) >= FREE_TIER_WARNING_THRESHOLD,
        }

    def _register_usage(self):
        """Registrar una llamada a la API (contador diario + ventana de 1 min)."""
        import time
        now = time.time()
        today = str(date.today())
        if self._usage.get("date") != today:
            self._usage = {"date": today, "count": 0, "per_minute": []}
        self._usage["count"] = self._usage.get("count", 0) + 1
        # Ventana móvil de 60s para el límite por minuto
        window = [t for t in self._usage.get("per_minute", []) if now - t < 60]
        window.append(now)
        self._usage["per_minute"] = window
        self._save_usage()

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
            # FIX v0.15.0: registrar uso ANTES de la llamada (contador diario del tier free)
            self._register_usage()
            stats = self.get_usage_stats()
            self.logger.info(
                f"GeminiASR: uso hoy {stats['used_today']}/{stats['daily_limit']} "
                f"(quedan {stats['remaining']})"
            )
            if stats["near_limit"]:
                self.logger.warning(
                    f"GeminiASR: cerca del límite diario ({stats['used_today']}/{stats['daily_limit']})"
                )
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
