"""@File: audio2text/pipeline/stages.py
@Description: PipelineStage definition — a named, configurable processing step.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class PipelineStage:
    """A single processing step in the transcription pipeline.

    Each stage has a name, an optional description, a processor function
    that transforms text, and an enabled flag.

    Attributes:
        name: Unique stage identifier.
        description: Human-readable description of what this stage does.
        processor: Callable that takes a str and returns a str.
        enabled: Whether this stage is active (default True).
    """

    name: str
    description: str
    processor: Callable[[str], str]
    enabled: bool = True

    def execute(self, text: str) -> tuple[str, bool, str | None]:
        """Execute the stage on the given text.

        Args:
            text: The input text.

        Returns:
            Tuple of (output_text, success, error_message).
            If error_message is not None, output_text is the original text.
        """
        if not self.enabled:
            return (text, True, None)

        try:
            result = self.processor(text)
            return (result, True, None)
        except Exception as exc:
            return (text, False, str(exc))
