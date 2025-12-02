"""DeFiLlama MCP Server - DeFi Analytics Tools.

Exposes DeFiLlama API functionality as MCP tools for AI agents.
Provides protocol analytics, TVL data, yields, fees, and market intelligence.

Tools:
    - get_protocol_tvl: Get Total Value Locked for protocols
    - get_chain_tvl: Get TVL breakdown by blockchain
    - get_yields: Get yield farming opportunities and APY
    - get_protocol_fees: Get protocol revenue and fee data
    - get_stablecoin_data: Get stablecoin market cap and chains
    - compare_protocols: Compare multiple protocols by metrics
    - get_trending_protocols: Get protocols with highest growth
    - get_protocol_info: Get detailed protocol information

Integration Points:
    - DeFiLlama public API (no key required)
    - Cached responses for performance
    - Rate limiting (300 req/5min)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx

from app.infrastructure.mcp.base import MCPServer


class DeFiLlamaMCPServer(MCPServer):
    """
    MCP server for DeFiLlama analytics and market data.
    
    Provides AI agents with tools to:
    - Query protocol TVL and metrics
    - Find best yield opportunities
    - Analyze protocol revenues
    - Track stablecoin adoption
    - Compare DeFi protocols
    
    Example usage by agent:
        # Get protocol TVL
        tvl = await call_tool("get_protocol_tvl", {
            "protocol": "aave"
        })
        
        # Find best yields
        yields = await call_tool("get_yields", {
            "chain": "Ethereum",
            "min_tvl": 1000000
        })
    """
    
    def __init__(self):
        """Initialize DeFiLlama MCP server."""
        super().__init__(
            name="defillama",
            version="1.0.0",
            description="DeFiLlama analytics for DeFi protocols and yields",
        )
        
        self.base_url = "https://api.llama.fi"
        self.yields_url = "https://yields.llama.fi"
        
        # Common chains
        self.chains = [
            "Ethereum", "BSC", "Polygon", "Arbitrum", "Optimism",
            "Avalanche", "Fantom", "Solana", "Base", "zkSync"
        ]
        
        self.setup_tools()
    
    def setup_tools(self):
        """Register all DeFiLlama tools."""
        
        # Tool 1: Get protocol TVL
        self.register_tool(
            name="get_protocol_tvl",
            description=(
                "Get Total Value Locked (TVL) data for a specific DeFi protocol. "
                "Returns current TVL, historical data, chain breakdown, and token composition."
            ),
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
        
        # Tool 2: Get chain TVL
        self.register_tool(
            name="get_chain_tvl",
            description=(
                "Get TVL breakdown by blockchain. Shows which chains have the most value locked "
                "and protocol distribution."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "chain": {
                        "type": "string",
                        "description": "Chain name (e.g., 'Ethereum', 'Polygon', 'Arbitrum')",
                    },
                },
                "required": [],
            },
            handler=self._get_chain_tvl,
        )
        
        # Tool 3: Get yields
        self.register_tool(
            name="get_yields",
            description=(
                "Get yield farming opportunities across DeFi protocols. "
                "Returns APY, TVL, risk scores, and pool information. "
                "Useful for finding best returns."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "chain": {
                        "type": "string",
                        "description": "Filter by chain (optional)",
                    },
                    "protocol": {
                        "type": "string",
                        "description": "Filter by protocol (optional)",
                    },
                    "min_tvl": {
                        "type": "number",
                        "description": "Minimum TVL in USD (default: 1000000)",
                        "default": 1000000,
                    },
                    "min_apy": {
                        "type": "number",
                        "description": "Minimum APY percentage (default: 0)",
                        "default": 0,
                    },
                    "stablecoin_only": {
                        "type": "boolean",
                        "description": "Only return stablecoin pools (lower risk)",
                        "default": False,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of results (default: 20)",
                        "default": 20,
                    },
                },
                "required": [],
            },
            handler=self._get_yields,
        )
        
        # Tool 4: Get protocol fees
        self.register_tool(
            name="get_protocol_fees",
            description=(
                "Get protocol revenue and fee data. Shows daily fees, revenue, "
                "and protocol earnings. Useful for analyzing protocol sustainability."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "protocol": {
                        "type": "string",
                        "description": "Protocol slug (e.g., 'uniswap', 'gmx')",
                    },
                },
                "required": ["protocol"],
            },
            handler=self._get_protocol_fees,
        )
        
        # Tool 5: Get stablecoin data
        self.register_tool(
            name="get_stablecoin_data",
            description=(
                "Get stablecoin market data including circulating supply, "
                "chain distribution, and market dominance."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "stablecoin": {
                        "type": "string",
                        "description": "Stablecoin symbol (e.g., 'USDC', 'USDT', 'DAI')",
                    },
                },
                "required": [],
            },
            handler=self._get_stablecoin_data,
        )
        
        # Tool 6: Compare protocols
        self.register_tool(
            name="compare_protocols",
            description=(
                "Compare multiple DeFi protocols side-by-side. "
                "Returns TVL, users, volume, fees, and other metrics."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "protocols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of protocol slugs to compare (e.g., ['aave', 'compound', 'venus'])",
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to compare: 'tvl', 'users', 'fees', 'revenue', 'volume'",
                        "default": ["tvl", "fees"],
                    },
                },
                "required": ["protocols"],
            },
            handler=self._compare_protocols,
        )
        
        # Tool 7: Get trending protocols
        self.register_tool(
            name="get_trending_protocols",
            description=(
                "Get protocols with highest growth in TVL or volume. "
                "Useful for discovering new opportunities."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe for growth calculation",
                        "enum": ["1d", "7d", "30d"],
                        "default": "7d",
                    },
                    "metric": {
                        "type": "string",
                        "description": "Metric to rank by: 'tvl', 'volume', 'fees'",
                        "enum": ["tvl", "volume", "fees"],
                        "default": "tvl",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of protocols to return",
                        "default": 10,
                    },
                },
                "required": [],
            },
            handler=self._get_trending_protocols,
        )
        
        # Tool 8: Get protocol info
        self.register_tool(
            name="get_protocol_info",
            description=(
                "Get detailed information about a protocol including description, "
                "category, links, audits, and token information."
            ),
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
            handler=self._get_protocol_info,
        )
    
    # ==================== Tool Handlers ====================
    
    async def _get_protocol_tvl(
        self,
        protocol: str,
    ) -> Dict[str, Any]:
        """Get protocol TVL from DeFiLlama API."""
        # TODO: Integrate with actual DeFiLlama API
        # For now, return mock data
        
        # In production:
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(f"{self.base_url}/protocol/{protocol}")
        #     data = response.json()
        
        # Mock TVL data for common protocols
        mock_protocols = {
            "aave": {
                "name": "Aave",
                "slug": "aave",
                "tvl": 11500000000,  # $11.5B
                "chainTvls": {
                    "Ethereum": 7800000000,
                    "Polygon": 1200000000,
                    "Arbitrum": 950000000,
                    "Optimism": 850000000,
                    "Avalanche": 700000000,
                },
                "change_1d": 2.5,
                "change_7d": 8.3,
                "change_30d": 15.7,
                "category": "Lending",
                "chains": ["Ethereum", "Polygon", "Arbitrum", "Optimism", "Avalanche"],
            },
            "uniswap": {
                "name": "Uniswap",
                "slug": "uniswap",
                "tvl": 5200000000,  # $5.2B
                "chainTvls": {
                    "Ethereum": 4100000000,
                    "Polygon": 450000000,
                    "Arbitrum": 350000000,
                    "Optimism": 200000000,
                    "Base": 100000000,
                },
                "change_1d": 1.2,
                "change_7d": 5.1,
                "change_30d": 12.3,
                "category": "Dexes",
                "chains": ["Ethereum", "Polygon", "Arbitrum", "Optimism", "Base"],
            },
        }
        
        protocol_data = mock_protocols.get(
            protocol.lower(),
            {
                "name": protocol.title(),
                "slug": protocol,
                "tvl": 0,
                "chainTvls": {},
                "change_1d": 0,
                "change_7d": 0,
                "change_30d": 0,
                "category": "Unknown",
                "chains": [],
            },
        )
        
        return {
            **protocol_data,
            "tvl_formatted": f"${protocol_data['tvl'] / 1e9:.2f}B",
            "timestamp": datetime.utcnow().isoformat(),
            "note": "This is mock data. Real implementation will call DeFiLlama API.",
        }
    
    async def _get_chain_tvl(
        self,
        chain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get TVL by chain."""
        # TODO: Integrate with actual DeFiLlama API
        
        # Mock chain TVL data
        mock_chain_tvls = {
            "Ethereum": {
                "tvl": 65000000000,  # $65B
                "change_1d": 1.5,
                "protocols_count": 450,
                "top_protocols": ["Lido", "MakerDAO", "Aave", "Uniswap", "Curve"],
            },
            "BSC": {
                "tvl": 4200000000,  # $4.2B
                "change_1d": 2.1,
                "protocols_count": 380,
                "top_protocols": ["PancakeSwap", "Venus", "Radiant", "Alpaca", "Biswap"],
            },
            "Polygon": {
                "tvl": 1800000000,  # $1.8B
                "change_1d": 3.2,
                "protocols_count": 250,
                "top_protocols": ["Aave", "QuickSwap", "Balancer", "Gains Network", "Stargate"],
            },
        }
        
        if chain:
            chain_data = mock_chain_tvls.get(chain, {
                "tvl": 0,
                "change_1d": 0,
                "protocols_count": 0,
                "top_protocols": [],
            })
            return {
                "chain": chain,
                **chain_data,
                "tvl_formatted": f"${chain_data['tvl'] / 1e9:.2f}B",
                "note": "This is mock data.",
            }
        else:
            # Return all chains
            return {
                "total_tvl": sum(c["tvl"] for c in mock_chain_tvls.values()),
                "chains": [
                    {
                        "name": name,
                        **data,
                        "tvl_formatted": f"${data['tvl'] / 1e9:.2f}B",
                    }
                    for name, data in mock_chain_tvls.items()
                ],
                "note": "This is mock data.",
            }
    
    async def _get_yields(
        self,
        chain: Optional[str] = None,
        protocol: Optional[str] = None,
        min_tvl: float = 1000000,
        min_apy: float = 0,
        stablecoin_only: bool = False,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Get yield farming opportunities."""
        # TODO: Integrate with actual DeFiLlama Yields API
        
        # Mock yield pools
        mock_pools = [
            {
                "chain": "Ethereum",
                "project": "Aave",
                "symbol": "USDC",
                "tvl": 2800000000,
                "apy": 3.5,
                "apyBase": 2.8,
                "apyReward": 0.7,
                "stablecoin": True,
                "il_risk": "none",
                "pool_id": "aave-usdc-eth",
            },
            {
                "chain": "Ethereum",
                "project": "Curve",
                "symbol": "3pool",
                "tvl": 1200000000,
                "apy": 4.2,
                "apyBase": 3.5,
                "apyReward": 0.7,
                "stablecoin": True,
                "il_risk": "low",
                "pool_id": "curve-3pool",
            },
            {
                "chain": "Arbitrum",
                "project": "GMX",
                "symbol": "GLP",
                "tvl": 450000000,
                "apy": 28.5,
                "apyBase": 22.0,
                "apyReward": 6.5,
                "stablecoin": False,
                "il_risk": "medium",
                "pool_id": "gmx-glp-arb",
            },
            {
                "chain": "Polygon",
                "project": "Gains Network",
                "symbol": "DAI",
                "tvl": 95000000,
                "apy": 12.5,
                "apyBase": 12.5,
                "apyReward": 0,
                "stablecoin": True,
                "il_risk": "none",
                "pool_id": "gains-dai-poly",
            },
        ]
        
        # Apply filters
        filtered_pools = [
            p for p in mock_pools
            if (not chain or p["chain"] == chain)
            and (not protocol or p["project"].lower() == protocol.lower())
            and p["tvl"] >= min_tvl
            and p["apy"] >= min_apy
            and (not stablecoin_only or p["stablecoin"])
        ]
        
        # Sort by APY descending
        filtered_pools.sort(key=lambda x: x["apy"], reverse=True)
        
        # Limit results
        filtered_pools = filtered_pools[:limit]
        
        return {
            "pools_count": len(filtered_pools),
            "filters": {
                "chain": chain,
                "protocol": protocol,
                "min_tvl": min_tvl,
                "min_apy": min_apy,
                "stablecoin_only": stablecoin_only,
            },
            "pools": filtered_pools,
            "note": "This is mock data. Real implementation will call DeFiLlama Yields API.",
        }
    
    async def _get_protocol_fees(
        self,
        protocol: str,
    ) -> Dict[str, Any]:
        """Get protocol fees and revenue."""
        # TODO: Integrate with actual DeFiLlama Fees API
        
        # Mock fee data
        mock_fees = {
            "uniswap": {
                "daily_fees": 3500000,  # $3.5M
                "daily_revenue": 0,  # Goes to LPs
                "daily_volume": 1200000000,  # $1.2B
                "fees_7d": 25000000,
                "fees_30d": 105000000,
                "protocol_revenue": 0,
            },
            "gmx": {
                "daily_fees": 850000,
                "daily_revenue": 850000 * 0.3,  # 30% to GMX stakers
                "daily_volume": 280000000,
                "fees_7d": 6000000,
                "fees_30d": 26000000,
                "protocol_revenue": 26000000 * 0.3,
            },
        }
        
        fee_data = mock_fees.get(
            protocol.lower(),
            {
                "daily_fees": 0,
                "daily_revenue": 0,
                "daily_volume": 0,
                "fees_7d": 0,
                "fees_30d": 0,
                "protocol_revenue": 0,
            },
        )
        
        return {
            "protocol": protocol,
            **fee_data,
            "daily_fees_formatted": f"${fee_data['daily_fees'] / 1e6:.2f}M",
            "monthly_fees_formatted": f"${fee_data['fees_30d'] / 1e6:.2f}M",
            "timestamp": datetime.utcnow().isoformat(),
            "note": "This is mock data. Real implementation will call DeFiLlama Fees API.",
        }
    
    async def _get_stablecoin_data(
        self,
        stablecoin: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get stablecoin market data."""
        # TODO: Integrate with actual DeFiLlama Stablecoins API
        
        # Mock stablecoin data
        mock_stablecoins = {
            "USDT": {
                "name": "Tether",
                "circulating": 91000000000,  # $91B
                "chains": {
                    "Ethereum": 48000000000,
                    "Tron": 42000000000,
                    "BSC": 900000000,
                },
                "change_1d": -0.2,
                "change_7d": 1.5,
                "peg_deviation": 0.0002,  # 0.02%
            },
            "USDC": {
                "name": "USD Coin",
                "circulating": 28000000000,  # $28B
                "chains": {
                    "Ethereum": 21000000000,
                    "Polygon": 2100000000,
                    "Arbitrum": 1900000000,
                    "Optimism": 1500000000,
                    "Base": 1500000000,
                },
                "change_1d": 0.5,
                "change_7d": 2.8,
                "peg_deviation": 0.0001,
            },
            "DAI": {
                "name": "Dai",
                "circulating": 5300000000,  # $5.3B
                "chains": {
                    "Ethereum": 4900000000,
                    "Polygon": 200000000,
                    "Arbitrum": 150000000,
                    "Optimism": 50000000,
                },
                "change_1d": -0.1,
                "change_7d": 0.8,
                "peg_deviation": 0.0003,
            },
        }
        
        if stablecoin:
            stable_data = mock_stablecoins.get(stablecoin.upper(), {
                "name": stablecoin,
                "circulating": 0,
                "chains": {},
                "change_1d": 0,
                "change_7d": 0,
                "peg_deviation": 0,
            })
            return {
                "symbol": stablecoin.upper(),
                **stable_data,
                "circulating_formatted": f"${stable_data['circulating'] / 1e9:.2f}B",
                "note": "This is mock data.",
            }
        else:
            # Return all stablecoins
            return {
                "total_stablecoin_market_cap": sum(s["circulating"] for s in mock_stablecoins.values()),
                "stablecoins": [
                    {
                        "symbol": symbol,
                        **data,
                        "circulating_formatted": f"${data['circulating'] / 1e9:.2f}B",
                    }
                    for symbol, data in mock_stablecoins.items()
                ],
                "note": "This is mock data.",
            }
    
    async def _compare_protocols(
        self,
        protocols: List[str],
        metrics: List[str] = ["tvl", "fees"],
    ) -> Dict[str, Any]:
        """Compare multiple protocols."""
        # TODO: Integrate with actual DeFiLlama API
        
        # Mock comparison data
        comparisons = []
        for protocol in protocols:
            tvl_data = await self._get_protocol_tvl(protocol)
            
            comparison = {
                "protocol": protocol,
                "name": tvl_data.get("name", protocol.title()),
                "category": tvl_data.get("category", "Unknown"),
            }
            
            if "tvl" in metrics:
                comparison["tvl"] = tvl_data.get("tvl", 0)
                comparison["tvl_change_7d"] = tvl_data.get("change_7d", 0)
            
            if "fees" in metrics:
                fee_data = await self._get_protocol_fees(protocol)
                comparison["daily_fees"] = fee_data.get("daily_fees", 0)
                comparison["fees_30d"] = fee_data.get("fees_30d", 0)
            
            comparisons.append(comparison)
        
        # Sort by TVL (if included)
        if "tvl" in metrics:
            comparisons.sort(key=lambda x: x.get("tvl", 0), reverse=True)
        
        return {
            "protocols_count": len(comparisons),
            "metrics": metrics,
            "comparisons": comparisons,
            "note": "This is mock data.",
        }
    
    async def _get_trending_protocols(
        self,
        timeframe: str = "7d",
        metric: str = "tvl",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get trending protocols by growth."""
        # TODO: Integrate with actual DeFiLlama API
        
        # Mock trending data
        mock_trending = [
            {"protocol": "gains-network", "name": "Gains Network", "growth": 45.2, "tvl": 95000000, "category": "Derivatives"},
            {"protocol": "radiant", "name": "Radiant Capital", "growth": 38.5, "tvl": 320000000, "category": "Lending"},
            {"protocol": "gmx", "name": "GMX", "growth": 28.3, "tvl": 450000000, "category": "Derivatives"},
            {"protocol": "stargate", "name": "Stargate Finance", "growth": 22.1, "tvl": 580000000, "category": "Bridge"},
            {"protocol": "pendle", "name": "Pendle", "growth": 19.8, "tvl": 180000000, "category": "Yield"},
        ]
        
        return {
            "timeframe": timeframe,
            "metric": metric,
            "limit": limit,
            "trending": mock_trending[:limit],
            "note": "This is mock data. Real implementation will call DeFiLlama API.",
        }
    
    async def _get_protocol_info(
        self,
        protocol: str,
    ) -> Dict[str, Any]:
        """Get detailed protocol information."""
        # TODO: Integrate with actual DeFiLlama API
        
        # Mock protocol info
        mock_info = {
            "aave": {
                "name": "Aave",
                "slug": "aave",
                "description": "Aave is a decentralized lending protocol where users can lend and borrow crypto assets.",
                "category": "Lending",
                "logo": "https://icons.llama.fi/aave.png",
                "url": "https://aave.com",
                "twitter": "https://twitter.com/aaveaave",
                "github": "https://github.com/aave",
                "audit_links": ["https://docs.aave.com/developers/security-and-audits"],
                "governance_token": "AAVE",
                "chains": ["Ethereum", "Polygon", "Arbitrum", "Optimism", "Avalanche"],
                "launched_at": "2020-01-08",
            },
        }
        
        info = mock_info.get(protocol.lower(), {
            "name": protocol.title(),
            "slug": protocol,
            "description": "Protocol information not available",
            "category": "Unknown",
        })
        
        return {
            **info,
            "note": "This is mock data. Real implementation will call DeFiLlama API.",
        }


# Standalone FastAPI app
if __name__ == "__main__":
    import uvicorn
    
    server = DeFiLlamaMCPServer()
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          DeFiLlama MCP Server Starting...                ║
╚══════════════════════════════════════════════════════════╝

Server: {server.name} v{server.version}
Tools: {len(server.tools)} registered
Port: 8083

Tools Available:
""")
    for tool_name, tool in server.tools.items():
        print(f"  • {tool_name}: {tool.description[:60]}...")
    
    print("""
Data Sources:
  • DeFiLlama API (public, no key required)
  • Yields API (yield farming data)
  • Fees API (protocol revenue)
  • Stablecoins API (market cap data)

Endpoints:
  GET  /           - Server info
  GET  /tools      - List all tools
  POST /tools/{name} - Call a tool
  GET  /health     - Health check

Starting server...
    """)
    
    uvicorn.run(
        server.app,
        host="0.0.0.0",
        port=8083,
        log_level="info",
    )
