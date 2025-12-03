"""
Integration tests for MCP Base Server.

Tests the MCP protocol implementation:
- Tool registration
- Discovery endpoint
- Execution endpoint
- Error handling
"""

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.mcp.base_server import MCPServer, MCPTool


@pytest.mark.integration
class TestMCPServerStructure:
    """Structural tests for MCP server."""
    
    def test_mcp_server_exists(self):
        """Test MCPServer class exists."""
        assert MCPServer is not None
    
    def test_mcp_tool_exists(self):
        """Test MCPTool dataclass exists."""
        assert MCPTool is not None
    
    def test_mcp_server_instantiation(self):
        """Test MCPServer can be instantiated."""
        server = MCPServer(
            server_name="test",
            description="Test server",
            port=9999,
        )
        assert server is not None
        assert server.server_name == "test"
        assert server.description == "Test server"
        assert server.port == 9999


@pytest.mark.integration
class TestMCPServerEndpoints:
    """Integration tests for MCP server endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns server info."""
        # Arrange
        server = MCPServer("test", "Test MCP Server")
        client = TestClient(server.app)
        
        # Act
        response = client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["server"] == "test"
        assert "endpoints" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        # Arrange
        server = MCPServer("test", "Test MCP Server")
        client = TestClient(server.app)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["server"] == "test"
        assert "tools_registered" in data
    
    def test_tools_discovery_endpoint(self):
        """Test tools discovery endpoint."""
        # Arrange
        server = MCPServer("test", "Test MCP Server")
        client = TestClient(server.app)
        
        # Act
        response = client.get("/tools")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["server"] == "test"
        assert "tools" in data
        assert isinstance(data["tools"], list)


@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPToolRegistration:
    """Tests for MCP tool registration."""
    
    async def test_register_tool(self):
        """Test registering a tool."""
        # Arrange
        server = MCPServer("test", "Test MCP Server")
        
        async def test_handler(**params):
            return {"result": "success"}
        
        # Act
        server.register_tool(
            name="test_tool",
            description="Test tool",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                },
            },
            handler=test_handler,
        )
        
        # Assert
        assert "test_tool" in server.tools
        assert server.tools["test_tool"].name == "test_tool"
    
    def test_tool_appears_in_discovery(self):
        """Test registered tool appears in discovery endpoint."""
        # Arrange
        server = MCPServer("test", "Test MCP Server")
        
        async def test_handler(**params):
            return {"result": "success"}
        
        server.register_tool(
            name="test_tool",
            description="Test tool",
            parameters={"type": "object", "properties": {}},
            handler=test_handler,
        )
        
        client = TestClient(server.app)
        
        # Act
        response = client.get("/tools")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "test_tool"
        assert data["tools"][0]["qualified_name"] == "test_test_tool"


@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPToolExecution:
    """Tests for MCP tool execution."""
    
    def test_execute_tool_success(self):
        """Test executing a tool successfully."""
        # Arrange
        server = MCPServer("test", "Test MCP Server")
        
        async def test_handler(param1: str):
            return {"result": f"Received: {param1}"}
        
        server.register_tool(
            name="test_tool",
            description="Test tool",
            parameters={"type": "object", "properties": {}},
            handler=test_handler,
        )
        
        client = TestClient(server.app)
        
        # Act
        response = client.post(
            "/execute/test_tool",
            json={"params": {"param1": "test_value"}},
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["result"] == "Received: test_value"
    
    def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist."""
        # Arrange
        server = MCPServer("test", "Test MCP Server")
        client = TestClient(server.app)
        
        # Act
        response = client.post(
            "/execute/nonexistent_tool",
            json={"params": {}},
        )
        
        # Assert
        assert response.status_code == 404
    
    def test_execute_tool_with_error(self):
        """Test executing a tool that raises an error."""
        # Arrange
        server = MCPServer("test", "Test MCP Server")
        
        async def error_handler(**params):
            raise ValueError("Test error")
        
        server.register_tool(
            name="error_tool",
            description="Tool that errors",
            parameters={"type": "object", "properties": {}},
            handler=error_handler,
        )
        
        client = TestClient(server.app)
        
        # Act
        response = client.post(
            "/execute/error_tool",
            json={"params": {}},
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data
