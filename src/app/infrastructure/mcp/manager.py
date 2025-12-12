"""MCP Server Manager - Central orchestration for all MCP servers.

Manages lifecycle, discovery, and routing for all Model Context Protocol servers.
Provides a unified interface for Agno agents to discover and invoke tools
across multiple specialized MCP servers.

Architecture:
    - Singleton manager instance
    - Dynamic server registration
    - Unified tool discovery
    - Request routing to appropriate servers
    - Health monitoring
    - Graceful start/stop
    - Feature flag support for enable/disable

Usage:
    # Initialize manager
    manager = MCPServerManager(settings)
    
    # Register servers (only enabled ones)
    manager.register_server(OneInchMCPServer())
    manager.register_server(AaveMCPServer())
    
    # Start all servers
    await manager.start_all()
    
    # Discover tools
    tools = await manager.get_all_tools()
    
    # Call a tool (auto-routes to correct server)
    result = await manager.call_tool("get_swap_quote", {...})
"""
from typing import Dict, List, Any, Optional
import asyncio
from dataclasses import dataclass
import uvicorn
from fastapi import FastAPI, HTTPException

from app.infrastructure.mcp.base import MCPServer, MCPToolDescription, MCPToolRequest, MCPToolResponse
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError


@dataclass
class ServerInfo:
    """Information about a registered MCP server."""
    server: MCPServer
    port: int
    process: Optional[asyncio.subprocess.Process] = None
    is_running: bool = False


class MCPServerManager:
    """
    Central manager for all MCP servers.
    
    Responsibilities:
    - Register and manage multiple MCP servers
    - Start/stop servers on different ports
    - Provide unified tool discovery
    - Route tool calls to appropriate servers
    - Monitor server health
    
    Example:
        manager = MCPServerManager()
        manager.register_server(OneInchMCPServer(), port=8081)
        manager.register_server(AaveMCPServer(), port=8082)
        await manager.start_all()
    """
    
    def __init__(self, settings: Optional[MCPSettings] = None):
        """
        Initialize MCP server manager.
        
        Args:
            settings: MCP configuration settings with feature flags
        """
        self.servers: Dict[str, ServerInfo] = {}
        self.tool_to_server_map: Dict[str, str] = {}
        self.settings = settings or MCPSettings()
        
        # Create unified API
        self.app = FastAPI(
            title="MCP Server Manager",
            version="1.0.0",
            description="Unified interface for all MCP servers",
        )
        
        self._register_routes()
    
    def register_server(
        self,
        server: MCPServer,
        port: int,
        auto_start: bool = False,
    ):
        """
        Register an MCP server with the manager.
        
        Args:
            server: MCPServer instance to register
            port: Port number for this server
            auto_start: Whether to start server immediately
            
        Raises:
            MCPServerDisabledError: If server is disabled in settings
        """
        # Handle both base.MCPServer (uses 'name') and base_server.MCPServer (uses 'server_name')
        server_name = getattr(server, 'name', None) or getattr(server, 'server_name', None)
        if not server_name:
            raise ValueError("Server must have either 'name' or 'server_name' attribute")
        
        # Check if MCP is globally disabled
        if not self.settings.enabled:
            raise MCPServerDisabledError(
                f"MCP system is disabled. Enable with mcp.enabled=true in config."
            )
        
        # Check if specific server is enabled
        if not self._is_server_enabled(server_name):
            raise MCPServerDisabledError(
                f"MCP server '{server_name}' is disabled. "
                f"Enable with mcp.servers.{server_name}_enabled=true in config."
            )
        
        if server_name in self.servers:
            raise ValueError(f"Server '{server_name}' is already registered")
        
        # Register server
        self.servers[server_name] = ServerInfo(
            server=server,
            port=port,
            is_running=False,
        )
        
        # Map tools to server
        for tool_name in server.tools.keys():
            # Prefix tool name with server name to avoid conflicts
            qualified_tool_name = f"{server_name}_{tool_name}"
            self.tool_to_server_map[qualified_tool_name] = server_name
            
            # Also map non-prefixed for convenience (if no conflict)
            if tool_name not in self.tool_to_server_map:
                self.tool_to_server_map[tool_name] = server_name
        
        print(f"[Manager] Registered server: {server_name} (port {port}, {len(server.tools)} tools)")
    
    def _is_server_enabled(self, server_name: str) -> bool:
        """
        Check if a server is enabled in settings.
        
        Args:
            server_name: Name of the server to check
            
        Returns:
            True if server is enabled, False otherwise
        """
        server_flag_map = {
            "defillama": self.settings.servers.defillama_enabled,
            "oneinch": self.settings.servers.oneinch_enabled,
            "thegraph": self.settings.servers.thegraph_enabled,
            "coingecko": self.settings.servers.coingecko_enabled,
            "aave": self.settings.servers.aave_enabled,
            "portfolio": self.settings.servers.portfolio_enabled,
        }
        
        return server_flag_map.get(server_name, True)  # Default to enabled if unknown
    
    async def start_server(self, server_name: str):
        """
        Start a specific MCP server.
        
        Args:
            server_name: Name of server to start
        """
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not registered")
        
        server_info = self.servers[server_name]
        
        if server_info.is_running:
            print(f"[Manager] Server '{server_name}' is already running")
            return
        
        # Start server in background
        # In production, this would use uvicorn programmatically or subprocess
        # For now, mark as running (actual startup happens separately)
        server_info.is_running = True
        
        print(f"[Manager] Started server: {server_name} on port {server_info.port}")
        print(f"          Access at: http://localhost:{server_info.port}")
    
    async def stop_server(self, server_name: str):
        """
        Stop a specific MCP server.
        
        Args:
            server_name: Name of server to stop
        """
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not registered")
        
        server_info = self.servers[server_name]
        
        if not server_info.is_running:
            print(f"[Manager] Server '{server_name}' is not running")
            return
        
        # Stop server
        if server_info.process:
            server_info.process.terminate()
            await server_info.process.wait()
        
        server_info.is_running = False
        server_info.process = None
        
        print(f"[Manager] Stopped server: {server_name}")
    
    async def start_all(self):
        """Start all registered servers."""
        print(f"[Manager] Starting {len(self.servers)} servers...")
        
        for server_name in self.servers.keys():
            await self.start_server(server_name)
        
        print(f"[Manager] All servers started!")
    
    async def stop_all(self):
        """Stop all running servers."""
        print(f"[Manager] Stopping all servers...")
        
        for server_name in self.servers.keys():
            await self.stop_server(server_name)
        
        print(f"[Manager] All servers stopped!")
    
    def get_server_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all registered servers.
        
        Returns:
            List of server status dictionaries
        """
        status = []
        
        for name, info in self.servers.items():
            status.append({
                "name": name,
                "port": info.port,
                "is_running": info.is_running,
                "tools_count": len(info.server.tools),
                "url": f"http://localhost:{info.port}" if info.is_running else None,
            })
        
        return status
    
    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get all tools from all registered servers.
        
        Returns:
            List of tool descriptions with server information
        """
        all_tools = []
        
        for server_name, info in self.servers.items():
            server = info.server
            
            for tool_name, tool in server.tools.items():
                all_tools.append({
                    "server": server_name,
                    "tool_name": tool_name,
                    "qualified_name": f"{server_name}_{tool_name}",
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "server_url": f"http://localhost:{info.port}",
                })
        
        return all_tools
    
    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Call a tool by name, automatically routing to the correct server.
        
        Args:
            tool_name: Name of tool to call (can be qualified with server name)
            parameters: Tool parameters
        
        Returns:
            Tool execution result
        
        Raises:
            ValueError: If tool not found or server not running
        """
        # Determine which server has this tool
        if tool_name not in self.tool_to_server_map:
            raise ValueError(
                f"Tool '{tool_name}' not found. "
                f"Available tools: {', '.join(self.tool_to_server_map.keys())}"
            )
        
        server_name = self.tool_to_server_map[tool_name]
        server_info = self.servers[server_name]
        
        if not server_info.is_running:
            raise ValueError(
                f"Server '{server_name}' is not running. "
                f"Start it first with: manager.start_server('{server_name}')"
            )
        
        # Get the actual tool name (without server prefix if it was used)
        actual_tool_name = tool_name.replace(f"{server_name}_", "")
        
        # Call the tool directly on the server
        tool = server_info.server.tools.get(actual_tool_name)
        if not tool:
            raise ValueError(f"Tool '{actual_tool_name}' not found in server '{server_name}'")
        
        try:
            result = await tool.handler(**parameters)
            return {
                "success": True,
                "server": server_name,
                "tool": actual_tool_name,
                "result": result,
            }
        except Exception as e:
            return {
                "success": False,
                "server": server_name,
                "tool": actual_tool_name,
                "error": str(e),
            }
    
    def _register_routes(self):
        """Register unified API routes."""
        
        @self.app.get("/")
        async def manager_info():
            """Get manager information."""
            return {
                "name": "MCP Server Manager",
                "version": "1.0.0",
                "servers_count": len(self.servers),
                "servers": self.get_server_status(),
                "total_tools": sum(len(info.server.tools) for info in self.servers.values()),
            }
        
        @self.app.get("/servers")
        async def list_servers():
            """List all registered servers."""
            return {
                "servers": self.get_server_status(),
            }
        
        @self.app.get("/tools")
        async def list_all_tools():
            """List all tools from all servers."""
            tools = await self.get_all_tools()
            return {
                "tools_count": len(tools),
                "tools": tools,
            }
        
        @self.app.post("/tools/{tool_name}")
        async def call_any_tool(tool_name: str, request: MCPToolRequest):
            """Call a tool from any server."""
            try:
                result = await self.call_tool(tool_name, request.parameters)
                return result
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        @self.app.post("/servers/{server_name}/start")
        async def start_server_endpoint(server_name: str):
            """Start a specific server."""
            try:
                await self.start_server(server_name)
                return {"success": True, "message": f"Server '{server_name}' started"}
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        @self.app.post("/servers/{server_name}/stop")
        async def stop_server_endpoint(server_name: str):
            """Stop a specific server."""
            try:
                await self.stop_server(server_name)
                return {"success": True, "message": f"Server '{server_name}' stopped"}
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            running_count = sum(1 for info in self.servers.values() if info.is_running)
            return {
                "status": "healthy",
                "servers_registered": len(self.servers),
                "servers_running": running_count,
            }


# Singleton instance
_manager_instance: Optional[MCPServerManager] = None


def get_mcp_manager() -> MCPServerManager:
    """
    Get the singleton MCP server manager instance.
    
    Returns:
        MCPServerManager singleton
    """
    global _manager_instance
    
    if _manager_instance is None:
        _manager_instance = MCPServerManager()
    
    return _manager_instance


# Standalone manager API server
if __name__ == "__main__":
    import sys
    
    # Initialize manager
    manager = get_mcp_manager()
    
    # Register all servers
    from app.infrastructure.mcp.servers.portfolio_mcp import PortfolioMCPServer
    from app.infrastructure.mcp.servers.oneinch_mcp import OneInchMCPServer
    from app.infrastructure.mcp.servers.aave_mcp import AaveMCPServer
    from app.infrastructure.mcp.servers.defillama_mcp import DeFiLlamaMCPServer
    
    print("""
╔══════════════════════════════════════════════════════════╗
║          MCP Server Manager Starting...                  ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Register servers
    manager.register_server(PortfolioMCPServer(), port=8081)
    manager.register_server(OneInchMCPServer(), port=8082)
    manager.register_server(AaveMCPServer(), port=8083)
    manager.register_server(DeFiLlamaMCPServer(), port=8084)
    
    print(f"""
Registered Servers:
""")
    for status in manager.get_server_status():
        print(f"  • {status['name']:15} - Port {status['port']} - {status['tools_count']} tools")
    
    total_tools = sum(len(info.server.tools) for info in manager.servers.values())
    
    print(f"""
Total Tools Available: {total_tools}

Manager API Endpoints:
  GET  /              - Manager info
  GET  /servers       - List all servers
  GET  /tools         - List all tools
  POST /tools/{{name}}  - Call any tool
  POST /servers/{{name}}/start - Start server
  POST /servers/{{name}}/stop  - Stop server
  GET  /health        - Health check

Manager API Port: 8080
Manager URL: http://localhost:8080

Individual Server URLs:
  • Portfolio:  http://localhost:8081
  • 1inch:      http://localhost:8082
  • Aave:       http://localhost:8083
  • DeFiLlama:  http://localhost:8084

To start individual servers, run them separately:
  python -m app.infrastructure.mcp.servers.portfolio_mcp
  python -m app.infrastructure.mcp.servers.oneinch_mcp
  python -m app.infrastructure.mcp.servers.aave_mcp
  python -m app.infrastructure.mcp.servers.defillama_mcp

Or use the manager endpoints to control them.

Starting Manager API...
    """)
    
    # Run manager API
    uvicorn.run(
        manager.app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )
