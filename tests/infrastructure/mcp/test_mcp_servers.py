"""Integration tests for MCP servers.

Tests MCP servers with real FastAPI test client.
"""
import pytest
from fastapi.testclient import TestClient

from app.infrastructure.mcp.servers.portfolio_mcp import PortfolioMCPServer
from app.infrastructure.mcp.servers.oneinch_mcp import OneInchMCPServer
from app.infrastructure.mcp.servers.aave_mcp import AaveMCPServer
from app.infrastructure.mcp.servers.defillama_mcp import DeFiLlamaMCPServer
from app.infrastructure.mcp.manager import MCPServerManager


# Fixtures

@pytest.fixture
def portfolio_server():
    """Provide Portfolio MCP server."""
    return PortfolioMCPServer()


@pytest.fixture
def oneinch_server():
    """Provide 1inch MCP server."""
    return OneInchMCPServer()


@pytest.fixture
def aave_server():
    """Provide Aave MCP server."""
    return AaveMCPServer()


@pytest.fixture
def defillama_server():
    """Provide DeFiLlama MCP server."""
    return DeFiLlamaMCPServer()


@pytest.fixture
def mcp_manager():
    """Provide MCP Server Manager."""
    return MCPServerManager()


# Portfolio MCP Tests

class TestPortfolioMCP:
    """Test Portfolio MCP server."""
    
    def test_server_initialization(self, portfolio_server):
        """Test server can be initialized."""
        assert portfolio_server.name == "portfolio"
        assert len(portfolio_server.tools) == 3
    
    def test_tools_endpoint(self, portfolio_server):
        """Test /tools endpoint."""
        client = TestClient(portfolio_server.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 3
    
    def test_get_user_balance_tool(self, portfolio_server):
        """Test get_user_balance tool."""
        client = TestClient(portfolio_server.app)
        response = client.post(
            "/tools/get_user_balance",
            json={
                "parameters": {
                    "user_id": "test_user",
                    "chain_id": 1,
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "balances" in data["result"]


# 1inch MCP Tests

class TestOneInchMCP:
    """Test 1inch MCP server."""
    
    def test_server_initialization(self, oneinch_server):
        """Test server can be initialized."""
        assert oneinch_server.name == "1inch"
        assert len(oneinch_server.tools) == 7
    
    def test_tools_endpoint(self, oneinch_server):
        """Test /tools endpoint."""
        client = TestClient(oneinch_server.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 7
    
    def test_get_swap_quote_tool(self, oneinch_server):
        """Test get_swap_quote tool."""
        client = TestClient(oneinch_server.app)
        response = client.post(
            "/tools/get_swap_quote",
            json={
                "parameters": {
                    "chain_id": 1,
                    "from_token": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                    "to_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "amount": "1000000000000000000",
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "to_amount" in data["result"]


# Aave MCP Tests

class TestAaveMCP:
    """Test Aave MCP server."""
    
    def test_server_initialization(self, aave_server):
        """Test server can be initialized."""
        assert aave_server.name == "aave"
        assert len(aave_server.tools) == 9
    
    def test_tools_endpoint(self, aave_server):
        """Test /tools endpoint."""
        client = TestClient(aave_server.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 9
    
    def test_get_market_data_tool(self, aave_server):
        """Test get_market_data tool."""
        client = TestClient(aave_server.app)
        response = client.post(
            "/tools/get_market_data",
            json={
                "parameters": {
                    "chain_id": 1,
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "markets" in data["result"]


# DeFiLlama MCP Tests

class TestDeFiLlamaMCP:
    """Test DeFiLlama MCP server."""
    
    def test_server_initialization(self, defillama_server):
        """Test server can be initialized."""
        assert defillama_server.name == "defillama"
        assert len(defillama_server.tools) == 8
    
    def test_tools_endpoint(self, defillama_server):
        """Test /tools endpoint."""
        client = TestClient(defillama_server.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 8
    
    def test_get_protocol_tvl_tool(self, defillama_server):
        """Test get_protocol_tvl tool."""
        client = TestClient(defillama_server.app)
        response = client.post(
            "/tools/get_protocol_tvl",
            json={
                "parameters": {
                    "protocol": "aave",
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "tvl" in data["result"]


# MCP Manager Tests

class TestMCPManager:
    """Test MCP Server Manager."""
    
    def test_manager_initialization(self, mcp_manager):
        """Test manager can be initialized."""
        assert len(mcp_manager.servers) == 0
        assert mcp_manager.app is not None
    
    def test_register_server(self, mcp_manager, portfolio_server):
        """Test server registration."""
        mcp_manager.register_server(portfolio_server)
        
        assert "portfolio" in mcp_manager.servers
        assert len(mcp_manager.tool_to_server_map) == 3
    
    def test_tools_endpoint(self, mcp_manager, portfolio_server):
        """Test unified /tools endpoint."""
        mcp_manager.register_server(portfolio_server)
        
        client = TestClient(mcp_manager.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "servers" in data
        assert data["total_tools"] == 3
    
    def test_call_tool_via_manager(self, mcp_manager, portfolio_server):
        """Test calling tool via manager."""
        mcp_manager.register_server(portfolio_server)
        
        client = TestClient(mcp_manager.app)
        response = client.post(
            "/tools/portfolio__get_user_balance",
            json={
                "parameters": {
                    "user_id": "test_user",
                    "chain_id": 1,
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data


# Integration Tests

class TestMCPIntegration:
    """Test MCP integration scenarios."""
    
    def test_all_servers_registered(self):
        """Test all servers can be registered."""
        manager = MCPServerManager()
        
        # Register all servers
        manager.register_server(PortfolioMCPServer())
        manager.register_server(OneInchMCPServer())
        manager.register_server(AaveMCPServer())
        manager.register_server(DeFiLlamaMCPServer())
        
        # Verify registration
        assert len(manager.servers) == 4
        assert "portfolio" in manager.servers
        assert "1inch" in manager.servers
        assert "aave" in manager.servers
        assert "defillama" in manager.servers
        
        # Verify total tools
        assert len(manager.tool_to_server_map) == 27
    
    def test_tool_discovery_across_servers(self):
        """Test tool discovery across all servers."""
        manager = MCPServerManager()
        
        # Register all servers
        manager.register_server(PortfolioMCPServer())
        manager.register_server(OneInchMCPServer())
        manager.register_server(AaveMCPServer())
        manager.register_server(DeFiLlamaMCPServer())
        
        client = TestClient(manager.app)
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all tools are listed
        assert data["total_tools"] == 27
        assert len(data["servers"]) == 4
        
        # Verify tools from each server
        tool_names = [tool["name"] for tool in data["tools"]]
        assert "portfolio__get_user_balance" in tool_names
        assert "1inch__get_swap_quote" in tool_names
        assert "aave__get_market_data" in tool_names
        assert "defillama__get_protocol_tvl" in tool_names
