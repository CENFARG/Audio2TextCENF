"""
Backward-compatibility shim — re-exports from audio2text.providers.ports.

The old ABC-based TranscriptionProvider has been replaced by a Protocol.
Import from audio2text.providers.ports for the canonical definition.
"""

from audio2text.providers.ports.transcription_provider import TranscriptionProvider

__all__ = ["TranscriptionProvider"]