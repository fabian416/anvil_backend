"""
The Graph MCP Server.

Provides MCP tools for:
- Subgraph queries
- Protocol-specific data
- Historical blockchain data
- Entity queries

Feature Flag: mcp.servers.thegraph_enabled
"""

from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.infrastructure.mcp.base_server import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError


class TheGraphMCPServer(MCPServer):
    """MCP Server for The Graph protocol data."""
    
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.thegraph.com",
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize The Graph MCP server.
        
        Args:
            api_key: The Graph API key (optional)
            base_url: The Graph API base URL
            settings: MCP configuration settings
            
        Raises:
            MCPServerDisabledError: If The Graph server is disabled
        """
        self.settings = settings or MCPSettings()
        
        # Check if server is enabled
        if not self.settings.enabled or not self.settings.servers.thegraph_enabled:
            raise MCPServerDisabledError(
                "The Graph MCP server is disabled. "
                "Enable with mcp.servers.thegraph_enabled=true in config."
            )
        
        super().__init__(
            server_name="thegraph",
            description="The Graph subgraph queries for blockchain data",
            port=8083,
        )
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=30.0,
        )
        
        # Common subgraph endpoints
        self.subgraphs = {
            "uniswap_v3": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
            "aave_v3": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
            "curve": "https://api.thegraph.com/subgraphs/name/messari/curve-finance-ethereum",
        }
        
        # Create retry decorator for this server
        self._retry = retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            reraise=True,
        )
        
        # Register tools
        self.setup_tools()

    def setup_tools(self):
        """Register all The Graph tools."""
        
        # Tool 1: Query Uniswap V3
        self.register_tool(
            name="query_uniswap_v3",
            description="Query Uniswap V3 subgraph for pool, swap, and position data",
            parameters={
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "description": "Type of query: 'pools', 'swaps', 'positions'",
                        "enum": ["pools", "swaps", "positions"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query_type"],
            },
            handler=self._query_uniswap_v3,
        )
        
        # Tool 2: Query Aave V3
        self.register_tool(
            name="query_aave_v3",
            description="Query Aave V3 subgraph for lending pool and reserve data",
            parameters={
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "description": "Type of query: 'reserves', 'borrows', 'deposits'",
                        "enum": ["reserves", "borrows", "deposits"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query_type"],
            },
            handler=self._query_aave_v3,
        )
        
        # Tool 3: Custom GraphQL query
        self.register_tool(
            name="custom_query",
            description="Execute a custom GraphQL query on a subgraph",
            parameters={
                "type": "object",
                "properties": {
                    "subgraph": {
                        "type": "string",
                        "description": "Subgraph identifier (e.g., 'uniswap_v3', 'aave_v3', 'curve')",
                    },
                    "query": {
                        "type": "string",
                        "description": "GraphQL query string",
                    },
                },
                "required": ["subgraph", "query"],
            },
            handler=self._custom_query,
        )
        
        # Tool 4: Get available subgraphs
        self.register_tool(
            name="get_subgraphs",
            description="Get list of available subgraphs",
            parameters={
                "type": "object",
                "properties": {},
            },
            handler=self._get_subgraphs,
        )
    
    async def _query_uniswap_v3(
        self,
        query_type: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Query Uniswap V3 subgraph.
        
        Args:
            query_type: Type of query
            limit: Number of results
        
        Returns:
            Query results
        """
        try:
            if query_type == "pools":
                query = f"""
                {{
                    pools(first: {limit}, orderBy: totalValueLockedUSD, orderDirection: desc) {{
                        id
                        token0 {{
                            symbol
                        }}
                        token1 {{
                            symbol
                        }}
                        totalValueLockedUSD
                        volumeUSD
                        feeTier
                    }}
                }}
                """
            elif query_type == "swaps":
                query = f"""
                {{
                    swaps(first: {limit}, orderBy: timestamp, orderDirection: desc) {{
                        id
                        timestamp
                        amount0
                        amount1
                        amountUSD
                        token0 {{
                            symbol
                        }}
                        token1 {{
                            symbol
                        }}
                    }}
                }}
                """
            elif query_type == "positions":
                query = f"""
                {{
                    positions(first: {limit}, orderBy: liquidity, orderDirection: desc) {{
                        id
                        liquidity
                        owner
                        token0 {{
                            symbol
                        }}
                        token1 {{
                            symbol
                        }}
                    }}
                }}
                """
            else:
                return {"error": f"Invalid query type: {query_type}"}
            
            response = await self.client.post(
                self.subgraphs["uniswap_v3"],
                json={"query": query},
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "subgraph": "uniswap_v3",
                "query_type": query_type,
                "data": data.get("data", {}),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"The Graph API error: {str(e)}",
                "subgraph": "uniswap_v3",
            }
        except Exception as e:
            return {
                "error": f"Error querying Uniswap V3: {str(e)}",
                "subgraph": "uniswap_v3",
            }
    
    async def _query_aave_v3(
        self,
        query_type: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Query Aave V3 subgraph.
        
        Args:
            query_type: Type of query
            limit: Number of results
        
        Returns:
            Query results
        """
        try:
            if query_type == "reserves":
                query = f"""
                {{
                    reserves(first: {limit}, orderBy: totalLiquidity, orderDirection: desc) {{
                        id
                        symbol
                        name
                        totalLiquidity
                        availableLiquidity
                        liquidityRate
                        stableBorrowRate
                        variableBorrowRate
                    }}
                }}
                """
            elif query_type == "borrows":
                query = f"""
                {{
                    borrows(first: {limit}, orderBy: timestamp, orderDirection: desc) {{
                        id
                        timestamp
                        amount
                        reserve {{
                            symbol
                        }}
                        user {{
                            id
                        }}
                    }}
                }}
                """
            elif query_type == "deposits":
                query = f"""
                {{
                    deposits(first: {limit}, orderBy: timestamp, orderDirection: desc) {{
                        id
                        timestamp
                        amount
                        reserve {{
                            symbol
                        }}
                        user {{
                            id
                        }}
                    }}
                }}
                """
            else:
                return {"error": f"Invalid query type: {query_type}"}
            
            response = await self.client.post(
                self.subgraphs["aave_v3"],
                json={"query": query},
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "subgraph": "aave_v3",
                "query_type": query_type,
                "data": data.get("data", {}),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"The Graph API error: {str(e)}",
                "subgraph": "aave_v3",
            }
        except Exception as e:
            return {
                "error": f"Error querying Aave V3: {str(e)}",
                "subgraph": "aave_v3",
            }
    
    async def _custom_query(
        self,
        subgraph: str,
        query: str,
    ) -> Dict[str, Any]:
        """
        Execute custom GraphQL query.
        
        Args:
            subgraph: Subgraph identifier
            query: GraphQL query
        
        Returns:
            Query results
        """
        try:
            if subgraph not in self.subgraphs:
                return {
                    "error": f"Unknown subgraph: {subgraph}",
                    "available": list(self.subgraphs.keys()),
                }
            
            response = await self.client.post(
                self.subgraphs[subgraph],
                json={"query": query},
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "subgraph": subgraph,
                "data": data.get("data", {}),
                "errors": data.get("errors", []),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"The Graph API error: {str(e)}",
                "subgraph": subgraph,
            }
        except Exception as e:
            return {
                "error": f"Error executing query: {str(e)}",
                "subgraph": subgraph,
            }
    
    async def _get_subgraphs(self) -> Dict[str, Any]:
        """
        Get available subgraphs.
        
        Returns:
            List of subgraphs
        """
        return {
            "subgraphs": [
                {
                    "name": "uniswap_v3",
                    "description": "Uniswap V3 DEX data",
                    "endpoint": self.subgraphs["uniswap_v3"],
                },
                {
                    "name": "aave_v3",
                    "description": "Aave V3 lending protocol data",
                    "endpoint": self.subgraphs["aave_v3"],
                },
                {
                    "name": "curve",
                    "description": "Curve Finance stable swap data",
                    "endpoint": self.subgraphs["curve"],
                },
            ],
            "count": len(self.subgraphs),
        }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Main entry point for running server standalone
if __name__ == "__main__":
    import os
    import uvicorn
    
    # Get API key from environment
    api_key = os.getenv("THEGRAPH_API_KEY", "")
    
    # Create server
    server = TheGraphMCPServer(api_key=api_key)
    
    print(f"Starting The Graph MCP Server on http://0.0.0.0:8083")
    print(f"Tools endpoint: http://localhost:8083/tools")
    print(f"Health check: http://localhost:8083/health")
    
    # Run server
    uvicorn.run(server.app, host="0.0.0.0", port=8083)
