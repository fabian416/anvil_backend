"""Integration tests for MCP servers.

Tests MCP servers with real FastAPI test client.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.infrastructure.mcp.servers.portfolio_mcp import PortfolioMCPServer
from app.infrastructure.mcp.servers.oneinch_mcp import OneInchMCPServer
from app.infrastructure.mcp.servers.aave_mcp import AaveMCPServer
from app.infrastructure.mcp.servers.defillama_mcp import DeFiLlamaMCPServer


# Fixtures

@pytest.fixture
def mock_mcp_settings():
    """Create mock MCP settings with all servers enabled."""
    from app.setup.config.mcp import MCPSettings, MCPServerSettings
    
    settings = MCPSettings(
        enabled=True,
        servers=MCPServerSettings(
            portfolio_enabled=True,
            oneinch_enabled=True,
            aave_enabled=True,
            defillama_enabled=True,
            coingecko_enabled=True,
            perplexity_enabled=True,
            thegraph_enabled=True,
        ),
    )
    return settings


@pytest.fixture
def portfolio_server(mock_mcp_settings):
    """Provide Portfolio MCP server."""
    return PortfolioMCPServer(settings=mock_mcp_settings)


@pytest.fixture
def oneinch_server(mock_mcp_settings):
    """Provide 1inch MCP server."""
    return OneInchMCPServer(settings=mock_mcp_settings)


@pytest.fixture
def aave_server(mock_mcp_settings):
    """Provide Aave MCP server."""
    return AaveMCPServer(settings=mock_mcp_settings)


@pytest.fixture
def defillama_server(mock_mcp_settings):
    """Provide DeFiLlama MCP server."""
    return DeFiLlamaMCPServer(settings=mock_mcp_settings)


def get_server_name(server) -> str:
    """Get server name from either name or server_name attribute."""
    return getattr(server, 'name', getattr(server, 'server_name', 'unknown'))


# Portfolio MCP Tests

@pytest.mark.unit
class TestPortfolioMCP:
    """Test Portfolio MCP server."""
    
    def test_server_initialization(self, portfolio_server):
        """Test server can be initialized."""
        name = get_server_name(portfolio_server)
        assert name == "portfolio"
        assert len(portfolio_server.tools) >= 1
    
    def test_tools_endpoint(self, portfolio_server):
        """Test /tools endpoint."""
        client = TestClient(portfolio_server.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        # Response is either {"tools": [...]} or [...] directly
        tools = data.get("tools", data) if isinstance(data, dict) else data
        assert len(tools) >= 1
    
    def test_get_user_balance_tool(self, portfolio_server):
        """Test get_user_balance tool exists."""
        tool_names = [t.name for t in portfolio_server.tools.values()]
        assert "get_user_balance" in tool_names


# 1inch MCP Tests

@pytest.mark.unit
class TestOneInchMCP:
    """Test 1inch MCP server."""
    
    def test_server_initialization(self, oneinch_server):
        """Test server can be initialized."""
        name = get_server_name(oneinch_server)
        assert name == "1inch"
        assert len(oneinch_server.tools) >= 1
    
    def test_tools_endpoint(self, oneinch_server):
        """Test /tools endpoint."""
        client = TestClient(oneinch_server.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        tools = data.get("tools", data) if isinstance(data, dict) else data
        assert len(tools) >= 1
    
    def test_has_swap_quote_tool(self, oneinch_server):
        """Test get_swap_quote tool exists."""
        tool_names = [t.name for t in oneinch_server.tools.values()]
        assert "get_swap_quote" in tool_names


# Aave MCP Tests

@pytest.mark.unit
class TestAaveMCP:
    """Test Aave MCP server."""
    
    def test_server_initialization(self, aave_server):
        """Test server can be initialized."""
        name = get_server_name(aave_server)
        assert name == "aave"
        assert len(aave_server.tools) >= 1
    
    def test_tools_endpoint(self, aave_server):
        """Test /tools endpoint."""
        client = TestClient(aave_server.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        tools = data.get("tools", data) if isinstance(data, dict) else data
        assert len(tools) >= 1


# DeFiLlama MCP Tests

@pytest.mark.unit
class TestDeFiLlamaMCP:
    """Test DeFiLlama MCP server."""
    
    def test_server_initialization(self, defillama_server):
        """Test server can be initialized."""
        name = get_server_name(defillama_server)
        assert name == "defillama"
        assert len(defillama_server.tools) >= 1
    
    def test_tools_endpoint(self, defillama_server):
        """Test /tools endpoint."""
        client = TestClient(defillama_server.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        tools = data.get("tools", data) if isinstance(data, dict) else data
        assert len(tools) >= 1
    
    def test_has_tvl_tool(self, defillama_server):
        """Test get_protocol_tvl tool exists."""
        tool_names = [t.name for t in defillama_server.tools.values()]
        assert "get_protocol_tvl" in tool_names


# MCP Manager Tests

@pytest.mark.unit
class TestMCPManager:
    """Test MCP Server Manager."""
    
    def test_manager_can_be_imported(self):
        """Test MCP manager can be imported."""
        from app.infrastructure.mcp.manager import MCPServerManager
        manager = MCPServerManager()
        assert manager is not None
    
    def test_manager_has_servers_dict(self):
        """Test manager initializes with servers dict."""
        from app.infrastructure.mcp.manager import MCPServerManager
        manager = MCPServerManager()
        assert hasattr(manager, 'servers')


# Integration Tests

@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests for MCP system."""
    
    def test_multiple_servers_can_coexist(self, portfolio_server, aave_server):
        """Test multiple MCP servers can be created."""
        portfolio_name = get_server_name(portfolio_server)
        aave_name = get_server_name(aave_server)
        
        assert portfolio_name == "portfolio"
        assert aave_name == "aave"
        assert portfolio_name != aave_name
    
    def test_servers_have_unique_tools(self, portfolio_server, aave_server):
        """Test servers have different tools."""
        portfolio_tools = set(t.name for t in portfolio_server.tools.values())
        aave_tools = set(t.name for t in aave_server.tools.values())
        
        # They should have different tools
        assert portfolio_tools != aave_tools
