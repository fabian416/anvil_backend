"""
CoinGecko MCP Server.

Provides MCP tools for:
- Token prices
- Market data
- Historical prices
- Token information

Feature Flag: mcp.servers.coingecko_enabled
"""

from typing import Dict, Any, Optional, List
import httpx

from app.infrastructure.mcp.base_server import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError


class CoinGeckoMCPServer(MCPServer):
    """MCP Server for CoinGecko market data."""
    
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.coingecko.com/api/v3",
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize CoinGecko MCP server.
        
        Args:
            api_key: CoinGecko API key (optional for public API)
            base_url: CoinGecko API base URL
            settings: MCP configuration settings
            
        Raises:
            MCPServerDisabledError: If CoinGecko server is disabled
        """
        self.settings = settings or MCPSettings()
        
        # Check if server is enabled
        if not self.settings.enabled or not self.settings.servers.coingecko_enabled:
            raise MCPServerDisabledError(
                "CoinGecko MCP server is disabled. "
                "Enable with mcp.servers.coingecko_enabled=true in config."
            )
        
        super().__init__(
            server_name="coingecko",
            description="CoinGecko market data and token prices",
            port=8084,
        )
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "x-cg-pro-api-key": api_key if api_key else "",
            },
            timeout=30.0,
        )
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all CoinGecko tools."""
        
        # Tool 1: Get token price
        self.register_tool(
            name="get_token_price",
            description="Get current USD price for one or more tokens",
            parameters={
                "type": "object",
                "properties": {
                    "token_ids": {
                        "type": "string",
                        "description": "Comma-separated token IDs (e.g., 'bitcoin,ethereum,uniswap')",
                    },
                    "vs_currency": {
                        "type": "string",
                        "description": "Currency to compare against (default: usd)",
                        "default": "usd",
                    },
                },
                "required": ["token_ids"],
            },
            handler=self._get_token_price,
        )
        
        # Tool 2: Get token market data
        self.register_tool(
            name="get_token_market_data",
            description="Get comprehensive market data for a token",
            parameters={
                "type": "object",
                "properties": {
                    "token_id": {
                        "type": "string",
                        "description": "Token ID (e.g., 'bitcoin', 'ethereum')",
                    },
                },
                "required": ["token_id"],
            },
            handler=self._get_token_market_data,
        )
        
        # Tool 3: Get historical price
        self.register_tool(
            name="get_historical_price",
            description="Get historical price data for a token",
            parameters={
                "type": "object",
                "properties": {
                    "token_id": {
                        "type": "string",
                        "description": "Token ID",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data (1, 7, 14, 30, 90, 365, max)",
                        "default": 7,
                    },
                },
                "required": ["token_id"],
            },
            handler=self._get_historical_price,
        )
        
        # Tool 4: Get trending tokens
        self.register_tool(
            name="get_trending_tokens",
            description="Get list of currently trending tokens",
            parameters={
                "type": "object",
                "properties": {},
            },
            handler=self._get_trending_tokens,
        )
        
        # Tool 5: Search tokens
        self.register_tool(
            name="search_tokens",
            description="Search for tokens by name or symbol",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (token name or symbol)",
                    },
                },
                "required": ["query"],
            },
            handler=self._search_tokens,
        )
        
        # Tool 6: Get top tokens by market cap
        self.register_tool(
            name="get_top_tokens",
            description="Get top tokens by market capitalization",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of tokens to return (default: 20)",
                        "default": 20,
                    },
                },
            },
            handler=self._get_top_tokens,
        )
    
    async def _get_token_price(
        self,
        token_ids: str,
        vs_currency: str = "usd",
    ) -> Dict[str, Any]:
        """
        Get current token prices.
        
        Args:
            token_ids: Comma-separated token IDs
            vs_currency: Currency to compare against
        
        Returns:
            Token prices
        """
        try:
            response = await self.client.get(
                "/simple/price",
                params={
                    "ids": token_ids,
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "prices": data,
                "currency": vs_currency,
                "tokens": token_ids.split(","),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"CoinGecko API error: {str(e)}",
                "token_ids": token_ids,
            }
        except Exception as e:
            return {
                "error": f"Error getting token price: {str(e)}",
                "token_ids": token_ids,
            }
    
    async def _get_token_market_data(self, token_id: str) -> Dict[str, Any]:
        """
        Get comprehensive market data.
        
        Args:
            token_id: Token ID
        
        Returns:
            Market data
        """
        try:
            response = await self.client.get(f"/coins/{token_id}")
            response.raise_for_status()
            data = response.json()
            
            market_data = data.get("market_data", {})
            
            return {
                "token_id": token_id,
                "name": data.get("name"),
                "symbol": data.get("symbol"),
                "current_price": market_data.get("current_price", {}).get("usd", 0),
                "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                "total_volume": market_data.get("total_volume", {}).get("usd", 0),
                "price_change_24h": market_data.get("price_change_percentage_24h", 0),
                "price_change_7d": market_data.get("price_change_percentage_7d", 0),
                "price_change_30d": market_data.get("price_change_percentage_30d", 0),
                "ath": market_data.get("ath", {}).get("usd", 0),
                "atl": market_data.get("atl", {}).get("usd", 0),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"CoinGecko API error: {str(e)}",
                "token_id": token_id,
            }
        except Exception as e:
            return {
                "error": f"Error getting market data: {str(e)}",
                "token_id": token_id,
            }
    
    async def _get_historical_price(
        self,
        token_id: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get historical price data.
        
        Args:
            token_id: Token ID
            days: Number of days
        
        Returns:
            Historical price data
        """
        try:
            response = await self.client.get(
                f"/coins/{token_id}/market_chart",
                params={
                    "vs_currency": "usd",
                    "days": days,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            prices = data.get("prices", [])
            
            return {
                "token_id": token_id,
                "days": days,
                "prices": [
                    {
                        "timestamp": int(p[0]),
                        "price": p[1],
                    }
                    for p in prices
                ],
                "count": len(prices),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"CoinGecko API error: {str(e)}",
                "token_id": token_id,
            }
        except Exception as e:
            return {
                "error": f"Error getting historical price: {str(e)}",
                "token_id": token_id,
            }
    
    async def _get_trending_tokens(self) -> Dict[str, Any]:
        """
        Get trending tokens.
        
        Returns:
            Trending tokens list
        """
        try:
            response = await self.client.get("/search/trending")
            response.raise_for_status()
            data = response.json()
            
            trending = data.get("coins", [])
            
            return {
                "trending": [
                    {
                        "id": coin["item"].get("id"),
                        "name": coin["item"].get("name"),
                        "symbol": coin["item"].get("symbol"),
                        "market_cap_rank": coin["item"].get("market_cap_rank"),
                        "price_btc": coin["item"].get("price_btc"),
                    }
                    for coin in trending
                ],
                "count": len(trending),
            }
        except httpx.HTTPError as e:
            return {"error": f"CoinGecko API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error getting trending tokens: {str(e)}"}
    
    async def _search_tokens(self, query: str) -> Dict[str, Any]:
        """
        Search for tokens.
        
        Args:
            query: Search query
        
        Returns:
            Search results
        """
        try:
            response = await self.client.get(
                "/search",
                params={"query": query},
            )
            response.raise_for_status()
            data = response.json()
            
            coins = data.get("coins", [])[:10]  # Top 10 results
            
            return {
                "query": query,
                "results": [
                    {
                        "id": coin.get("id"),
                        "name": coin.get("name"),
                        "symbol": coin.get("symbol"),
                        "market_cap_rank": coin.get("market_cap_rank"),
                    }
                    for coin in coins
                ],
                "count": len(coins),
            }
        except httpx.HTTPError as e:
            return {
                "error": f"CoinGecko API error: {str(e)}",
                "query": query,
            }
        except Exception as e:
            return {
                "error": f"Error searching tokens: {str(e)}",
                "query": query,
            }
    
    async def _get_top_tokens(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get top tokens by market cap.
        
        Args:
            limit: Number of tokens
        
        Returns:
            Top tokens list
        """
        try:
            response = await self.client.get(
                "/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": limit,
                    "page": 1,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "tokens": [
                    {
                        "id": token.get("id"),
                        "name": token.get("name"),
                        "symbol": token.get("symbol"),
                        "current_price": token.get("current_price"),
                        "market_cap": token.get("market_cap"),
                        "market_cap_rank": token.get("market_cap_rank"),
                        "price_change_24h": token.get("price_change_percentage_24h"),
                    }
                    for token in data
                ],
                "count": len(data),
            }
        except httpx.HTTPError as e:
            return {"error": f"CoinGecko API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error getting top tokens: {str(e)}"}
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Main entry point for running server standalone
if __name__ == "__main__":
    import os
    import uvicorn
    
    # Get API key from environment
    api_key = os.getenv("COINGECKO_API_KEY", "")
    
    # Create server
    server = CoinGeckoMCPServer(api_key=api_key)
    
    print(f"Starting CoinGecko MCP Server on http://0.0.0.0:8084")
    print(f"Tools endpoint: http://localhost:8084/tools")
    print(f"Health check: http://localhost:8084/health")
    
    # Run server
    uvicorn.run(server.app, host="0.0.0.0", port=8084)
