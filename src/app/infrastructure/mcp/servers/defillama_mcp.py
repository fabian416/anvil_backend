"""
DeFiLlama MCP Server.

Provides MCP tools for:
- Protocol TVL queries
- Historical TVL data
- Protocol information
- Chain TVL comparisons

Feature Flag: mcp.servers.defillama_enabled
"""

from typing import Dict, Any, Optional, List
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.infrastructure.mcp.base_server import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError


class DeFiLlamaMCPServer(MCPServer):
    """MCP Server for DeFiLlama protocol analytics."""

    def __init__(
        self,
        base_url: str = "https://api.llama.fi",
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize DeFiLlama MCP server.

        Args:
            base_url: DeFiLlama API base URL
            settings: MCP configuration settings

        Raises:
            MCPServerDisabledError: If DeFiLlama server is disabled
        """
        self.settings = settings or MCPSettings()

        # Check if server is enabled
        if not self.settings.enabled or not self.settings.servers.defillama_enabled:
            raise MCPServerDisabledError(
                "DeFiLlama MCP server is disabled. "
                "Enable with mcp.servers.defillama_enabled=true in config."
            )

        super().__init__(
            server_name="defillama",
            description="DeFiLlama protocol analytics and TVL data",
            port=8082,
        )
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
        )

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
        """Register all DeFiLlama tools."""

        # Tool 1: Get protocol TVL
        self.register_tool(
            name="get_protocol_tvl",
            description="Get current Total Value Locked (TVL) for a specific protocol",
            parameters={
                "type": "object",
                "properties": {
                    "protocol": {
                        "type": "string",
                        "description": "Protocol slug (e.g., 'aave', 'uniswap', 'curve')",
                    },
                },
                "required": ["protocol"],
            },
            handler=self._get_protocol_tvl,
        )

        # Tool 2: Get all protocols
        self.register_tool(
            name="get_all_protocols",
            description="Get list of all tracked DeFi protocols with basic info",
            parameters={
                "type": "object",
                "properties": {},
            },
            handler=self._get_all_protocols,
        )

        # Tool 3: Get historical TVL
        self.register_tool(
            name="get_historical_tvl",
            description="Get historical TVL data for a protocol",
            parameters={
                "type": "object",
                "properties": {
                    "protocol": {
                        "type": "string",
                        "description": "Protocol slug",
                    },
                },
                "required": ["protocol"],
            },
            handler=self._get_historical_tvl,
        )

        # Tool 4: Get chain TVL
        self.register_tool(
            name="get_chain_tvl",
            description="Get current TVL for all protocols on a specific chain",
            parameters={
                "type": "object",
                "properties": {
                    "chain": {
                        "type": "string",
                        "description": "Chain name (e.g., 'Ethereum', 'Polygon', 'Arbitrum')",
                    },
                },
                "required": ["chain"],
            },
            handler=self._get_chain_tvl,
        )

        # Tool 5: Get chains list
        self.register_tool(
            name="get_chains",
            description="Get list of all supported blockchain chains",
            parameters={
                "type": "object",
                "properties": {},
            },
            handler=self._get_chains,
        )

    async def _get_protocol_tvl(self, protocol: str) -> Dict[str, Any]:
        """
        Get current TVL for a protocol.

        Args:
            protocol: Protocol slug

        Returns:
            Protocol TVL data
        """

        @self._retry
        async def _fetch():
            response = await self.client.get(f"/protocol/{protocol}")
            response.raise_for_status()
            return response.json()

        try:
            data = await _fetch()

            return {
                "protocol": protocol,
                "name": data.get("name", protocol),
                "tvl": data.get("tvl", 0),
                "chain_tvls": data.get("chainTvls", {}),
                "change_1d": data.get("change_1d", 0),
                "change_7d": data.get("change_7d", 0),
                "category": data.get("category", "Unknown"),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"DeFiLlama API error: {str(e)}",
                "protocol": protocol,
            }
        except Exception as e:
            return {
                "error": f"Error getting protocol TVL: {str(e)}",
                "protocol": protocol,
            }

    async def _get_all_protocols(self) -> Dict[str, Any]:
        """
        Get all tracked protocols.

        Returns:
            List of protocols with basic info
        """

        @self._retry
        async def _fetch():
            response = await self.client.get("/protocols")
            response.raise_for_status()
            return response.json()

        try:
            data = await _fetch()

            # Return top 50 by TVL
            protocols = sorted(data, key=lambda x: x.get("tvl", 0), reverse=True)[:50]

            return {
                "count": len(protocols),
                "protocols": [
                    {
                        "name": p.get("name"),
                        "slug": p.get("slug"),
                        "tvl": p.get("tvl", 0),
                        "category": p.get("category", "Unknown"),
                        "chain": p.get("chain", "Multi-chain"),
                    }
                    for p in protocols
                ],
            }
        except httpx.HTTPError as e:
            return {"error": f"DeFiLlama API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error getting protocols: {str(e)}"}

    async def _get_historical_tvl(self, protocol: str) -> Dict[str, Any]:
        """
        Get historical TVL data.

        Args:
            protocol: Protocol slug

        Returns:
            Historical TVL data
        """

        @self._retry
        async def _fetch():
            response = await self.client.get(f"/protocol/{protocol}")
            response.raise_for_status()
            return response.json()

        try:
            data = await _fetch()

            # Get last 30 days
            tvl_history = data.get("tvl", [])[-30:]

            return {
                "protocol": protocol,
                "history": [
                    {
                        "date": item.get("date"),
                        "tvl": item.get("totalLiquidityUSD", 0),
                    }
                    for item in tvl_history
                ],
                "count": len(tvl_history),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"DeFiLlama API error: {str(e)}",
                "protocol": protocol,
            }
        except Exception as e:
            return {
                "error": f"Error getting historical TVL: {str(e)}",
                "protocol": protocol,
            }

    async def _get_chain_tvl(self, chain: str) -> Dict[str, Any]:
        """
        Get TVL for all protocols on a chain.

        Args:
            chain: Chain name

        Returns:
            Chain TVL data
        """

        @self._retry
        async def _fetch():
            response = await self.client.get(f"/v2/chains")
            response.raise_for_status()
            return response.json()

        try:
            data = await _fetch()

            # Find chain data
            chain_data = next(
                (c for c in data if c.get("name", "").lower() == chain.lower()), None
            )

            if not chain_data:
                return {
                    "error": f"Chain '{chain}' not found",
                    "chain": chain,
                }

            return {
                "chain": chain,
                "tvl": chain_data.get("tvl", 0),
                "protocols": chain_data.get("protocols", 0),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"DeFiLlama API error: {str(e)}",
                "chain": chain,
            }
        except Exception as e:
            return {
                "error": f"Error getting chain TVL: {str(e)}",
                "chain": chain,
            }

    async def _get_chains(self) -> Dict[str, Any]:
        """
        Get all supported chains.

        Returns:
            List of chains with TVL
        """

        @self._retry
        async def _fetch():
            response = await self.client.get("/v2/chains")
            response.raise_for_status()
            return response.json()

        try:
            data = await _fetch()

            return {
                "chains": [
                    {
                        "name": c.get("name"),
                        "tvl": c.get("tvl", 0),
                        "protocols": c.get("protocols", 0),
                    }
                    for c in data[:20]  # Top 20 chains
                ],
                "count": len(data),
            }
        except httpx.HTTPError as e:
            return {"error": f"DeFiLlama API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error getting chains: {str(e)}"}

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Main entry point for running server standalone
if __name__ == "__main__":
    import uvicorn

    # Create server
    server = DeFiLlamaMCPServer()

    print(f"Starting DeFiLlama MCP Server on http://0.0.0.0:8082")
    print(f"Tools endpoint: http://localhost:8082/tools")
    print(f"Health check: http://localhost:8082/health")

    # Run server
    uvicorn.run(server.app, host="0.0.0.0", port=8082)
