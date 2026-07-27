"""@File: audio2text/services/__init__.py
@Description: Business logic services for Audio2Text — the core intelligence layer.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from audio2text.services.ai_enhancement_service import (  # noqa: F401
    AIEnhancementService,
    EnhancementProfile,
)

# AudioCaptureService imports sounddevice — lazy import to avoid optional dep failure
# from audio2text.services.audio_capture_service import AudioCaptureService  # noqa: F401
from audio2text.services.block_loader_service import BlockLoaderService  # noqa: F401
from audio2text.services.block_processing_service import (  # noqa: F401
    BlockProcessingService,
)
from audio2text.services.metadata_service import MetadataService  # noqa: F401
from audio2text.services.transcription_service import TranscriptionService  # noqa: F401
from audio2text.services.utf8_validation_service import (  # noqa: F401
    UTF8ValidationService,
    ValidationResult,
)
from audio2text.services.vocabulary_service import VocabularyService  # noqa: F401
