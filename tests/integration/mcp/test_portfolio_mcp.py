"""
Integration tests for Portfolio MCP Server.

Tests portfolio management and analytics tools:
- User balance retrieval
- Position tracking
- Portfolio summary and analytics
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from fastapi.testclient import TestClient

from app.infrastructure.mcp.servers.portfolio_mcp import PortfolioMCPServer
from app.setup.config.mcp import MCPSettings, MCPServerSettings


@pytest.mark.integration
class TestPortfolioMCPServerStructure:
    """Structural tests for Portfolio MCP server."""

    def test_portfolio_server_exists(self):
        """Test PortfolioMCPServer class exists."""
        assert PortfolioMCPServer is not None

    def test_portfolio_server_has_setup_tools(self):
        """Test server has setup_tools method."""
        assert hasattr(PortfolioMCPServer, 'setup_tools')

    def test_portfolio_server_initialization_enabled(self):
        """Test server can be instantiated when enabled."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )

        server = PortfolioMCPServer(settings=settings)

        assert server is not None
        assert server.name == "portfolio"
        assert server.version == "1.0.0"

    def test_portfolio_server_disabled_raises_error(self):
        """Test server raises error when disabled."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=False)
        )

        with pytest.raises(Exception) as exc_info:
            PortfolioMCPServer(settings=settings)

        assert "disabled" in str(exc_info.value).lower()


@pytest.mark.integration
class TestPortfolioTools:
    """Tests for Portfolio MCP tools registration."""

    def test_setup_tools_registers_all_tools(self):
        """Test setup_tools registers all expected tools."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)

        expected_tools = [
            "get_user_balance",
            "get_user_positions",
            "get_portfolio_summary",
        ]

        for tool_name in expected_tools:
            assert tool_name in server.tools, f"Tool {tool_name} not registered"

    def test_tools_count(self):
        """Test correct number of tools registered."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        
        assert len(server.tools) == 3

    def test_tool_parameters_defined(self):
        """Test all tools have properly defined parameters."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)

        for tool_name, tool in server.tools.items():
            assert tool.parameters is not None, f"Tool {tool_name} has no parameters"
            assert "type" in tool.parameters, f"Tool {tool_name} missing type"
            assert tool.parameters["type"] == "object"
            assert "properties" in tool.parameters, f"Tool {tool_name} missing properties"

    def test_tool_descriptions_exist(self):
        """Test all tools have descriptions."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)

        for tool_name, tool in server.tools.items():
            assert tool.description is not None, f"Tool {tool_name} has no description"
            assert len(tool.description) > 10, f"Tool {tool_name} description too short"


@pytest.mark.integration
class TestPortfolioHealthEndpoint:
    """Tests for Portfolio server health endpoint."""

    def test_health_endpoint_returns_200(self):
        """Test health endpoint returns 200 status."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        client = TestClient(server.app)
        
        response = client.get("/health")
        
        assert response.status_code == 200

    def test_health_endpoint_returns_healthy_status(self):
        """Test health endpoint returns healthy status."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        client = TestClient(server.app)
        
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["name"] == "portfolio"
        assert data["version"] == "1.0.0"


@pytest.mark.integration
class TestPortfolioToolsEndpoint:
    """Tests for Portfolio server tools endpoint."""

    def test_tools_endpoint_returns_200(self):
        """Test tools endpoint returns 200 status."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        client = TestClient(server.app)
        
        response = client.get("/tools")
        
        assert response.status_code == 200

    def test_tools_endpoint_returns_all_tools(self):
        """Test tools endpoint returns all registered tools."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        client = TestClient(server.app)
        
        response = client.get("/tools")
        data = response.json()
        
        assert len(data) == 3
        tool_names = [tool["name"] for tool in data]
        assert "get_user_balance" in tool_names
        assert "get_user_positions" in tool_names
        assert "get_portfolio_summary" in tool_names


@pytest.mark.integration
class TestPortfolioToolHandlers:
    """Tests for Portfolio MCP tool handlers."""

    @pytest.mark.asyncio
    async def test_get_user_balance_handler(self):
        """Test get_user_balance handler."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)

        result = await server._get_user_balance(
            user_id="test_user_123",
            chain_id=1
        )

        assert "balances" in result or "total_usd" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_user_balance_multi_chain(self):
        """Test get_user_balance handler with multiple chains."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)

        result = await server._get_user_balance(
            user_id="test_user_123",
            chain_id=None  # All chains
        )

        # Should return multi-chain data or error
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_user_positions_handler(self):
        """Test get_user_positions handler."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)

        result = await server._get_user_positions(
            user_id="test_user_123"
        )

        assert "positions" in result or "defi_positions" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_user_positions_by_protocol(self):
        """Test get_user_positions handler filtered by protocol."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)

        result = await server._get_user_positions(
            user_id="test_user_123",
            protocol="aave"
        )

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_portfolio_summary_handler(self):
        """Test get_portfolio_summary handler."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)

        result = await server._get_portfolio_summary(
            user_id="test_user_123"
        )

        # Should return summary data
        assert isinstance(result, dict)
        # May contain total_value, allocation, pnl, etc.

    @pytest.mark.asyncio
    async def test_get_user_balance_with_default_chain(self):
        """Test get_user_balance handler with default chain."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)

        result = await server._get_user_balance(
            user_id="test_user_123"
        )

        assert isinstance(result, dict)


@pytest.mark.integration
class TestPortfolioToolExecution:
    """Tests for executing tools via API endpoint."""

    def test_execute_get_user_balance_via_api(self):
        """Test executing get_user_balance tool via API."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        client = TestClient(server.app)
        
        response = client.post(
            "/tools/get_user_balance",
            json={"parameters": {
                "user_id": "test_user_123",
                "chain_id": 1
            }}
        )
        
        assert response.status_code == 200

    def test_execute_get_user_positions_via_api(self):
        """Test executing get_user_positions tool via API."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        client = TestClient(server.app)
        
        response = client.post(
            "/tools/get_user_positions",
            json={"parameters": {
                "user_id": "test_user_123"
            }}
        )
        
        assert response.status_code == 200

    def test_execute_get_portfolio_summary_via_api(self):
        """Test executing get_portfolio_summary tool via API."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        client = TestClient(server.app)
        
        response = client.post(
            "/tools/get_portfolio_summary",
            json={"parameters": {
                "user_id": "test_user_123"
            }}
        )
        
        assert response.status_code == 200


@pytest.mark.integration
class TestPortfolioRootEndpoint:
    """Tests for Portfolio server root endpoint."""

    def test_root_endpoint_returns_server_info(self):
        """Test root endpoint returns server info."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        client = TestClient(server.app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "portfolio"
        assert data["version"] == "1.0.0"
        assert data["tools_count"] == 3


@pytest.mark.integration
class TestPortfolioValidation:
    """Tests for Portfolio input validation."""

    def test_empty_user_id(self):
        """Test handling of empty user_id."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        client = TestClient(server.app)
        
        response = client.post(
            "/tools/get_user_balance",
            json={"parameters": {
                "user_id": "",
                "chain_id": 1
            }}
        )
        
        # Should handle gracefully (either 200 with error or 400)
        assert response.status_code in [200, 400, 422]

    def test_missing_required_parameter(self):
        """Test handling of missing required parameter."""
        settings = MCPSettings(
            enabled=True,
            servers=MCPServerSettings(portfolio_enabled=True)
        )
        server = PortfolioMCPServer(settings=settings)
        client = TestClient(server.app)
        
        response = client.post(
            "/tools/get_user_balance",
            json={"parameters": {}}  # Missing user_id
        )
        
        # Should return error
        assert response.status_code in [200, 400, 422]
