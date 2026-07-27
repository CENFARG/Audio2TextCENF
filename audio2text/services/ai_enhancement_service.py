"""@File: audio2text/services/ai_enhancement_service.py
@Description: AIEnhancementService — optionally improves transcribed text using AI (Groq default).
    Supports light/medium/aggressive profiles and preserves original meaning.
    All user-facing prompts are loaded from locale YAML files.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class EnhancementProfile(str, Enum):
    """Enhancement intensity profiles.

    Attributes:
        LIGHT: Punctuation and capitalization only.
        MEDIUM: Punctuation, structure, and minor smoothing.
        AGGRESSIVE: Full rewrite while preserving meaning.
    """

    LIGHT = "light"
    MEDIUM = "medium"
    AGGRESSIVE = "aggressive"


# Fallback prompts per profile (used when locale is unavailable)
_FALLBACK_SYSTEM_PROMPT = "Eres un corrector de texto profesional."

_FALLBACK_USER_PROMPTS: dict[EnhancementProfile, str] = {
    EnhancementProfile.LIGHT: (
        "Corrige solo la puntuacion y mayusculas del siguiente texto en espanol. "
        "No cambies palabras ni la estructura. "
        "Devuelve UNICAMENTE el texto corregido, sin explicaciones:\n\n{text}"
    ),
    EnhancementProfile.MEDIUM: (
        "Mejora la puntuacion, estructura y fluidez del siguiente texto en espanol. "
        "Corrige errores gramaticales leves pero CONSERVA el significado original. "
        "No agregues informacion nueva. "
        "Devuelve UNICAMENTE el texto mejorado, sin explicaciones:\n\n{text}"
    ),
    EnhancementProfile.AGGRESSIVE: (
        "Reescribe el siguiente texto en espanol para mejorar claridad, fluidez y "
        "profesionalismo. CONSERVA el significado y la intencion original. "
        "Elimina muletillas, repeticiones y pausas. "
        "Devuelve UNICAMENTE el texto reescrito, sin explicaciones:\n\n{text}"
    ),
}


class AIEnhancementService:
    """Optionally enhance transcribed text using an AI model.

    Uses Groq API (whisper-large-v3 or Llama) by default for text polishing.
    Falls back to returning the original text when the API is unavailable or
    when an error occurs.

    The service supports locale-based prompts via an optional LocalizationManager.
    When no locale manager is available, Spanish fallback prompts are used.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com",
        timeout_s: float = 30.0,
        locale_manager: Any | None = None,
    ) -> None:
        """Initialize the enhancement service.

        Args:
            api_key: Groq API key. If None, the service is unavailable.
            model: Model name for text enhancement.
            base_url: API base URL.
            timeout_s: Request timeout in seconds.
            locale_manager: Optional LocalizationManager for prompt strings.
        """
        self._model = model
        self._base_url = base_url
        self._timeout_s = timeout_s
        self._client: Any = None
        self._locale = locale_manager

        if api_key:
            self._init_client(api_key)

    def _init_client(self, api_key: str) -> None:
        """Initialize the Groq SDK client."""
        try:
            import groq as groq_sdk

            self._client = groq_sdk.Client(
                api_key=api_key,
                base_url=self._base_url,
                timeout=self._timeout_s,
            )
        except ImportError:
            self._client = None
        except Exception:
            self._client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Check if the enhancement service is ready."""
        return self._client is not None

    def enhance(
        self,
        text: str,
        profile: EnhancementProfile = EnhancementProfile.MEDIUM,
    ) -> str:
        """Enhance transcribed text using AI.

        Args:
            text: The transcribed text to improve.
            profile: Enhancement intensity (LIGHT, MEDIUM, AGGRESSIVE).

        Returns:
            Enhanced text, or the original text if enhancement fails
            or the service is unavailable.
        """
        if not text or not self._client:
            return text

        try:
            system_prompt = self._get_prompt("ai_prompts.system")
            user_template = self._get_prompt(f"ai_prompts.{profile.value}")
            if user_template.startswith("??"):
                user_template = _FALLBACK_USER_PROMPTS[profile]
            if system_prompt.startswith("??"):
                system_prompt = _FALLBACK_SYSTEM_PROMPT

            prompt = user_template.format(text=text)
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            enhanced: str | None = response.choices[0].message.content
            if enhanced and isinstance(enhanced, str):
                return enhanced.strip()
        except Exception:
            pass

        return text

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_prompt(self, key_path: str) -> str:
        """Get a prompt string from the locale manager, with fallback."""
        if self._locale is not None:
            try:
                result: str = self._locale.get(key_path)
                return result
            except Exception:
                pass
        return f"??{key_path}??"
