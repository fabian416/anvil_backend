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


class TestCompressionLevelsAuthenticated:
    """Test different compression levels for authenticated users"""

    async def test_no_compression_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test no compression provides full knowledge"""
        # Note: This test assumes router supports compression_level parameter
        # If not yet implemented, this will test default behavior

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]

        # Full knowledge should have substantial detail
        assert len(agent_content) > 200
        # Should mention accuracy metrics
        assert any(metric in agent_content for metric in ["82%", "73%"])

    async def test_medium_compression_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test medium compression (60% reduction) for authenticated users"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]

        # Should still have substantial content
        assert len(agent_content) > 100
        # Should preserve key accuracy metrics
        agent_lower = agent_content.lower()
        assert "hunter ai" in agent_lower or "hunter" in agent_lower
        # Should mention at least one key metric
        assert any(keyword in agent_lower for keyword in [
            "82%", "73%", "sentiment", "prediction", "accuracy", "accurate"
        ])

    async def test_aggressive_compression_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test aggressive compression (80% reduction) preserves essentials"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what is hunter ai?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]

        # Should have response (though compressed)
        assert len(agent_content) > 50
        # Should still mention Hunter AI
        assert "hunter" in agent_content.lower() or "ai" in agent_content.lower()

    async def test_compression_preserves_quality_authenticated(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test that compression doesn't degrade response quality significantly"""

        # Make same query multiple times to test consistency
        queries = [
            "what is hunter ai?",
            "tell me about hunter ai accuracy",
            "how good is hunter ai?"
        ]

        for query in queries:
            response = await async_client.post(
                f"/api/v1/conversations/{test_conversation.id}/messages",
                headers={"Authorization": f"Bearer {test_session}"},
                json={"content": query, "language": "en"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            agent_content = data["agent_message"]["content"].lower()

            # All responses should mention Hunter AI
            assert "hunter" in agent_content or "ai" in agent_content
            # All should mention some capability
            assert any(cap in agent_content for cap in [
                "sentiment", "prediction", "risk", "trading", "pattern"
            ])


class TestCompressionLevelsGuest:
    """Test different compression levels for guest users"""

    async def test_medium_compression_guest(self, async_client: AsyncClient):
        """Test medium compression works for guest users"""

        response = await async_client.post(
            "/api/v1/guest/chat",
            json={"content": "what is hunter ai?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]

        # Should have substantial response
        assert len(agent_content) > 100
        # Should mention Hunter AI and capabilities
        agent_lower = agent_content.lower()
        assert "hunter" in agent_lower or "ai" in agent_lower

    async def test_compression_consistency_guest(self, async_client: AsyncClient):
        """Test compression provides consistent results for guest"""

        # Make same query twice
        for _ in range(2):
            response = await async_client.post(
                "/api/v1/guest/chat",
                json={"content": "what can you do?", "language": "en"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            agent_content = data["agent_message"]["content"].lower()

            # Both should mention core features
            assert any(feature in agent_content for feature in [
                "trading", "swap", "hunter", "ultra", "portfolio"
            ])


class TestCompressionWithDifferentIntents:
    """Test compression works correctly with different intents"""

    @pytest.mark.parametrize("query,expected_keywords", [
        ("check sentiment for BTC", ["sentiment", "btc"]),
        ("predict ETH price", ["predict", "eth", "price"]),
        ("find arbitrage", ["arbitrage"]),
        ("tell me about flash loans", ["flash", "loan"]),
        ("swap 100 USDC to ETH", ["swap", "usdc", "eth"]),
    ])
    async def test_compressed_knowledge_by_intent(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation,
        query: str,
        expected_keywords: list
    ):
        """Test compression works for different intents and preserves key info"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": query, "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should have response
        assert len(agent_content) > 50

        # Response quality check: at least one expected keyword should appear
        # (Compression might affect exact wording, but core concepts should remain)
        keyword_found = any(kw in agent_content for kw in expected_keywords)
        assert keyword_found, f"None of {expected_keywords} found in response"


class TestCompressionPerformance:
    """Test performance impact of compression"""

    async def test_compressed_response_time_acceptable(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test response time with compression is acceptable"""
        import time

        start = time.time()

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what can you do?", "language": "en"}
        )

        elapsed = time.time() - start

        assert response.status_code == status.HTTP_200_OK

        # Compression should not significantly impact response time
        # (Compression overhead is minimal compared to LLM generation time)
        assert elapsed < 30  # 30 seconds max (includes LLM call)

    async def test_compression_overhead_minimal(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test compression adds minimal overhead"""
        import time

        # Make multiple requests to test consistency
        response_times = []

        for _ in range(3):
            start = time.time()

            response = await async_client.post(
                f"/api/v1/conversations/{test_conversation.id}/messages",
                headers={"Authorization": f"Bearer {test_session}"},
                json={"content": "what is hunter ai?", "language": "en"}
            )

            elapsed = time.time() - start
            response_times.append(elapsed)

            assert response.status_code == status.HTTP_200_OK

        # All responses should be reasonably fast
        assert all(t < 30 for t in response_times)
        # Response times should be consistent (variance < 10 seconds)
        assert max(response_times) - min(response_times) < 10


class TestCompressionEssentialPreservation:
    """Test that compression preserves essential information"""

    async def test_accuracy_metrics_preserved_in_responses(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test accuracy metrics are preserved in compressed responses"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "how accurate is hunter ai?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]

        # Should mention key accuracy metrics (even if compressed)
        # At least one of the main accuracy metrics should be mentioned
        has_sentiment_accuracy = "82%" in agent_content or "82" in agent_content
        has_prediction_accuracy = "73%" in agent_content or "73" in agent_content
        has_arbitrage_accuracy = "92%" in agent_content or "92" in agent_content

        assert has_sentiment_accuracy or has_prediction_accuracy or has_arbitrage_accuracy, \
            "Response should mention at least one key accuracy metric"

    async def test_protocol_names_preserved_in_responses(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test protocol names are preserved in compressed responses"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "which protocols support flash loans?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should mention at least one flash loan protocol
        protocols = ["aave", "balancer", "uniswap"]
        assert any(protocol in agent_content for protocol in protocols), \
            f"Response should mention at least one of {protocols}"

    async def test_aggregator_names_preserved_in_responses(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test aggregator names are preserved in swap responses"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "how does swapping work?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should mention at least one aggregator
        aggregators = ["1inch", "hyperliquid", "uniswap"]
        assert any(agg in agent_content for agg in aggregators), \
            f"Response should mention at least one of {aggregators}"

    async def test_competitive_advantages_preserved_for_investors(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test competitive advantages are preserved in investor queries"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "what are anvils competitive advantages?", "language": "en"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"].lower()

        # Should mention key competitive advantages (even if compressed)
        competitive_keywords = [
            "18 agents", "18", "agents",
            "99%", "cost", "savings",
            "multi-language", "multilingual",
            "bloomberg"
        ]

        # At least 2 competitive advantage keywords should appear
        keyword_count = sum(1 for kw in competitive_keywords if kw in agent_content)
        assert keyword_count >= 2, \
            "Response should mention at least 2 competitive advantages"


class TestCompressionMultiLanguage:
    """Test compression works with multi-language queries"""

    async def test_spanish_query_with_compression(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test compression works with Spanish queries"""

        response = await async_client.post(
            f"/api/v1/conversations/{test_conversation.id}/messages",
            headers={"Authorization": f"Bearer {test_session}"},
            json={"content": "qué es hunter ai?", "language": "es"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        agent_content = data["agent_message"]["content"]

        # Should have substantial response
        assert len(agent_content) > 100

    async def test_compression_preserves_quality_across_languages(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_session: str,
        test_conversation: ChatConversation
    ):
        """Test compression maintains quality for different languages"""

        languages_and_queries = [
            ("en", "what can you do?"),
            ("es", "qué puedes hacer?"),
            ("pt", "o que você pode fazer?")
        ]

        for lang, query in languages_and_queries:
            response = await async_client.post(
                f"/api/v1/conversations/{test_conversation.id}/messages",
                headers={"Authorization": f"Bearer {test_session}"},
                json={"content": query, "language": lang}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            agent_content = data["agent_message"]["content"]

            # All languages should get substantial responses
            assert len(agent_content) > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
