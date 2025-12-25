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
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.infrastructure.mcp.base import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError


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
        wallet_service: Optional[Any] = None,
        subgraph_url: Optional[str] = None,
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize Aave MCP server.
        
        Args:
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
        
        self.wallet_service = wallet_service
        self.subgraph_url = subgraph_url or "https://api.thegraph.com/subgraphs/name/aave/protocol-v3"
        
        # Create retry decorator for this server
        self._retry = retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, Exception)),
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
            1: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",     # Ethereum
            137: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",   # Polygon
            42161: "0x794a61358D6845594F94dc1DB02A252b5b4814aD", # Arbitrum
            10: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",    # Optimism
            43114: "0x794a61358D6845594F94dc1DB02A252b5b4814aD", # Avalanche
        }
        
        self.setup_tools()
    
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
        """Get Aave market data for assets."""
        # TODO: Integrate with Aave V3 contracts and subgraph
        # For now, return mock data
        
        # If no assets specified, return data for major assets
        if not assets:
            assets = ["USDC", "ETH", "DAI", "WBTC"]
        
        mock_markets = []
        for asset in assets:
            # Mock rates (simplified)
            supply_apy = 2.5 if asset in ["USDC", "DAI"] else 1.8
            borrow_apy_variable = 4.2 if asset in ["USDC", "DAI"] else 3.1
            borrow_apy_stable = 5.5 if asset in ["USDC", "DAI"] else 4.0
            
            mock_markets.append({
                "asset": asset,
                "supply_apy": supply_apy,
                "borrow_apy_variable": borrow_apy_variable,
                "borrow_apy_stable": borrow_apy_stable,
                "total_supplied": "10000000.00",
                "total_borrowed": "7500000.00",
                "utilization_rate": 75.0,
                "available_liquidity": "2500000.00",
                "ltv": 0.75,  # Loan-to-value ratio
                "liquidation_threshold": 0.80,
                "liquidation_bonus": 0.05,
                "can_be_collateral": True,
                "can_be_borrowed": True,
                "is_frozen": False,
            })
        
        return {
            "chain_id": chain_id,
            "chain_name": self.chains.get(chain_id, "unknown"),
            "pool_address": self.pool_addresses.get(chain_id),
            "markets_count": len(mock_markets),
            "markets": mock_markets,
            "timestamp": "2024-12-02T00:00:00Z",
            "note": "This is mock data. Real implementation will query Aave V3 contracts.",
        }
    
    async def _get_user_positions(
        self,
        chain_id: int,
        user_address: str,
    ) -> Dict[str, Any]:
        """Get user's Aave positions."""
        # TODO: Integrate with Aave V3 contracts
        # For now, return mock position
        
        mock_position = {
            "user_address": user_address,
            "chain_id": chain_id,
            "supplied": [
                {
                    "asset": "USDC",
                    "amount": "10000.00",
                    "amount_usd": "10000.00",
                    "apy": 2.5,
                    "is_collateral": True,
                    "atoken_address": "0x...",
                },
                {
                    "asset": "ETH",
                    "amount": "5.0",
                    "amount_usd": "11000.00",
                    "apy": 1.8,
                    "is_collateral": True,
                    "atoken_address": "0x...",
                },
            ],
            "borrowed": [
                {
                    "asset": "USDC",
                    "amount": "5000.00",
                    "amount_usd": "5000.00",
                    "apy": 4.2,
                    "rate_mode": "variable",
                    "debt_token_address": "0x...",
                },
            ],
            "total_supplied_usd": "21000.00",
            "total_borrowed_usd": "5000.00",
            "total_collateral_usd": "21000.00",
            "available_borrow_usd": "10750.00",  # Based on LTV
            "health_factor": "3.36",  # (21000 * 0.80) / 5000
            "ltv": "23.8",  # 5000 / 21000 * 100
            "liquidation_threshold": "80.0",
            "current_liquidation_price_eth": "1250.00",  # Price at which HF = 1.0
        }
        
        return {
            **mock_position,
            "timestamp": "2024-12-02T00:00:00Z",
            "note": "This is mock data. Real implementation will query Aave V3 contracts.",
        }
    
    async def _calculate_health_factor(
        self,
        chain_id: int,
        user_address: str,
    ) -> Dict[str, Any]:
        """Calculate health factor."""
        # TODO: Integrate with Aave V3 contracts
        # For now, return mock calculation
        
        # Health Factor = (Total Collateral * Liquidation Threshold) / Total Debt
        # If HF < 1.0, position can be liquidated
        
        total_collateral_usd = 21000.00
        liquidation_threshold = 0.80
        total_debt_usd = 5000.00
        
        health_factor = (total_collateral_usd * liquidation_threshold) / total_debt_usd
        
        # Determine risk level
        if health_factor >= 2.0:
            risk_level = "low"
            risk_color = "green"
        elif health_factor >= 1.5:
            risk_level = "moderate"
            risk_color = "yellow"
        elif health_factor >= 1.2:
            risk_level = "high"
            risk_color = "orange"
        else:
            risk_level = "critical"
            risk_color = "red"
        
        # Calculate buffer before liquidation
        price_drop_before_liquidation = ((health_factor - 1.0) / health_factor) * 100
        
        return {
            "chain_id": chain_id,
            "user_address": user_address,
            "health_factor": f"{health_factor:.2f}",
            "risk_level": risk_level,
            "risk_color": risk_color,
            "total_collateral_usd": total_collateral_usd,
            "total_debt_usd": total_debt_usd,
            "liquidation_threshold": liquidation_threshold,
            "price_drop_before_liquidation": f"{price_drop_before_liquidation:.2f}%",
            "is_liquidatable": health_factor < 1.0,
            "recommendation": (
                "Healthy position. Consider borrowing more if needed."
                if health_factor >= 2.0
                else "Monitor closely. Consider repaying debt or adding collateral."
                if health_factor >= 1.2
                else "⚠️ URGENT: Add collateral or repay debt immediately!"
            ),
            "timestamp": "2024-12-02T00:00:00Z",
            "note": "This is mock data. Real implementation will query Aave V3 contracts.",
        }
    
    async def _get_available_to_borrow(
        self,
        chain_id: int,
        user_address: str,
        asset: str,
        target_health_factor: float = 1.5,
    ) -> Dict[str, Any]:
        """Calculate available borrowing capacity."""
        # TODO: Integrate with Aave V3 contracts
        # For now, return mock calculation
        
        # Mock user position
        total_collateral_usd = 21000.00
        current_debt_usd = 5000.00
        liquidation_threshold = 0.80
        asset_price_usd = 1.0  # Assume USDC for simplicity
        
        # Calculate max borrow to maintain target health factor
        # target_hf = (collateral * liq_threshold) / (current_debt + new_borrow)
        # Solving for new_borrow:
        max_borrow_usd = (
            (total_collateral_usd * liquidation_threshold) / target_health_factor
        ) - current_debt_usd
        
        max_borrow_amount = max_borrow_usd / asset_price_usd
        
        return {
            "chain_id": chain_id,
            "user_address": user_address,
            "asset": asset,
            "max_borrow_amount": f"{max_borrow_amount:.2f}",
            "max_borrow_usd": f"{max_borrow_usd:.2f}",
            "target_health_factor": target_health_factor,
            "current_debt_usd": current_debt_usd,
            "total_collateral_usd": total_collateral_usd,
            "asset_price_usd": asset_price_usd,
            "warning": (
                "Always maintain health factor above 1.5 for safety. "
                "Market volatility can cause liquidation."
            ),
            "timestamp": "2024-12-02T00:00:00Z",
            "note": "This is mock data. Real implementation will query Aave V3 contracts.",
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
        """Supply asset to Aave."""
        # TODO: Integrate with wallet service and Aave V3 contracts
        # For now, return mock transaction
        
        return {
            "success": False,  # Always fail in mock mode for safety
            "error": "Supply execution is disabled in development mode",
            "message": (
                "To execute supply operations, integrate with:\n"
                "1. Aave V3 Pool contract for supply() call\n"
                "2. Internal wallet service for transaction signing\n"
                "3. Token approval flow (approve Pool to spend tokens)"
            ),
            "mock_transaction": {
                "chain_id": chain_id,
                "from": from_address,
                "to": self.pool_addresses.get(chain_id),
                "function": "supply",
                "params": {
                    "asset": asset,
                    "amount": amount,
                    "onBehalfOf": from_address,
                    "referralCode": 0,
                },
                "estimated_gas": "200000",
                "note": "This transaction was NOT executed. It's a mock response.",
            },
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
        """Borrow asset from Aave."""
        # TODO: Integrate with wallet service and Aave V3 contracts
        # For now, return mock transaction
        
        # Rate mode: 1 = stable, 2 = variable
        interest_rate_mode = 2 if rate_mode == "variable" else 1
        
        return {
            "success": False,  # Always fail in mock mode for safety
            "error": "Borrow execution is disabled in development mode",
            "message": (
                "To execute borrow operations, integrate with:\n"
                "1. Aave V3 Pool contract for borrow() call\n"
                "2. Internal wallet service for transaction signing\n"
                "3. Health factor check before execution"
            ),
            "mock_transaction": {
                "chain_id": chain_id,
                "from": from_address,
                "to": self.pool_addresses.get(chain_id),
                "function": "borrow",
                "params": {
                    "asset": asset,
                    "amount": amount,
                    "interestRateMode": interest_rate_mode,
                    "referralCode": 0,
                    "onBehalfOf": from_address,
                },
                "estimated_gas": "250000",
                "note": "This transaction was NOT executed. It's a mock response.",
            },
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
        """Repay borrowed asset."""
        # TODO: Integrate with wallet service and Aave V3 contracts
        
        interest_rate_mode = 2 if rate_mode == "variable" else 1
        
        return {
            "success": False,
            "error": "Repay execution is disabled in development mode",
            "mock_transaction": {
                "chain_id": chain_id,
                "from": from_address,
                "to": self.pool_addresses.get(chain_id),
                "function": "repay",
                "params": {
                    "asset": asset,
                    "amount": amount,
                    "interestRateMode": interest_rate_mode,
                    "onBehalfOf": from_address,
                },
                "estimated_gas": "180000",
                "note": "This transaction was NOT executed.",
            },
        }
    
    async def _withdraw_supply(
        self,
        user_id: str,
        chain_id: int,
        asset: str,
        amount: str,
        from_address: str,
    ) -> Dict[str, Any]:
        """Withdraw supplied asset."""
        # TODO: Integrate with wallet service and Aave V3 contracts
        
        return {
            "success": False,
            "error": "Withdraw execution is disabled in development mode",
            "mock_transaction": {
                "chain_id": chain_id,
                "from": from_address,
                "to": self.pool_addresses.get(chain_id),
                "function": "withdraw",
                "params": {
                    "asset": asset,
                    "amount": amount,
                    "to": from_address,
                },
                "estimated_gas": "150000",
                "note": "This transaction was NOT executed.",
            },
        }
    
    async def _get_liquidation_risk(
        self,
        chain_id: int,
        user_address: str,
    ) -> Dict[str, Any]:
        """Analyze liquidation risk."""
        # TODO: Integrate with Aave V3 contracts and price oracles
        # For now, return mock risk analysis
        
        # Mock position data
        supplied_eth = 5.0
        eth_price = 2200.0
        borrowed_usdc = 5000.0
        liquidation_threshold = 0.80
        
        # Calculate liquidation price for ETH
        # At liquidation: (eth_amount * liquidation_price * liq_threshold) = borrowed_usd
        liquidation_price = borrowed_usdc / (supplied_eth * liquidation_threshold)
        
        price_drop_to_liquidation = ((eth_price - liquidation_price) / eth_price) * 100
        
        # Determine risk level based on price buffer
        if price_drop_to_liquidation > 50:
            risk_level = "low"
            risk_description = "Very safe. Large price buffer before liquidation."
        elif price_drop_to_liquidation > 30:
            risk_level = "moderate"
            risk_description = "Moderate risk. Monitor market conditions."
        elif price_drop_to_liquidation > 15:
            risk_level = "high"
            risk_description = "High risk. Consider reducing leverage."
        else:
            risk_level = "critical"
            risk_description = "⚠️ CRITICAL: Very close to liquidation!"
        
        return {
            "chain_id": chain_id,
            "user_address": user_address,
            "risk_level": risk_level,
            "risk_description": risk_description,
            "liquidation_scenarios": [
                {
                    "collateral_asset": "ETH",
                    "current_price": eth_price,
                    "liquidation_price": f"{liquidation_price:.2f}",
                    "price_drop_percentage": f"{price_drop_to_liquidation:.2f}%",
                },
            ],
            "recommendations": [
                "Add more collateral to increase health factor" if risk_level in ["high", "critical"] else "",
                "Repay part of the debt" if risk_level in ["high", "critical"] else "",
                "Set up price alerts" if risk_level != "low" else "",
                "Consider switching to stable rate if concerned about variable rate increases" if risk_level != "low" else "",
            ],
            "timestamp": "2024-12-02T00:00:00Z",
            "note": "This is mock data. Real implementation will use live price feeds.",
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
