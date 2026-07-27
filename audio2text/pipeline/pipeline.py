"""@File: audio2text/pipeline/pipeline.py
@Description: TranscriptionPipeline — ordered execution of PipelineStage instances.
    Each stage transforms text; failed stages are skipped gracefully.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from audio2text.pipeline.stages import PipelineStage

if TYPE_CHECKING:
    from audio2text.services.ai_enhancement_service import AIEnhancementService
    from audio2text.services.block_processing_service import BlockProcessingService
    from audio2text.services.vocabulary_service import VocabularyService


@dataclass
class PipelineStepResult:
    """Result of a single pipeline stage execution.

    Attributes:
        stage_name: Name of the stage that ran.
        output_text: Text produced by this stage.
        success: True if the stage completed without error.
        failed: True if the stage raised an exception.
        error: Error message if the stage failed.
    """

    stage_name: str
    output_text: str
    success: bool
    failed: bool
    error: str | None = None


@dataclass
class PipelineResult:
    """Aggregate result of running the full pipeline.

    Attributes:
        final_text: The text after all stages have been applied.
        stages_executed: Number of stages that actually ran.
        stage_results: Per-stage results in execution order.
    """

    final_text: str
    stages_executed: int
    stage_results: list[PipelineStepResult] = field(default_factory=list)


class TranscriptionPipeline:
    """Orchestrates ordered execution of text processing stages.

    Stages are executed in the order they are added. Each stage receives
    the output of the previous stage as input. If a stage fails (raises
    an exception), the original text (input to that stage) is passed to
    the next stage — failures are non-fatal.

    Typical pipeline: Validate → Vocabulary → Blocks → AI Enhance
    """

    def __init__(self) -> None:
        """Initialize an empty pipeline."""
        self._stages: list[PipelineStage] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_stage(self, stage: PipelineStage) -> None:
        """Add a stage to the end of the pipeline.

        Args:
            stage: The PipelineStage to add.
        """
        self._stages.append(stage)

    def remove_stage(self, stage_name: str) -> bool:
        """Remove a stage by name.

        Args:
            stage_name: Name of the stage to remove.

        Returns:
            True if the stage was found and removed.
        """
        for i, stage in enumerate(self._stages):
            if stage.name == stage_name:
                self._stages.pop(i)
                return True
        return False

    def process(self, text: str) -> PipelineResult:
        """Run all enabled stages on the given text.

        Args:
            text: The input text to process.

        Returns:
            A PipelineResult with the final text and per-stage details.
        """
        stage_results: list[PipelineStepResult] = []
        current_text = text
        stages_executed = 0

        for stage in self._stages:
            if not stage.enabled:
                continue

            output, success, error = stage.execute(current_text)
            stages_executed += 1

            step_result = PipelineStepResult(
                stage_name=stage.name,
                output_text=output,
                success=success,
                failed=not success,
                error=error,
            )
            stage_results.append(step_result)

            # Pass output to next stage (even if this stage failed,
            # the execute() method returns original text on failure)
            current_text = output

        return PipelineResult(
            final_text=current_text,
            stages_executed=stages_executed,
            stage_results=stage_results,
        )

    def with_defaults(
        self,
        vocab_service: VocabularyService | None = None,
        block_service: BlockProcessingService | None = None,
        ai_service: AIEnhancementService | None = None,
    ) -> TranscriptionPipeline:
        """Wire default pipeline stages: validate → vocabulary → blocks → AI.

        Args:
            vocab_service: Optional VocabularyService for text correction.
            block_service: Optional BlockProcessingService for context blocks.
            ai_service: Optional AIEnhancementService for text polishing.

        Returns:
            Self for method chaining.
        """
        # Stage 1: UTF-8 validation (always safe, no deps)
        self.add_stage(
            PipelineStage(
                name="validate_utf8",
                description="Validate and fix UTF-8 encoding issues.",
                processor=self._validate_utf8,
            )
        )

        # Stage 2: Vocabulary corrections
        if vocab_service is not None:
            self.add_stage(
                PipelineStage(
                    name="apply_vocabulary",
                    description="Apply custom vocabulary corrections.",
                    processor=vocab_service.apply_corrections,
                )
            )

        # Stage 3: Process context blocks (wrap to return str)
        if block_service is not None:
            self.add_stage(
                PipelineStage(
                    name="process_blocks",
                    description="Process context blocks on the text.",
                    processor=lambda t: self._run_blocks(block_service, t),
                )
            )

        # Stage 4: AI enhancement
        if ai_service is not None:
            self.add_stage(
                PipelineStage(
                    name="ai_enhance",
                    description="Polish text using AI.",
                    processor=lambda text: ai_service.enhance(text),
                )
            )

        return self

    @staticmethod
    def _validate_utf8(text: str) -> str:
        """Basic UTF-8 validation pass."""
        try:
            # Normalize Unicode and remove replacement characters
            import unicodedata
            result = unicodedata.normalize("NFKC", text)
            result = result.replace("\ufffd", "")
            return result
        except Exception:
            return text

    @staticmethod
    def _run_blocks(
        block_service: BlockProcessingService, text: str
    ) -> str:
        """Run block processing and return combined text output."""
        results = block_service.process(text)
        # Join block outputs into a single string
        parts: list[str] = [text]
        for result in results:
            if result.data:
                parts.append(str(result.data))
        return "\n\n".join(parts)

    @property
    def stage_count(self) -> int:
        """Number of stages in the pipeline (including disabled)."""
        return len(self._stages)
