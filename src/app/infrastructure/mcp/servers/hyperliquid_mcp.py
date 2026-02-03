"""Hyperliquid MCP Server - Perpetual Futures Trading.

Exposes Hyperliquid perpetual DEX functionality as MCP tools for AI agents.
Provides market data, order books, funding rates, liquidations, and risk analysis.

Tools:
    - get_markets: Get all perpetual markets with stats
    - get_order_book: Get orderbook depth for a market
    - get_funding_rate: Get current funding rate
    - get_funding_rates: Get all funding rates
    - get_liquidations: Get recent liquidations
    - get_positions: Get user's open positions
    - calculate_liquidation_price: Calculate liquidation price
    - calculate_risk_metrics: Calculate position risk metrics
    - find_funding_arbitrage: Find funding rate arbitrage opportunities

Integration Points:
    - Hyperliquid L1 blockchain
    - Hyperliquid API for market data
    - Position risk calculators

Feature Flag: mcp.servers.hyperliquid_enabled
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.infrastructure.mcp.base import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError
from app.domain.ports.perpetual_gateway import PerpetualGateway


class HyperliquidMCPServer(MCPServer):
    """
    MCP server for Hyperliquid perpetual futures trading.

    Provides AI agents with tools to:
    - Discover perpetual markets
    - Analyze funding rates
    - Track liquidations
    - Monitor positions
    - Calculate risk metrics

    Example usage by agent:
        # Get funding rates for arbitrage
        funding = await call_tool("hyperliquid_get_funding_rates", {})

        # Calculate liquidation price
        liq_price = await call_tool("hyperliquid_calculate_liquidation_price", {
            "entry_price": "2000",
            "leverage": "10",
            "side": "long"
        })

        # Get order book depth
        book = await call_tool("hyperliquid_get_order_book", {
            "symbol": "ETH",
            "depth": 10
        })
    """

    def __init__(
        self,
        perpetual_gateway: Optional[PerpetualGateway] = None,
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize Hyperliquid MCP server.

        Args:
            perpetual_gateway: Perpetual futures gateway for data access
            settings: MCP configuration settings

        Raises:
            MCPServerDisabledError: If Hyperliquid server is disabled
        """
        self.settings = settings or MCPSettings()

        # Check if server is enabled
        if not self.settings.enabled or not getattr(
            self.settings.servers, "hyperliquid_enabled", False
        ):
            raise MCPServerDisabledError(
                "Hyperliquid MCP server is disabled. "
                "Enable with mcp.servers.hyperliquid_enabled=true in config."
            )

        super().__init__(
            name="hyperliquid",
            version="1.0.0",
            description="Hyperliquid perpetual futures DEX",
        )

        self.perpetual_gateway = perpetual_gateway

        # Register tools
        self.setup_tools()

    def setup_tools(self):
        """Register Hyperliquid perpetual trading tools."""

        # Tool 1: Get Markets
        self.register_tool(
            name="hyperliquid_get_markets",
            description=(
                "Get all perpetual markets on Hyperliquid. "
                "Returns market stats including price, volume, open interest."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "min_volume": {
                        "type": "number",
                        "description": "Minimum 24h volume in USD",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["volume", "open_interest", "funding_rate"],
                        "default": "volume",
                        "description": "Sort criterion",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Maximum results",
                    },
                },
                "required": [],
            },
            handler=self._get_markets_handler,
        )

        # Tool 2: Get Order Book
        self.register_tool(
            name="hyperliquid_get_order_book",
            description=(
                "Get order book depth for a perpetual market. "
                "Shows bids and asks with prices and sizes."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol (e.g., 'ETH', 'BTC')",
                    },
                    "depth": {
                        "type": "integer",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Number of levels per side",
                    },
                },
                "required": ["symbol"],
            },
            handler=self._get_order_book_handler,
        )

        # Tool 3: Get Funding Rate
        self.register_tool(
            name="hyperliquid_get_funding_rate",
            description=(
                "Get current funding rate for a symbol. "
                "Positive rate = longs pay shorts. Negative = shorts pay longs."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol",
                    },
                },
                "required": ["symbol"],
            },
            handler=self._get_funding_rate_handler,
        )

        # Tool 4: Get All Funding Rates
        self.register_tool(
            name="hyperliquid_get_funding_rates",
            description=(
                "Get all funding rates across markets. "
                "Useful for finding funding arbitrage opportunities."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "sort_by_abs": {
                        "type": "boolean",
                        "default": False,
                        "description": "Sort by absolute value (highest magnitude first)",
                    },
                },
                "required": [],
            },
            handler=self._get_funding_rates_handler,
        )

        # Tool 5: Get Liquidations
        self.register_tool(
            name="hyperliquid_get_liquidations",
            description=(
                "Get recent liquidations to analyze market leverage and risks. "
                "Shows which positions got liquidated and at what prices."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Filter by symbol (optional)",
                    },
                    "hours": {
                        "type": "integer",
                        "default": 24,
                        "minimum": 1,
                        "maximum": 168,
                        "description": "Lookback period in hours",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200,
                        "description": "Maximum results",
                    },
                },
                "required": [],
            },
            handler=self._get_liquidations_handler,
        )

        # Tool 6: Get Positions
        self.register_tool(
            name="hyperliquid_get_positions",
            description=(
                "Get user's open positions on Hyperliquid. "
                "Shows size, leverage, PnL, and liquidation prices."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Wallet address (0x...)",
                    },
                },
                "required": ["address"],
            },
            handler=self._get_positions_handler,
        )

        # Tool 7: Calculate Liquidation Price
        self.register_tool(
            name="hyperliquid_calculate_liquidation_price",
            description=(
                "Calculate liquidation price for a potential position. "
                "Helps assess risk before opening a trade."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "entry_price": {
                        "type": "string",
                        "description": "Entry price (e.g., '2000')",
                    },
                    "leverage": {
                        "type": "string",
                        "description": "Leverage multiplier (e.g., '10' for 10x)",
                    },
                    "side": {
                        "type": "string",
                        "enum": ["long", "short"],
                        "description": "Position side",
                    },
                    "maintenance_margin": {
                        "type": "string",
                        "default": "0.005",
                        "description": "Maintenance margin rate (default 0.5%)",
                    },
                },
                "required": ["entry_price", "leverage", "side"],
            },
            handler=self._calculate_liquidation_price_handler,
        )

        # Tool 8: Calculate Risk Metrics
        self.register_tool(
            name="hyperliquid_calculate_risk_metrics",
            description=(
                "Calculate comprehensive risk metrics for a position. "
                "Returns liquidation price, required margin, max loss, etc."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "entry_price": {
                        "type": "string",
                        "description": "Entry price",
                    },
                    "size": {
                        "type": "string",
                        "description": "Position size in base asset (e.g., '1' ETH)",
                    },
                    "leverage": {
                        "type": "string",
                        "description": "Leverage multiplier",
                    },
                    "side": {
                        "type": "string",
                        "enum": ["long", "short"],
                        "description": "Position side",
                    },
                    "account_balance": {
                        "type": "string",
                        "description": "Optional account balance in USD",
                    },
                },
                "required": ["entry_price", "size", "leverage", "side"],
            },
            handler=self._calculate_risk_metrics_handler,
        )

        # Tool 9: Find Funding Arbitrage
        self.register_tool(
            name="hyperliquid_find_funding_arbitrage",
            description=(
                "Find funding rate arbitrage opportunities. "
                "Shows markets with extreme funding rates suitable for neutral strategies."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "min_rate": {
                        "type": "number",
                        "default": 0.01,
                        "description": "Minimum absolute funding rate (e.g., 0.01 = 1%)",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum results",
                    },
                },
                "required": [],
            },
            handler=self._find_funding_arbitrage_handler,
        )

    # =========================================================================
    # Tool Handlers
    # =========================================================================

    async def _get_markets_handler(
        self,
        min_volume: Optional[float] = None,
        sort_by: str = "volume",
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Handler for get_markets tool."""
        if not self.perpetual_gateway:
            return {"error": "Perpetual gateway not configured", "markets": []}

        try:
            markets = await self.perpetual_gateway.get_markets()

            # Filter by minimum volume
            if min_volume:
                markets = [m for m in markets if float(m.volume_24h_usd) >= min_volume]

            # Sort markets
            if sort_by == "volume":
                markets.sort(key=lambda m: m.volume_24h_usd, reverse=True)
            elif sort_by == "open_interest":
                markets.sort(key=lambda m: m.open_interest_usd, reverse=True)
            elif sort_by == "funding_rate":
                markets.sort(key=lambda m: abs(m.funding_rate), reverse=True)

            # Limit results
            markets = markets[:limit]

            market_data = []
            for m in markets:
                market_data.append({
                    "symbol": m.symbol,
                    "mark_price": f"${float(m.mark_price):,.2f}",
                    "index_price": f"${float(m.index_price):,.2f}",
                    "funding_rate": f"{float(m.funding_rate) * 100:.4f}%",
                    "volume_24h": f"${float(m.volume_24h_usd):,.2f}",
                    "open_interest": f"${float(m.open_interest_usd):,.2f}",
                    "max_leverage": f"{m.max_leverage}x",
                })

            return {
                "markets": market_data,
                "count": len(market_data),
            }

        except Exception as e:
            return {"error": str(e), "markets": []}

    async def _get_order_book_handler(
        self,
        symbol: str,
        depth: int = 20,
    ) -> Dict[str, Any]:
        """Handler for get_order_book tool."""
        if not self.perpetual_gateway:
            return {"error": "Perpetual gateway not configured"}

        try:
            order_book = await self.perpetual_gateway.get_order_book(
                symbol=symbol,
                depth=depth,
            )

            return {
                "symbol": order_book.symbol,
                "timestamp": str(order_book.timestamp),
                "bids": [
                    {"price": str(price), "size": str(size)}
                    for price, size in order_book.bids[:depth]
                ],
                "asks": [
                    {"price": str(price), "size": str(size)}
                    for price, size in order_book.asks[:depth]
                ],
                "spread": str(order_book.spread),
                "spread_pct": f"{float(order_book.spread_pct) * 100:.4f}%",
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_funding_rate_handler(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """Handler for get_funding_rate tool."""
        if not self.perpetual_gateway:
            return {"error": "Perpetual gateway not configured"}

        try:
            funding = await self.perpetual_gateway.get_funding_rate(symbol=symbol)

            direction = (
                "Longs pay shorts" if funding.current_rate > 0 else "Shorts pay longs"
            )

            return {
                "symbol": funding.symbol,
                "current_rate": f"{float(funding.current_rate) * 100:.4f}%",
                "predicted_rate": f"{float(funding.predicted_rate) * 100:.4f}%",
                "funding_interval_hours": funding.funding_interval_hours,
                "next_funding": str(funding.next_funding_time),
                "direction": direction,
                "annualized_rate": f"{float(funding.current_rate) * 365 * 3 * 100:.2f}%",
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_funding_rates_handler(
        self,
        sort_by_abs: bool = False,
    ) -> Dict[str, Any]:
        """Handler for get_funding_rates tool."""
        if not self.perpetual_gateway:
            return {"error": "Perpetual gateway not configured", "funding_rates": []}

        try:
            funding_rates = await self.perpetual_gateway.get_funding_rates()

            # Sort by absolute value or regular
            if sort_by_abs:
                funding_rates.sort(key=lambda f: abs(f.current_rate), reverse=True)
            else:
                funding_rates.sort(key=lambda f: f.current_rate, reverse=True)

            rate_data = []
            for f in funding_rates:
                direction = (
                    "Longs pay shorts" if f.current_rate > 0 else "Shorts pay longs"
                )
                annualized = float(f.current_rate) * 365 * 3 * 100  # 3 times per day

                rate_data.append({
                    "symbol": f.symbol,
                    "current_rate": f"{float(f.current_rate) * 100:.4f}%",
                    "annualized": f"{annualized:.2f}%",
                    "direction": direction,
                })

            return {
                "funding_rates": rate_data,
                "count": len(rate_data),
            }

        except Exception as e:
            return {"error": str(e), "funding_rates": []}

    async def _get_liquidations_handler(
        self,
        symbol: Optional[str] = None,
        hours: int = 24,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Handler for get_liquidations tool."""
        if not self.perpetual_gateway:
            return {"error": "Perpetual gateway not configured", "liquidations": []}

        try:
            liquidations = await self.perpetual_gateway.get_liquidations(
                symbol=symbol,
                hours=hours,
            )

            # Limit results
            liquidations = liquidations[:limit]

            liq_data = []
            total_value = Decimal("0")

            for liq in liquidations:
                liq_data.append({
                    "symbol": liq.symbol,
                    "side": liq.side,
                    "size": str(liq.size),
                    "price": f"${float(liq.price):,.2f}",
                    "value": f"${float(liq.value_usd):,.2f}",
                    "timestamp": str(liq.timestamp),
                })
                total_value += liq.value_usd

            return {
                "liquidations": liq_data,
                "count": len(liq_data),
                "total_value": f"${float(total_value):,.2f}",
                "timeframe_hours": hours,
            }

        except Exception as e:
            return {"error": str(e), "liquidations": []}

    async def _get_positions_handler(
        self,
        address: str,
    ) -> Dict[str, Any]:
        """Handler for get_positions tool."""
        if not self.perpetual_gateway:
            return {"error": "Perpetual gateway not configured", "positions": []}

        try:
            positions = await self.perpetual_gateway.get_positions(address=address)

            position_data = []
            total_pnl = Decimal("0")
            total_notional = Decimal("0")

            for p in positions:
                position_data.append({
                    "symbol": p.symbol,
                    "side": p.side,
                    "size": str(p.size),
                    "entry_price": f"${float(p.entry_price):,.2f}",
                    "mark_price": f"${float(p.mark_price):,.2f}",
                    "leverage": f"{float(p.leverage):.1f}x",
                    "unrealized_pnl": f"${float(p.unrealized_pnl):,.2f}",
                    "liquidation_price": f"${float(p.liquidation_price):,.2f}",
                    "margin": f"${float(p.margin):,.2f}",
                    "notional": f"${float(p.notional_value):,.2f}",
                })
                total_pnl += p.unrealized_pnl
                total_notional += p.notional_value

            return {
                "positions": position_data,
                "count": len(position_data),
                "total_pnl": f"${float(total_pnl):,.2f}",
                "total_notional": f"${float(total_notional):,.2f}",
            }

        except Exception as e:
            return {"error": str(e), "positions": []}

    async def _calculate_liquidation_price_handler(
        self,
        entry_price: str,
        leverage: str,
        side: str,
        maintenance_margin: str = "0.005",
    ) -> Dict[str, Any]:
        """Handler for calculate_liquidation_price tool."""
        if not self.perpetual_gateway:
            return {"error": "Perpetual gateway not configured"}

        try:
            liq_price = self.perpetual_gateway.calculate_liquidation_price(
                entry_price=Decimal(entry_price),
                leverage=Decimal(leverage),
                side=side,
                maintenance_margin=Decimal(maintenance_margin),
            )

            # Calculate distance from entry
            entry = Decimal(entry_price)
            distance_pct = abs((liq_price - entry) / entry) * 100

            return {
                "liquidation_price": f"${float(liq_price):,.2f}",
                "entry_price": f"${float(entry):,.2f}",
                "distance": f"{float(distance_pct):.2f}%",
                "side": side,
                "leverage": f"{leverage}x",
                "maintenance_margin": f"{float(Decimal(maintenance_margin)) * 100:.2f}%",
            }

        except Exception as e:
            return {"error": str(e)}

    async def _calculate_risk_metrics_handler(
        self,
        entry_price: str,
        size: str,
        leverage: str,
        side: str,
        account_balance: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handler for calculate_risk_metrics tool."""
        if not self.perpetual_gateway:
            return {"error": "Perpetual gateway not configured"}

        try:
            balance = Decimal(account_balance) if account_balance else None

            metrics = self.perpetual_gateway.calculate_risk_metrics(
                entry_price=Decimal(entry_price),
                size=Decimal(size),
                leverage=Decimal(leverage),
                side=side,
                account_balance=balance,
            )

            return {
                "position_notional": f"${float(metrics.position_notional):,.2f}",
                "required_margin": f"${float(metrics.required_margin):,.2f}",
                "liquidation_price": f"${float(metrics.liquidation_price):,.2f}",
                "max_loss": f"${float(metrics.max_loss):,.2f}",
                "distance_to_liquidation": f"{float(metrics.distance_to_liquidation_pct):.2f}%",
                "leverage": f"{float(leverage)}x",
                "side": side,
            }

        except Exception as e:
            return {"error": str(e)}

    async def _find_funding_arbitrage_handler(
        self,
        min_rate: float = 0.01,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Handler for find_funding_arbitrage tool."""
        if not self.perpetual_gateway:
            return {"error": "Perpetual gateway not configured", "opportunities": []}

        try:
            funding_rates = await self.perpetual_gateway.get_funding_rates()

            # Filter by minimum rate (absolute value)
            opportunities = [
                f for f in funding_rates if abs(float(f.current_rate)) >= min_rate
            ]

            # Sort by absolute rate
            opportunities.sort(key=lambda f: abs(f.current_rate), reverse=True)

            # Limit results
            opportunities = opportunities[:limit]

            opp_data = []
            for f in opportunities:
                strategy = (
                    "Short perp (collect funding)"
                    if f.current_rate > 0
                    else "Long perp (collect funding)"
                )
                annualized = float(f.current_rate) * 365 * 3 * 100

                opp_data.append({
                    "symbol": f.symbol,
                    "funding_rate": f"{float(f.current_rate) * 100:.4f}%",
                    "annualized": f"{annualized:.2f}%",
                    "strategy": strategy,
                    "next_payment": str(f.next_funding_time),
                })

            return {
                "opportunities": opp_data,
                "count": len(opp_data),
                "min_rate_filter": f"{min_rate * 100:.2f}%",
            }

        except Exception as e:
            return {"error": str(e), "opportunities": []}


# Main entry point for running server standalone
if __name__ == "__main__":
    import uvicorn

    print("""
╔══════════════════════════════════════════════════════════╗
║       Hyperliquid MCP Server Starting...                ║
╚══════════════════════════════════════════════════════════╝

Port: 8090

Tools Available:
  • get_markets: Get all perpetual markets with stats
  • get_order_book: Get orderbook depth for a market
  • get_funding_rate: Get current funding rate
  • get_funding_rates: Get all funding rates
  • get_liquidations: Get recent liquidations
  • get_positions: Get user's open positions
  • calculate_liquidation_price: Calculate liquidation price
  • calculate_risk_metrics: Calculate position risk metrics
  • find_funding_arbitrage: Find funding rate arbitrage opportunities

Endpoints:
  GET  /           - Server info
  GET  /tools      - List all tools
  POST /tools/{name} - Call a tool
  GET  /health     - Health check

Starting server...
    """)

    server = HyperliquidMCPServer()
    uvicorn.run(server.app, host="0.0.0.0", port=8090, log_level="info")
