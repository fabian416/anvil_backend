"""Base MCP server implementation for tool abstraction."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class MCPToolRequest(BaseModel):
    """MCP tool invocation request."""
    parameters: Dict[str, Any]


class MCPToolResponse(BaseModel):
    """MCP tool invocation response."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class MCPToolDescription(BaseModel):
    """MCP tool description for discovery."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema


@dataclass
class MCPTool:
    """Internal representation of an MCP tool."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable


class MCPServer(ABC):
    """
    Base MCP server for exposing tools to AI agents.
    
    Implements the Model Context Protocol (MCP) standard for tool discovery
    and invocation. Agents can:
    1. Discover available tools via GET /tools
    2. Invoke tools via POST /tools/{tool_name}
    
    Example usage:
        class MyMCPServer(MCPServer):
            def __init__(self):
                super().__init__(name="my-service", version="1.0.0")
                self.setup_tools()
            
            def setup_tools(self):
                self.register_tool(
                    name="my_tool",
                    description="Does something useful",
                    parameters={
                        "type": "object",
                        "properties": {
                            "param1": {"type": "string"},
                        },
                        "required": ["param1"],
                    },
                    handler=self._my_tool_handler,
                )
            
            async def _my_tool_handler(self, param1: str) -> Dict[str, Any]:
                return {"result": f"Processed {param1}"}
    """
    
    def __init__(self, name: str, version: str = "1.0.0", description: str = ""):
        """
        Initialize MCP server.
        
        Args:
            name: Server name (e.g., "1inch", "portfolio")
            version: Server version
            description: Server description
        """
        self.name = name
        self.version = version
        self.description = description
        self.tools: Dict[str, MCPTool] = {}
        
        # Create FastAPI app
        self.app = FastAPI(
            title=f"{name} MCP Server",
            version=version,
            description=description or f"MCP server for {name}",
        )
        
        # Register standard MCP routes
        self._register_routes()
    
    def _register_routes(self):
        """Register standard MCP endpoints."""
        
        @self.app.get("/")
        async def server_info():
            """Get server information."""
            return {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "protocol": "mcp",
                "tools_count": len(self.tools),
            }
        
        @self.app.get("/tools", response_model=List[MCPToolDescription])
        async def list_tools():
            """
            List all available tools.
            
            Agents call this endpoint to discover what tools are available.
            """
            return [
                MCPToolDescription(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.parameters,
                )
                for tool in self.tools.values()
            ]
        
        @self.app.post("/tools/{tool_name}", response_model=MCPToolResponse)
        async def call_tool(tool_name: str, request: MCPToolRequest):
            """
            Invoke a specific tool.
            
            Agents call this endpoint to execute tool functionality.
            """
            if tool_name not in self.tools:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tool '{tool_name}' not found"
                )
            
            tool = self.tools[tool_name]
            
            try:
                # Call the tool handler with parameters
                result = await tool.handler(**request.parameters)
                
                return MCPToolResponse(
                    success=True,
                    result=result,
                )
            except TypeError as e:
                # Parameter mismatch
                return MCPToolResponse(
                    success=False,
                    error=f"Invalid parameters: {str(e)}",
                )
            except Exception as e:
                # Handler error
                return MCPToolResponse(
                    success=False,
                    error=f"Tool execution failed: {str(e)}",
                )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "name": self.name,
                "version": self.version,
            }
    
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
            description: Human-readable description for agents
            parameters: JSON Schema describing tool parameters
            handler: Async callable that implements the tool logic
        
        Example:
            self.register_tool(
                name="get_balance",
                description="Get user's token balance",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "token": {"type": "string"},
                    },
                    "required": ["user_id", "token"],
                },
                handler=self._get_balance_handler,
            )
        """
        self.tools[name] = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )
        
        print(f"[MCP:{self.name}] Registered tool: {name}")
    
    @abstractmethod
    def setup_tools(self):
        """
        Override this method to register your tools.
        
        Called during initialization.
        """
        pass
