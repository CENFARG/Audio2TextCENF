"""@File: tests/unit/test_ai_enhancement_service.py
@Description: Unit tests for AIEnhancementService (Task 3.5). TDD cycle.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations


class TestEnhancementProfile:
    """Tests for the EnhancementProfile enum."""

    def test_profiles_exist(self) -> None:
        """EnhancementProfile defines LIGHT, MEDIUM, AGGRESSIVE."""
        from audio2text.services.ai_enhancement_service import EnhancementProfile

        assert EnhancementProfile.LIGHT is not None
        assert EnhancementProfile.MEDIUM is not None
        assert EnhancementProfile.AGGRESSIVE is not None

    def test_profile_string_values(self) -> None:
        """EnhancementProfile values are descriptive strings."""
        from audio2text.services.ai_enhancement_service import EnhancementProfile

        assert EnhancementProfile.LIGHT.value == "light"
        assert EnhancementProfile.MEDIUM.value == "medium"
        assert EnhancementProfile.AGGRESSIVE.value == "aggressive"


class TestAIEnhancementServiceInit:
    """Tests for service initialization."""

    def test_create_without_api_key_is_unavailable(self) -> None:
        """Service without API key reports as unavailable."""
        from audio2text.services.ai_enhancement_service import AIEnhancementService

        service = AIEnhancementService(api_key=None)
        assert service.is_available() is False

    def test_create_with_api_key_is_available(self) -> None:
        """Service with API key reports as available."""
        from audio2text.services.ai_enhancement_service import AIEnhancementService

        service = AIEnhancementService(api_key="gsk_test_key")
        assert service.is_available() is True


class TestAIEnhancementServiceEnhance:
    """Tests for the enhance() method."""

    def test_enhance_unavailable_returns_original(self) -> None:
        """When service is unavailable, original text is returned unchanged."""
        from audio2text.services.ai_enhancement_service import AIEnhancementService

        service = AIEnhancementService(api_key=None)
        result = service.enhance("hola mundo")

        assert result == "hola mundo"

    def test_enhance_empty_text(self) -> None:
        """Empty text returns empty string."""
        from audio2text.services.ai_enhancement_service import AIEnhancementService

        service = AIEnhancementService(api_key="gsk_test")
        assert service.enhance("") == ""

    def test_enhance_respects_profile(self) -> None:
        """Enhancement respects the selected profile enum."""
        from audio2text.services.ai_enhancement_service import (
            AIEnhancementService,
            EnhancementProfile,
        )

        service = AIEnhancementService(api_key="gsk_test")
        # When API call is mocked/not available, different profiles still work
        result = service.enhance("text", profile=EnhancementProfile.AGGRESSIVE)
        assert isinstance(result, str)
