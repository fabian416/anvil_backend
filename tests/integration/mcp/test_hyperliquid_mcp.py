"""
Integration tests for Hyperliquid MCP Server.

Tests Hyperliquid perpetual futures tools:
- Markets and order books
- Funding rates
- Liquidations
- Positions
- Risk calculations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.infrastructure.mcp.servers.hyperliquid_mcp import HyperliquidMCPServer
from app.setup.config.mcp import MCPSettings, MCPServerSettings


@pytest.mark.integration
class TestHyperliquidMCPServerStructure:
    """Structural tests for Hyperliquid MCP server."""

    def test_hyperliquid_server_exists(self):
        """Test HyperliquidMCPServer class exists."""
        assert HyperliquidMCPServer is not None

    def test_hyperliquid_server_has_setup_tools(self):
        """Test server has setup_tools method."""
        assert hasattr(HyperliquidMCPServer, 'setup_tools')

    def test_hyperliquid_server_initialization_enabled(self):
        """Test server can be instantiated when enabled."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(hyperliquid_enabled=True)
        )
        mock_gateway = MagicMock()

        server = HyperliquidMCPServer(
            perpetual_gateway=mock_gateway,
            settings=settings
        )

        assert server is not None
        assert server.name == "hyperliquid"


@pytest.mark.integration
class TestHyperliquidTools:
    """Tests for Hyperliquid MCP tools registration."""

    def test_setup_tools_registers_all_tools(self):
        """Test setup_tools registers all expected tools."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(hyperliquid_enabled=True)
        )
        mock_gateway = MagicMock()
        server = HyperliquidMCPServer(
            perpetual_gateway=mock_gateway,
            settings=settings
        )

        server.setup_tools()

        expected_tools = [
            "hyperliquid_get_markets",
            "hyperliquid_get_order_book",
            "hyperliquid_get_funding_rate",
            "hyperliquid_get_funding_rates",
            "hyperliquid_get_liquidations",
            "hyperliquid_get_positions",
            "hyperliquid_calculate_liquidation_price",
            "hyperliquid_calculate_risk_metrics",
            "hyperliquid_find_funding_arbitrage",
        ]

        for tool_name in expected_tools:
            assert tool_name in server.tools, f"Tool {tool_name} not registered"


@pytest.mark.integration
class TestHyperliquidToolHandlers:
    """Tests for Hyperliquid MCP tool handlers."""

    @pytest.mark.asyncio
    async def test_get_markets_handler(self):
        """Test get_markets handler."""
        mock_market = MagicMock()
        mock_market.symbol = "ETH"
        mock_market.mark_price = Decimal("2000")
        mock_market.index_price = Decimal("2001")
        mock_market.funding_rate = Decimal("0.0001")
        mock_market.volume_24h_usd = Decimal("100000000")
        mock_market.open_interest_usd = Decimal("50000000")
        mock_market.max_leverage = 50

        mock_gateway = AsyncMock()
        mock_gateway.get_markets.return_value = [mock_market]

        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(hyperliquid_enabled=True)
        )
        server = HyperliquidMCPServer(
            perpetual_gateway=mock_gateway,
            settings=settings
        )
        server.setup_tools()

        result = await server._get_markets_handler(sort_by="volume", limit=20)

        assert "markets" in result
        assert len(result["markets"]) == 1
        assert result["markets"][0]["symbol"] == "ETH"

    @pytest.mark.asyncio
    async def test_calculate_liquidation_price_handler(self):
        """Test calculate_liquidation_price handler."""
        mock_gateway = MagicMock()
        mock_gateway.calculate_liquidation_price.return_value = Decimal("1800")

        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(hyperliquid_enabled=True)
        )
        server = HyperliquidMCPServer(
            perpetual_gateway=mock_gateway,
            settings=settings
        )
        server.setup_tools()

        result = await server._calculate_liquidation_price_handler(
            entry_price="2000",
            leverage="10",
            side="long"
        )

        assert "liquidation_price" in result
        assert "distance" in result
        assert result["side"] == "long"
