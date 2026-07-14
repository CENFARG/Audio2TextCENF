"""@File: tests/unit/test_pipeline.py
@Description: Unit tests for TranscriptionPipeline and PipelineStage (Task 3.6). TDD cycle.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations


class TestPipelineStage:
    """Tests for the PipelineStage protocol/enum."""

    def test_create_stage(self) -> None:
        """PipelineStage can be created with name and processor."""
        from audio2text.pipeline.stages import PipelineStage

        stage = PipelineStage(
            name="test_stage", description="A test stage", processor=lambda t: t.upper()
        )
        assert stage.name == "test_stage"
        assert stage.description == "A test stage"

    def test_stage_enabled_by_default(self) -> None:
        """Stages are enabled by default."""
        from audio2text.pipeline.stages import PipelineStage

        stage = PipelineStage(name="s", description="d", processor=lambda t: t)
        assert stage.enabled is True

    def test_stage_can_be_disabled(self) -> None:
        """Stages can be explicitly disabled."""
        from audio2text.pipeline.stages import PipelineStage

        stage = PipelineStage(name="s", description="d", processor=lambda t: t, enabled=False)
        assert stage.enabled is False


class TestTranscriptionPipeline:
    """Tests for the TranscriptionPipeline class."""

    def test_create_empty_pipeline(self) -> None:
        """Pipeline can be created with no stages."""
        from audio2text.pipeline.pipeline import TranscriptionPipeline

        pipeline = TranscriptionPipeline()
        assert pipeline is not None

    def test_add_stage(self) -> None:
        """Stages can be added to the pipeline."""
        from audio2text.pipeline.pipeline import TranscriptionPipeline
        from audio2text.pipeline.stages import PipelineStage

        pipeline = TranscriptionPipeline()
        pipeline.add_stage(PipelineStage(name="up", description="Upper", processor=lambda t: t.upper()))
        assert pipeline.stage_count == 1

    def test_process_text_through_stages(self) -> None:
        """Text flows through pipeline stages in order."""
        from audio2text.pipeline.pipeline import TranscriptionPipeline
        from audio2text.pipeline.stages import PipelineStage

        pipeline = TranscriptionPipeline()
        pipeline.add_stage(
            PipelineStage(
                name="upper", description="To uppercase", processor=lambda t: t.upper()
            )
        )
        pipeline.add_stage(
            PipelineStage(
                name="reverse", description="Reverse text", processor=lambda t: t[::-1]
            )
        )

        result = pipeline.process("hola")

        # "hola" → upper → "HOLA" → reverse → "ALOH"
        assert result.final_text == "ALOH"
        assert result.stages_executed == 2
        assert len(result.stage_results) == 2

    def test_disabled_stage_is_skipped(self) -> None:
        """Disabled stages do not process text."""
        from audio2text.pipeline.pipeline import TranscriptionPipeline
        from audio2text.pipeline.stages import PipelineStage

        pipeline = TranscriptionPipeline()
        pipeline.add_stage(
            PipelineStage(
                name="skip_me", description="Disabled",
                processor=lambda t: t + "!!!", enabled=False,
            )
        )
        pipeline.add_stage(
            PipelineStage(name="echo", description="Pass", processor=lambda t: t)
        )

        result = pipeline.process("hello")
        assert result.final_text == "hello"
        assert result.stages_executed == 1

    def test_stage_failure_graceful(self) -> None:
        """A failing stage does not crash the pipeline."""
        from audio2text.pipeline.pipeline import TranscriptionPipeline
        from audio2text.pipeline.stages import PipelineStage

        def failing_processor(text: str) -> str:
            raise ValueError("Boom!")

        pipeline = TranscriptionPipeline()
        pipeline.add_stage(
            PipelineStage(name="failer", description="Fails", processor=failing_processor)
        )
        pipeline.add_stage(
            PipelineStage(name="continue", description="Still runs", processor=lambda t: t + "_ok")
        )

        result = pipeline.process("test")
        # The second stage should still execute
        assert result.final_text == "test_ok"
        # But one stage failed
        assert any(s.failed for s in result.stage_results)

    def test_remove_stage(self) -> None:
        """Stage can be removed by name."""
        from audio2text.pipeline.pipeline import TranscriptionPipeline
        from audio2text.pipeline.stages import PipelineStage

        pipeline = TranscriptionPipeline()
        pipeline.add_stage(PipelineStage(name="remove_me", description="X", processor=lambda t: t))
        pipeline.remove_stage("remove_me")

        assert pipeline.stage_count == 0
