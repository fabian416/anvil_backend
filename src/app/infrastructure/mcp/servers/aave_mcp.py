"""Aave MCP Server - Lending Protocol Tools.

Exposes Aave V3 lending protocol functionality as MCP tools for AI agents.
Provides market data, supply/borrow operations, position management, and analytics.

Tools:
    - get_market_data: Get lending/borrowing rates and liquidity for assets
    - get_user_positions: Get user's supply and borrow positions
    - calculate_health_factor: Calculate account health and liquidation risk
    - get_available_to_borrow: Calculate max borrowing capacity
    - supply_asset: Supply assets to earn yield (with safety checks)
    - borrow_asset: Borrow assets against collateral
    - repay_loan: Repay borrowed assets
    - withdraw_supply: Withdraw supplied assets
    - get_liquidation_risk: Analyze liquidation risk for position

Integration Points:
    - Aave V3 protocol contracts
    - Aave subgraph for historical data
    - Internal wallet service for transactions
    - Price oracles for accurate valuations

Feature Flag: mcp.servers.aave_enabled
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.infrastructure.mcp.base import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError
from app.infrastructure.adapters.external.aave_contract_helper import (
    generate_supply_transaction,
    generate_borrow_transaction,
    generate_repay_transaction,
    generate_withdraw_transaction,
)


class AaveMCPServer(MCPServer):
    """
    MCP server for Aave lending protocol operations.

    Provides AI agents with tools to:
    - Check lending/borrowing rates
    - Manage supply positions
    - Execute borrow operations
    - Monitor health factors
    - Analyze liquidation risks

    Example usage by agent:
        # Get market data
        markets = await call_tool("get_market_data", {
            "chain_id": 1,
            "assets": ["USDC", "ETH", "WBTC"]
        })

        # Check user positions
        positions = await call_tool("get_user_positions", {
            "chain_id": 1,
            "user_address": "0x..."
        })
    """

    def __init__(
        self,
        aave_gateway: Optional[Any] = None,
        wallet_service: Optional[Any] = None,
        subgraph_url: Optional[str] = None,
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize Aave MCP server.

        Args:
            aave_gateway: AaveGateway implementation for blockchain queries
            wallet_service: Internal wallet service for transaction execution
            subgraph_url: Aave subgraph URL for historical data queries
            settings: MCP configuration settings

        Raises:
            MCPServerDisabledError: If Aave server is disabled
        """
        self.settings = settings or MCPSettings()

        # Check if server is enabled
        if not self.settings.enabled or not self.settings.servers.aave_enabled:
            raise MCPServerDisabledError(
                "Aave MCP server is disabled. "
                "Enable with mcp.servers.aave_enabled=true in config."
            )

        super().__init__(
            name="aave",
            version="1.0.0",
            description="Aave V3 lending and borrowing protocol",
        )

        self.aave_gateway = aave_gateway
        self.wallet_service = wallet_service
        self.subgraph_url = (
            subgraph_url or "https://api.thegraph.com/subgraphs/name/aave/protocol-v3"
        )

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

        # Supported chains for Aave V3
        self.chains = {
            1: "ethereum",
            137: "polygon",
            42161: "arbitrum",
            10: "optimism",
            43114: "avalanche",
        }

        # Aave V3 Pool addresses per chain
        self.pool_addresses = {
            1: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",  # Ethereum
            137: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",  # Polygon
            42161: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",  # Arbitrum
            10: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",  # Optimism
            43114: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",  # Avalanche
        }

        self.setup_tools()

    def _chain_id_to_name(self, chain_id: int) -> str:
        """Convert chain ID to chain name."""
        return self.chains.get(chain_id, "ethereum")

    def _safe_decimal(self, value: Any, default: str = "0") -> str:
        """Safely convert Decimal to string, handling None."""
        if value is None:
            return default
        return str(value)

    def setup_tools(self):
        """Register all Aave tools."""

        # Tool 1: Get market data
        self.register_tool(
            name="get_market_data",
            description=(
                "Get current lending and borrowing rates, total liquidity, and utilization "
                "for specified assets on Aave. Returns APY for suppliers and borrowers."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID (1=Ethereum, 137=Polygon, 42161=Arbitrum)",
                        "enum": [1, 137, 42161, 10, 43114],
                    },
                    "assets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of asset symbols (e.g., ['USDC', 'ETH', 'DAI'])",
                    },
                },
                "required": ["chain_id"],
            },
            handler=self._get_market_data,
        )

        # Tool 2: Get user positions
        self.register_tool(
            name="get_user_positions",
            description=(
                "Get user's complete Aave position including supplied assets, borrowed assets, "
                "collateral status, health factor, and available borrowing power."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                        "enum": [1, 137, 42161, 10, 43114],
                    },
                    "user_address": {
                        "type": "string",
                        "description": "User's wallet address",
                    },
                },
                "required": ["chain_id", "user_address"],
            },
            handler=self._get_user_positions,
        )

        # Tool 3: Calculate health factor
        self.register_tool(
            name="calculate_health_factor",
            description=(
                "Calculate account health factor. Values < 1.0 mean position can be liquidated. "
                "Returns health factor, liquidation threshold, and safety margin."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                    },
                    "user_address": {
                        "type": "string",
                        "description": "User's wallet address",
                    },
                },
                "required": ["chain_id", "user_address"],
            },
            handler=self._calculate_health_factor,
        )

        # Tool 4: Get available to borrow
        self.register_tool(
            name="get_available_to_borrow",
            description=(
                "Calculate maximum amount user can borrow for a specific asset "
                "based on their collateral and current health factor."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                    },
                    "user_address": {
                        "type": "string",
                        "description": "User's wallet address",
                    },
                    "asset": {
                        "type": "string",
                        "description": "Asset symbol to borrow (e.g., 'USDC', 'ETH')",
                    },
                    "target_health_factor": {
                        "type": "number",
                        "description": "Target health factor after borrow (min 1.1 recommended)",
                        "default": 1.5,
                    },
                },
                "required": ["chain_id", "user_address", "asset"],
            },
            handler=self._get_available_to_borrow,
        )

        # Tool 5: Supply asset
        self.register_tool(
            name="supply_asset",
            description=(
                "Supply (deposit) assets to Aave to earn yield. Assets become collateral "
                "and user receives aTokens representing their position. "
                "IMPORTANT: Requires user approval and executes real transactions."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID (required for wallet access)",
                    },
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                    },
                    "asset": {
                        "type": "string",
                        "description": "Asset symbol to supply (e.g., 'USDC', 'ETH')",
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount to supply (in human-readable format, e.g., '100.5')",
                    },
                    "use_as_collateral": {
                        "type": "boolean",
                        "description": "Whether to use supplied asset as collateral",
                        "default": True,
                    },
                    "from_address": {
                        "type": "string",
                        "description": "User's wallet address",
                    },
                },
                "required": ["user_id", "chain_id", "asset", "amount", "from_address"],
            },
            handler=self._supply_asset,
        )

        # Tool 6: Borrow asset
        self.register_tool(
            name="borrow_asset",
            description=(
                "Borrow assets from Aave against supplied collateral. "
                "Can choose variable or stable rate. "
                "IMPORTANT: Check health factor before borrowing."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID (required for wallet access)",
                    },
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                    },
                    "asset": {
                        "type": "string",
                        "description": "Asset symbol to borrow (e.g., 'USDC', 'DAI')",
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount to borrow (in human-readable format)",
                    },
                    "rate_mode": {
                        "type": "string",
                        "description": "Interest rate mode: 'variable' or 'stable'",
                        "enum": ["variable", "stable"],
                        "default": "variable",
                    },
                    "from_address": {
                        "type": "string",
                        "description": "User's wallet address",
                    },
                },
                "required": ["user_id", "chain_id", "asset", "amount", "from_address"],
            },
            handler=self._borrow_asset,
        )

        # Tool 7: Repay loan
        self.register_tool(
            name="repay_loan",
            description=(
                "Repay borrowed assets to Aave. Can repay partial or full amount. "
                "Repaying improves health factor and frees up borrowing capacity."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID (required for wallet access)",
                    },
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                    },
                    "asset": {
                        "type": "string",
                        "description": "Asset symbol to repay",
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount to repay (use 'max' for full repayment)",
                    },
                    "rate_mode": {
                        "type": "string",
                        "description": "Rate mode of the debt to repay",
                        "enum": ["variable", "stable"],
                    },
                    "from_address": {
                        "type": "string",
                        "description": "User's wallet address",
                    },
                },
                "required": ["user_id", "chain_id", "asset", "amount", "from_address"],
            },
            handler=self._repay_loan,
        )

        # Tool 8: Withdraw supply
        self.register_tool(
            name="withdraw_supply",
            description=(
                "Withdraw supplied assets from Aave. Burns aTokens and returns underlying assets. "
                "Cannot withdraw if it would cause health factor to drop below 1.0."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID (required for wallet access)",
                    },
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                    },
                    "asset": {
                        "type": "string",
                        "description": "Asset symbol to withdraw",
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount to withdraw (use 'max' for full withdrawal)",
                    },
                    "from_address": {
                        "type": "string",
                        "description": "User's wallet address",
                    },
                },
                "required": ["user_id", "chain_id", "asset", "amount", "from_address"],
            },
            handler=self._withdraw_supply,
        )

        # Tool 9: Get liquidation risk
        self.register_tool(
            name="get_liquidation_risk",
            description=(
                "Analyze liquidation risk for user's position. Returns risk level, "
                "price drop percentage before liquidation, and recommended actions."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                    },
                    "user_address": {
                        "type": "string",
                        "description": "User's wallet address",
                    },
                },
                "required": ["chain_id", "user_address"],
            },
            handler=self._get_liquidation_risk,
        )

    # ==================== Tool Handlers ====================

    async def _get_market_data(
        self,
        chain_id: int,
        assets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get Aave market data for assets using real blockchain data."""
        if not self.aave_gateway:
            return {
                "success": False,
                "error": "Aave gateway not initialized",
                "chain_id": chain_id,
            }

        try:
            chain_name = self._chain_id_to_name(chain_id)

            # Get markets from AaveAdapter (uses caching)
            if assets:
                # Fetch specific assets
                markets_data = []
                for asset in assets:
                    try:
                        market = await self.aave_gateway.get_market_details(
                            asset=asset,
                            chain=chain_name,
                        )
                        markets_data.append(market)
                    except Exception as e:
                        # Log and continue if specific asset fails
                        continue
            else:
                # Get all markets
                markets_data = await self.aave_gateway.get_markets(chain=chain_name)

            # Convert domain entities to response format
            markets = []
            for market in markets_data:
                markets.append({
                    "asset": market.symbol,
                    "asset_address": market.asset_address,
                    "name": market.name,
                    "supply_apy": float(
                        market.supply_apy * 100
                    ),  # Convert to percentage
                    "borrow_apy_variable": float(market.borrow_apy_variable * 100),
                    "borrow_apy_stable": float(market.borrow_apy_stable * 100),
                    "total_supplied": self._safe_decimal(market.total_supplied),
                    "total_supplied_usd": self._safe_decimal(market.total_supplied_usd),
                    "total_borrowed": self._safe_decimal(market.total_borrowed),
                    "total_borrowed_usd": self._safe_decimal(market.total_borrowed_usd),
                    "utilization_rate": float(market.utilization_rate),
                    "available_liquidity": self._safe_decimal(
                        market.liquidity_available
                    ),
                    "ltv": float(market.ltv),
                    "liquidation_threshold": float(market.liquidation_threshold),
                    "liquidation_bonus": float(market.liquidation_bonus),
                    "can_be_collateral": market.can_use_as_collateral,
                    "can_be_borrowed": market.can_borrow,
                    "is_frozen": market.is_frozen,
                    "is_active": market.is_active,
                    "price_usd": self._safe_decimal(market.price_usd),
                    "decimals": market.decimals,
                })

            return {
                "success": True,
                "chain_id": chain_id,
                "chain_name": chain_name,
                "pool_address": self.pool_addresses.get(chain_id),
                "markets_count": len(markets),
                "markets": markets,
                "timestamp": markets_data[0].updated_at.isoformat()
                if markets_data
                else None,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chain_id": chain_id,
                "chain_name": self._chain_id_to_name(chain_id),
            }

    async def _get_user_positions(
        self,
        chain_id: int,
        user_address: str,
    ) -> Dict[str, Any]:
        """Get user's Aave positions using real blockchain data."""
        if not self.aave_gateway:
            return {
                "success": False,
                "error": "Aave gateway not initialized",
                "chain_id": chain_id,
                "user_address": user_address,
            }

        try:
            chain_name = self._chain_id_to_name(chain_id)

            # Get user position from AaveAdapter (uses caching)
            try:
                position = await self.aave_gateway.get_user_position(
                    address=user_address,
                    chain=chain_name,
                )
            except Exception as e:
                # User has no position
                return {
                    "success": True,
                    "user_address": user_address.lower(),
                    "chain_id": chain_id,
                    "chain_name": chain_name,
                    "has_position": False,
                    "supplied": [],
                    "borrowed": [],
                    "total_supplied_usd": "0",
                    "total_borrowed_usd": "0",
                    "total_collateral_usd": "0",
                    "available_borrow_usd": "0",
                    "health_factor": "inf",
                    "net_worth_usd": "0",
                }

            # Convert supplies
            supplied = []
            for supply in position.supplies:
                supplied.append({
                    "asset": supply.symbol,
                    "asset_address": supply.asset_address,
                    "amount": self._safe_decimal(supply.balance),
                    "amount_usd": self._safe_decimal(supply.balance_usd),
                    "apy": float(supply.apy * 100),  # Convert to percentage
                    "is_collateral": supply.is_collateral,
                })

            # Convert borrows
            borrowed = []
            for borrow in position.borrows:
                borrowed.append({
                    "asset": borrow.symbol,
                    "asset_address": borrow.asset_address,
                    "amount": self._safe_decimal(borrow.balance),
                    "amount_usd": self._safe_decimal(borrow.balance_usd),
                    "apy": float(borrow.apy * 100),  # Convert to percentage
                    "rate_mode": borrow.borrow_type,
                })

            return {
                "success": True,
                "user_address": position.user_address,
                "chain_id": chain_id,
                "chain_name": position.chain,
                "has_position": True,
                "supplied": supplied,
                "borrowed": borrowed,
                "total_supplied_usd": self._safe_decimal(position.total_collateral_usd),
                "total_borrowed_usd": self._safe_decimal(position.total_debt_usd),
                "total_collateral_usd": self._safe_decimal(
                    position.total_collateral_usd
                ),
                "available_borrow_usd": self._safe_decimal(
                    position.available_borrow_usd
                ),
                "health_factor": self._safe_decimal(position.health_factor, "inf"),
                "current_ltv": float(
                    position.current_ltv * 100
                ),  # Convert to percentage
                "max_ltv": float(position.max_ltv * 100),
                "net_worth_usd": self._safe_decimal(position.net_worth_usd),
                "timestamp": position.updated_at.isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chain_id": chain_id,
                "user_address": user_address,
                "chain_name": self._chain_id_to_name(chain_id),
            }

    async def _calculate_health_factor(
        self,
        chain_id: int,
        user_address: str,
    ) -> Dict[str, Any]:
        """Calculate health factor using real blockchain data."""
        if not self.aave_gateway:
            return {
                "success": False,
                "error": "Aave gateway not initialized",
                "chain_id": chain_id,
                "user_address": user_address,
            }

        try:
            chain_name = self._chain_id_to_name(chain_id)

            # Get health factor from AaveAdapter
            health_factor_obj = await self.aave_gateway.get_health_factor(
                address=user_address,
                chain=chain_name,
            )

            # Extract risk classification from HealthFactor value object
            risk_level = (
                health_factor_obj.risk_level.value
            )  # "low", "moderate", "high", "critical"

            # Map risk level to color
            risk_color_map = {
                "low": "green",
                "moderate": "yellow",
                "high": "orange",
                "critical": "red",
            }
            risk_color = risk_color_map.get(risk_level, "gray")

            # Calculate price drop buffer
            hf_value = float(health_factor_obj.value)
            if hf_value > 1.0 and hf_value != float("inf"):
                price_drop_before_liquidation = ((hf_value - 1.0) / hf_value) * 100
            elif hf_value == float("inf"):
                price_drop_before_liquidation = 100.0  # No debt, can't be liquidated
            else:
                price_drop_before_liquidation = 0.0  # Already liquidatable

            # Generate recommendation
            if hf_value >= 2.0:
                recommendation = "Healthy position. Consider borrowing more if needed."
            elif hf_value >= 1.5:
                recommendation = "Good position. Monitor market conditions."
            elif hf_value >= 1.2:
                recommendation = (
                    "Monitor closely. Consider repaying debt or adding collateral."
                )
            elif hf_value >= 1.0:
                recommendation = "⚠️ URGENT: Add collateral or repay debt immediately!"
            else:
                recommendation = "🚨 CRITICAL: Position can be liquidated NOW! Take action immediately!"

            return {
                "success": True,
                "chain_id": chain_id,
                "chain_name": chain_name,
                "user_address": user_address.lower(),
                "health_factor": self._safe_decimal(health_factor_obj.value, "inf"),
                "risk_level": risk_level,
                "risk_color": risk_color,
                "total_collateral_usd": self._safe_decimal(
                    health_factor_obj.collateral_usd
                ),
                "total_debt_usd": self._safe_decimal(health_factor_obj.debt_usd),
                "liquidation_threshold": float(health_factor_obj.liquidation_threshold),
                "distance_to_liquidation": self._safe_decimal(
                    health_factor_obj.distance_to_liquidation
                ),
                "price_drop_before_liquidation": f"{price_drop_before_liquidation:.2f}%",
                "is_liquidatable": hf_value < 1.0,
                "recommendation": recommendation,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chain_id": chain_id,
                "user_address": user_address,
                "chain_name": self._chain_id_to_name(chain_id),
            }

    async def _get_available_to_borrow(
        self,
        chain_id: int,
        user_address: str,
        asset: str,
        target_health_factor: float = 1.5,
    ) -> Dict[str, Any]:
        """Calculate available borrowing capacity using real blockchain data."""
        if not self.aave_gateway:
            return {
                "success": False,
                "error": "Aave gateway not initialized",
                "chain_id": chain_id,
                "user_address": user_address,
            }

        try:
            chain_name = self._chain_id_to_name(chain_id)

            # Get available borrow amount from AaveAdapter
            max_borrow_amount = await self.aave_gateway.get_available_to_borrow(
                address=user_address,
                asset=asset,
                chain=chain_name,
            )

            # Get market details for asset price
            market = await self.aave_gateway.get_market_details(
                asset=asset, chain=chain_name
            )

            # Get current position for context
            try:
                position = await self.aave_gateway.get_user_position(
                    address=user_address,
                    chain=chain_name,
                )
                current_debt_usd = position.total_debt_usd
                total_collateral_usd = position.total_collateral_usd
                current_hf = position.health_factor
            except:
                # No position
                current_debt_usd = Decimal("0")
                total_collateral_usd = Decimal("0")
                current_hf = Decimal("inf")

            # Calculate USD value of max borrow
            max_borrow_usd = max_borrow_amount * market.price_usd

            # Calculate what HF would be after borrowing max amount
            new_debt_usd = current_debt_usd + max_borrow_usd
            if new_debt_usd > 0:
                # HF = (collateral * liq_threshold) / debt
                estimated_hf = (
                    total_collateral_usd * market.liquidation_threshold
                ) / new_debt_usd
            else:
                estimated_hf = Decimal("inf")

            return {
                "success": True,
                "chain_id": chain_id,
                "chain_name": chain_name,
                "user_address": user_address.lower(),
                "asset": asset,
                "asset_address": market.asset_address,
                "max_borrow_amount": self._safe_decimal(max_borrow_amount),
                "max_borrow_usd": self._safe_decimal(max_borrow_usd),
                "asset_price_usd": self._safe_decimal(market.price_usd),
                "current_debt_usd": self._safe_decimal(current_debt_usd),
                "total_collateral_usd": self._safe_decimal(total_collateral_usd),
                "current_health_factor": self._safe_decimal(current_hf, "inf"),
                "estimated_health_factor_after": self._safe_decimal(
                    estimated_hf, "inf"
                ),
                "target_health_factor": target_health_factor,
                "available_liquidity": self._safe_decimal(market.liquidity_available),
                "warning": (
                    "Always maintain health factor above 1.5 for safety. "
                    "Market volatility can cause liquidation."
                ),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chain_id": chain_id,
                "user_address": user_address,
                "asset": asset,
                "chain_name": self._chain_id_to_name(chain_id),
            }

    async def _supply_asset(
        self,
        user_id: str,
        chain_id: int,
        asset: str,
        amount: str,
        from_address: str,
        use_as_collateral: bool = True,
    ) -> Dict[str, Any]:
        """Supply asset to Aave - generates real transaction calldata."""
        if not self.aave_gateway:
            return {
                "success": False,
                "error": "Aave gateway not initialized",
                "chain_id": chain_id,
            }

        try:
            chain_name = self._chain_id_to_name(chain_id)
            pool_address = self.pool_addresses.get(chain_id)

            if not pool_address:
                return {
                    "success": False,
                    "error": f"Aave V3 Pool not deployed on chain {chain_id}",
                    "chain_id": chain_id,
                }

            # Get market details for asset
            market = await self.aave_gateway.get_market_details(
                asset=asset, chain=chain_name
            )

            if not market.is_active or market.is_frozen:
                return {
                    "success": False,
                    "error": f"Asset {asset} is not available for supply (frozen or inactive)",
                    "chain_id": chain_id,
                }

            # Generate transaction data using helper
            tx_data = generate_supply_transaction(
                pool_address=pool_address,
                asset_address=market.asset_address,
                amount=amount,
                asset_decimals=market.decimals,
                user_address=from_address,
                use_as_collateral=use_as_collateral,
            )

            return {
                "success": True,
                "action": "supply",
                "chain_id": chain_id,
                "chain_name": chain_name,
                "asset": asset,
                "asset_address": market.asset_address,
                "amount": amount,
                "use_as_collateral": use_as_collateral,
                "from_address": from_address.lower(),
                "transaction": tx_data,
                "requires_approval": True,  # ERC-20 tokens need approval first
                "approval_spender": pool_address,
                "expected_apy": float(market.supply_apy * 100),
                "warning": (
                    "⚠️ Before signing this transaction, ensure you have:\n"
                    "1. Approved the Pool contract to spend your tokens\n"
                    "2. Sufficient balance of the asset\n"
                    "3. Sufficient gas (ETH/MATIC) for transaction fees"
                ),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chain_id": chain_id,
                "asset": asset,
            }

    async def _borrow_asset(
        self,
        user_id: str,
        chain_id: int,
        asset: str,
        amount: str,
        from_address: str,
        rate_mode: str = "variable",
    ) -> Dict[str, Any]:
        """Borrow asset from Aave - generates real transaction calldata with health factor validation."""
        if not self.aave_gateway:
            return {
                "success": False,
                "error": "Aave gateway not initialized",
                "chain_id": chain_id,
            }

        try:
            chain_name = self._chain_id_to_name(chain_id)
            pool_address = self.pool_addresses.get(chain_id)

            if not pool_address:
                return {
                    "success": False,
                    "error": f"Aave V3 Pool not deployed on chain {chain_id}",
                    "chain_id": chain_id,
                }

            # Get market details
            market = await self.aave_gateway.get_market_details(
                asset=asset, chain=chain_name
            )

            if not market.can_borrow:
                return {
                    "success": False,
                    "error": f"Asset {asset} cannot be borrowed",
                    "chain_id": chain_id,
                }

            # CRITICAL: Check health factor BEFORE allowing borrow
            try:
                current_hf_obj = await self.aave_gateway.get_health_factor(
                    address=from_address,
                    chain=chain_name,
                )

                # Calculate estimated health factor after borrow
                position = await self.aave_gateway.get_user_position(
                    address=from_address,
                    chain=chain_name,
                )

                # Estimate new debt
                borrow_amount_usd = Decimal(amount) * market.price_usd
                new_debt_usd = position.total_debt_usd + borrow_amount_usd

                # Calculate new health factor
                if new_debt_usd > 0:
                    # HF = (collateral * liq_threshold) / debt
                    estimated_hf = (
                        position.total_collateral_usd * market.liquidation_threshold
                    ) / new_debt_usd
                else:
                    estimated_hf = Decimal("inf")

                # Safety check: block borrows that would result in HF < 1.2
                if estimated_hf < Decimal("1.2"):
                    return {
                        "success": False,
                        "error": "UNSAFE BORROW BLOCKED",
                        "reason": f"This borrow would reduce your health factor to {estimated_hf:.2f}",
                        "current_health_factor": self._safe_decimal(
                            current_hf_obj.value, "inf"
                        ),
                        "estimated_health_factor_after": self._safe_decimal(
                            estimated_hf
                        ),
                        "minimum_required": "1.20",
                        "recommendation": (
                            "To borrow this amount safely:\n"
                            "1. Supply more collateral, OR\n"
                            "2. Borrow a smaller amount, OR\n"
                            "3. Repay existing debt"
                        ),
                        "chain_id": chain_id,
                    }

            except Exception as hf_error:
                # If no position exists, user can't borrow (no collateral)
                return {
                    "success": False,
                    "error": "Cannot borrow: No collateral supplied",
                    "details": str(hf_error),
                    "chain_id": chain_id,
                }

            # Generate transaction data using helper
            tx_data = generate_borrow_transaction(
                pool_address=pool_address,
                asset_address=market.asset_address,
                amount=amount,
                asset_decimals=market.decimals,
                user_address=from_address,
                rate_mode=rate_mode,
            )

            return {
                "success": True,
                "action": "borrow",
                "chain_id": chain_id,
                "chain_name": chain_name,
                "asset": asset,
                "asset_address": market.asset_address,
                "amount": amount,
                "rate_mode": rate_mode,
                "from_address": from_address.lower(),
                "transaction": tx_data,
                "current_health_factor": self._safe_decimal(
                    current_hf_obj.value, "inf"
                ),
                "estimated_health_factor_after": self._safe_decimal(estimated_hf),
                "expected_borrow_apy": float(market.borrow_apy_variable * 100)
                if rate_mode == "variable"
                else float(market.borrow_apy_stable * 100),
                "warning": (
                    "⚠️ BORROWING CREATES LIQUIDATION RISK\n"
                    f"• Your health factor will be: {estimated_hf:.2f}\n"
                    f"• Liquidation occurs if HF drops below 1.0\n"
                    "• Monitor your position regularly\n"
                    "• Consider repaying if HF drops below 1.5"
                ),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chain_id": chain_id,
                "asset": asset,
            }

    async def _repay_loan(
        self,
        user_id: str,
        chain_id: int,
        asset: str,
        amount: str,
        from_address: str,
        rate_mode: str = "variable",
    ) -> Dict[str, Any]:
        """Repay borrowed asset - generates real transaction calldata."""
        if not self.aave_gateway:
            return {
                "success": False,
                "error": "Aave gateway not initialized",
                "chain_id": chain_id,
            }

        try:
            chain_name = self._chain_id_to_name(chain_id)
            pool_address = self.pool_addresses.get(chain_id)

            if not pool_address:
                return {
                    "success": False,
                    "error": f"Aave V3 Pool not deployed on chain {chain_id}",
                    "chain_id": chain_id,
                }

            # Get market details
            market = await self.aave_gateway.get_market_details(
                asset=asset, chain=chain_name
            )

            # Get current position to calculate health factor improvement
            try:
                position = await self.aave_gateway.get_user_position(
                    address=from_address,
                    chain=chain_name,
                )
                current_hf = position.health_factor

                # Calculate estimated health factor after repayment
                if amount.lower() == "max":
                    # Full repayment - HF becomes infinite (no debt)
                    estimated_hf = Decimal("inf")
                else:
                    repay_amount_usd = Decimal(amount) * market.price_usd
                    new_debt_usd = max(
                        Decimal("0"), position.total_debt_usd - repay_amount_usd
                    )

                    if new_debt_usd > 0:
                        estimated_hf = (
                            position.total_collateral_usd * market.liquidation_threshold
                        ) / new_debt_usd
                    else:
                        estimated_hf = Decimal("inf")

            except Exception:
                # No position - can't repay
                return {
                    "success": False,
                    "error": "Cannot repay: No outstanding debt found",
                    "chain_id": chain_id,
                }

            # Generate transaction data using helper
            tx_data = generate_repay_transaction(
                pool_address=pool_address,
                asset_address=market.asset_address,
                amount=amount,
                asset_decimals=market.decimals,
                user_address=from_address,
                rate_mode=rate_mode,
            )

            return {
                "success": True,
                "action": "repay",
                "chain_id": chain_id,
                "chain_name": chain_name,
                "asset": asset,
                "asset_address": market.asset_address,
                "amount": amount,
                "rate_mode": rate_mode,
                "from_address": from_address.lower(),
                "transaction": tx_data,
                "requires_approval": True,  # Need to approve Pool to spend tokens
                "approval_spender": pool_address,
                "current_health_factor": self._safe_decimal(current_hf, "inf"),
                "estimated_health_factor_after": self._safe_decimal(
                    estimated_hf, "inf"
                ),
                "health_factor_improvement": "Improved"
                if estimated_hf > current_hf
                else "N/A",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chain_id": chain_id,
                "asset": asset,
            }

    async def _withdraw_supply(
        self,
        user_id: str,
        chain_id: int,
        asset: str,
        amount: str,
        from_address: str,
    ) -> Dict[str, Any]:
        """Withdraw supplied asset - generates real transaction calldata with safety checks."""
        if not self.aave_gateway:
            return {
                "success": False,
                "error": "Aave gateway not initialized",
                "chain_id": chain_id,
            }

        try:
            chain_name = self._chain_id_to_name(chain_id)
            pool_address = self.pool_addresses.get(chain_id)

            if not pool_address:
                return {
                    "success": False,
                    "error": f"Aave V3 Pool not deployed on chain {chain_id}",
                    "chain_id": chain_id,
                }

            # Get market details
            market = await self.aave_gateway.get_market_details(
                asset=asset, chain=chain_name
            )

            # Get current position to check if withdrawal is safe
            try:
                position = await self.aave_gateway.get_user_position(
                    address=from_address,
                    chain=chain_name,
                )
                current_hf = position.health_factor

                # Calculate estimated health factor after withdrawal
                if amount.lower() == "max":
                    # Full withdrawal - need to check if any debt exists
                    if position.total_debt_usd > 0:
                        return {
                            "success": False,
                            "error": "Cannot withdraw all collateral while debt exists",
                            "current_debt_usd": self._safe_decimal(
                                position.total_debt_usd
                            ),
                            "chain_id": chain_id,
                        }
                    estimated_hf = Decimal("inf")
                else:
                    # Partial withdrawal
                    withdraw_amount_usd = Decimal(amount) * market.price_usd
                    new_collateral_usd = max(
                        Decimal("0"),
                        position.total_collateral_usd - withdraw_amount_usd,
                    )

                    if position.total_debt_usd > 0:
                        # Calculate new health factor
                        estimated_hf = (
                            new_collateral_usd * market.liquidation_threshold
                        ) / position.total_debt_usd

                        # Safety check: block withdrawals that would result in HF < 1.5
                        if estimated_hf < Decimal("1.5"):
                            return {
                                "success": False,
                                "error": "UNSAFE WITHDRAWAL BLOCKED",
                                "reason": f"This withdrawal would reduce your health factor to {estimated_hf:.2f}",
                                "current_health_factor": self._safe_decimal(
                                    current_hf, "inf"
                                ),
                                "estimated_health_factor_after": self._safe_decimal(
                                    estimated_hf
                                ),
                                "minimum_required": "1.50",
                                "recommendation": "Repay some debt before withdrawing, or withdraw a smaller amount",
                                "chain_id": chain_id,
                            }
                    else:
                        # No debt - can withdraw freely
                        estimated_hf = Decimal("inf")

            except Exception:
                # No position - can't withdraw
                return {
                    "success": False,
                    "error": "Cannot withdraw: No supply position found",
                    "chain_id": chain_id,
                }

            # Generate transaction data using helper
            tx_data = generate_withdraw_transaction(
                pool_address=pool_address,
                asset_address=market.asset_address,
                amount=amount,
                asset_decimals=market.decimals,
                user_address=from_address,
            )

            return {
                "success": True,
                "action": "withdraw",
                "chain_id": chain_id,
                "chain_name": chain_name,
                "asset": asset,
                "asset_address": market.asset_address,
                "amount": amount,
                "from_address": from_address.lower(),
                "transaction": tx_data,
                "current_health_factor": self._safe_decimal(current_hf, "inf"),
                "estimated_health_factor_after": self._safe_decimal(
                    estimated_hf, "inf"
                ),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chain_id": chain_id,
                "asset": asset,
            }

    async def _get_liquidation_risk(
        self,
        chain_id: int,
        user_address: str,
    ) -> Dict[str, Any]:
        """Analyze liquidation risk using real position and market data."""
        if not self.aave_gateway:
            return {
                "success": False,
                "error": "Aave gateway not initialized",
                "chain_id": chain_id,
                "user_address": user_address,
            }

        try:
            chain_name = self._chain_id_to_name(chain_id)

            # Get user position
            try:
                position = await self.aave_gateway.get_user_position(
                    address=user_address,
                    chain=chain_name,
                )
            except Exception:
                # No position - no risk
                return {
                    "success": True,
                    "chain_id": chain_id,
                    "chain_name": chain_name,
                    "user_address": user_address.lower(),
                    "has_position": False,
                    "risk_level": "none",
                    "risk_description": "No active position - no liquidation risk",
                }

            # Get health factor
            health_factor_obj = await self.aave_gateway.get_health_factor(
                address=user_address,
                chain=chain_name,
            )

            hf_value = float(health_factor_obj.value)

            # Calculate price drop buffer
            if hf_value > 1.0 and hf_value != float("inf"):
                price_drop_to_liquidation = ((hf_value - 1.0) / hf_value) * 100
            elif hf_value == float("inf"):
                price_drop_to_liquidation = 100.0  # No debt
            else:
                price_drop_to_liquidation = 0.0  # Already liquidatable

            # Determine risk level
            risk_level = (
                health_factor_obj.risk_level.value
            )  # "low", "moderate", "high", "critical"

            if risk_level == "low":
                risk_description = "Very safe. Large price buffer before liquidation."
            elif risk_level == "moderate":
                risk_description = "Moderate risk. Monitor market conditions."
            elif risk_level == "high":
                risk_description = "High risk. Consider reducing leverage."
            else:
                risk_description = "⚠️ CRITICAL: Very close to liquidation!"

            # Analyze each collateral asset
            liquidation_scenarios = []
            for supply in position.supplies:
                if supply.is_collateral and supply.balance_usd > 0:
                    # Get market details for liquidation threshold
                    try:
                        market = await self.aave_gateway.get_market_details(
                            asset=supply.symbol, chain=chain_name
                        )

                        # Calculate liquidation price for this asset
                        # At liquidation: (asset_amount * liquidation_price * liq_threshold) / total_debt = 1.0 HF
                        # liquidation_price = (total_debt / (asset_amount * liq_threshold))

                        if supply.balance > 0 and position.total_debt_usd > 0:
                            # Simplified: assume this is the only collateral
                            liquidation_price_usd = float(
                                position.total_debt_usd
                                / (supply.balance * market.liquidation_threshold)
                            )
                            current_price_usd = float(market.price_usd)

                            price_drop_pct = (
                                (
                                    (current_price_usd - liquidation_price_usd)
                                    / current_price_usd
                                )
                                * 100
                                if current_price_usd > 0
                                else 0
                            )

                            liquidation_scenarios.append({
                                "collateral_asset": supply.symbol,
                                "collateral_amount": self._safe_decimal(supply.balance),
                                "collateral_usd": self._safe_decimal(
                                    supply.balance_usd
                                ),
                                "current_price_usd": self._safe_decimal(
                                    market.price_usd
                                ),
                                "liquidation_price_usd": f"{liquidation_price_usd:.2f}",
                                "price_drop_percentage": f"{price_drop_pct:.2f}%",
                                "liquidation_threshold": float(
                                    market.liquidation_threshold
                                ),
                            })
                    except Exception as e:
                        # Skip if market not found
                        continue

            # Generate recommendations
            recommendations = []
            if risk_level in ["high", "critical"]:
                recommendations.extend([
                    "🚨 Add more collateral to increase health factor",
                    "💰 Repay part of the debt to reduce risk",
                    "📊 Monitor your position every few hours",
                ])
            if risk_level in ["moderate", "high", "critical"]:
                recommendations.extend([
                    "🔔 Set up price alerts for your collateral assets",
                    "⚙️ Consider switching to stable rate if variable rates are rising",
                ])
            if risk_level == "low":
                recommendations.append(
                    "✅ Position is healthy. Continue monitoring periodically."
                )

            return {
                "success": True,
                "chain_id": chain_id,
                "chain_name": chain_name,
                "user_address": user_address.lower(),
                "has_position": True,
                "risk_level": risk_level,
                "risk_description": risk_description,
                "health_factor": self._safe_decimal(health_factor_obj.value, "inf"),
                "distance_to_liquidation": self._safe_decimal(
                    health_factor_obj.distance_to_liquidation
                ),
                "price_drop_before_liquidation": f"{price_drop_to_liquidation:.2f}%",
                "total_collateral_usd": self._safe_decimal(
                    position.total_collateral_usd
                ),
                "total_debt_usd": self._safe_decimal(position.total_debt_usd),
                "liquidation_scenarios": liquidation_scenarios,
                "recommendations": recommendations,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chain_id": chain_id,
                "user_address": user_address,
                "chain_name": self._chain_id_to_name(chain_id),
            }


# Standalone FastAPI app
if __name__ == "__main__":
    import uvicorn

    server = AaveMCPServer()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║            Aave MCP Server Starting...                   ║
╚══════════════════════════════════════════════════════════╝

Server: {server.name} v{server.version}
Tools: {len(server.tools)} registered
Port: 8085

Tools Available:
""")
    for tool_name, tool in server.tools.items():
        print(f"  • {tool_name}: {tool.description[:60]}...")

    print("""
Supported Chains:
  • Ethereum (1)
  • Polygon (137)
  • Arbitrum (42161)
  • Optimism (10)
  • Avalanche (43114)

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
        port=8085,
        log_level="info",
    )
