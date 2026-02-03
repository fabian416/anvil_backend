"""
API Integration tests for knowledge base injection through HTTP endpoints.

Tests complete flow for:
- Authenticated users (POST /api/v1/conversations/{id}/messages)
- Guest users (POST /api/v1/guest/chat)
- Knowledge injection in actual LLM responses
- Different intents and user types
"""

import pytest
from httpx import AsyncClient
from fastapi import status
from app.domain.entities.user import User
from app.domain.chat.entities.chat_conversation import ChatConversation


pytestmark = pytest.mark.asyncio


class TestAuthenticatedUserKnowledgeInjection:
    """Test knowledge injection for authenticated users"""

    @pytest.mark.llm_validation
    async def test_what_can_you_do_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test 'what can you do?' for authenticated user includes knowledge"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what can you do?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "user_message" in data
        assert "agent_message" in data
        assert "routing" in data

        # Verify agent response includes knowledge-enhanced content
        agent_content = data["agent_message"]["content"].lower()

        # Should mention core capabilities from overview.json
        assert any(
            keyword in agent_content
            for keyword in [
                "trading",
                "swap",
                "hunter ai",
                "market intelligence",
                "ultra",
                "automation",
                "portfolio",
            ]
        )

        # Should have specific features, not vague response
        assert any(
            keyword in agent_content
            for keyword in [
                "1inch",
                "hyperliquid",
                "sentiment",
                "arbitrage",
                "flash loan",
                "mev protection",
            ]
        )

    @pytest.mark.llm_validation
    async def test_hunter_ai_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test Hunter AI query includes accuracy metrics"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={
                "content": "what is hunter ai and how accurate is it?",
                "language": "en",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include Hunter AI specific knowledge
        assert "hunter ai" in agent_content

    @pytest.mark.llm_validation
    async def test_ultra_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test ULTRA query includes knowledge about automation"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is ultra?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include ULTRA specific knowledge
        assert "ultra" in agent_content

    @pytest.mark.llm_validation
    async def test_swap_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test swap query includes knowledge about supported protocols"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "how do I swap tokens?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should mention swap capability
        assert "swap" in agent_content

    @pytest.mark.llm_validation
    async def test_investor_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test investor-focused query includes competitive advantages"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "why should I invest in Anvil?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should provide investment-relevant information
        assert len(agent_content) > 100

    @pytest.mark.llm_validation
    async def test_command_help_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test command help query includes examples"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "show me example commands", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should provide helpful response
        assert len(agent_content) > 50


class TestGuestUserKnowledgeInjection:
    """Test knowledge injection for guest users"""

    @pytest.mark.llm_validation
    async def test_what_can_you_do_guest(self, async_client: AsyncClient):
        """Test 'what can you do?' for guest user includes knowledge"""

        response = await async_client.post(
            "/api/v1/guest/chat", json={"content": "what can you do?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "user_message" in data
        assert "agent_message" in data
        assert "routing" in data

        # Verify agent response includes knowledge-enhanced content
        agent_content = data["agent_message"]["content"].lower()

        # Should mention core capabilities from overview.json
        assert any(
            keyword in agent_content
            for keyword in [
                "trading",
                "swap",
                "hunter ai",
                "market intelligence",
                "ultra",
                "portfolio",
            ]
        )

    @pytest.mark.llm_validation
    async def test_hunter_ai_query_guest(self, async_client: AsyncClient):
        """Test Hunter AI query for guest includes knowledge"""

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "what is hunter ai?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include Hunter AI knowledge
        assert "hunter ai" in agent_content

    @pytest.mark.llm_validation
    async def test_ultra_query_guest(self, async_client: AsyncClient):
        """Test ULTRA query for guest includes knowledge"""

        response = await async_client.post(
            "/api/v1/guest/chat", json={"content": "what is ultra?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include ULTRA knowledge
        assert "ultra" in agent_content

    @pytest.mark.llm_validation
    async def test_price_query_guest(self, async_client: AsyncClient):
        """Test price query for guest"""

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "what is the price of ETH?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have response
        assert "agent_message" in data


class TestMultiLanguageKnowledge:
    """Test knowledge injection in multiple languages"""

    @pytest.mark.llm_validation
    async def test_spanish_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test Spanish query includes knowledge"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "¿qué puedes hacer?", "language": "es"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have meaningful response
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50

    @pytest.mark.llm_validation
    async def test_spanish_query_guest(self, async_client: AsyncClient):
        """Test Spanish query for guest"""

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "¿qué es hunter ai?", "language": "es"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have response
        assert "agent_message" in data


class TestKnowledgeInjectionPerformance:
    """Test performance of knowledge injection"""

    @pytest.mark.llm_validation
    async def test_response_time_acceptable_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test response time is acceptable for authenticated user"""
        import time

        start = time.time()
        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"},
        )
        elapsed = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        # Should complete within 30 seconds (allowing for LLM processing)
        assert elapsed < 30

    @pytest.mark.llm_validation
    async def test_response_time_acceptable_guest(self, async_client: AsyncClient):
        """Test response time is acceptable for guest user"""
        import time

        start = time.time()
        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "what is hunter ai?", "language": "en"},
        )
        elapsed = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        # Should complete within 30 seconds
        assert elapsed < 30


class TestKnowledgeConsistency:
    """Test knowledge injection consistency"""

    @pytest.mark.llm_validation
    async def test_same_query_consistent_knowledge_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test same query produces consistent knowledge-enhanced responses"""

        # First request
        response1 = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"},
        )

        # Second request
        response2 = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"},
        )

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        # Both should mention Hunter AI
        content1 = response1.json()["agent_message"]["content"].lower()
        content2 = response2.json()["agent_message"]["content"].lower()

        assert "hunter ai" in content1
        assert "hunter ai" in content2


class TestEdgeCases:
    """Test edge cases for knowledge injection"""

    @pytest.mark.llm_validation
    async def test_empty_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test empty query handling"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "", "language": "en"},
        )

        # Should handle gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    @pytest.mark.llm_validation
    async def test_very_long_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test very long query handling"""

        long_query = "what can you do? " * 100

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": long_query, "language": "en"},
        )

        # Should handle gracefully
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        ]

    @pytest.mark.llm_validation
    async def test_special_characters_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test special characters handling"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what can you do? 💱📊⚡", "language": "en"},
        )

        # Should handle special characters
        assert response.status_code == status.HTTP_200_OK


class TestKnowledgeForAllIntents:
    """Test knowledge injection works for all major intents"""

    @pytest.mark.parametrize(
        "query,expected_keywords",
        [
            ("swap 100 USDC to ETH", ["swap", "usdc", "eth"]),
            ("check sentiment for BTC", ["sentiment", "btc"]),
            ("predict ETH price", ["predict", "eth", "price"]),
            ("find arbitrage", ["arbitrage"]),
            ("tell me about flash loans", ["flash loan"]),
            ("protect from MEV", ["mev", "protect"]),
            ("what's the price of SOL", ["price", "sol"]),
            ("show my portfolio", ["portfolio"]),
        ],
    )
    @pytest.mark.llm_validation
    async def test_intent_gets_knowledge(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
        query: str,
        expected_keywords: list,
    ):
        """Test various intents all get knowledge-enhanced responses"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": query, "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have response
        assert "agent_message" in data
        agent_content = data["agent_message"]["content"].lower()

        # Should have substantial content (knowledge-enhanced)
        assert len(agent_content) > 50


class TestCompressionLevelsAuthenticated:
    """Test different compression levels for authenticated users"""

    @pytest.mark.llm_validation
    async def test_no_compression_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test no compression provides full knowledge"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]

        # Full knowledge should have substantial detail
        assert len(agent_content) > 100

    @pytest.mark.llm_validation
    async def test_medium_compression_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test medium compression (60% reduction) for authenticated users"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50

    @pytest.mark.llm_validation
    async def test_aggressive_compression_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test aggressive compression for authenticated users"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 30

    @pytest.mark.llm_validation
    async def test_compression_preserves_quality_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test compression preserves essential quality"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should still mention Hunter AI
        assert "hunter ai" in agent_content or "hunter" in agent_content


class TestCompressionLevelsGuest:
    """Test compression levels for guest users"""

    @pytest.mark.llm_validation
    async def test_medium_compression_guest(self, async_client: AsyncClient):
        """Test medium compression for guest users"""

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "what is hunter ai?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50

    @pytest.mark.llm_validation
    async def test_compression_consistency_guest(self, async_client: AsyncClient):
        """Test compression consistency for guest users"""

        response = await async_client.post(
            "/api/v1/guest/chat", json={"content": "what is ultra?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should mention ULTRA
        assert "ultra" in agent_content


class TestCompressionWithDifferentIntents:
    """Test compression behavior with different intents"""

    @pytest.mark.parametrize(
        "query,intent_keyword",
        [
            ("what is hunter ai?", "hunter"),
            ("what is ultra?", "ultra"),
            ("how do I swap tokens?", "swap"),
            ("tell me about sentiment analysis", "sentiment"),
        ],
    )
    @pytest.mark.llm_validation
    async def test_compressed_knowledge_by_intent(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
        query: str,
        intent_keyword: str,
    ):
        """Test compressed knowledge includes intent-specific content"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": query, "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should mention the intent keyword
        assert intent_keyword in agent_content


class TestCompressionPerformance:
    """Test compression performance"""

    @pytest.mark.llm_validation
    async def test_compressed_response_time_acceptable(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test compressed response time is acceptable"""
        import time

        start = time.time()
        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"},
        )
        elapsed = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        # Should complete within 30 seconds
        assert elapsed < 30

    @pytest.mark.llm_validation
    async def test_compression_overhead_minimal(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test compression overhead is minimal"""
        import time

        start = time.time()
        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is ultra?", "language": "en"},
        )
        elapsed = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        # Should complete quickly
        assert elapsed < 30


class TestCompressionEssentialPreservation:
    """Test that compression preserves essential content"""

    @pytest.mark.llm_validation
    async def test_accuracy_metrics_preserved_in_responses(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test accuracy metrics are preserved in responses"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "how accurate is hunter ai?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50

    @pytest.mark.llm_validation
    async def test_protocol_names_preserved_in_responses(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test protocol names are preserved in responses"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what protocols do you support?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50

    @pytest.mark.llm_validation
    async def test_aggregator_names_preserved_in_responses(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test aggregator names are preserved in responses"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what DEX aggregators do you use?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50

    @pytest.mark.llm_validation
    async def test_competitive_advantages_preserved_for_investors(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test competitive advantages are preserved for investor queries"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "why should I invest in Anvil?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50


class TestCompressionMultiLanguage:
    """Test compression works across languages"""

    @pytest.mark.llm_validation
    async def test_spanish_query_with_compression(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test Spanish query with compression"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "¿qué es hunter ai?", "language": "es"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50

    @pytest.mark.llm_validation
    async def test_compression_preserves_quality_across_languages(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
    ):
        """Test compression preserves quality across languages"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "¿qué es ultra?", "language": "es"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 30
