"""
Integration tests for 1inch MCP Server.

Tests 1inch DEX aggregator tools:
- Swap quotes
- Liquidity sources
- Token prices
- Supported chains
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.infrastructure.mcp.servers.oneinch_mcp import OneInchMCPServer


@pytest.mark.integration
class TestOneInchMCPServerStructure:
    """Structural tests for 1inch MCP server."""
    
    def test_oneinch_server_exists(self):
        """Test OneInchMCPServer class exists."""
        assert OneInchMCPServer is not None
    
    def test_oneinch_server_instantiation(self):
        """Test server can be instantiated."""
        server = OneInchMCPServer(api_key="test_key")
        assert server is not None
        assert server.server_name == "1inch"
        assert server.port == 8081


@pytest.mark.integration
class TestOneInchTools:
    """Tests for 1inch MCP tools."""
    
    def test_tools_registered(self):
        """Test all expected tools are registered."""
        # Arrange
        server = OneInchMCPServer()
        client = TestClient(server.app)
        
        # Act
        response = client.get("/tools")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        tools = data["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        assert "get_swap_quote" in tool_names
        assert "get_liquidity_sources" in tool_names
        assert "get_token_price" in tool_names
        assert "get_supported_chains" in tool_names
    
    def test_health_endpoint(self):
        """Test 1inch server health endpoint."""
        # Arrange
        server = OneInchMCPServer()
        client = TestClient(server.app)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "1inch"


@pytest.mark.integration
@pytest.mark.skip(reason="Requires 1inch API key and live API access")
class TestOneInchToolExecution:
    """Tests for 1inch tool execution (requires API key)."""
    
    def test_get_swap_quote(self):
        """Test get_swap_quote tool execution."""
        # Arrange
        server = OneInchMCPServer(api_key="test_key")
        client = TestClient(server.app)
        
        # Act
        response = client.post(
            "/execute/get_swap_quote",
            json={
                "params": {
                    "chain_id": 1,
                    "from_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                    "to_token": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",    # WETH
                    "amount": "1000000",  # 1 USDC
                }
            },
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_get_supported_chains(self):
        """Test get_supported_chains tool execution."""
        # Arrange
        server = OneInchMCPServer()
        client = TestClient(server.app)
        
        # Act
        response = client.post(
            "/execute/get_supported_chains",
            json={"params": {}},
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "chains" in data["result"]
        assert len(data["result"]["chains"]) > 0
