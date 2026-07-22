"""Provider adapters — concrete implementations of TranscriptionProvider Protocol.

Each adapter satisfies the TranscriptionProvider Protocol through duck-typing.
Import from audio2text.providers.ports for the Protocol contract.
"""

from audio2text.providers.adapters.groq_adapter import GroqProvider
from audio2text.providers.adapters.faster_whisper_adapter import FasterWhisperProvider
from audio2text.providers.adapters.nvidia_riva_adapter import NvidiaRivaProvider
from audio2text.providers.adapters.mock_adapter import MockProvider

__all__ = [
    "GroqProvider",
    "FasterWhisperProvider",
    "NvidiaRivaProvider",
    "MockProvider",
]