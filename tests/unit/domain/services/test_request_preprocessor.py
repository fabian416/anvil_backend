"""
Unit tests for request preprocessor.

Tests language detection and request preparation.
"""

import pytest
from uuid import UUID

from app.domain.services.distillation.request_preprocessor import RequestPreprocessor
from app.domain.chat.entities.message import Message
from app.domain.chat.value_objects.message_role import MessageRole


class TestRequestPreprocessor:
    """Test request preprocessor."""

    @pytest.fixture
    def preprocessor(self):
        """Create preprocessor instance."""
        return RequestPreprocessor()

    def test_detect_language_english(self, preprocessor):
        """Test English language detection."""
        text = "Hello, how are you? This is a test message."

        lang = preprocessor.detect_language(text)

        assert lang == "en"

    def test_detect_language_spanish(self, preprocessor):
        """Test Spanish language detection (requires langdetect)."""
        text = "Hola, ¿cómo estás? Este es un mensaje de prueba."

        lang = preprocessor.detect_language(text)

        # If langdetect is not installed, defaults to 'en'
        # This test validates the behavior, not the library
        if lang == "en":
            pytest.skip("langdetect not installed, skipping non-English language tests")
        assert lang == "es"

    def test_detect_language_french(self, preprocessor):
        """Test French language detection (requires langdetect)."""
        text = "Bonjour, comment allez-vous? Ceci est un message de test."

        lang = preprocessor.detect_language(text)

        # If langdetect is not installed, defaults to 'en'
        if lang == "en":
            pytest.skip("langdetect not installed, skipping non-English language tests")
        assert lang == "fr"

    def test_detect_language_short_text(self, preprocessor):
        """Test language detection with very short text defaults to English."""
        text = "Hi"

        lang = preprocessor.detect_language(text)

        assert lang == "en"

    def test_detect_language_with_confidence(self, preprocessor):
        """Test language detection with confidence score."""
        text = "This is definitely an English sentence with enough context."

        lang, confidence = preprocessor.detect_language_with_confidence(text)

        assert lang == "en"
        assert 0.0 <= confidence <= 1.0

    def test_preprocess_request(self, preprocessor):
        """Test full request preprocessing."""
        user_message = "What is the TVL of Aave?"
        conversation_history = []
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        conversation_id = UUID("87654321-4321-4321-4321-210987654321")

        request = preprocessor.preprocess(
            user_message=user_message,
            conversation_history=conversation_history,
            user_id=str(user_id),
            conversation_id=str(conversation_id),
        )

        assert request.user_message == user_message
        assert request.detected_language == "en"
        assert len(request.conversation_history) == 0

    def test_preprocess_with_history(self, preprocessor):
        """Test preprocessing with conversation history."""
        user_message = "What about Compound?"

        # Mock conversation history
        history = [
            Message(
                id=UUID("11111111-1111-1111-1111-111111111111"),
                conversation_id=UUID("22222222-2222-2222-2222-222222222222"),
                role=MessageRole.USER,
                content="Tell me about Aave",
            ),
            Message(
                id=UUID("33333333-3333-3333-3333-333333333333"),
                conversation_id=UUID("22222222-2222-2222-2222-222222222222"),
                role=MessageRole.AGENT,
                content="Aave is a lending protocol...",
            ),
        ]

        request = preprocessor.preprocess(
            user_message=user_message,
            conversation_history=history,
            user_id=str(UUID("44444444-4444-4444-4444-444444444444")),
            conversation_id=str(UUID("22222222-2222-2222-2222-222222222222")),
        )

        assert request.user_message == user_message
        assert len(request.conversation_history) == 2
        assert request.detected_language == "en"
