"""@File: tests/unit/test_provider_base.py
@Description: Unit tests for TranscriptionProvider ABC (Task 2.3).
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import pytest


class TestTranscriptionProviderABC:
    """Tests that the ABC contract is correctly defined and enforceable."""

    def test_cannot_instantiate_abc_directly(self) -> None:
        """TranscriptionProvider cannot be instantiated directly."""
        from audio2text.providers.base import TranscriptionProvider

        with pytest.raises(TypeError):
            TranscriptionProvider()  # type: ignore[abstract]

    def test_concrete_subclass_must_implement_all_abstracts(self) -> None:
        """A subclass missing abstract methods cannot be instantiated."""
        from audio2text.providers.base import TranscriptionProvider

        class IncompleteProvider(TranscriptionProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore[abstract]

    def test_concrete_subclass_with_all_methods_instantiable(self) -> None:
        """A subclass implementing all abstract methods can be instantiated."""
        from audio2text.domain.transcription import TranscriptionResult
        from audio2text.providers.base import TranscriptionProvider

        class FullProvider(TranscriptionProvider):
            def transcribe_file(
                self, audio_path: str, language: str = "es"
            ) -> TranscriptionResult | None:
                return TranscriptionResult(
                    text="mock", duration_seconds=0.0, language=language
                )

            def transcribe_stream(
                self, audio_stream, language: str = "es"
            ) -> TranscriptionResult | None:
                return None

            @property
            def is_available(self) -> bool:
                return True

            @property
            def provider_name(self) -> str:
                return "full"

            @property
            def model_name(self) -> str:
                return "mock-model"

            def validate_config(self) -> list[str]:
                return []

        provider = FullProvider()
        assert provider.is_available is True
        assert provider.provider_name == "full"
        assert provider.model_name == "mock-model"
        result = provider.transcribe_file("test.wav")
        assert result is not None
        assert result.text == "mock"

    def test_transcribe_file_signature(self) -> None:
        """ABC defines transcribe_file with correct signature."""
        import inspect

        from audio2text.providers.base import TranscriptionProvider

        sig = inspect.signature(TranscriptionProvider.transcribe_file)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "audio_path" in params
        assert "language" in params
        # Default value for language must be "es"
        lang_param = sig.parameters["language"]
        assert lang_param.default == "es"

    def test_transcribe_stream_signature(self) -> None:
        """ABC defines transcribe_stream with correct signature."""
        import inspect

        from audio2text.providers.base import TranscriptionProvider

        sig = inspect.signature(TranscriptionProvider.transcribe_stream)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "audio_stream" in params
        assert "language" in params
        lang_param = sig.parameters["language"]
        assert lang_param.default == "es"

    def test_is_available_is_abstract_property(self) -> None:
        """is_available is an abstract property returning bool."""
        from audio2text.providers.base import TranscriptionProvider

        # Verify it's a property via the class
        assert isinstance(
            TranscriptionProvider.__dict__.get("is_available"),
            property,
        )

    def test_provider_name_is_abstract_property(self) -> None:
        """provider_name is an abstract property returning str."""
        from audio2text.providers.base import TranscriptionProvider

        assert isinstance(
            TranscriptionProvider.__dict__.get("provider_name"),
            property,
        )

    def test_model_name_is_abstract_property(self) -> None:
        """model_name is an abstract property returning str."""
        from audio2text.providers.base import TranscriptionProvider

        assert isinstance(
            TranscriptionProvider.__dict__.get("model_name"),
            property,
        )

    def test_validate_config_returns_list_of_strings(self) -> None:
        """validate_config returns list[str] with validation issues."""
        from audio2text.domain.transcription import TranscriptionResult
        from audio2text.providers.base import TranscriptionProvider

        class ValidatingProvider(TranscriptionProvider):
            def transcribe_file(self, audio_path, language="es"):
                return TranscriptionResult(text="", duration_seconds=0.0, language=language)

            def transcribe_stream(self, audio_stream, language="es"):
                return None

            @property
            def is_available(self) -> bool:
                return False

            @property
            def provider_name(self) -> str:
                return "validator"

            @property
            def model_name(self) -> str:
                return "none"

            def validate_config(self) -> list[str]:
                return ["Missing API key", "Model not found"]

        provider = ValidatingProvider()
        issues = provider.validate_config()
        assert isinstance(issues, list)
        assert len(issues) == 2
        assert "Missing API key" in issues
