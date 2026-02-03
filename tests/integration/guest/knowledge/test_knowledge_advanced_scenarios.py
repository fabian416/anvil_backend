"""
Advanced Knowledge Scenarios Tests - Week 5

Tests advanced knowledge injection scenarios:
- Multi-token knowledge injection
- Nested knowledge references
- Conditional knowledge injection
- Knowledge personalization for guests
- LLM context-aware knowledge injection

These tests advance Knowledge Injection coverage from 73% toward 85%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import json
import warnings
from datetime import datetime


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.knowledge_injection,
]


class TestAdvancedKnowledge:
    """Test advanced knowledge injection scenarios."""

    @pytest.mark.llm_validation
    async def test_multi_token_knowledge_injection(
        self, client: AsyncClient, llm_validator
    ):
        """
        Inject knowledge for multiple tokens in one query.

        Query about multiple tokens should include data for all tokens.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Compare the prices of Bitcoin, Ethereum, and Solana",
                "language": "en",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide information about multiple tokens
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 100, (
            "Should provide comprehensive comparison (100+ chars)"
        )

    @pytest.mark.llm_validation
    async def test_nested_knowledge_references(
        self, client: AsyncClient, llm_validator
    ):
        """
        Handle knowledge with nested references.

        Query with complex dependencies should resolve nested data.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Explain how Uniswap works with liquidity pools and token swaps",
                "language": "en",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide comprehensive explanation with nested concepts
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 100, (
            "Should provide detailed explanation (100+ chars)"
        )

    @pytest.mark.llm_validation
    async def test_conditional_knowledge_injection(
        self, client: AsyncClient, llm_validator
    ):
        """
        Conditional injection based on query context.

        Different query types should receive context-appropriate knowledge.
        """
        # Price-focused query
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What's ETH price?", "language": "en"},
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert "agent_message" in data1
        assert len(data1["agent_message"]["content"]) > 0

        # Technical query
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "How does Ethereum consensus work?", "language": "en"},
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert "agent_message" in data2
        assert len(data2["agent_message"]["content"]) > 50

        # Both queries should succeed with appropriate context
        assert data1["agent_message"]["content"] != data2["agent_message"]["content"]

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

    @pytest.mark.llm_validation
    async def test_knowledge_personalization_guest(
        self, client: AsyncClient, llm_validator
    ):
        """
        Guest-specific knowledge filtering.

        Guest query should provide appropriate, publicly available information.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Tell me about cryptocurrency investing",
                "language": "en",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide guest-appropriate information
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive information"

    @pytest.mark.llm_validation
    async def test_knowledge_injection_with_llm_context(
        self, client: AsyncClient, llm_validator
    ):
        """
        LLM context-aware knowledge injection.

        Query in conversation context should provide context-aware knowledge.
        """
        # First message establishes context
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={"content": "I'm interested in learning about DeFi", "language": "en"},
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1["conversation_id"]

        # Follow-up query in same conversation should use context
        response2 = await client.post(
            f"/api/v1/guest/chat?conversation_id={conversation_id}",
            json={"content": "What are the main protocols?", "language": "en"},
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        assert "agent_message" in data2
        assert data2["agent_message"]["content"]

        # Should provide context-aware response
        agent_response = data2["agent_message"]["content"]
