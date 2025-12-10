"""
Integration tests for Curve MCP Server.

Tests Curve Finance tools:
- Liquidity pools
- Pool APY and details
- Swap quotes
- Gauge rewards
- TVL data
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.infrastructure.mcp.servers.curve_mcp import CurveMCPServer
from app.setup.config.mcp import MCPSettings, MCPServerSettings


@pytest.mark.integration
class TestCurveMCPServerStructure:
    """Structural tests for Curve MCP server."""

    def test_curve_server_exists(self):
        """Test CurveMCPServer class exists."""
        assert CurveMCPServer is not None

    def test_curve_server_has_setup_tools(self):
        """Test server has setup_tools method."""
        assert hasattr(CurveMCPServer, 'setup_tools')

    def test_curve_server_initialization_enabled(self):
        """Test server can be instantiated when enabled."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(curve_enabled=True)
        )
        mock_gateway = MagicMock()

        server = CurveMCPServer(
            curve_gateway=mock_gateway,
            settings=settings
        )

        assert server is not None
        assert server.name == "curve"
        assert server.version == "1.0.0"


@pytest.mark.integration
class TestCurveTools:
    """Tests for Curve MCP tools registration."""

    def test_setup_tools_registers_all_tools(self):
        """Test setup_tools registers all expected tools."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(curve_enabled=True)
        )
        mock_gateway = MagicMock()
        server = CurveMCPServer(
            curve_gateway=mock_gateway,
            settings=settings
        )

        server.setup_tools()

        expected_tools = [
            "curve_get_pools",
            "curve_get_pool_details",
            "curve_get_pool_apy",
            "curve_get_swap_quote",
            "curve_get_gauges",
            "curve_get_tvl",
            "curve_find_best_pools",
        ]

        for tool_name in expected_tools:
            assert tool_name in server.tools, f"Tool {tool_name} not registered"


@pytest.mark.integration
class TestCurveToolHandlers:
    """Tests for Curve MCP tool handlers."""

    @pytest.mark.asyncio
    async def test_get_pools_handler_with_gateway(self):
        """Test get_pools handler with mocked gateway."""
        mock_coin1 = MagicMock()
        mock_coin1.symbol = "USDC"
        mock_coin2 = MagicMock()
        mock_coin2.symbol = "DAI"

        mock_pool = MagicMock()
        mock_pool.address = "0x3pool"
        mock_pool.name = "3pool"
        mock_pool.coins = [mock_coin1, mock_coin2]
        mock_pool.total_liquidity_usd = Decimal("100000000")
        mock_pool.volume_24h_usd = Decimal("5000000")
        mock_pool.fees_24h_usd = Decimal("10000")
        mock_pool.pool_type = "stable"

        mock_gateway = AsyncMock()
        mock_gateway.get_pools.return_value = [mock_pool]

        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(curve_enabled=True)
        )
        server = CurveMCPServer(
            curve_gateway=mock_gateway,
            settings=settings
        )
        server.setup_tools()

        result = await server._get_pools_handler(chain="ethereum", limit=20)

        assert "pools" in result
        assert len(result["pools"]) == 1
        assert result["pools"][0]["name"] == "3pool"
        assert "USDC" in result["pools"][0]["coins"]

    @pytest.mark.asyncio
    async def test_find_best_pools_handler(self):
        """Test find_best_pools handler."""
        mock_coin = MagicMock()
        mock_coin.symbol = "USDC"
        mock_coin.address = "0xusdc"

        mock_pool = MagicMock()
        mock_pool.address = "0xpool1"
        mock_pool.name = "USDC Pool"
        mock_pool.coins = [mock_coin]
        mock_pool.total_liquidity_usd = Decimal("50000000")
        mock_pool.volume_24h_usd = Decimal("1000000")
        mock_pool.pool_type = "stable"

        mock_apy = MagicMock()
        mock_apy.total_apy = Decimal("8.5")

        mock_gateway = AsyncMock()
        mock_gateway.get_pools.return_value = [mock_pool]
        mock_gateway.get_pool_apy.return_value = mock_apy

        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(curve_enabled=True)
        )
        server = CurveMCPServer(
            curve_gateway=mock_gateway,
            settings=settings
        )
        server.setup_tools()

        result = await server._find_best_pools_handler(
            token="USDC",
            sort_by="apy",
            chain="ethereum",
            limit=10
        )

        assert "pools" in result
        assert result["token"] == "USDC"
        assert len(result["pools"]) > 0
