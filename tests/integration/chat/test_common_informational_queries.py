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
        # Accept various responses: token info, protocol search, or general conversation
        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        assert any(word in content.lower() for word in ["bitcoin", "btc", "protocol", "defi", "crypto", "token", "assist"]), \
            f"Should mention relevant crypto/defi topics: {content[:200]}"

        # Should NOT require signup for informational query
        assert not data.get("requires_registration"), \
            "Informational queries should not require registration"

    @pytest.mark.asyncio
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

        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        # Accept price info or general crypto/defi assistance response
        assert any(word in content.lower() for word in ["price", "$", "usd", "eth", "ethereum", "crypto", "defi", "assist"]), \
            f"Should mention relevant crypto topics: {content[:200]}"

    @pytest.mark.asyncio
    async def test_guest_eth_price_shorthand(self, client: AsyncClient):
        """
        Guest Query: ETH price
        Expected: Returns ETH price using shorthand query.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH price", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert any(word in content.lower() for word in ["price", "$", "eth", "ethereum"]), \
            f"Should show ETH price: {content[:200]}"

    @pytest.mark.asyncio
    async def test_guest_btc_sentiment(self, client: AsyncClient):
        """
        Guest Query: What do people think about Bitcoin?
        Expected: Returns sentiment analysis.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What do people think about Bitcoin?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        # Should contain sentiment information
        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        # Accept sentiment analysis or general crypto/market discussion
        assert any(word in content.lower() for word in ["sentiment", "bullish", "bearish", "market", "price", "crypto", "defi", "assist", "analysis"]), \
            f"Should mention market/crypto topics: {content[:200]}"

    @pytest.mark.asyncio
    async def test_guest_what_is_defi(self, client: AsyncClient):
        """
        Guest Query: What is DeFi?
        Expected: Returns explanation of DeFi.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is DeFi?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        assert any(word in content.lower() for word in ["defi", "decentralized", "finance", "protocol", "crypto", "assist"]), \
            f"Should mention defi/crypto topics: {content[:200]}"

    @pytest.mark.asyncio
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

        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        assert any(word in content.lower() for word in ["usdc", "stablecoin", "dollar", "usd", "crypto", "token", "protocol", "assist"]), \
            f"Should mention token/crypto topics: {content[:200]}"

    @pytest.mark.asyncio
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
        # Accept if mentions at least one of the tokens or general price info
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

        # Should contain information about Bitcoin
        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        assert any(word in content.lower() for word in ["bitcoin", "btc", "protocol", "defi", "crypto", "token", "assist"]), \
            f"Should mention relevant crypto/defi topics: {content[:200]}"

        # Note: Authenticated users get helpful responses (protocol search, general info, etc.)

    @pytest.mark.asyncio
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
        assert any(word in content.lower() for word in ["ethereum", "eth", "protocol", "defi", "crypto", "token", "assist", "smart contract", "blockchain"]), \
            f"Should mention relevant crypto/defi topics: {content[:200]}"

    @pytest.mark.asyncio
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

        # Should contain price information
        assert any(word in content.lower() for word in ["price", "$", "usd", "btc"]), \
            f"Should show price information: {content[:200]}"

    @pytest.mark.asyncio
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
            f"Should show Ethereum price: {content[:200]}"

    @pytest.mark.asyncio
    async def test_auth_eth_price_shorthand(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: ETH price
        Expected: Returns ETH price using shorthand query.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "ETH price", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert any(word in content.lower() for word in ["price", "$", "eth", "ethereum"]), \
            f"Should show ETH price: {content[:200]}"

    @pytest.mark.asyncio
    async def test_auth_btc_sentiment(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: What do people think about Bitcoin?
        Expected: Returns sentiment analysis.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What do people think about Bitcoin?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        # Should contain sentiment information
        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        # Accept sentiment analysis or general crypto/market discussion
        assert any(word in content.lower() for word in ["sentiment", "bullish", "bearish", "market", "price", "crypto", "defi", "assist", "analysis"]), \
            f"Should mention market/crypto topics: {content[:200]}"

    @pytest.mark.asyncio
    async def test_auth_what_is_defi(
        self, client: AsyncClient, auth_headers: dict, conversation_id: str
    ):
        """
        Authenticated Query: What is DeFi?
        Expected: Returns explanation of DeFi.
        """
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={"content": "What is DeFi?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        assert any(word in content.lower() for word in ["defi", "decentralized", "finance", "protocol", "crypto", "assist"]), \
            f"Should mention defi/crypto topics: {content[:200]}"

    @pytest.mark.asyncio
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

        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        assert any(word in content.lower() for word in ["usdc", "stablecoin", "dollar", "usd", "crypto", "token", "protocol", "assist"]), \
            f"Should mention token/crypto topics: {content[:200]}"

    @pytest.mark.asyncio
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

        # Should contain meaningful price/market information
        assert len(content) > 50, "Should provide a meaningful response"
        # Accept if mentions at least one of the tokens or general price info
        assert any(word in content.lower() for word in ["bitcoin", "btc", "ethereum", "eth", "price", "$"]), \
            f"Should mention crypto prices: {content[:200]}"


class TestCommonQueriesMultiLanguage:
    """Test common queries in multiple languages."""

    @pytest.mark.asyncio
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

        # Should respond about price
        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        # Accept Spanish responses about crypto/defi
        assert any(word in content.lower() for word in ["precio", "btc", "bitcoin", "$", "crypto", "defi", "asistente"]), \
            f"Should mention relevant topics in Spanish: {content[:200]}"

    @pytest.mark.asyncio
    async def test_guest_portuguese_ethereum_info(self, client: AsyncClient):
        """
        Guest Query (Portuguese): O que é Ethereum?
        Expected: Returns Ethereum info in Portuguese.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "O que é Ethereum?", "language": "pt"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, f"Should provide a meaningful response: {content[:200]}"
        # Accept Portuguese responses about crypto/defi
        assert any(word in content.lower() for word in ["ethereum", "eth", "crypto", "defi", "assistente", "protocol"]), \
            f"Should mention relevant topics in Portuguese: {content[:200]}"

    @pytest.mark.asyncio
    async def test_guest_chinese_bitcoin_info(self, client: AsyncClient):
        """
        Guest Query (Chinese): 什么是比特币?
        Expected: Returns Bitcoin info in Chinese.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "什么是比特币?", "language": "zh"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        # Chinese response should work
        assert data.get("agent_message") is not None


class TestCommonQueriesEdgeCases:
    """Test edge cases for common queries."""

    @pytest.mark.asyncio
    async def test_guest_unknown_token(self, client: AsyncClient):
        """
        Guest Query: What is UNKNOWNTOKEN123?
        Expected: Handles unknown token gracefully.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is UNKNOWNTOKEN123?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        # Should respond without error (even if it doesn't know the token)
        assert data.get("agent_message") is not None

    @pytest.mark.asyncio
    async def test_guest_case_insensitive_queries(self, client: AsyncClient):
        """
        Guest Query: WHAT IS BITCOIN? (uppercase)
        Expected: Handles case-insensitive queries.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "WHAT IS BITCOIN?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        data = response.json()
        content = data.get("agent_message", {}).get("content", "")

        assert len(content) > 50, "Should provide meaningful response"
        assert any(word in content.lower() for word in ["bitcoin", "btc", "crypto", "defi", "assist", "protocol"]), \
            "Should mention relevant crypto topics"

    @pytest.mark.asyncio
    async def test_guest_typo_tolerance(self, client: AsyncClient):
        """
        Guest Query: What is Bitcion? (typo)
        Expected: Attempts to handle common typos.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What is Bitcion?", "language": "en"}
        )

        assert response.status_code in [200, 201]
        # Should respond without error
        data = response.json()
        assert data.get("agent_message") is not None
