"""
1inch DEX MCP Server.

Provides MCP tools for:
- Getting swap quotes
- Finding best swap routes
- Checking liquidity sources

Feature Flag: mcp.servers.oneinch_enabled
"""

from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.infrastructure.mcp.base_server import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError


class OneInchMCPServer(MCPServer):
    """MCP Server for 1inch DEX aggregator."""
    
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.1inch.dev",
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize 1inch MCP server.
        
        Args:
            api_key: 1inch API key (optional for public endpoints)
            base_url: 1inch API base URL
            settings: MCP configuration settings
            
        Raises:
            MCPServerDisabledError: If 1inch server is disabled
        """
        self.settings = settings or MCPSettings()
        
        # Check if server is enabled
        if not self.settings.enabled or not self.settings.servers.oneinch_enabled:
            raise MCPServerDisabledError(
                "1inch MCP server is disabled. "
                "Enable with mcp.servers.oneinch_enabled=true in config."
            )
        
        super().__init__(
            server_name="1inch",
            description="1inch DEX aggregator for best swap routes and prices",
            port=8081,
        )
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}" if api_key else "",
            },
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
        self._register_tools()
    
    def _register_tools(self):
        """Register all 1inch tools."""
        
        # Tool 1: Get swap quote
        self.register_tool(
            name="get_swap_quote",
            description="Get best swap quote from 1inch aggregator for token swaps",
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID (1=Ethereum, 137=Polygon, 56=BSC, 42161=Arbitrum, 10=Optimism)",
                        "enum": [1, 56, 137, 10, 42161],
                    },
                    "from_token": {
                        "type": "string",
                        "description": "Source token contract address (e.g., 0xA0b86991...)",
                    },
                    "to_token": {
                        "type": "string",
                        "description": "Destination token contract address",
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount to swap in wei (e.g., '1000000' for 1 USDC)",
                    },
                },
                "required": ["chain_id", "from_token", "to_token", "amount"],
            },
            handler=self._get_swap_quote,
        )
        
        # Tool 2: Get liquidity sources
        self.register_tool(
            name="get_liquidity_sources",
            description="Get available liquidity sources (DEXes) for a chain",
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                        "enum": [1, 56, 137, 10, 42161],
                    },
                },
                "required": ["chain_id"],
            },
            handler=self._get_liquidity_sources,
        )
        
        # Tool 3: Get token price
        self.register_tool(
            name="get_token_price",
            description="Get current USD price for a token",
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                        "enum": [1, 56, 137, 10, 42161],
                    },
                    "token_address": {
                        "type": "string",
                        "description": "Token contract address",
                    },
                },
                "required": ["chain_id", "token_address"],
            },
            handler=self._get_token_price,
        )
        
        # Tool 4: Get supported chains
        self.register_tool(
            name="get_supported_chains",
            description="Get list of blockchain chains supported by 1inch",
            parameters={
                "type": "object",
                "properties": {},
            },
            handler=self._get_supported_chains,
        )
    
    async def _get_swap_quote(
        self,
        chain_id: int,
        from_token: str,
        to_token: str,
        amount: str,
    ) -> Dict[str, Any]:
        """
        Get swap quote from 1inch.
        
        Args:
            chain_id: Chain ID
            from_token: Source token address
            to_token: Destination token address
            amount: Amount in wei
        
        Returns:
            Quote details with estimated output, gas, and route
        """
        try:
            # 1inch API v5 quote endpoint
            response = await self.client.get(
                f"/swap/v5.2/{chain_id}/quote",
                params={
                    "src": from_token,
                    "dst": to_token,
                    "amount": amount,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "estimated_output": data.get("toAmount", "0"),
                "estimated_gas": data.get("estimatedGas", "0"),
                "protocols": data.get("protocols", []),
                "from_token": from_token,
                "to_token": to_token,
                "amount": amount,
                "chain_id": chain_id,
            }
        except httpx.HTTPError as e:
            return {
                "error": f"1inch API error: {str(e)}",
                "chain_id": chain_id,
            }
        except Exception as e:
            return {
                "error": f"Error getting quote: {str(e)}",
                "chain_id": chain_id,
            }
    
    async def _get_liquidity_sources(
        self,
        chain_id: int,
    ) -> Dict[str, Any]:
        """
        Get available liquidity sources.
        
        Args:
            chain_id: Chain ID
        
        Returns:
            List of liquidity sources (DEXes)
        """
        try:
            response = await self.client.get(
                f"/swap/v5.2/{chain_id}/liquidity-sources"
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "chain_id": chain_id,
                "sources": data.get("protocols", []),
                "count": len(data.get("protocols", [])),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"1inch API error: {str(e)}",
                "chain_id": chain_id,
            }
        except Exception as e:
            return {
                "error": f"Error getting liquidity sources: {str(e)}",
                "chain_id": chain_id,
            }
    
    async def _get_token_price(
        self,
        chain_id: int,
        token_address: str,
    ) -> Dict[str, Any]:
        """
        Get token price in USD.
        
        Args:
            chain_id: Chain ID
            token_address: Token contract address
        
        Returns:
            Token price in USD
        """
        try:
            response = await self.client.get(
                f"/price/v1.1/{chain_id}/{token_address}"
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "chain_id": chain_id,
                "token_address": token_address,
                "price_usd": data.get(token_address, "0"),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"1inch API error: {str(e)}",
                "chain_id": chain_id,
            }
        except Exception as e:
            return {
                "error": f"Error getting token price: {str(e)}",
                "chain_id": chain_id,
            }
    
    async def _get_supported_chains(self) -> Dict[str, Any]:
        """
        Get supported chains.
        
        Returns:
            List of supported chains with details
        """
        return {
            "chains": [
                {"id": 1, "name": "Ethereum", "symbol": "ETH"},
                {"id": 56, "name": "BNB Chain", "symbol": "BNB"},
                {"id": 137, "name": "Polygon", "symbol": "MATIC"},
                {"id": 10, "name": "Optimism", "symbol": "ETH"},
                {"id": 42161, "name": "Arbitrum", "symbol": "ETH"},
            ],
            "count": 5,
        }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Main entry point for running server standalone
if __name__ == "__main__":
    import os
    import uvicorn
    
    # Get API key from environment
    api_key = os.getenv("ONEINCH_API_KEY", "")
    
    # Create server
    server = OneInchMCPServer(api_key=api_key)
    
    print(f"Starting 1inch MCP Server on http://0.0.0.0:8081")
    print(f"Tools endpoint: http://localhost:8081/tools")
    print(f"Health check: http://localhost:8081/health")
    
    # Run server
    uvicorn.run(server.app, host="0.0.0.0", port=8081)
