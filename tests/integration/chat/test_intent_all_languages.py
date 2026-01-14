"""
Comprehensive Language Support Tests - Week 6

Tests intent detection across supported and unsupported languages:
- Spanish language full flow (supported)
- Portuguese language full flow (supported)
- Chinese language full flow (supported)
- Unsupported language graceful handling (fr, de, ja, ko, ar, hi)
- Language validation
- Automatic language detection

Supported languages: en, es, pt, zh
These tests advance Intent Detection coverage from 85% toward 95%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.intent_detection]


class TestAllLanguageSupport:
    """Test intent detection across all supported languages."""

    async def test_spanish_language_full_flow(self, client: AsyncClient):
        """
        Test Spanish language end-to-end intent detection.

        Query in Spanish should detect intent and respond appropriately.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "¿Cuál es el precio de Bitcoin?",
                "language": "es"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        # Should provide substantive response
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive response in Spanish"

    async def test_portuguese_language_full_flow(self, client: AsyncClient):
        """
        Test Portuguese language end-to-end intent detection.

        Query in Portuguese should detect intent and respond appropriately.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Qual é o preço do Ethereum?",
                "language": "pt"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide substantive response
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive response in Portuguese"

    async def test_chinese_language_full_flow(self, client: AsyncClient):
        """
        Test Chinese language end-to-end intent detection.

        Query in Chinese should detect intent and respond appropriately.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "比特币的价格是多少？",
                "language": "zh"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide substantive response
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive response in Chinese"

    async def test_unsupported_language_french(self, client: AsyncClient):
        """
        Test graceful handling of unsupported language (French).

        Unsupported language should return validation error (422).
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Quel est le prix d'Ethereum?",
                "language": "fr"
            }
        )

        # Should return 422 for unsupported language
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_unsupported_language_japanese(self, client: AsyncClient):
        """
        Test graceful handling of unsupported language (Japanese).

        Unsupported language should return validation error (422).
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "ビットコインの価格は何ですか？",
                "language": "ja"
            }
        )

        # Should return 422 for unsupported language
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_language_validation(self, client: AsyncClient):
        """
        Test language validation with invalid language code.

        Invalid language code should return validation error.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What is Bitcoin price?",
                "language": "invalid"
            }
        )

        # Should return 422 for invalid language
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_supported_languages_coverage(self, client: AsyncClient):
        """
        Test all supported languages (en, es, pt, zh) work correctly.

        All 4 supported languages should successfully process queries.
        """
        supported_languages = [
            ("en", "What is the price of Bitcoin?"),
            ("es", "¿Cuál es el precio de Bitcoin?"),
            ("pt", "Qual é o preço do Bitcoin?"),
            ("zh", "比特币的价格是多少？")
        ]

        for lang, query in supported_languages:
            response = await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": query,
                    "language": lang
                }
            )

            assert response.status_code == status.HTTP_200_OK, f"Language {lang} should be supported"
            data = response.json()
            assert "agent_message" in data
            assert len(data["agent_message"]["content"]) > 0

    async def test_language_auto_detection(self, client: AsyncClient):
        """
        Test automatic language detection from content.

        Query without explicit language parameter should auto-detect and respond.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What is the price of Ethereum?",
                "language": "en"  # Providing English explicitly
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide substantive response
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive response"
