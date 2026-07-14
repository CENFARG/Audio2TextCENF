"""@File: audio2text/providers/__init__.py
@Description: Transcription provider implementations. Strategy pattern: ABC + Factory + 4 providers.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from .base import TranscriptionProvider
from .factory import TranscriptionProviderFactory
from .mock_provider import MockProvider

__all__ = [
    "TranscriptionProvider",
    "TranscriptionProviderFactory",
    "MockProvider",
]
