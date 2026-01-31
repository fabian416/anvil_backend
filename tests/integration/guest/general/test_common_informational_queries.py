"""
Integration tests for common informational queries.

Tests that basic informational queries work for both authenticated users and guests:
- Token information queries ("What is Bitcoin?", "What is Ethereum?")
- Price queries ("What is the price of Bitcoin?", "How much is ETH?")
- Market sentiment queries ("What do people think about BTC?")
- General crypto questions

These queries should work for both user types without requiring registration.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import uuid4


class TestCommonQueriesGuest:
    """Test common informational queries for guest users."""

    @pytest_asyncio.fixture
    async def guest_conversation_id(self, client: AsyncClient) -> str:
        """Create a guest conversation."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "Hello", "language": "en"}
        )
        assert response.status_code in [200, 201]
        data = response.json()
        return data["conversation_id"]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_what_is_bitcoin(self, client: AsyncClient):
        """
        Guest Query: What is Bitcoin?
        Expected: Returns information about Bitcoin without signup prompt.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is Bitcoin?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        # Should contain information about Bitcoin or provide a helpful response
        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        assert any(word in content.lower() for word in ["bitcoin", "btc", "protocol", "defi", "crypto", "token", "assist"]), \
            f"Should mention relevant crypto/defi topics: {content[:200]}"

        # Should NOT require signup for informational query
        assert not data.get("requires_registration"), \
            "Informational queries should not require registration"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_what_is_ethereum(self, client: AsyncClient):
        """
        Guest Query: What is Ethereum?
        Expected: Returns information about Ethereum.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is Ethereum?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        assert any(word in content.lower() for word in ["ethereum", "eth", "protocol", "defi", "crypto", "token", "assist", "smart contract", "blockchain"]), \
            f"Should mention relevant crypto/defi topics: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_bitcoin_price(self, client: AsyncClient):
        """
        Guest Query: What is the price of Bitcoin?
        Expected: Returns current Bitcoin price.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is the price of Bitcoin?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        # Should contain price information
        assert any(word in content.lower() for word in ["price", "$", "usd", "btc"]), \
            f"Should show price information: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_ethereum_price(self, client: AsyncClient):
        """
        Guest Query: How much is Ethereum?
        Expected: Returns current Ethereum price.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "How much is Ethereum?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert any(word in content.lower() for word in ["price", "$", "usd", "eth", "ethereum"]), \
            f"Should show price information: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_eth_price_shorthand(self, client: AsyncClient):
        """
        Guest Query: ETH price?
        Expected: Returns current ETH price with shorthand query.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH price?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 30, "Should provide a response"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_btc_sentiment(self, client: AsyncClient):
        """
        Guest Query: What do people think about Bitcoin?
        Expected: Returns market sentiment information.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What do people think about Bitcoin?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, "Should provide a meaningful response"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_what_is_defi(self, client: AsyncClient):
        """
        Guest Query: What is DeFi?
        Expected: Returns information about DeFi.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is DeFi?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, "Should provide a meaningful response"
        assert any(word in content.lower() for word in ["defi", "decentralized", "finance", "protocol"]), \
            f"Should mention DeFi topics: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_what_is_usdc(self, client: AsyncClient):
        """
        Guest Query: What is USDC?
        Expected: Returns information about USDC stablecoin.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is USDC?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, "Should provide a meaningful response"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_multiple_tokens_price(self, client: AsyncClient):
        """
        Guest Query: What are the prices of Bitcoin and Ethereum?
        Expected: Returns prices for multiple tokens.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What are the prices of Bitcoin and Ethereum?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        # Should contain meaningful price/market information
        assert len(content) > 50, "Should provide a meaningful response"
        assert any(word in content.lower() for word in ["bitcoin", "btc", "ethereum", "eth", "price", "$"]), \
            f"Should mention crypto prices: {content[:200]}"


class TestCommonQueriesAuthenticated:
    """Test common informational queries for authenticated users."""

    @pytest.fixture
    def auth_headers(self) -> dict:
        """Create test auth headers."""
        return {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJ0ZXN0LXNlc3Npb24iLCJleHAiOjk5OTk5OTk5OTl9.test",
            "Content-Type": "application/json"
        }

    @pytest_asyncio.fixture
    async def conversation_id(self, client: AsyncClient, auth_headers: dict) -> str:
        """Create an authenticated conversation."""
        response = await client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "Test Conversation"}
        )
        assert response.status_code in [200, 201]
        data = response.json()
        return data["id"]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auth_what_is_bitcoin(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: What is Bitcoin?
        Expected: Returns information about Bitcoin without signup prompt.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What is Bitcoin?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auth_what_is_ethereum(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: What is Ethereum?
        Expected: Returns information about Ethereum.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What is Ethereum?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auth_bitcoin_price(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: What is the price of Bitcoin?
        Expected: Returns current Bitcoin price.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What is the price of Bitcoin?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert any(word in content.lower() for word in ["price", "$", "usd", "btc"]), \
            f"Should show price information: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auth_ethereum_price(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: How much is Ethereum?
        Expected: Returns current Ethereum price.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "How much is Ethereum?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert any(word in content.lower() for word in ["price", "$", "usd", "eth", "ethereum"]), \
            f"Should show price information: {content[:200]}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auth_eth_price_shorthand(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: ETH price?
        Expected: Returns current ETH price with shorthand query.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "ETH price?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 30, "Should provide a response"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auth_btc_sentiment(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: What do people think about Bitcoin?
        Expected: Returns market sentiment information.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What do people think about Bitcoin?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, "Should provide a meaningful response"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auth_what_is_defi(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: What is DeFi?
        Expected: Returns information about DeFi.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What is DeFi?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, "Should provide a meaningful response"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auth_what_is_usdc(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: What is USDC?
        Expected: Returns information about USDC stablecoin.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What is USDC?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, "Should provide a meaningful response"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_auth_multiple_tokens_price(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: What are the prices of Bitcoin and Ethereum?
        Expected: Returns prices for multiple tokens.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What are the prices of Bitcoin and Ethereum?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, "Should provide a meaningful response"


class TestCommonQueriesMultiLanguage:
    """Test common queries in multiple languages."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_spanish_bitcoin_price(self, client: AsyncClient):
        """
        Guest Query (Spanish): ¿Cuál es el precio de Bitcoin?
        Expected: Returns price in Spanish.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "¿Cuál es el precio de Bitcoin?", "language": "es"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 30, "Should provide a response"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_portuguese_ethereum_info(self, client: AsyncClient):
        """
        Guest Query (Portuguese): O que é Ethereum?
        Expected: Returns info in Portuguese.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "O que é Ethereum?", "language": "pt"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 30, "Should provide a response"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chinese_bitcoin_info(self, client: AsyncClient):
        """
        Guest Query (Chinese): 什么是比特币？
        Expected: Returns info about Bitcoin.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "什么是比特币？", "language": "zh"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 30, "Should provide a response"


class TestCommonQueriesEdgeCases:
    """Test edge cases for common queries."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_unknown_token(self, client: AsyncClient):
        """
        Guest Query: What is UNKNOWNTOKEN?
        Expected: Handles unknown tokens gracefully.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is UNKNOWNTOKEN?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        # Should provide some response, even for unknown tokens
        assert len(content) > 20, "Should provide a response for unknown tokens"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_case_insensitive_queries(self, client: AsyncClient):
        """
        Test that queries work regardless of case.
        """
        queries = [
            "what is bitcoin?",
            "WHAT IS BITCOIN?",
            "What Is Bitcoin?",
        ]

        for query in queries:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": query, "language": "en"}
            )

            assert response.status_code in [200, 201], f"Failed for query: {query}"
            data = response.json()
            content = data.get("agent_message", {}).get("content", "")
            assert len(content) > 30, f"Should provide response for: {query}"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_typo_tolerance(self, client: AsyncClient):
        """
        Test that queries with minor typos still work.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is Bitconi?", "language": "en"}  # Typo in Bitcoin
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        # Should still provide some helpful response
        assert len(content) > 20, "Should handle typos gracefully"
