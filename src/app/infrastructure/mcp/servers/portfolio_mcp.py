"""Portfolio MCP server - exposes internal portfolio tools to agents.

Feature Flag: mcp.servers.portfolio_enabled
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.infrastructure.mcp.base import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError


class PortfolioMCPServer(MCPServer):
    """
    MCP server for portfolio operations.

    Exposes tools for:
    - Getting user balances
    - Getting user positions (lending, staking, LPs)
    - Portfolio analytics

    This is an INTERNAL MCP server (not public-facing).
    It wraps our domain/application logic for agent consumption.
    """

    def __init__(
        self,
        portfolio_service: Optional[Any] = None,
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize Portfolio MCP server.

        Args:
            portfolio_service: Service for portfolio operations (injected via DI)
            settings: MCP configuration settings

        Raises:
            MCPServerDisabledError: If Portfolio server is disabled
        """
        self.settings = settings or MCPSettings()

        # Check if server is enabled
        if not self.settings.enabled or not self.settings.servers.portfolio_enabled:
            raise MCPServerDisabledError(
                "Portfolio MCP server is disabled. "
                "Enable with mcp.servers.portfolio_enabled=true in config."
            )

        super().__init__(
            name="portfolio",
            version="1.0.0",
            description="Internal portfolio operations for DeFi agents",
        )

        # In production, this would be injected via Dishka
        self.portfolio_service = portfolio_service

        # Create retry decorator for this server
        self._retry = retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((
                httpx.HTTPError,
                httpx.TimeoutException,
                Exception,
            )),
            reraise=True,
        )

        # Register tools
        self.setup_tools()

    def setup_tools(self):
        """Register portfolio tools."""

        # Tool 1: Get user balance
        self.register_tool(
            name="get_user_balance",
            description="Get user's token balances across all chains",
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier (UUID)",
                    },
                    "chain_id": {
                        "type": "integer",
                        "description": "Optional chain ID filter (1=Ethereum, 137=Polygon, etc.)",
                    },
                },
                "required": ["user_id"],
            },
            handler=self._get_user_balance,
        )

        # Tool 2: Get user positions
        self.register_tool(
            name="get_user_positions",
            description="Get user's open positions (lending, staking, liquidity pools)",
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier (UUID)",
                    },
                    "protocol": {
                        "type": "string",
                        "description": "Optional protocol filter (e.g., 'aave', 'compound', 'uniswap')",
                    },
                    "position_type": {
                        "type": "string",
                        "description": "Optional position type filter ('lending', 'staking', 'lp')",
                    },
                },
                "required": ["user_id"],
            },
            handler=self._get_user_positions,
        )

        # Tool 3: Get portfolio summary
        self.register_tool(
            name="get_portfolio_summary",
            description="Get high-level portfolio summary (total value, allocation, etc.)",
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier (UUID)",
                    },
                },
                "required": ["user_id"],
            },
            handler=self._get_portfolio_summary,
        )

    async def _get_user_balance(
        self,
        user_id: str,
        chain_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get user's token balances.

        Args:
            user_id: User identifier
            chain_id: Optional chain ID filter

        Returns:
            Dictionary with balance information
        """
        # TODO: Integrate with actual portfolio service
        # For now, return mock data

        return {
            "user_id": user_id,
            "chain_id": chain_id or "all",
            "balances": [
                {
                    "token": "ETH",
                    "symbol": "ETH",
                    "balance": "2.5",
                    "usd_value": 5250.00,
                    "chain_id": 1,
                },
                {
                    "token": "USDC",
                    "symbol": "USDC",
                    "balance": "10000.0",
                    "usd_value": 10000.00,
                    "chain_id": 1,
                },
                {
                    "token": "WETH",
                    "symbol": "WETH",
                    "balance": "1.2",
                    "usd_value": 2520.00,
                    "chain_id": 137,
                },
            ],
            "total_usd": 17770.00,
        }

    async def _get_user_positions(
        self,
        user_id: str,
        protocol: Optional[str] = None,
        position_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get user's open positions.

        Args:
            user_id: User identifier
            protocol: Optional protocol filter
            position_type: Optional position type filter

        Returns:
            Dictionary with position information
        """
        # TODO: Integrate with actual portfolio service
        # For now, return mock data

        return {
            "user_id": user_id,
            "positions": [
                {
                    "protocol": "aave",
                    "type": "lending",
                    "token": "USDC",
                    "amount": "5000.0",
                    "usd_value": 5000.00,
                    "apy": 3.2,
                    "chain_id": 1,
                },
                {
                    "protocol": "compound",
                    "type": "lending",
                    "token": "DAI",
                    "amount": "2000.0",
                    "usd_value": 2000.00,
                    "apy": 2.8,
                    "chain_id": 1,
                },
                {
                    "protocol": "uniswap",
                    "type": "lp",
                    "token": "ETH/USDC",
                    "amount": "1.0 ETH + 2100 USDC",
                    "usd_value": 4200.00,
                    "apy": 15.5,
                    "chain_id": 1,
                },
            ],
            "total_value_usd": 11200.00,
        }

    async def _get_portfolio_summary(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get portfolio summary.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with portfolio summary
        """
        # TODO: Integrate with actual portfolio service
        # For now, return mock data

        return {
            "user_id": user_id,
            "total_value_usd": 28970.00,
            "allocation": {
                "cash": {
                    "usd_value": 17770.00,
                    "percentage": 61.3,
                },
                "defi_positions": {
                    "usd_value": 11200.00,
                    "percentage": 38.7,
                },
            },
            "breakdown": {
                "lending": {
                    "usd_value": 7000.00,
                    "percentage": 24.2,
                },
                "liquidity_pools": {
                    "usd_value": 4200.00,
                    "percentage": 14.5,
                },
                "staking": {
                    "usd_value": 0.00,
                    "percentage": 0.0,
                },
            },
            "risk_score": 6.5,  # Out of 10 (higher = riskier)
            "chains": ["Ethereum", "Polygon"],
        }


# Main entry point for running server standalone
if __name__ == "__main__":
    import uvicorn

    print("""
╔══════════════════════════════════════════════════════════╗
║         Portfolio MCP Server Starting...                ║
╚══════════════════════════════════════════════════════════╝

Port: 8086

Endpoints:
  GET  /           - Server info
  GET  /tools      - List all tools
  POST /tools/{name} - Call a tool
  GET  /health     - Health check

Starting server...
    """)

    server = PortfolioMCPServer()
    uvicorn.run(server.app, host="0.0.0.0", port=8086, log_level="info")
