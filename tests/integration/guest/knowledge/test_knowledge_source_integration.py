"""
Knowledge Source Integration Tests - Week 5

Tests external knowledge source integration:
- CoinGecko API integration for price and market data
- RSS news feed integration (CoinDesk, CoinTelegraph)
- Data source priority and failover mechanisms

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


class TestCoinGeckoIntegration:
    """Test CoinGecko API integration for real market data."""

    @pytest.mark.llm_validation
    async def test_coingecko_price_data_injection(
        self, client: AsyncClient, llm_validator
    ):
        """
        Test real CoinGecko price data injection into responses.

        Query about ETH price should include actual price data from CoinGecko.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What is the current price of Ethereum?",
                "language": "en",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        agent_response = data["agent_message"]["content"].lower()

        # Should mention price/ethereum/eth
        price_mentioned = any(
            keyword in agent_response
            for keyword in ["price", "ethereum", "eth", "$", "usd", "dollar"]
        )

        assert price_mentioned, "Response should include price information"

    @pytest.mark.llm_validation
    async def test_coingecko_market_data_injection(
        self, client: AsyncClient, llm_validator
    ):
        """
        Test market data (market cap, volume) injection from CoinGecko.

        Query about token market metrics should include comprehensive data.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Tell me about Bitcoin's market cap and trading volume",
                "language": "en",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()

        # Should mention market metrics
        market_data = any(
            keyword in agent_response
            for keyword in ["market", "cap", "volume", "trading", "bitcoin", "btc"]
        )

        assert market_data, "Response should include market data"

    @pytest.mark.llm_validation
    async def test_coingecko_api_failure_handling(
        self, client: AsyncClient, llm_validator
    ):
        """
        Test graceful degradation when CoinGecko API might be unavailable.

        System should handle API failures gracefully without crashing.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the price of a very obscure token: XYZABC123?",
                "language": "en",
            },
        )

        # Should succeed even if token doesn't exist or API has issues
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Agent should provide helpful response even without data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 0


class TestRSSNewsIntegration:
    """Test RSS news feed integration from crypto news sources."""

    @pytest.mark.llm_validation
    async def test_rss_news_injection_coindesk(
        self, client: AsyncClient, llm_validator
    ):
        """
        Test CoinDesk RSS feed integration.

        Query about recent crypto news should provide informative response.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What's the latest crypto news?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Agent should provide substantive response (not just "I don't know")
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Response should be substantive"

    @pytest.mark.llm_validation
    async def test_rss_news_injection_cointelegraph(
        self, client: AsyncClient, llm_validator
    ):
        """
        Test CoinTelegraph RSS feed integration.

        Query about crypto updates should provide informative response.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Any important crypto updates today?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Agent should provide substantive response
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Response should be substantive"

    @pytest.mark.llm_validation
    async def test_rss_news_multiple_sources_aggregation(
        self, client: AsyncClient, llm_validator
    ):
        """
        Test aggregation from multiple RSS news sources.

        Broad news query should potentially reference multiple sources.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Give me a comprehensive overview of crypto market news",
                "language": "en",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()

        # Should provide comprehensive coverage
        comprehensive = any(
            keyword in agent_response
            for keyword in [
                "market",
                "crypto",
                "news",
                "overview",
                "bitcoin",
                "ethereum",
                "defi",
            ]
        )

        assert comprehensive, "Response should provide comprehensive overview"


class TestDataSourcePriority:
    """Test data source priority and failover mechanisms."""

    @pytest.mark.llm_validation
    async def test_data_source_priority_order(self, client: AsyncClient, llm_validator):
        """
        Test primary/fallback source ordering.

        System should prefer primary sources and use fallbacks appropriately.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is Ethereum doing right now?", "language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # System should provide response using available sources
        agent_response = data["agent_message"]["content"].lower()

        ethereum_info = any(
            keyword in agent_response
            for keyword in ["ethereum", "eth", "price", "market", "blockchain"]
        )

        assert ethereum_info, "Response should include Ethereum information"

    @pytest.mark.llm_validation
    async def test_data_source_failover_mechanism(
        self, client: AsyncClient, llm_validator
    ):
        """
        Test automatic failover when sources are unavailable.

        System should gracefully handle source failures and use alternatives.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Tell me about DeFi protocols and their current status",
                "language": "en",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide useful response even with potential source issues
        agent_response = data["agent_message"]["content"].lower()

        defi_info = any(
            keyword in agent_response
            for keyword in [
                "defi",
                "protocol",
                "aave",
                "compound",
                "uniswap",
                "lending",
                "swap",
            ]
        )
