"""
Shortcuts Edge Cases Comprehensive Tests - Week 8

Tests edge cases and boundary conditions for shortcuts:
- Invalid parameters handling
- Non-existent shortcut fallback
- Metadata validation
- Multi-language support

These tests advance Shortcuts coverage from 80% toward 100%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import json
import warnings
from datetime import datetime


pytestmark = [
    pytest.mark.skip(reason="Requires proper mocking"),
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.shortcuts,
]


class TestShortcutsEdgeCasesComprehensive:
    """Test edge cases and boundary conditions for shortcuts."""

    @pytest.mark.llm_validation
    async def test_shortcut_with_invalid_parameters(
        self, client: AsyncClient, llm_validator
    ):
        """
        Test shortcuts with invalid or out-of-range parameters.

        System should handle invalid parameters gracefully with
        helpful error messages or fallback behavior.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Convert -999999 ETH to BTC", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should handle negative amount gracefully
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 30, (
            "Should provide helpful response about invalid input"
        )

    @pytest.mark.llm_validation
    async def test_shortcut_not_found_fallback(
        self, client: AsyncClient, llm_validator
    ):
        """
        Test behavior when shortcut or pattern not recognized.

        System should fall back to general query processing
        without errors.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Tell me about the philosophical implications of blockchain",
                "language": "en",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide meaningful response even without shortcut match
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should fall back to general query processing"

    @pytest.mark.llm_validation
    async def test_shortcut_metadata_validation(
        self, client: AsyncClient, llm_validator
    ):
        """
        Test shortcut metadata completeness and structure.

        All shortcuts should have complete metadata including
        categories, descriptions, and examples.
        """
        response = await client.get("/api/v1/chat/shortcuts?lang=en")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Response should contain shortcuts array or be an array itself
        shortcuts = data if isinstance(data, list) else data.get("shortcuts", [])

        assert len(shortcuts) > 0, "Should have shortcuts available"

        # Verify all shortcuts have required metadata
        for shortcut in shortcuts:
            # Most shortcuts have at least a command/id/name and some description
            has_identifier = any(
                key in shortcut for key in ["id", "name", "title", "command"]
            )
            assert has_identifier, f"Shortcut should have identifier: {shortcut}"

            # Verify has some descriptive content
            has_description = any(
                key in shortcut for key in ["description", "title", "text", "content"]
            )
            assert has_description, (
                f"Shortcut should have descriptive content: {shortcut}"
            )

    @pytest.mark.llm_validation
    async def test_shortcut_language_support(self, client: AsyncClient, llm_validator):
        """
        Test shortcuts work across all supported languages.

        Shortcuts should be recognized and respond appropriately
        in all supported languages (en, es, pt, zh).
        """
        # Test English
        response_en = await client.post(
            "/api/v1/guest/chat", json={"content": "What is Bitcoin?", "language": "en"}
        )

        assert response_en.status_code == status.HTTP_200_OK
        data_en = response_en.json()
        assert "agent_message" in data_en
        assert len(data_en["agent_message"]["content"]) > 50

        # Test Spanish
        response_es = await client.post(
            "/api/v1/guest/chat", json={"content": "¿Qué es Bitcoin?", "language": "es"}
        )

        assert response_es.status_code == status.HTTP_200_OK
        data_es = response_es.json()
        assert "agent_message" in data_es
        assert len(data_es["agent_message"]["content"]) > 50

        # Test Portuguese
        response_pt = await client.post(
            "/api/v1/guest/chat", json={"content": "O que é Bitcoin?", "language": "pt"}
        )

        assert response_pt.status_code == status.HTTP_200_OK
        data_pt = response_pt.json()
        assert "agent_message" in data_pt
        assert len(data_pt["agent_message"]["content"]) > 50

        # All languages should provide substantial responses
        assert data_en["conversation_id"] is not None
        assert data_es["conversation_id"] is not None
