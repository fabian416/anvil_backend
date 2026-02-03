"""
Integration tests for Morpho MCP Server.

Tests Morpho Protocol tools:
- MetaMorpho vaults
- Vault details and APY
- Morpho Blue markets
- User positions
- Yield comparison
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.infrastructure.mcp.servers.morpho_mcp import MorphoMCPServer
from app.setup.config.mcp import MCPSettings, MCPServerSettings


@pytest.mark.integration
class TestMorphoMCPServerStructure:
    """Structural tests for Morpho MCP server."""

    def test_morpho_server_exists(self):
        """Test MorphoMCPServer class exists."""
        assert MorphoMCPServer is not None

    def test_morpho_server_has_setup_tools(self):
        """Test server has setup_tools method."""
        assert hasattr(MorphoMCPServer, "setup_tools")

    def test_morpho_server_initialization_enabled(self):
        """Test server can be instantiated when enabled."""
        # Arrange
        settings = MCPSettings(
            enabled=True, servers=MCPServerSettings(morpho_enabled=True)
        )
        mock_gateway = MagicMock()

        # Act
        server = MorphoMCPServer(morpho_gateway=mock_gateway, settings=settings)

        # Assert
        assert server is not None
        assert server.name == "morpho"
        assert server.version == "1.0.0"

    def test_morpho_server_disabled_raises_error(self):
        """Test server raises error when disabled."""
        # Arrange
        settings = MCPSettings(
            enabled=True, servers=MCPServerSettings(morpho_enabled=False)
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            MorphoMCPServer(settings=settings)

        assert "disabled" in str(exc_info.value).lower()


@pytest.mark.integration
class TestMorphoTools:
    """Tests for Morpho MCP tools registration."""

    def test_setup_tools_registers_all_tools(self):
        """Test setup_tools registers all expected tools."""
        # Arrange
        settings = MCPSettings(
            enabled=True, servers=MCPServerSettings(morpho_enabled=True)
        )
        mock_gateway = MagicMock()
        server = MorphoMCPServer(morpho_gateway=mock_gateway, settings=settings)

        # Act
        server.setup_tools()

        # Assert - Check all expected tools are registered
        expected_tools = [
            "morpho_get_vaults",
            "morpho_get_vault_details",
            "morpho_get_vault_apy",
            "morpho_get_markets",
            "morpho_get_user_positions",
            "morpho_compare_yields",
        ]

        for tool_name in expected_tools:
            assert tool_name in server.tools, f"Tool {tool_name} not registered"

    def test_tool_parameters_defined(self):
        """Test all tools have properly defined parameters."""
        # Arrange
        settings = MCPSettings(
            enabled=True, servers=MCPServerSettings(morpho_enabled=True)
        )
        mock_gateway = MagicMock()
        server = MorphoMCPServer(morpho_gateway=mock_gateway, settings=settings)
        server.setup_tools()

        # Act & Assert
        for tool_name, tool in server.tools.items():
            assert tool.parameters is not None
            assert "type" in tool.parameters
            assert tool.parameters["type"] == "object"
            assert "properties" in tool.parameters


@pytest.mark.integration
class TestMorphoToolHandlers:
    """Tests for Morpho MCP tool handlers."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_vaults_handler_no_gateway(self):
        """Test get_vaults handler when gateway is None."""
        # Arrange
        settings = MCPSettings(
            enabled=True, servers=MCPServerSettings(morpho_enabled=True)
        )
        server = MorphoMCPServer(morpho_gateway=None, settings=settings)
        server.setup_tools()

        # Act
        result = await server._get_vaults_handler()

        # Assert
        assert "error" in result
        assert "vaults" in result
        assert result["vaults"] == []

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_vaults_handler_with_gateway(self):
        """Test get_vaults handler with mocked gateway."""
        # Arrange
        mock_vault = MagicMock()
        mock_vault.address = "0x123"
        mock_vault.name = "Test Vault"
        mock_vault.symbol = "TEST"
        mock_vault.asset = "USDC"
        mock_vault.apy = Decimal("5.5")
        mock_vault.net_apy = Decimal("5.0")
        mock_vault.total_assets = Decimal("1000000")
        mock_vault.risk_tier = MagicMock(value="low")
        mock_vault.fee_percentage = Decimal("0.05")
        mock_vault.curator_address = "0xcurator"

        mock_gateway = AsyncMock()
        mock_gateway.get_vaults.return_value = [mock_vault]

        settings = MCPSettings(
            enabled=True, servers=MCPServerSettings(morpho_enabled=True)
        )
        server = MorphoMCPServer(morpho_gateway=mock_gateway, settings=settings)
        server.setup_tools()

        # Act
        result = await server._get_vaults_handler(asset="USDC", chain="ethereum")

        # Assert
        assert "vaults" in result
        assert len(result["vaults"]) == 1
        assert result["vaults"][0]["address"] == "0x123"
        assert result["vaults"][0]["name"] == "Test Vault"
        mock_gateway.get_vaults.assert_called_once_with(asset="USDC", chain="ethereum")

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_compare_yields_handler(self):
        """Test compare_yields handler."""
        # Arrange
        mock_vault = MagicMock()
        mock_vault.name = "High Yield Vault"
        mock_vault.apy = Decimal("10.5")
        mock_vault.net_apy = Decimal("10.0")
        mock_vault.risk_tier = MagicMock(value="medium")
        mock_vault.total_assets = Decimal("5000000")

        mock_gateway = AsyncMock()
        mock_gateway.get_vaults.return_value = [mock_vault]

        settings = MCPSettings(
            enabled=True, servers=MCPServerSettings(morpho_enabled=True)
        )
        server = MorphoMCPServer(morpho_gateway=mock_gateway, settings=settings)
        server.setup_tools()

        # Act
        result = await server._compare_yields_handler(
            asset="WETH", protocols=["morpho"], chain="ethereum"
        )

        # Assert
        assert "comparisons" in result
        assert len(result["comparisons"]) > 0
        assert result["comparisons"][0]["protocol"] == "morpho"


@pytest.mark.integration
class TestMorphoIntegration:
    """Integration tests for Morpho MCP server end-to-end."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_full_vault_discovery_flow(self):
        """Test complete vault discovery and analysis flow."""
        # Arrange - Create mock vaults
        vault1 = MagicMock()
        vault1.address = "0xvault1"
        vault1.name = "USDC Vault High"
        vault1.symbol = "mvUSDCH"
        vault1.asset = "USDC"
        vault1.apy = Decimal("8.5")
        vault1.net_apy = Decimal("8.0")
        vault1.total_assets = Decimal("10000000")
        vault1.risk_tier = MagicMock(value="medium")
        vault1.fee_percentage = Decimal("0.05")
        vault1.curator_address = "0xcurator1"

        vault2 = MagicMock()
        vault2.address = "0xvault2"
        vault2.name = "USDC Vault Low"
        vault2.symbol = "mvUSDCL"
        vault2.asset = "USDC"
        vault2.apy = Decimal("5.0")
        vault2.net_apy = Decimal("4.75")
        vault2.total_assets = Decimal("20000000")
        vault2.risk_tier = MagicMock(value="low")
        vault2.fee_percentage = Decimal("0.05")
        vault2.curator_address = "0xcurator2"

        mock_gateway = AsyncMock()
        mock_gateway.get_vaults.return_value = [vault1, vault2]

        settings = MCPSettings(
            enabled=True, servers=MCPServerSettings(morpho_enabled=True)
        )
        server = MorphoMCPServer(morpho_gateway=mock_gateway, settings=settings)
        server.setup_tools()

        # Act - Get vaults and filter by APY
        result = await server._get_vaults_handler(
            asset="USDC", min_apy=6.0, sort_by="apy", chain="ethereum", limit=10
        )

        # Assert
        assert "vaults" in result
        assert len(result["vaults"]) == 1  # Only vault1 meets min_apy
        assert result["vaults"][0]["name"] == "USDC Vault High"

        assert "8.50%" in result["vaults"][0]["apy"]
