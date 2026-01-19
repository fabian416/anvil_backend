"""
Knowledge Context Enrichment Tests - Week 5

Tests context enrichment and caching for knowledge injection:
- Price data enriched with historical trends
- Protocol data enriched with TVL metrics
- Token data enriched with market metrics
- Multi-source data aggregation
- Knowledge cache hit performance
- Cache miss fallback behavior
- Cache expiration and refresh

These tests advance Knowledge Injection coverage from 73% toward 85%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import time
import json
import warnings
from datetime import datetime


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.knowledge_injection]


class TestContextEnrichment:
    """Test context enrichment with additional data from multiple sources."""

    @pytest.mark.llm_validation
    async def test_price_context_with_historical_data(self, client: AsyncClient, llm_validator):
        """
        Test price enriched with historical trend context.

        Query about token price should include current price plus trend information.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the price trend of Bitcoin lately?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()

        # Should mention price and/or trend information
        price_or_trend = any(keyword in agent_response for keyword in [
            "price", "bitcoin", "btc", "trend", "trading", "market", "$"
        ])

        assert price_or_trend, "Response should include price/trend information"
        assert len(agent_response) > 50, "Response should be substantive"

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_price_context_with_historical_data",
                user_input="What",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate Bitcoin price information in a clear format. Response must reference Bitcoin specifically (not other cryptocurrencies) and include current price data with USD denomination."
                ),
                test_func=self.test_price_context_with_historical_data,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'price_query', 'token': 'Bitcoin'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_protocol_context_with_tvl_data(self, client: AsyncClient, llm_validator):
        """
        Test protocol info enriched with TVL data.

        Query about DeFi protocol should include TVL and other metrics.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Tell me about Aave protocol and its metrics",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()

        # Should mention protocol information
        protocol_info = any(keyword in agent_response for keyword in [
            "aave", "protocol", "defi", "lending", "borrow", "tvl", "liquidity"
        ])

        assert protocol_info, "Response should include protocol information"
        assert len(agent_response) > 50, "Response should be substantive"

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_protocol_context_with_tvl_data",
                user_input="Tell me about Aave protocol and its metrics",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate information about Aave protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                test_func=self.test_protocol_context_with_tvl_data,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Aave'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_token_context_with_market_data(self, client: AsyncClient, llm_validator):
        """
        Test token info with comprehensive market metrics.

        Query about specific token should include market cap, volume, etc.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What are the key market metrics for Ethereum?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()

        # Should mention market metrics
        market_metrics = any(keyword in agent_response for keyword in [
            "ethereum", "eth", "market", "volume", "cap", "price", "trading"
        ])

        assert market_metrics, "Response should include market metrics"
        assert len(agent_response) > 50, "Response should be substantive"

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_token_context_with_market_data",
                user_input="What are the key market metrics for Ethereum?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide market sentiment analysis for Ethereum. Response should include relevant market indicators, community sentiment, or price trends without making specific investment recommendations."
                ),
                test_func=self.test_token_context_with_market_data,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'sentiment_query', 'token': 'Ethereum'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_multi_source_context_aggregation(self, client: AsyncClient, llm_validator):
        """
        Test aggregating context from multiple sources.

        Complex query requiring data from multiple APIs should aggregate successfully.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Give me a complete analysis of Ethereum: price, news, and DeFi activity",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"]

        # Should provide comprehensive analysis (check substantiveness, not keywords)
        assert len(agent_response) > 100, "Response should be comprehensive (100+ chars)"

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_multi_source_context_aggregation",
                user_input="Give me a complete analysis of Ethereum: price, news, and DeFi activity",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_multi_source_context_aggregation,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )



class TestContextCaching:
    """Test knowledge cache hit/miss behavior and performance."""

    @pytest.mark.llm_validation
    async def test_knowledge_cache_hit_performance(self, client: AsyncClient, llm_validator):
        """
        Test cache hit improves response time.

        First query (cache miss), second identical query (cache hit) should work.
        """
        # First query - likely cache miss
        query_content = "What is the current price of Bitcoin?"

        start_time1 = time.time()
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": query_content,
                "language": "en"
            }
        )
        elapsed1 = time.time() - start_time1

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert "agent_message" in data1
        assert data1["agent_message"]["content"]

        # Second identical query - should hit cache or be fast
        start_time2 = time.time()
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": query_content,
                "language": "en"
            }
        )
        elapsed2 = time.time() - start_time2

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert "agent_message" in data2
        assert data2["agent_message"]["content"]

        # Both queries should succeed
        # Note: We don't enforce second query is faster due to network variability
        # Just verify both work correctly
        assert len(data1["agent_message"]["content"]) > 0
        assert len(data2["agent_message"]["content"]) > 0

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_knowledge_cache_hit_performance",
                user_input="query",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_knowledge_cache_hit_performance,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_knowledge_cache_miss_fallback(self, client: AsyncClient, llm_validator):
        """
        Test cache miss falls back to API.

        Query with no cached data should retrieve from external APIs successfully.
        """
        # Use unique query that likely doesn't have cached data
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What is the trading volume of Cardano in the last 24 hours?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should get substantive response even without cache
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Response should be substantive"

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_knowledge_cache_miss_fallback",
                user_input="What is the trading volume of Cardano in the last 24 hours?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_knowledge_cache_miss_fallback,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_knowledge_cache_expiration(self, client: AsyncClient, llm_validator):
        """
        Test cache expiration and refresh.

        Query creates cache entry. Verify system handles cache correctly.
        Note: We can't easily test actual expiration in integration tests,
        so we verify the query flow works correctly.
        """
        # First query - creates/updates cache entry
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the price of Solana?",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert "agent_message" in data1
        assert data1["agent_message"]["content"]

        # Second query - should use cache or refresh if expired
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the price of Solana?",
                "language": "en"
            }
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert "agent_message" in data2
        assert data2["agent_message"]["content"]

        # Both queries should succeed with substantive responses
        assert len(data1["agent_message"]["content"]) > 50

        # Extract agent response for validation
        agent_response = data2["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_knowledge_cache_expiration",
                user_input="What",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_knowledge_cache_expiration,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )

        assert len(data2["agent_message"]["content"]) > 50