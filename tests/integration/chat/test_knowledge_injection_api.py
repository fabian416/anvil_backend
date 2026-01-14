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
from app.main import app
from app.domain.user.entities import User
from app.domain.chat.value_objects import ChatConversation
from tests.fixtures.user_fixtures import test_user, test_session
from tests.fixtures.chat_fixtures import test_conversation


pytestmark = pytest.mark.asyncio


class TestAuthenticatedUserKnowledgeInjection:
    """Test knowledge injection for authenticated users"""

    async def test_what_can_you_do_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test 'what can you do?' for authenticated user includes knowledge"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what can you do?", "language": "en"}
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
        assert any(keyword in agent_content for keyword in [
            "trading", "swap", "hunter ai", "market intelligence",
            "ultra", "automation", "portfolio"
        ])

        # Should have specific features, not vague response
        assert any(keyword in agent_content for keyword in [
            "1inch", "hyperliquid", "sentiment", "arbitrage",
            "flash loan", "mev protection"
        ])

    async def test_hunter_ai_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test Hunter AI query includes accuracy metrics"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai and how accurate is it?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include Hunter AI specific knowledge
        assert "hunter ai" in agent_content

        # Should include accuracy metrics from hunter_ai.json
        assert any(keyword in agent_content for keyword in [
            "82%", "73%", "accuracy", "accurate", "correlation"
        ])

        # Should mention data sources
        assert any(keyword in agent_content for keyword in [
            "twitter", "reddit", "news", "sentiment", "prediction"
        ])

    async def test_ultra_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test ULTRA query includes detailed capabilities"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "tell me about flash loans and which protocols you support", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include ULTRA flash loan knowledge
        assert "flash loan" in agent_content

        # Should mention specific protocols from ultra.json
        assert any(protocol in agent_content for protocol in [
            "aave", "balancer", "uniswap"
        ])

        # Should mention fees
        assert any(keyword in agent_content for keyword in [
            "0%", "fee", "0.09%"
        ])

    async def test_swap_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test swap query includes aggregator information"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "how does swapping work on anvil?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include swap process from swap.json
        assert "swap" in agent_content

        # Should mention aggregators
        assert any(aggregator in agent_content for aggregator in [
            "1inch", "hyperliquid", "uniswap"
        ])

        # Should mention features
        assert any(feature in agent_content for keyword in [
            "rate", "gas", "mev", "protection", "slippage"
        ])

    async def test_investor_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test investor query includes competitive advantages"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what are anvils competitive advantages?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include investor-specific knowledge
        assert any(keyword in agent_content for keyword in [
            "competitive", "advantage", "market", "opportunity"
        ])

        # Should mention specific advantages from overview.json
        assert any(keyword in agent_content for keyword in [
            "18 agents", "99%", "cost", "multi-language", "bloomberg"
        ])

    async def test_command_help_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test command help includes shortcuts"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "how do I check bitcoin price?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include command examples from shortcuts.json
        assert any(keyword in agent_content for keyword in [
            "price", "btc", "bitcoin", "command"
        ])

        # Should show example command
        assert any(example in agent_content for example in [
            "what's the price", "price of btc", "btc price"
        ])


class TestGuestUserKnowledgeInjection:
    """Test knowledge injection for guest users"""

    async def test_what_can_you_do_guest(self, async_client: AsyncClient):
        """Test 'what can you do?' for guest user includes knowledge"""

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "what can you do?", "language": "en"}
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
        assert any(keyword in agent_content for keyword in [
            "trading", "swap", "hunter ai", "market intelligence",
            "ultra", "portfolio"
        ])

        # Should have specific features
        assert any(keyword in agent_content for keyword in [
            "sentiment", "arbitrage", "price", "flash loan"
        ])

    async def test_hunter_ai_query_guest(self, async_client: AsyncClient):
        """Test Hunter AI query for guest includes knowledge"""

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "what is hunter ai?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include Hunter AI knowledge
        assert "hunter ai" in agent_content

        # Should mention capabilities
        assert any(keyword in agent_content for keyword in [
            "sentiment", "prediction", "risk", "trading signals"
        ])

    async def test_ultra_query_guest(self, async_client: AsyncClient):
        """Test ULTRA query for guest includes knowledge"""

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "what is ultra?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should include ULTRA knowledge
        assert "ultra" in agent_content

        # Should mention capabilities
        assert any(keyword in agent_content for keyword in [
            "arbitrage", "flash loan", "mev", "automation"
        ])

    async def test_price_query_guest(self, async_client: AsyncClient):
        """Test price query for guest works with knowledge"""

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "what's the price of BTC?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should route to price query, not need knowledge injection for simple price
        assert "routing" in data
        # Price query should work normally


class TestMultiLanguageKnowledge:
    """Test knowledge injection works with multi-language queries"""

    async def test_spanish_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test Spanish query gets knowledge-enhanced response"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "qué puedes hacer?", "language": "es"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should still work and include knowledge
        assert "agent_message" in data
        agent_content = data["agent_message"]["content"]

        # Response should be in Spanish (if LLM supports it)
        # At minimum, should have comprehensive answer
        assert len(agent_content) > 100

    async def test_spanish_query_guest(self, async_client: AsyncClient):
        """Test Spanish query for guest gets knowledge-enhanced response"""

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "qué es hunter ai?", "language": "es"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should work with knowledge injection
        assert "agent_message" in data


class TestKnowledgeInjectionPerformance:
    """Test performance impact of knowledge injection"""

    async def test_response_time_acceptable_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test response time with knowledge injection is acceptable"""
        import time

        start = time.time()

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what can you do?", "language": "en"}
        )

        elapsed = time.time() - start

        assert response.status_code == status.HTTP_200_OK

        # Should respond in reasonable time (knowledge injection adds ~100-500ms)
        # Total time includes LLM call, so this is just a sanity check
        assert elapsed < 30  # 30 seconds max (includes LLM generation)

    async def test_response_time_acceptable_guest(self, async_client: AsyncClient):
        """Test response time for guest with knowledge injection"""
        import time

        start = time.time()

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "what can you do?", "language": "en"}
        )

        elapsed = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        assert elapsed < 30


class TestKnowledgeConsistency:
    """Test knowledge injection provides consistent results"""

    async def test_same_query_consistent_knowledge_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test same query gets consistent knowledge injection"""

        # Make same query twice
        response1 = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"}
        )

        response2 = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"}
        )

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        data1 = response1.json()
        data2 = response2.json()

        # Both should have substantial responses (knowledge-enhanced)
        content1 = data1["agent_message"]["content"]
        content2 = data2["agent_message"]["content"]

        assert len(content1) > 100
        assert len(content2) > 100

        # Both should mention similar key concepts (Hunter AI capabilities)
        content1_lower = content1.lower()
        content2_lower = content2.lower()

        hunter_ai_keywords = ["sentiment", "prediction", "risk", "trading"]

        # At least 2 keywords should appear in both responses
        keywords_in_1 = sum(1 for kw in hunter_ai_keywords if kw in content1_lower)
        keywords_in_2 = sum(1 for kw in hunter_ai_keywords if kw in content2_lower)

        assert keywords_in_1 >= 2
        assert keywords_in_2 >= 2


class TestEdgeCases:
    """Test edge cases for knowledge injection"""

    async def test_empty_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test empty query doesn't crash knowledge injection"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "", "language": "en"}
        )

        # Should handle gracefully (validation error or default response)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    async def test_very_long_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test very long query with knowledge injection"""

        long_query = "what can you do? " * 50  # Very long query

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": long_query, "language": "en"}
        )

        # Should handle without crashing
        assert response.status_code == status.HTTP_200_OK

    async def test_special_characters_query_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test query with special characters"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what can you do? 💱📊⚡", "language": "en"}
        )

        # Should handle special characters
        assert response.status_code == status.HTTP_200_OK


class TestKnowledgeForAllIntents:
    """Test knowledge injection works for all major intents"""

    @pytest.mark.parametrize("query,expected_keywords", [
        ("swap 100 USDC to ETH", ["swap", "usdc", "eth"]),
        ("check sentiment for BTC", ["sentiment", "btc"]),
        ("predict ETH price", ["predict", "eth", "price"]),
        ("find arbitrage", ["arbitrage"]),
        ("tell me about flash loans", ["flash loan"]),
        ("protect from MEV", ["mev", "protect"]),
        ("what's the price of SOL", ["price", "sol"]),
        ("show my portfolio", ["portfolio"]),
    ])
    async def test_intent_gets_knowledge(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
        query: str,
        expected_keywords: list
    ):
        """Test various intents all get knowledge-enhanced responses"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": query, "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have response
        assert "agent_message" in data
        agent_content = data["agent_message"]["content"].lower()

        # Should have substantial content (knowledge-enhanced)
        assert len(agent_content) > 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
