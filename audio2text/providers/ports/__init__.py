"""Provider ports — structural typing contracts for transcription adapters."""

from audio2text.providers.ports.transcription_provider import TranscriptionProvider
from audio2text.providers.ports.post_processing_provider import PostProcessingBlock
from audio2text.providers.ports.metadata_provider import MetadataProvider

__all__ = ["TranscriptionProvider", "PostProcessingBlock", "MetadataProvider"]