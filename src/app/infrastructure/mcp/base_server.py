"""
Base MCP Server for Anvil.

Provides foundation for all MCP tool servers.
Implements Model Context Protocol for tool discovery and execution.
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


@dataclass
class MCPTool:
    """
    MCP Tool definition.
    
    Attributes:
        name: Tool name (e.g., "get_swap_quote")
        description: Human-readable tool description
        parameters: JSON Schema for parameters
        handler: Async function that executes the tool
    """
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable


class MCPToolExecutionRequest(BaseModel):
    """Request model for tool execution."""
    params: Dict[str, Any]


class MCPToolExecutionResponse(BaseModel):
    """Response model for tool execution."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MCPServer:
    """
    Base MCP Server implementation.
    
    Provides:
    - Tool registration
    - Discovery endpoint (/tools)
    - Execution endpoint (/execute/{tool_name})
    - Error handling
    - FastAPI application
    
    Usage:
        server = MCPServer(server_name="1inch", description="DEX aggregator")
        server.register_tool("get_quote", "Get swap quote", schema, handler)
        app = server.app
    """
    
    def __init__(self, server_name: str, description: str, port: int = 8080):
        """
        Initialize MCP server.
        
        Args:
            server_name: Unique server identifier (e.g., "1inch", "defillama")
            description: Server description
            port: Server port (default: 8080)
        """
        self.server_name = server_name
        self.description = description
        self.port = port
        self.tools: Dict[str, MCPTool] = {}
        self.app = FastAPI(
            title=f"{server_name} MCP Server",
            description=description,
            version="1.0.0",
        )
        
        # Register MCP endpoints
        self._setup_routes()
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
    ):
        """
        Register a tool with this MCP server.
        
        Args:
            name: Tool name (e.g., "get_swap_quote")
            description: Tool description
            parameters: JSON Schema for parameters
            handler: Async function that executes the tool
        
        Example:
            def handler(**params):
                return {"result": "success"}
            
            server.register_tool(
                name="get_quote",
                description="Get swap quote",
                parameters={
                    "type": "object",
                    "properties": {
                        "token_in": {"type": "string"},
                        "token_out": {"type": "string"},
                    },
                    "required": ["token_in", "token_out"],
                },
                handler=handler,
            )
        """
        tool = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )
        self.tools[name] = tool
        
        print(f"[{self.server_name}] Registered tool: {name}")
    
    def _setup_routes(self):
        """Set up FastAPI routes for MCP protocol."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with server information."""
            return {
                "server": self.server_name,
                "description": self.description,
                "version": "1.0.0",
                "endpoints": {
                    "tools": f"http://localhost:{self.port}/tools",
                    "execute": f"http://localhost:{self.port}/execute/{{tool_name}}",
                },
            }
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "server": self.server_name,
                "tools_registered": len(self.tools),
            }
        
        @self.app.get("/tools")
        async def list_tools():
            """
            List all available tools (MCP discovery endpoint).
            
            Returns:
                Dictionary with server info and tool list
            """
            return {
                "server": self.server_name,
                "description": self.description,
                "tools": [
                    {
                        "name": tool.name,
                        "qualified_name": f"{self.server_name}_{tool.name}",
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                    for tool in self.tools.values()
                ]
            }
        
        @self.app.post("/execute/{tool_name}", response_model=MCPToolExecutionResponse)
        async def execute_tool(tool_name: str, request: MCPToolExecutionRequest):
            """
            Execute a specific tool (MCP execution endpoint).
            
            Args:
                tool_name: Name of the tool to execute
                request: Execution request with parameters
            
            Returns:
                Execution response with success status and result
            
            Raises:
                HTTPException: If tool not found or execution fails
            """
            if tool_name not in self.tools:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Tool '{tool_name}' not found on server '{self.server_name}'"
                )
            
            tool = self.tools[tool_name]
            
            try:
                # Execute tool handler with provided parameters
                result = await tool.handler(**request.params)
                
                return MCPToolExecutionResponse(
                    success=True,
                    result=result,
                )
            except Exception as e:
                # Log error
                print(f"[{self.server_name}] Error executing {tool_name}: {str(e)}")
                
                return MCPToolExecutionResponse(
                    success=False,
                    error=str(e),
                )
    
    def run(self, host: str = "0.0.0.0"):
        """
        Run the MCP server.
        
        Args:
            host: Host address (default: 0.0.0.0)
        
        Example:
            import uvicorn
            server = MCPServer("1inch", "DEX aggregator")
            uvicorn.run(server.app, host="0.0.0.0", port=8081)
        """
        import uvicorn
        print(f"Starting {self.server_name} MCP Server on http://{host}:{self.port}")
        uvicorn.run(self.app, host=host, port=self.port)
