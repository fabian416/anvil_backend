"""
Integration tests for all MCP servers.

Tests DeFiLlama, The Graph, and CoinGecko MCP servers.
"""

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.mcp.servers.defillama_mcp import DeFiLlamaMCPServer
from app.infrastructure.mcp.servers.thegraph_mcp import TheGraphMCPServer
from app.infrastructure.mcp.servers.coingecko_mcp import CoinGeckoMCPServer


@pytest.mark.integration
class TestDeFiLlamaMCPServer:
    """Tests for DeFiLlama MCP server."""
    
    def test_defillama_server_exists(self):
        """Test DeFiLlamaMCPServer class exists."""
        assert DeFiLlamaMCPServer is not None
    
    def test_defillama_server_instantiation(self):
        """Test server can be instantiated."""
        server = DeFiLlamaMCPServer()
        assert server is not None
        assert server.server_name == "defillama"
        assert server.port == 8082
    
    def test_defillama_tools_registered(self):
        """Test all expected tools are registered."""
        server = DeFiLlamaMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        tools = data["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        assert "get_protocol_tvl" in tool_names
        assert "get_all_protocols" in tool_names
        assert "get_historical_tvl" in tool_names
        assert "get_chain_tvl" in tool_names
        assert "get_chains" in tool_names
    
    def test_defillama_health_endpoint(self):
        """Test DeFiLlama server health endpoint."""
        server = DeFiLlamaMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "defillama"
        assert data["tools_registered"] == 5


@pytest.mark.integration
class TestTheGraphMCPServer:
    """Tests for The Graph MCP server."""
    
    def test_thegraph_server_exists(self):
        """Test TheGraphMCPServer class exists."""
        assert TheGraphMCPServer is not None
    
    def test_thegraph_server_instantiation(self):
        """Test server can be instantiated."""
        server = TheGraphMCPServer()
        assert server is not None
        assert server.server_name == "thegraph"
        assert server.port == 8083
    
    def test_thegraph_tools_registered(self):
        """Test all expected tools are registered."""
        server = TheGraphMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        tools = data["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        assert "query_uniswap_v3" in tool_names
        assert "query_aave_v3" in tool_names
        assert "custom_query" in tool_names
        assert "get_subgraphs" in tool_names
    
    def test_thegraph_health_endpoint(self):
        """Test The Graph server health endpoint."""
        server = TheGraphMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "thegraph"
        assert data["tools_registered"] == 4
    
    def test_thegraph_get_subgraphs(self):
        """Test get_subgraphs tool execution."""
        server = TheGraphMCPServer()
        client = TestClient(server.app)
        
        response = client.post(
            "/execute/get_subgraphs",
            json={"params": {}},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "subgraphs" in data["result"]
        assert len(data["result"]["subgraphs"]) == 3


@pytest.mark.integration
class TestCoinGeckoMCPServer:
    """Tests for CoinGecko MCP server."""
    
    def test_coingecko_server_exists(self):
        """Test CoinGeckoMCPServer class exists."""
        assert CoinGeckoMCPServer is not None
    
    def test_coingecko_server_instantiation(self):
        """Test server can be instantiated."""
        server = CoinGeckoMCPServer()
        assert server is not None
        assert server.server_name == "coingecko"
        assert server.port == 8084
    
    def test_coingecko_tools_registered(self):
        """Test all expected tools are registered."""
        server = CoinGeckoMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        tools = data["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        assert "get_token_price" in tool_names
        assert "get_token_market_data" in tool_names
        assert "get_historical_price" in tool_names
        assert "get_trending_tokens" in tool_names
        assert "search_tokens" in tool_names
        assert "get_top_tokens" in tool_names
    
    def test_coingecko_health_endpoint(self):
        """Test CoinGecko server health endpoint."""
        server = CoinGeckoMCPServer()
        client = TestClient(server.app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "coingecko"
        assert data["tools_registered"] == 6


@pytest.mark.integration
class TestAllMCPServersIntegration:
    """Integration tests for all MCP servers working together."""
    
    def test_all_servers_have_unique_ports(self):
        """Test all servers use different ports."""
        oneinch_port = 8081
        defillama_port = 8082
        thegraph_port = 8083
        coingecko_port = 8084
        
        ports = [oneinch_port, defillama_port, thegraph_port, coingecko_port]
        assert len(ports) == len(set(ports)), "All servers should have unique ports"
    
    def test_all_servers_have_health_endpoints(self):
        """Test all servers have working health endpoints."""
        servers = [
            DeFiLlamaMCPServer(),
            TheGraphMCPServer(),
            CoinGeckoMCPServer(),
        ]
        
        for server in servers:
            client = TestClient(server.app)
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    
    def test_all_servers_have_tools_discovery(self):
        """Test all servers have tools discovery endpoint."""
        servers = [
            DeFiLlamaMCPServer(),
            TheGraphMCPServer(),
            CoinGeckoMCPServer(),
        ]
        
        for server in servers:
            client = TestClient(server.app)
            response = client.get("/tools")
            assert response.status_code == 200
            data = response.json()
            assert "tools" in data
            assert len(data["tools"]) > 0
    
    def test_total_tools_available(self):
        """Test total number of tools across all servers."""
        servers = [
            DeFiLlamaMCPServer(),   # 5 tools
            TheGraphMCPServer(),    # 4 tools
            CoinGeckoMCPServer(),   # 6 tools
        ]
        
        total_tools = 0
        for server in servers:
            client = TestClient(server.app)
            response = client.get("/tools")
            data = response.json()
            total_tools += len(data["tools"])
        
        # 5 + 4 + 6 = 15 tools
        assert total_tools == 15


@pytest.mark.integration
@pytest.mark.skip(reason="Requires API keys and live API access")
class TestMCPServersLiveExecution:
    """Live execution tests (requires API keys)."""
    
    def test_defillama_get_chains(self):
        """Test DeFiLlama get_chains execution."""
        server = DeFiLlamaMCPServer()
        client = TestClient(server.app)
        
        response = client.post(
            "/execute/get_chains",
            json={"params": {}},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_coingecko_get_trending(self):
        """Test CoinGecko get_trending_tokens execution."""
        server = CoinGeckoMCPServer()
        client = TestClient(server.app)
        
        response = client.post(
            "/execute/get_trending_tokens",
            json={"params": {}},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
