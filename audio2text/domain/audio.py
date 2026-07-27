"""@File: audio2text/domain/audio.py
@Description: Audio domain models — AudioSegment and AudioFormat definitions.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

import numpy as np
import numpy.typing as npt


@dataclass
class AudioSegment:
    """A segment of audio data with metadata.

    Attributes:
        data: NumPy array of audio samples. Shape is (n_samples,) for mono,
              (n_samples, n_channels) for multi-channel.
        sample_rate: Sample rate in Hz.
        channels: Number of audio channels (1 = mono, 2 = stereo).
        duration: Duration of the segment in seconds (computed).
    """

    data: npt.NDArray[np.float32]
    sample_rate: int
    channels: int = 1

    @property
    def duration(self) -> float:
        """Duration of the audio segment in seconds.

        Derived from the number of samples and the sample rate.
        For multi-channel data, duration is based on the first dimension.
        """
        if self.data.size == 0:
            return 0.0
        n_frames: int = self.data.shape[0]
        return n_frames / self.sample_rate


class AudioFormat(str, Enum):
    """Supported audio file formats for transcription."""

    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"

    @classmethod
    def from_extension(cls, extension: str) -> AudioFormat:
        """Resolve an AudioFormat from a file extension string.

        Args:
            extension: File extension, with or without leading dot (e.g., "wav" or ".wav").

        Returns:
            The matching AudioFormat.

        Raises:
            ValueError: If the extension does not match any supported format.
        """
        clean = extension.lower().lstrip(".")
        for fmt in cls:
            if fmt.value == clean:
                return fmt
        raise ValueError(
            f"Unsupported audio format: {extension!r}. Supported: "
            f"{', '.join(f.value for f in cls)}"
        )

    @classmethod
    def from_path(cls, file_path: str | os.PathLike[str]) -> AudioFormat:
        """Resolve an AudioFormat from a file path.

        Args:
            file_path: Path to an audio file.

        Returns:
            The AudioFormat derived from the file extension.

        Raises:
            ValueError: If the extension is not supported.
        """
        _, ext = os.path.splitext(str(file_path))
        return cls.from_extension(ext)
