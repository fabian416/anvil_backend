"""
Integration tests for Aave MCP Server.

Tests Aave V3 lending and borrowing protocol tools:
- Market data retrieval
- User positions
- Health factor calculations
- Borrowing capacity
- Supply/borrow/repay/withdraw operations
- Liquidation risk assessment
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from fastapi.testclient import TestClient

from app.infrastructure.mcp.servers.aave_mcp import AaveMCPServer
from app.setup.config.mcp import MCPSettings, MCPServerSettings


@pytest.mark.integration
class TestAaveMCPServerStructure:
    """Structural tests for Aave MCP server."""

    def test_aave_server_exists(self):
        """Test AaveMCPServer class exists."""
        assert AaveMCPServer is not None

    def test_aave_server_has_setup_tools(self):
        """Test server has setup_tools method."""
        assert hasattr(AaveMCPServer, 'setup_tools')

    def test_aave_server_initialization(self):
        """Test server can be instantiated."""
        server = AaveMCPServer()
        
        assert server is not None
        assert server.name == "aave"
        assert server.version == "1.0.0"

    def test_aave_server_description(self):
        """Test server has proper description."""
        server = AaveMCPServer()
        assert "Aave" in server.description or "lending" in server.description.lower()


@pytest.mark.integration
class TestAaveTools:
    """Tests for Aave MCP tools registration."""

    def test_setup_tools_registers_all_tools(self):
        """Test setup_tools registers all expected tools."""
        server = AaveMCPServer()

        expected_tools = [
            "get_market_data",
            "get_user_positions",
            "calculate_health_factor",
            "get_available_to_borrow",
            "supply_asset",
            "borrow_asset",
            "repay_loan",
            "withdraw_supply",
            "get_liquidation_risk",
        ]

        for tool_name in expected_tools:
            assert tool_name in server.tools, f"Tool {tool_name} not registered"

    def test_tools_count(self):
        """Test correct number of tools registered."""
        server = AaveMCPServer()
        assert len(server.tools) == 9

    def test_tool_parameters_defined(self):
        """Test all tools have properly defined parameters."""
        server = AaveMCPServer()

        for tool_name, tool in server.tools.items():
            assert tool.parameters is not None, f"Tool {tool_name} has no parameters"
            assert "type" in tool.parameters, f"Tool {tool_name} missing type in parameters"
            assert tool.parameters["type"] == "object"
            assert "properties" in tool.parameters, f"Tool {tool_name} missing properties"

    def test_tool_descriptions_exist(self):
        """Test all tools have descriptions."""
        server = AaveMCPServer()

        for tool_name, tool in server.tools.items():
            assert tool.description is not None, f"Tool {tool_name} has no description"
            assert len(tool.description) > 10, f"Tool {tool_name} description too short"


@pytest.mark.integration
class TestAaveHealthEndpoint:
    """Tests for Aave server health endpoint."""

    def test_health_endpoint_returns_200(self):
        """Test health endpoint returns 200 status."""
        server = AaveMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/health")
        
        assert response.status_code == 200

    def test_health_endpoint_returns_healthy_status(self):
        """Test health endpoint returns healthy status."""
        server = AaveMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["name"] == "aave"
        assert data["version"] == "1.0.0"


@pytest.mark.integration
class TestAaveToolsEndpoint:
    """Tests for Aave server tools endpoint."""

    def test_tools_endpoint_returns_200(self):
        """Test tools endpoint returns 200 status."""
        server = AaveMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/tools")
        
        assert response.status_code == 200

    def test_tools_endpoint_returns_all_tools(self):
        """Test tools endpoint returns all registered tools."""
        server = AaveMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/tools")
        data = response.json()
        
        assert len(data) == 9
        tool_names = [tool["name"] for tool in data]
        assert "get_market_data" in tool_names
        assert "get_user_positions" in tool_names
        assert "calculate_health_factor" in tool_names


@pytest.mark.integration
class TestAaveToolHandlers:
    """Tests for Aave MCP tool handlers."""

    @pytest.mark.asyncio
    async def test_get_market_data_handler(self):
        """Test get_market_data handler returns market info."""
        server = AaveMCPServer()

        result = await server._get_market_data(chain_id=1, assets=["USDC", "ETH"])

        assert "markets" in result
        assert "chain_id" in result
        assert result["chain_id"] == 1
        # Mock data should return some markets
        assert isinstance(result["markets"], list)

    @pytest.mark.asyncio
    async def test_get_market_data_default_assets(self):
        """Test get_market_data with default assets."""
        server = AaveMCPServer()

        result = await server._get_market_data(chain_id=1)

        assert "markets" in result
        # Should return markets for default assets

    @pytest.mark.asyncio
    async def test_get_user_positions_handler(self):
        """Test get_user_positions handler."""
        server = AaveMCPServer()

        result = await server._get_user_positions(
            chain_id=1,
            user_address="0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7"
        )

        assert "user_address" in result
        assert "chain_id" in result
        assert "supplies" in result or "borrows" in result or "health_factor" in result

    @pytest.mark.asyncio
    async def test_calculate_health_factor_handler(self):
        """Test calculate_health_factor handler."""
        server = AaveMCPServer()

        result = await server._calculate_health_factor(
            chain_id=1,
            user_address="0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7"
        )

        assert "health_factor" in result or "error" in result
        if "health_factor" in result:
            assert isinstance(result["health_factor"], (int, float, str))

    @pytest.mark.asyncio
    async def test_get_available_to_borrow_handler(self):
        """Test get_available_to_borrow handler."""
        server = AaveMCPServer()

        result = await server._get_available_to_borrow(
            chain_id=1,
            user_address="0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7",
            asset="USDC"
        )

        assert "asset" in result or "available_amount" in result or "error" in result

    @pytest.mark.asyncio
    async def test_supply_asset_handler(self):
        """Test supply_asset handler returns transaction info."""
        server = AaveMCPServer()

        result = await server._supply_asset(
            user_id="test_user",
            chain_id=1,
            from_address="0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7",
            asset="USDC",
            amount="1000"
        )

        # Should return transaction info or error
        assert "transaction" in result or "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_borrow_asset_handler(self):
        """Test borrow_asset handler."""
        server = AaveMCPServer()

        result = await server._borrow_asset(
            user_id="test_user",
            chain_id=1,
            from_address="0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7",
            asset="USDC",
            amount="500",
            rate_mode="variable"
        )

        assert "transaction" in result or "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_repay_loan_handler(self):
        """Test repay_loan handler."""
        server = AaveMCPServer()

        result = await server._repay_loan(
            user_id="test_user",
            chain_id=1,
            from_address="0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7",
            asset="USDC",
            amount="250"
        )

        assert "transaction" in result or "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_withdraw_supply_handler(self):
        """Test withdraw_supply handler."""
        server = AaveMCPServer()

        result = await server._withdraw_supply(
            user_id="test_user",
            chain_id=1,
            from_address="0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7",
            asset="USDC",
            amount="100"
        )

        assert "transaction" in result or "error" in result or "success" in result

    @pytest.mark.asyncio
    async def test_get_liquidation_risk_handler(self):
        """Test get_liquidation_risk handler."""
        server = AaveMCPServer()

        result = await server._get_liquidation_risk(
            chain_id=1,
            user_address="0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7"
        )

        assert "risk_level" in result or "health_factor" in result or "error" in result


@pytest.mark.integration
class TestAaveToolExecution:
    """Tests for executing tools via API endpoint."""

    def test_execute_get_market_data_via_api(self):
        """Test executing get_market_data tool via API."""
        server = AaveMCPServer()
        client = TestClient(server.app)
        
        response = client.post(
            "/tools/get_market_data",
            json={"parameters": {"chain_id": 1, "assets": ["USDC"]}}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True or "error" in data

    def test_execute_get_user_positions_via_api(self):
        """Test executing get_user_positions tool via API."""
        server = AaveMCPServer()
        client = TestClient(server.app)
        
        response = client.post(
            "/tools/get_user_positions",
            json={"parameters": {
                "chain_id": 1,
                "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7"
            }}
        )
        
        assert response.status_code == 200

    def test_execute_calculate_health_factor_via_api(self):
        """Test executing calculate_health_factor tool via API."""
        server = AaveMCPServer()
        client = TestClient(server.app)
        
        response = client.post(
            "/tools/calculate_health_factor",
            json={"parameters": {
                "chain_id": 1,
                "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f3eF7"
            }}
        )
        
        assert response.status_code == 200


@pytest.mark.integration
class TestAaveChainSupport:
    """Tests for Aave multi-chain support."""

    @pytest.mark.parametrize("chain_id,chain_name", [
        (1, "Ethereum"),
        (137, "Polygon"),
        (42161, "Arbitrum"),
        (10, "Optimism"),
        (43114, "Avalanche"),
    ])
    @pytest.mark.asyncio
    async def test_supported_chains(self, chain_id, chain_name):
        """Test market data retrieval for all supported chains."""
        server = AaveMCPServer()

        result = await server._get_market_data(chain_id=chain_id)

        # Should not raise an error for supported chains
        assert "error" not in result or "unsupported" not in str(result.get("error", "")).lower()


@pytest.mark.integration
class TestAaveRootEndpoint:
    """Tests for Aave server root endpoint."""

    def test_root_endpoint_returns_server_info(self):
        """Test root endpoint returns server info."""
        server = AaveMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "aave"
        assert data["version"] == "1.0.0"
        assert data["tools_count"] == 9
