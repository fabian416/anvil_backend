"""
Pytest fixtures for MCP Server integration tests.

Provides common fixtures for testing all 11 MCP servers:
- 1inch (8081)
- DeFiLlama (8082)
- TheGraph (8083)
- CoinGecko (8084)
- Aave (8085)
- Portfolio (8086)
- Perplexity (8087)
- Morpho (8088)
- Curve (8089)
- Hyperliquid (8090)
- LayerZero (8091)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.setup.config.mcp import MCPSettings, MCPServerSettings, MCPRetrySettings


# =============================================================================
# Common Fixtures
# =============================================================================


@pytest.fixture
def mcp_settings_enabled():
    """
    Create MCP settings with all servers enabled.
    """
    return MCPSettings(
        enabled=True,
        servers=MCPServerSettings(
            oneinch_enabled=True,
            defillama_enabled=True,
            thegraph_enabled=True,
            coingecko_enabled=True,
            aave_enabled=True,
            portfolio_enabled=True,
            perplexity_enabled=True,
            morpho_enabled=True,
            curve_enabled=True,
            hyperliquid_enabled=True,
            layerzero_enabled=True,
        ),
        retry=MCPRetrySettings(
            enabled=True,
            max_retries=3,
            initial_backoff_seconds=0.1,
            max_backoff_seconds=1.0,
        ),
    )


@pytest.fixture
def mcp_settings_disabled():
    """
    Create MCP settings with all servers disabled.
    """
    return MCPSettings(
        enabled=False,
        servers=MCPServerSettings(
            oneinch_enabled=False,
            defillama_enabled=False,
            thegraph_enabled=False,
            coingecko_enabled=False,
            aave_enabled=False,
            portfolio_enabled=False,
            perplexity_enabled=False,
            morpho_enabled=False,
            curve_enabled=False,
            hyperliquid_enabled=False,
            layerzero_enabled=False,
        ),
    )


# =============================================================================
# Mock Gateway Fixtures
# =============================================================================


@pytest.fixture
def mock_morpho_gateway():
    """
    Create a mock Morpho gateway with sample vault data.
    """
    mock_vault = MagicMock()
    mock_vault.address = "0xvault123"
    mock_vault.name = "Test USDC Vault"
    mock_vault.symbol = "mvUSDC"
    mock_vault.asset = "USDC"
    mock_vault.apy = Decimal("8.5")
    mock_vault.net_apy = Decimal("8.0")
    mock_vault.total_assets = Decimal("10000000")
    mock_vault.risk_tier = MagicMock(value="low")
    mock_vault.fee_percentage = Decimal("0.05")
    mock_vault.curator_address = "0xcurator"

    gateway = AsyncMock()
    gateway.get_vaults.return_value = [mock_vault]
    gateway.get_vault_details.return_value = mock_vault
    gateway.get_vault_apy.return_value = {"apy": "8.50%", "net_apy": "8.00%"}

    return gateway


@pytest.fixture
def mock_curve_gateway():
    """
    Create a mock Curve gateway with sample pool data.
    """
    mock_coin = MagicMock()
    mock_coin.symbol = "USDC"
    mock_coin.address = "0xusdc"

    mock_pool = MagicMock()
    mock_pool.address = "0xpool123"
    mock_pool.name = "3pool"
    mock_pool.coins = [mock_coin]
    mock_pool.total_liquidity_usd = Decimal("100000000")
    mock_pool.volume_24h_usd = Decimal("5000000")
    mock_pool.fees_24h_usd = Decimal("10000")
    mock_pool.pool_type = "stable"

    gateway = AsyncMock()
    gateway.get_pools.return_value = [mock_pool]
    gateway.get_pool_details.return_value = mock_pool
    gateway.get_pool_apy.return_value = MagicMock(total_apy=Decimal("5.5"))

    return gateway


@pytest.fixture
def mock_hyperliquid_gateway():
    """
    Create a mock Hyperliquid gateway with sample market data.
    """
    mock_market = MagicMock()
    mock_market.symbol = "ETH"
    mock_market.mark_price = Decimal("2000")
    mock_market.index_price = Decimal("2001")
    mock_market.funding_rate = Decimal("0.0001")
    mock_market.volume_24h_usd = Decimal("100000000")
    mock_market.open_interest_usd = Decimal("50000000")
    mock_market.max_leverage = 50

    gateway = AsyncMock()
    gateway.get_markets.return_value = [mock_market]
    gateway.calculate_liquidation_price.return_value = Decimal("1800")

    return gateway


@pytest.fixture
def mock_layerzero_gateway():
    """
    Create a mock LayerZero gateway with sample message data.
    """
    mock_message = MagicMock()
    mock_message.message_id = "msg123"
    mock_message.status = "delivered"
    mock_message.source_chain = "ethereum"
    mock_message.destination_chain = "arbitrum"
    mock_message.sender = "0xsender"
    mock_message.receiver = "0xreceiver"
    mock_message.payload = "0xdata"
    mock_message.nonce = 1
    mock_message.source_tx_hash = "0xtx1"
    mock_message.destination_tx_hash = "0xtx2"
    mock_message.timestamp = "2024-01-01"
    mock_message.gas_used = 100000

    mock_chain = MagicMock()
    mock_chain.name = "ethereum"
    mock_chain.chain_id = 1
    mock_chain.lz_chain_id = 101
    mock_chain.endpoint_address = "0xendpoint"
    mock_chain.is_testnet = False

    gateway = AsyncMock()
    gateway.track_message.return_value = mock_message
    gateway.get_chains.return_value = [mock_chain]

    return gateway


# =============================================================================
# HTTP Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_mcp_manager_http(mocker):
    """
    Mock HTTP calls to MCP manager.

    This fixture mocks httpx.AsyncClient to simulate MCP manager responses
    without requiring an actual MCP manager server running.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "tools": [
            {
                "server": "defillama",
                "tool_name": "get_protocol_tvl",
                "qualified_name": "defillama__get_protocol_tvl",
                "description": "Get TVL for a DeFi protocol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "protocol": {"type": "string", "description": "Protocol name"}
                    },
                    "required": ["protocol"],
                },
                "server_url": "http://localhost:8082",
            },
            {
                "server": "coingecko",
                "tool_name": "get_token_price",
                "qualified_name": "coingecko__get_token_price",
                "description": "Get current token price",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "token_id": {"type": "string", "description": "Token ID"}
                    },
                    "required": ["token_id"],
                },
                "server_url": "http://localhost:8084",
            },
        ]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = None

    mocker.patch("httpx.AsyncClient", return_value=mock_context)

    return mock_client


@pytest.fixture
def mock_mcp_manager_unavailable(mocker):
    """
    Mock MCP manager as unavailable (connection error).

    Use this fixture to test fallback behavior when MCP manager is down.
    """
    import httpx

    mock_context = AsyncMock()
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = None

    mocker.patch("httpx.AsyncClient", return_value=mock_context)

    return mock_client


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def sample_wallet_address():
    """Return a sample wallet address for testing."""
    return "0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7"


@pytest.fixture
def sample_chain_ids():
    """Return supported chain IDs for testing."""
    return {
        "ethereum": 1,
        "polygon": 137,
        "arbitrum": 42161,
        "optimism": 10,
        "avalanche": 43114,
        "base": 8453,
    }


@pytest.fixture
def sample_tokens():
    """Return sample token data for testing."""
    return {
        "USDC": {
            "symbol": "USDC",
            "decimals": 6,
            "address_ethereum": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        },
        "WETH": {
            "symbol": "WETH",
            "decimals": 18,
            "address_ethereum": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        },
        "DAI": {
            "symbol": "DAI",
            "decimals": 18,
            "address_ethereum": "0x6B175474E89094C44Da98b954EesdeCD73181FE",
        },
    }
