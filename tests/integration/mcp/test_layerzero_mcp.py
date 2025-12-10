"""
Integration tests for LayerZero MCP Server.

Tests LayerZero cross-chain messaging tools:
- Message tracking
- Message history
- Chain discovery
- Fee estimation
- OFT transfers
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.infrastructure.mcp.servers.layerzero_mcp import LayerZeroMCPServer
from app.setup.config.mcp import MCPSettings, MCPServerSettings


@pytest.mark.integration
class TestLayerZeroMCPServerStructure:
    """Structural tests for LayerZero MCP server."""

    def test_layerzero_server_exists(self):
        """Test LayerZeroMCPServer class exists."""
        assert LayerZeroMCPServer is not None

    def test_layerzero_server_has_setup_tools(self):
        """Test server has setup_tools method."""
        assert hasattr(LayerZeroMCPServer, 'setup_tools')

    def test_layerzero_server_initialization_enabled(self):
        """Test server can be instantiated when enabled."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(layerzero_enabled=True)
        )
        mock_gateway = MagicMock()

        server = LayerZeroMCPServer(
            layerzero_gateway=mock_gateway,
            settings=settings
        )

        assert server is not None
        assert server.name == "layerzero"


@pytest.mark.integration
class TestLayerZeroTools:
    """Tests for LayerZero MCP tools registration."""

    def test_setup_tools_registers_all_tools(self):
        """Test setup_tools registers all expected tools."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(layerzero_enabled=True)
        )
        mock_gateway = MagicMock()
        server = LayerZeroMCPServer(
            layerzero_gateway=mock_gateway,
            settings=settings
        )

        server.setup_tools()

        expected_tools = [
            "layerzero_track_message",
            "layerzero_get_message_history",
            "layerzero_get_chains",
            "layerzero_estimate_fees",
            "layerzero_get_oft_transfers",
            "layerzero_check_message_status",
        ]

        for tool_name in expected_tools:
            assert tool_name in server.tools, f"Tool {tool_name} not registered"


@pytest.mark.integration
class TestLayerZeroToolHandlers:
    """Tests for LayerZero MCP tool handlers."""

    @pytest.mark.asyncio
    async def test_track_message_handler_found(self):
        """Test track_message handler when message is found."""
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

        mock_gateway = AsyncMock()
        mock_gateway.track_message.return_value = mock_message

        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(layerzero_enabled=True)
        )
        server = LayerZeroMCPServer(
            layerzero_gateway=mock_gateway,
            settings=settings
        )
        server.setup_tools()

        result = await server._track_message_handler(tx_hash="0xtx1")

        assert "message_id" in result
        assert result["message_id"] == "msg123"
        assert result["status"] == "delivered"

    @pytest.mark.asyncio
    async def test_get_chains_handler(self):
        """Test get_chains handler."""
        mock_chain1 = MagicMock()
        mock_chain1.name = "ethereum"
        mock_chain1.chain_id = 1
        mock_chain1.lz_chain_id = 101
        mock_chain1.endpoint_address = "0xendpoint1"
        mock_chain1.is_testnet = False

        mock_chain2 = MagicMock()
        mock_chain2.name = "arbitrum"
        mock_chain2.chain_id = 42161
        mock_chain2.lz_chain_id = 110
        mock_chain2.endpoint_address = "0xendpoint2"
        mock_chain2.is_testnet = False

        mock_gateway = AsyncMock()
        mock_gateway.get_chains.return_value = [mock_chain1, mock_chain2]

        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(layerzero_enabled=True)
        )
        server = LayerZeroMCPServer(
            layerzero_gateway=mock_gateway,
            settings=settings
        )
        server.setup_tools()

        result = await server._get_chains_handler(mainnet_only=True)

        assert "chains" in result
        assert len(result["chains"]) == 2
        assert result["chains"][0]["name"] == "ethereum"
