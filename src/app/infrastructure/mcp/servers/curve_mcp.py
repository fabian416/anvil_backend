"""Curve Finance MCP Server - DEX Liquidity Pools & Stable Swaps.

Exposes Curve Finance DEX functionality as MCP tools for AI agents.
Provides pool discovery, APY analysis, swap quotes, gauge rewards, and TVL data.

Tools:
    - get_pools: Get liquidity pools with APY and TVL data
    - get_pool_details: Get detailed pool information
    - get_pool_apy: Get APY breakdown for a pool
    - get_swap_quote: Get quote for token swaps
    - get_gauges: Get gauge reward data
    - get_tvl: Get total value locked data
    - find_best_pools: Find pools by token with highest APY

Integration Points:
    - Curve Finance smart contracts
    - Curve pool registry
    - Curve gauge controller
    - Swap routing engine

Feature Flag: mcp.servers.curve_enabled
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.infrastructure.mcp.base import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError
from app.domain.ports.curve_gateway import CurveGateway


class CurveMCPServer(MCPServer):
    """
    MCP server for Curve Finance DEX operations.

    Provides AI agents with tools to:
    - Discover liquidity pools
    - Analyze pool APYs
    - Get swap quotes
    - Track gauge rewards
    - Monitor TVL metrics

    Example usage by agent:
        # Find best pools for USDC
        pools = await call_tool("curve_find_best_pools", {
            "token": "USDC",
            "sort_by": "apy",
            "limit": 5
        })

        # Get swap quote
        quote = await call_tool("curve_get_swap_quote", {
            "from_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            "to_token": "0x6B175474E89094C44Da98b954EedeAC495271d0F",   # DAI
            "amount": "1000000000"  # 1000 USDC (6 decimals)
        })
    """

    def __init__(
        self,
        curve_gateway: Optional[CurveGateway] = None,
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize Curve MCP server.

        Args:
            curve_gateway: Curve Finance gateway for data access
            settings: MCP configuration settings

        Raises:
            MCPServerDisabledError: If Curve server is disabled
        """
        self.settings = settings or MCPSettings()

        # Check if server is enabled
        if not self.settings.enabled or not getattr(self.settings.servers, 'curve_enabled', False):
            raise MCPServerDisabledError(
                "Curve MCP server is disabled. "
                "Enable with mcp.servers.curve_enabled=true in config."
            )

        super().__init__(
            name="curve",
            version="1.0.0",
            description="Curve Finance DEX for stable swaps and liquidity provision",
        )

        self.curve_gateway = curve_gateway

    def setup_tools(self):
        """Register Curve Finance tools."""

        # Tool 1: Get Pools
        self.register_tool(
            name="curve_get_pools",
            description=(
                "Get all Curve liquidity pools on a chain. "
                "Returns pool details including APY, TVL, and composition."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "enum": ["ethereum", "arbitrum", "optimism", "polygon", "avalanche"],
                        "description": "Blockchain network",
                    },
                    "min_tvl": {
                        "type": "number",
                        "description": "Minimum TVL in USD (e.g., 1000000 for $1M)",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Maximum results to return",
                    },
                },
                "required": [],
            },
            handler=self._get_pools_handler,
        )

        # Tool 2: Get Pool Details
        self.register_tool(
            name="curve_get_pool_details",
            description=(
                "Get detailed information about a specific Curve pool. "
                "Includes token composition, fees, and performance metrics."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "pool_address": {
                        "type": "string",
                        "description": "Pool contract address (0x...)",
                    },
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                },
                "required": ["pool_address"],
            },
            handler=self._get_pool_details_handler,
        )

        # Tool 3: Get Pool APY
        self.register_tool(
            name="curve_get_pool_apy",
            description=(
                "Get detailed APY breakdown for a Curve pool. "
                "Shows base APY, CRV rewards, and total APY."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "pool_address": {
                        "type": "string",
                        "description": "Pool contract address",
                    },
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                },
                "required": ["pool_address"],
            },
            handler=self._get_pool_apy_handler,
        )

        # Tool 4: Get Swap Quote
        self.register_tool(
            name="curve_get_swap_quote",
            description=(
                "Get a quote for swapping tokens through Curve pools. "
                "Returns expected output amount and price impact."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "from_token": {
                        "type": "string",
                        "description": "Source token address (0x...)",
                    },
                    "to_token": {
                        "type": "string",
                        "description": "Destination token address (0x...)",
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount to swap in smallest unit (wei)",
                    },
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                },
                "required": ["from_token", "to_token", "amount"],
            },
            handler=self._get_swap_quote_handler,
        )

        # Tool 5: Get Gauges
        self.register_tool(
            name="curve_get_gauges",
            description=(
                "Get Curve gauge data for liquidity mining rewards. "
                "Shows CRV emission rates and reward multipliers."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                    "active_only": {
                        "type": "boolean",
                        "default": True,
                        "description": "Show only active gauges with rewards",
                    },
                },
                "required": [],
            },
            handler=self._get_gauges_handler,
        )

        # Tool 6: Get TVL
        self.register_tool(
            name="curve_get_tvl",
            description=(
                "Get total value locked in Curve Finance. "
                "Shows TVL breakdown by chain and pool type."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                },
                "required": [],
            },
            handler=self._get_tvl_handler,
        )

        # Tool 7: Find Best Pools
        self.register_tool(
            name="curve_find_best_pools",
            description=(
                "Find best Curve pools containing a specific token. "
                "Sorted by APY, TVL, or volume."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Token symbol or address (e.g., 'USDC', '0x...')",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["apy", "tvl", "volume"],
                        "default": "apy",
                        "description": "Sort criterion",
                    },
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Maximum results",
                    },
                },
                "required": ["token"],
            },
            handler=self._find_best_pools_handler,
        )

    # =========================================================================
    # Tool Handlers
    # =========================================================================

    async def _get_pools_handler(
        self,
        chain: str = "ethereum",
        min_tvl: Optional[float] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Handler for get_pools tool."""
        if not self.curve_gateway:
            return {"error": "Curve gateway not configured", "pools": []}

        try:
            pools = await self.curve_gateway.get_pools(chain=chain)

            # Filter by minimum TVL
            if min_tvl:
                pools = [p for p in pools if float(p.total_liquidity_usd) >= min_tvl]

            # Sort by TVL
            pools.sort(key=lambda p: p.total_liquidity_usd, reverse=True)

            # Limit results
            pools = pools[:limit]

            pool_data = []
            for p in pools:
                pool_data.append({
                    "address": p.address,
                    "name": p.name,
                    "coins": [c.symbol for c in p.coins],
                    "tvl": f"${float(p.total_liquidity_usd):,.2f}",
                    "volume_24h": f"${float(p.volume_24h_usd):,.2f}",
                    "fees_24h": f"${float(p.fees_24h_usd):,.2f}",
                    "pool_type": p.pool_type,
                })

            return {
                "pools": pool_data,
                "count": len(pool_data),
                "chain": chain,
            }

        except Exception as e:
            return {"error": str(e), "pools": []}

    async def _get_pool_details_handler(
        self,
        pool_address: str,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """Handler for get_pool_details tool."""
        if not self.curve_gateway:
            return {"error": "Curve gateway not configured"}

        try:
            pool = await self.curve_gateway.get_pool_by_address(
                pool_address=pool_address,
                chain=chain,
            )

            return {
                "pool": {
                    "address": pool.address,
                    "name": pool.name,
                    "pool_type": pool.pool_type,
                    "coins": [
                        {
                            "symbol": c.symbol,
                            "address": c.address,
                            "decimals": c.decimals,
                            "reserve": str(c.reserve),
                        }
                        for c in pool.coins
                    ],
                    "tvl": f"${float(pool.total_liquidity_usd):,.2f}",
                    "volume_24h": f"${float(pool.volume_24h_usd):,.2f}",
                    "fees_24h": f"${float(pool.fees_24h_usd):,.2f}",
                    "fee_percentage": f"{float(pool.fee) * 100:.4f}%",
                    "admin_fee": f"{float(pool.admin_fee) * 100:.2f}%",
                    "A_parameter": pool.amplification_coefficient,
                }
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_pool_apy_handler(
        self,
        pool_address: str,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """Handler for get_pool_apy tool."""
        if not self.curve_gateway:
            return {"error": "Curve gateway not configured"}

        try:
            apy = await self.curve_gateway.get_pool_apy(
                pool_address=pool_address,
                chain=chain,
            )

            return {
                "pool_address": apy.pool_address,
                "base_apy": f"{float(apy.base_apy):.2f}%",
                "crv_apy": f"{float(apy.crv_apy):.2f}%",
                "rewards_apy": f"{float(apy.rewards_apy):.2f}%",
                "total_apy": f"{float(apy.total_apy):.2f}%",
                "breakdown": {
                    "trading_fees": f"{float(apy.base_apy):.2f}%",
                    "crv_rewards": f"{float(apy.crv_apy):.2f}%",
                    "other_rewards": f"{float(apy.rewards_apy):.2f}%",
                },
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_swap_quote_handler(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """Handler for get_swap_quote tool."""
        if not self.curve_gateway:
            return {"error": "Curve gateway not configured"}

        try:
            quote = await self.curve_gateway.get_swap_quote(
                from_token=from_token,
                to_token=to_token,
                amount=amount,
                chain=chain,
            )

            return {
                "from_token": quote.from_token,
                "to_token": quote.to_token,
                "amount_in": str(quote.amount_in),
                "amount_out": str(quote.amount_out),
                "price_impact": f"{float(quote.price_impact) * 100:.4f}%",
                "exchange_rate": str(quote.exchange_rate),
                "route": quote.route,
                "gas_estimate": quote.gas_estimate,
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_gauges_handler(
        self,
        chain: str = "ethereum",
        active_only: bool = True,
    ) -> Dict[str, Any]:
        """Handler for get_gauges tool."""
        if not self.curve_gateway:
            return {"error": "Curve gateway not configured", "gauges": []}

        try:
            gauges = await self.curve_gateway.get_gauges(chain=chain)

            # Filter active gauges
            if active_only:
                gauges = [g for g in gauges if float(g.emission_rate) > 0]

            gauge_data = []
            for g in gauges:
                gauge_data.append({
                    "address": g.address,
                    "pool_address": g.pool_address,
                    "pool_name": g.pool_name,
                    "emission_rate": f"{float(g.emission_rate):.2f} CRV/day",
                    "weight": f"{float(g.weight) * 100:.2f}%",
                    "working_supply": str(g.working_supply),
                })

            return {
                "gauges": gauge_data,
                "count": len(gauge_data),
                "chain": chain,
            }

        except Exception as e:
            return {"error": str(e), "gauges": []}

    async def _get_tvl_handler(
        self,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """Handler for get_tvl tool."""
        if not self.curve_gateway:
            return {"error": "Curve gateway not configured"}

        try:
            tvl = await self.curve_gateway.get_tvl(chain=chain)

            return {
                "total_tvl": f"${float(tvl.total_tvl_usd):,.2f}",
                "chain": chain,
                "by_pool_type": {
                    "stable_pools": f"${float(tvl.stable_pools_tvl):,.2f}",
                    "crypto_pools": f"${float(tvl.crypto_pools_tvl):,.2f}",
                    "lending_pools": f"${float(tvl.lending_pools_tvl):,.2f}",
                },
                "timestamp": str(tvl.timestamp),
            }

        except Exception as e:
            return {"error": str(e)}

    async def _find_best_pools_handler(
        self,
        token: str,
        sort_by: str = "apy",
        chain: str = "ethereum",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Handler for find_best_pools tool."""
        if not self.curve_gateway:
            return {"error": "Curve gateway not configured", "pools": []}

        try:
            # Get all pools
            all_pools = await self.curve_gateway.get_pools(chain=chain)

            # Filter pools containing the token
            token_upper = token.upper()
            matching_pools = []

            for pool in all_pools:
                # Check if token is in pool by symbol or address
                has_token = any(
                    token_upper in c.symbol.upper() or token.lower() == c.address.lower()
                    for c in pool.coins
                )
                if has_token:
                    matching_pools.append(pool)

            # Get APY for matching pools
            pools_with_apy = []
            for pool in matching_pools:
                try:
                    apy = await self.curve_gateway.get_pool_apy(
                        pool_address=pool.address,
                        chain=chain,
                    )
                    pools_with_apy.append((pool, apy))
                except:
                    continue

            # Sort pools
            if sort_by == "apy":
                pools_with_apy.sort(key=lambda x: x[1].total_apy, reverse=True)
            elif sort_by == "tvl":
                pools_with_apy.sort(key=lambda x: x[0].total_liquidity_usd, reverse=True)
            elif sort_by == "volume":
                pools_with_apy.sort(key=lambda x: x[0].volume_24h_usd, reverse=True)

            # Limit results
            pools_with_apy = pools_with_apy[:limit]

            # Format response
            pool_data = []
            for pool, apy in pools_with_apy:
                pool_data.append({
                    "address": pool.address,
                    "name": pool.name,
                    "coins": [c.symbol for c in pool.coins],
                    "apy": f"{float(apy.total_apy):.2f}%",
                    "tvl": f"${float(pool.total_liquidity_usd):,.2f}",
                    "volume_24h": f"${float(pool.volume_24h_usd):,.2f}",
                    "pool_type": pool.pool_type,
                })

            return {
                "token": token,
                "pools": pool_data,
                "count": len(pool_data),
                "sorted_by": sort_by,
            }

        except Exception as e:
            return {"error": str(e), "pools": []}
