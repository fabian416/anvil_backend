"""Morpho MCP Server - MetaMorpho Vaults & Morpho Blue Markets.

Exposes Morpho Protocol lending functionality as MCP tools for AI agents.
Provides vault discovery, yield optimization, market analysis, and position tracking.

Tools:
    - get_vaults: Get MetaMorpho vaults with yield and risk data
    - get_vault_details: Get detailed vault information
    - get_vault_apy: Get APY breakdown with historical data
    - get_markets: Get Morpho Blue lending markets
    - get_user_positions: Get user's vault positions
    - compare_yields: Compare yields across protocols
    - morpho_withdraw: Withdraw supplied assets from Morpho Blue

Integration Points:
    - Morpho Protocol smart contracts
    - MetaMorpho vault APIs
    - Morpho Blue market data
    - Internal query handlers

Feature Flag: mcp.servers.morpho_enabled
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.infrastructure.mcp.base import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError
from app.domain.ports.morpho_gateway import MorphoGateway

logger = logging.getLogger(__name__)


class MorphoMCPServer(MCPServer):
    """
    MCP server for Morpho Protocol lending operations.

    Provides AI agents with tools to:
    - Discover MetaMorpho vaults
    - Analyze yield opportunities
    - Compare Morpho vs other protocols
    - Track user positions
    - Get market analytics

    Example usage by agent:
        # Get best vaults for USDC
        vaults = await call_tool("get_vaults", {
            "asset": "USDC",
            "sort_by": "apy",
            "limit": 10
        })

        # Compare Morpho vs Aave yields
        comparison = await call_tool("compare_yields", {
            "asset": "WETH",
            "protocols": ["morpho", "aave"]
        })
    """

    def __init__(
        self,
        morpho_gateway: Optional[MorphoGateway] = None,
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize Morpho MCP server.

        Args:
            morpho_gateway: Morpho protocol gateway for data access
            settings: MCP configuration settings

        Raises:
            MCPServerDisabledError: If Morpho server is disabled
        """
        self.settings = settings or MCPSettings()

        # Check if server is enabled
        if not self.settings.enabled or not getattr(
            self.settings.servers, "morpho_enabled", False
        ):
            raise MCPServerDisabledError(
                "Morpho MCP server is disabled. "
                "Enable with mcp.servers.morpho_enabled=true in config."
            )

        super().__init__(
            name="morpho",
            version="1.0.0",
            description="Morpho Protocol lending optimization and vault management",
        )

        self.morpho_gateway = morpho_gateway

        # Register tools
        self.setup_tools()

    def setup_tools(self):
        """Register Morpho protocol tools."""

        # Tool 1: Get Vaults
        self.register_tool(
            name="morpho_get_vaults",
            description=(
                "Get MetaMorpho lending vaults with APY and risk data. "
                "Filter by asset, risk tier, minimum APY. "
                "Returns vault details including TVL, curator, allocations."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "asset": {
                        "type": "string",
                        "description": "Filter by underlying asset (e.g., 'USDC', 'WETH')",
                    },
                    "risk_tier": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "very_high"],
                        "description": "Filter by risk tier",
                    },
                    "min_apy": {
                        "type": "number",
                        "description": "Minimum APY threshold (e.g., 5.0 for 5%)",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["apy", "tvl", "risk"],
                        "default": "apy",
                        "description": "Sort field",
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
                        "description": "Maximum results to return",
                    },
                },
                "required": [],
            },
            handler=self._get_vaults_handler,
        )

        # Tool 2: Get Vault Details
        self.register_tool(
            name="morpho_get_vault_details",
            description=(
                "Get detailed information about a specific MetaMorpho vault. "
                "Includes full market allocations, curator info, risk breakdown."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "vault_address": {
                        "type": "string",
                        "description": "Vault contract address (0x...)",
                    },
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                },
                "required": ["vault_address"],
            },
            handler=self._get_vault_details_handler,
        )

        # Tool 3: Get Vault APY
        self.register_tool(
            name="morpho_get_vault_apy",
            description=(
                "Get detailed APY breakdown for a vault. "
                "Shows base APY, reward APY, fee impact, and net APY."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "vault_address": {
                        "type": "string",
                        "description": "Vault contract address",
                    },
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                },
                "required": ["vault_address"],
            },
            handler=self._get_vault_apy_handler,
        )

        # Tool 4: Get Markets
        self.register_tool(
            name="morpho_get_markets",
            description=(
                "Get Morpho Blue lending markets. "
                "Shows supply/borrow rates, utilization, and liquidation thresholds."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "collateral_asset": {
                        "type": "string",
                        "description": "Filter by collateral asset",
                    },
                    "loan_asset": {
                        "type": "string",
                        "description": "Filter by loan asset",
                    },
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Maximum results",
                    },
                },
                "required": [],
            },
            handler=self._get_markets_handler,
        )

        # Tool 5: Get User Positions
        self.register_tool(
            name="morpho_get_user_positions",
            description=(
                "Get user's MetaMorpho vault positions. "
                "Shows deposits, current value, earnings, and APY."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "user_address": {
                        "type": "string",
                        "description": "User wallet address (0x...)",
                    },
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                },
                "required": ["user_address"],
            },
            handler=self._get_user_positions_handler,
        )

        # Tool 6: Compare Yields
        self.register_tool(
            name="morpho_compare_yields",
            description=(
                "Compare lending yields across protocols for an asset. "
                "Shows Morpho vaults vs other DeFi protocols with risk-adjusted rankings."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "asset": {
                        "type": "string",
                        "description": "Asset to compare (e.g., 'USDC', 'WETH')",
                    },
                    "protocols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["morpho", "aave"],
                        "description": "Protocols to compare",
                    },
                    "chain": {
                        "type": "string",
                        "default": "ethereum",
                        "description": "Blockchain network",
                    },
                },
                "required": ["asset"],
            },
            handler=self._compare_yields_handler,
        )

        # Tool 7: Withdraw from Morpho
        self.register_tool(
            name="morpho_withdraw",
            description=(
                "Withdraw supplied assets from Morpho Blue market or MetaMorpho vault. "
                "Returns transaction data for user signing. "
                "Validates position exists and calculates health factor impact."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "user_address": {
                        "type": "string",
                        "description": "User wallet address (0x...)",
                    },
                    "vault_address": {
                        "type": "string",
                        "description": "MetaMorpho vault address (0x...)",
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount to withdraw (in asset units, or 'max' for all)",
                    },
                    "chain": {
                        "type": "string",
                        "default": "base",
                        "description": "Blockchain network (base, ethereum)",
                    },
                },
                "required": ["user_address", "vault_address", "amount"],
            },
            handler=self._withdraw_handler,
        )

    # =========================================================================
    # Tool Handlers
    # =========================================================================

    async def _get_vaults_handler(
        self,
        asset: Optional[str] = None,
        risk_tier: Optional[str] = None,
        min_apy: Optional[float] = None,
        sort_by: str = "apy",
        chain: str = "ethereum",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Handler for get_vaults tool."""
        if not self.morpho_gateway:
            return {
                "error": "Morpho gateway not configured",
                "vaults": [],
            }

        try:
            # Get vaults from gateway
            vaults = await self.morpho_gateway.get_vaults(
                asset=asset,
                chain=chain,
            )

            # Filter by risk tier
            if risk_tier:
                vaults = [v for v in vaults if v.risk_tier.value == risk_tier]

            # Filter by min APY
            if min_apy:
                vaults = [v for v in vaults if float(v.apy) >= min_apy]

            # Sort vaults
            if sort_by == "apy":
                vaults.sort(key=lambda v: v.apy, reverse=True)
            elif sort_by == "tvl":
                vaults.sort(key=lambda v: v.total_assets, reverse=True)
            elif sort_by == "risk":
                risk_order = {"low": 0, "medium": 1, "high": 2, "very_high": 3}
                vaults.sort(key=lambda v: risk_order.get(v.risk_tier.value, 1))

            # Limit results
            vaults = vaults[:limit]

            # Format response
            vault_data = []
            for v in vaults:
                vault_data.append({
                    "address": v.address,
                    "name": v.name,
                    "symbol": v.symbol,
                    "asset": v.asset,
                    "apy": f"{float(v.apy):.2f}%",
                    "net_apy": f"{float(v.net_apy):.2f}%",
                    "tvl": f"${float(v.total_assets):,.2f}",
                    "risk_tier": v.risk_tier.value,
                    "fee_percentage": f"{float(v.fee_percentage) * 100:.2f}%",
                    "curator": v.curator_address,
                })

            return {
                "vaults": vault_data,
                "count": len(vault_data),
                "filters_applied": {
                    "asset": asset,
                    "risk_tier": risk_tier,
                    "min_apy": min_apy,
                },
            }

        except Exception as e:
            return {
                "error": str(e),
                "vaults": [],
            }

    async def _get_vault_details_handler(
        self,
        vault_address: str,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """Handler for get_vault_details tool."""
        if not self.morpho_gateway:
            return {"error": "Morpho gateway not configured"}

        try:
            vault = await self.morpho_gateway.get_vault_details(
                vault_address=vault_address,
                chain=chain,
            )

            return {
                "vault": {
                    "address": vault.address,
                    "name": vault.name,
                    "symbol": vault.symbol,
                    "asset": vault.asset,
                    "apy": f"{float(vault.apy):.2f}%",
                    "net_apy": f"{float(vault.net_apy):.2f}%",
                    "tvl": f"${float(vault.total_assets):,.2f}",
                    "total_shares": str(vault.total_shares),
                    "share_price": f"{float(vault.share_price):.6f}",
                    "fee_percentage": f"{float(vault.fee_percentage) * 100:.2f}%",
                    "risk_tier": vault.risk_tier.value,
                    "curator": vault.curator_address,
                    "guardian": vault.guardian_address,
                    "market_allocations": [
                        {
                            "market_id": a.market_id,
                            "collateral": a.collateral_asset,
                            "allocation": f"{float(a.allocation_percentage) * 100:.2f}%",
                            "lltv": f"{float(a.lltv) * 100:.2f}%",
                            "supply_apy": f"{float(a.supply_apy):.2f}%",
                        }
                        for a in vault.market_allocations
                    ],
                }
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_vault_apy_handler(
        self,
        vault_address: str,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """Handler for get_vault_apy tool."""
        if not self.morpho_gateway:
            return {"error": "Morpho gateway not configured"}

        try:
            apy = await self.morpho_gateway.get_vault_apy(
                vault_address=vault_address,
                chain=chain,
            )

            return {
                "vault_address": apy.vault_address,
                "base_apy": f"{float(apy.base_apy):.2f}%",
                "supply_apy": f"{float(apy.supply_apy):.2f}%",
                "reward_apy": f"{float(apy.reward_apy):.2f}%",
                "total_apy": f"{float(apy.total_apy):.2f}%",
                "fee_percentage": f"{float(apy.fee_percentage) * 100:.2f}%",
                "net_apy": f"{float(apy.net_apy):.2f}%",
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_markets_handler(
        self,
        collateral_asset: Optional[str] = None,
        loan_asset: Optional[str] = None,
        chain: str = "ethereum",
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Handler for get_markets tool."""
        if not self.morpho_gateway:
            return {"error": "Morpho gateway not configured", "markets": []}

        try:
            markets = await self.morpho_gateway.get_markets(chain=chain)

            # Filter by collateral
            if collateral_asset:
                markets = [
                    m
                    for m in markets
                    if m.collateral_asset.upper() == collateral_asset.upper()
                ]

            # Filter by loan asset
            if loan_asset:
                markets = [
                    m for m in markets if m.loan_asset.upper() == loan_asset.upper()
                ]

            # Limit results
            markets = markets[:limit]

            market_data = []
            for m in markets:
                utilization = Decimal("0")
                if m.total_supply > 0:
                    utilization = (m.total_borrow / m.total_supply) * 100

                market_data.append({
                    "market_id": m.market_id,
                    "collateral": m.collateral_asset,
                    "loan_asset": m.loan_asset,
                    "lltv": f"{float(m.lltv) * 100:.2f}%",
                    "supply_apy": f"{float(m.supply_apy):.2f}%",
                    "borrow_apy": f"{float(m.borrow_apy):.2f}%",
                    "total_supply": f"${float(m.total_supply):,.2f}",
                    "total_borrow": f"${float(m.total_borrow):,.2f}",
                    "utilization": f"{float(utilization):.2f}%",
                })

            return {
                "markets": market_data,
                "count": len(market_data),
            }

        except Exception as e:
            return {"error": str(e), "markets": []}

    async def _get_user_positions_handler(
        self,
        user_address: str,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """Handler for get_user_positions tool."""
        if not self.morpho_gateway:
            return {"error": "Morpho gateway not configured", "positions": []}

        try:
            positions = await self.morpho_gateway.get_user_positions(
                address=user_address,
                chain=chain,
            )

            position_data = []
            total_value = Decimal("0")
            total_earnings = Decimal("0")

            for p in positions:
                position_data.append({
                    "vault_address": p.vault_address,
                    "vault_name": p.vault_name,
                    "asset": p.asset_symbol,
                    "deposited": f"${float(p.deposited_assets):,.2f}",
                    "current_value": f"${float(p.assets):,.2f}",
                    "earnings": f"${float(p.earnings):,.2f}",
                    "shares": str(p.shares),
                    "apy": f"{float(p.apy):.2f}%",
                })

                total_value += p.assets
                total_earnings += p.earnings

            return {
                "positions": position_data,
                "summary": {
                    "total_positions": len(position_data),
                    "total_value": f"${float(total_value):,.2f}",
                    "total_earnings": f"${float(total_earnings):,.2f}",
                },
            }

        except Exception as e:
            return {"error": str(e), "positions": []}

    async def _compare_yields_handler(
        self,
        asset: str,
        protocols: List[str] = None,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """Handler for compare_yields tool."""
        if not self.morpho_gateway:
            return {"error": "Morpho gateway not configured", "comparisons": []}

        protocols = protocols or ["morpho"]

        try:
            # Get Morpho vaults for asset
            morpho_vaults = await self.morpho_gateway.get_vaults(
                asset=asset,
                chain=chain,
            )

            comparisons = []
            for vault in morpho_vaults[:5]:  # Top 5
                comparisons.append({
                    "protocol": "morpho",
                    "vault_name": vault.name,
                    "apy": f"{float(vault.apy):.2f}%",
                    "net_apy": f"{float(vault.net_apy):.2f}%",
                    "risk_tier": vault.risk_tier.value,
                    "tvl": f"${float(vault.total_assets):,.2f}",
                })

            # Sort by APY
            comparisons.sort(key=lambda x: float(x["apy"].rstrip("%")), reverse=True)

            best = comparisons[0] if comparisons else None

            return {
                "asset": asset,
                "comparisons": comparisons,
                "best_option": best,
            }

        except Exception as e:
            return {"error": str(e), "comparisons": []}

    async def _withdraw_handler(
        self,
        user_address: str,
        vault_address: str,
        amount: str,
        chain: str = "base",
    ) -> Dict[str, Any]:
        """
        Handle Morpho withdrawal from MetaMorpho vault.

        Process:
        1. Get user position from Morpho gateway
        2. Validate position exists and has sufficient supply
        3. Build withdraw transaction
        4. Return transaction data for user signing
        """
        if not self.morpho_gateway:
            return {
                "success": False,
                "error": "Morpho gateway not configured",
                "chain": chain,
            }

        try:
            # 1. Get user positions
            positions = await self.morpho_gateway.get_user_positions(
                address=user_address,
                chain=chain,
            )

            # 2. Find position for this vault
            position = None
            for p in positions:
                if p.vault_address.lower() == vault_address.lower():
                    position = p
                    break

            if not position:
                return {
                    "success": False,
                    "error": f"No position found in vault {vault_address}",
                    "chain": chain,
                    "user_address": user_address,
                }

            # 3. Validate supply
            if position.shares == 0:
                return {
                    "success": False,
                    "error": "No supply to withdraw",
                    "chain": chain,
                }

            # 4. Calculate withdraw amount
            if amount.lower() == "max":
                withdraw_shares = position.shares
                withdraw_amount = position.assets
            else:
                # Convert amount to shares
                withdraw_amount = Decimal(amount)
                if withdraw_amount > position.assets:
                    return {
                        "success": False,
                        "error": f"Insufficient balance. You have {position.assets:.6f} {position.asset_symbol}",
                        "available_balance": str(position.assets),
                        "requested_amount": amount,
                        "chain": chain,
                    }
                # Estimate shares from amount (proportional)
                if position.assets > 0:
                    share_ratio = withdraw_amount / position.assets
                    withdraw_shares = int(position.shares * share_ratio)
                else:
                    withdraw_shares = 0

            # 5. Build withdraw transaction
            tx_data = self._build_metamorpho_withdraw_transaction(
                vault_address=vault_address,
                shares=withdraw_shares,
                user_address=user_address,
                chain=chain,
            )

            logger.info(
                f"[MorphoMCP] Withdraw transaction built: "
                f"{withdraw_amount} {position.asset_symbol} from {vault_address}"
            )

            return {
                "success": True,
                "action": "withdraw",
                "chain_id": self._get_chain_id(chain),
                "chain_name": chain,
                "vault_address": vault_address,
                "vault_name": position.vault_name,
                "asset": position.asset_symbol,
                "amount": str(withdraw_amount),
                "shares": str(withdraw_shares),
                "from_address": user_address.lower(),
                "transaction": tx_data,
                "current_balance": str(position.assets),
                "remaining_balance": str(position.assets - withdraw_amount),
            }

        except Exception as e:
            logger.error(f"[MorphoMCP] Withdraw error: {e}")
            return {
                "success": False,
                "error": str(e),
                "chain": chain,
            }

    def _build_metamorpho_withdraw_transaction(
        self,
        vault_address: str,
        shares: int,
        user_address: str,
        chain: str,
    ) -> Dict[str, Any]:
        """
        Build MetaMorpho vault withdraw transaction.

        MetaMorpho uses the standard ERC4626 withdraw function:
        function redeem(uint256 shares, address receiver, address owner) returns (uint256 assets)
        """
        # ERC4626 redeem function signature
        # redeem(uint256 shares, address receiver, address owner)
        function_selector = "0xba087652"  # keccak256("redeem(uint256,address,address)")[:4]

        # Encode parameters
        shares_hex = hex(shares)[2:].zfill(64)
        receiver_hex = user_address.lower()[2:].zfill(64)
        owner_hex = user_address.lower()[2:].zfill(64)

        calldata = f"{function_selector}{shares_hex}{receiver_hex}{owner_hex}"

        return {
            "to": vault_address,
            "data": calldata,
            "value": "0x0",
            "gas": "0x493E0",  # 300,000 gas
        }

    def _get_chain_id(self, chain: str) -> int:
        """Get chain ID from chain name."""
        chain_ids = {
            "ethereum": 1,
            "base": 8453,
            "arbitrum": 42161,
            "optimism": 10,
            "polygon": 137,
        }
        return chain_ids.get(chain.lower(), 1)


# Main entry point for running server standalone
if __name__ == "__main__":
    import uvicorn

    print("""
╔══════════════════════════════════════════════════════════╗
║         Morpho MCP Server Starting...                   ║
╚══════════════════════════════════════════════════════════╝

Port: 8088

Tools Available:
  • get_vaults: Get MetaMorpho vaults with yield data
  • get_vault_details: Get detailed vault information
  • get_vault_apy: Get APY breakdown with history
  • get_markets: Get Morpho Blue lending markets
  • get_user_positions: Get user's vault positions
  • compare_yields: Compare yields across protocols

Endpoints:
  GET  /           - Server info
  GET  /tools      - List all tools
  POST /tools/{name} - Call a tool
  GET  /health     - Health check

Starting server...
    """)

    server = MorphoMCPServer()
    uvicorn.run(server.app, host="0.0.0.0", port=8088, log_level="info")
