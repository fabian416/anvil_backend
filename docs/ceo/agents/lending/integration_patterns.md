# MCP Integration Best Practices for Lending Protocols

## Overview
Comprehensive guide for integrating Aave (port 8085) and Morpho (port 8088) MCP servers into the Anvil Backend following Hexagonal Architecture and port-adapter patterns.

---

## 1. Aave MCP Adapter Pattern

### 1.1 Available Tools (9 Total)
```python
# Tool inventory from Aave MCP Server (port 8085)
AAVE_TOOLS = {
    # Market Data
    "mcp__aave__get_market_data": "Get supply/borrow APY, liquidity, and market stats",
    "mcp__aave__get_user_account_data": "Get user's collateral, debt, and health factor",

    # Supply Operations
    "mcp__aave__supply_asset": "Deposit asset as collateral",
    "mcp__aave__withdraw_asset": "Withdraw supplied asset",

    # Borrow Operations
    "mcp__aave__borrow_asset": "Borrow asset against collateral",
    "mcp__aave__repay_asset": "Repay borrowed asset",

    # Advanced Features
    "mcp__aave__set_user_emode": "Enable efficiency mode (e-mode) for correlated assets",
    "mcp__aave__swap_borrow_rate_mode": "Switch between stable and variable rate",

    # Utilities
    "mcp__aave__get_reserve_tokens": "Get aToken, stableDebtToken, variableDebtToken addresses",
}
```

### 1.2 Port Definition (Domain Layer)
```python
# src/app/domain/ports/lending_gateway.py
from typing import Protocol, List, Optional
from decimal import Decimal
from dataclasses import dataclass

@dataclass(frozen=True)
class MarketData:
    """Market statistics for a lending asset"""
    asset_address: str
    supply_apy: Decimal  # Annual Percentage Yield for suppliers
    borrow_apy_variable: Decimal  # Variable borrow APY
    borrow_apy_stable: Optional[Decimal]  # Stable borrow APY (Aave only)
    total_supply: Decimal  # Total supplied liquidity
    total_borrowed: Decimal  # Total borrowed amount
    utilization_rate: Decimal  # Borrow / Supply ratio
    liquidation_threshold: Decimal  # e.g., 0.85 (85%)
    ltv: Decimal  # Loan-to-Value ratio (e.g., 0.80)
    is_active: bool  # Can be supplied/borrowed
    is_frozen: bool  # Paused by governance
    updated_at: datetime

@dataclass(frozen=True)
class UserAccountData:
    """User's lending position across all assets"""
    wallet_address: str
    total_collateral_base: Decimal  # In base currency (e.g., USD)
    total_debt_base: Decimal
    available_borrow_base: Decimal
    current_liquidation_threshold: Decimal
    ltv: Decimal
    health_factor: Decimal  # Critical metric for liquidation risk
    updated_at: datetime

@dataclass(frozen=True)
class AssetPosition:
    """User's position in a single asset"""
    asset_address: str
    asset_symbol: str
    supplied_amount: Decimal
    borrowed_amount: Decimal
    supplied_value_usd: Decimal
    borrowed_value_usd: Decimal
    supply_apy: Decimal
    borrow_apy: Decimal

class ILendingProtocolGateway(Protocol):
    """Port for all lending protocol interactions"""

    # Market data queries (read-only)
    async def get_market_data(self, asset: str) -> MarketData:
        """Get current market data for an asset"""
        ...

    async def get_user_account_data(self, wallet: str) -> UserAccountData:
        """Get user's overall account health and positions"""
        ...

    async def get_user_positions(self, wallet: str) -> List[AssetPosition]:
        """Get detailed positions for each asset"""
        ...

    # Supply operations (write)
    async def supply_asset(
        self, wallet: str, asset: str, amount: Decimal
    ) -> str:  # Returns transaction hash
        """Supply asset as collateral"""
        ...

    async def withdraw_asset(
        self, wallet: str, asset: str, amount: Decimal
    ) -> str:
        """Withdraw supplied asset"""
        ...

    # Borrow operations (write)
    async def borrow_asset(
        self,
        wallet: str,
        asset: str,
        amount: Decimal,
        rate_mode: str = "variable",  # 'variable' | 'stable'
    ) -> str:
        """Borrow asset against collateral"""
        ...

    async def repay_asset(
        self,
        wallet: str,
        asset: str,
        amount: Decimal,
        rate_mode: str = "variable",
    ) -> str:
        """Repay borrowed asset"""
        ...

    # Health checks
    async def health_check(self) -> bool:
        """Check if protocol is reachable and operational"""
        ...
```

### 1.3 Adapter Implementation (Infrastructure Layer)
```python
# src/app/infrastructure/adapters/lending/aave_mcp_adapter.py
import httpx
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any

from app.domain.ports.lending_gateway import (
    ILendingProtocolGateway,
    MarketData,
    UserAccountData,
    AssetPosition,
)
from app.infrastructure.adapters.mcp.mcp_client import McpClient
from app.infrastructure.adapters.mcp.exceptions import (
    McpToolError,
    McpServerUnreachableError,
)

class AaveMcpAdapter(ILendingProtocolGateway):
    """Adapter for Aave protocol via MCP server"""

    def __init__(
        self,
        mcp_client: McpClient,
        base_url: str = "http://localhost:8085",
        timeout: int = 30,
    ):
        self._client = mcp_client
        self._base_url = base_url
        self._timeout = timeout

    async def get_market_data(self, asset: str) -> MarketData:
        """
        Call: mcp__aave__get_market_data

        Example response:
        {
            "asset": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "supplyAPY": "2.5",
            "variableBorrowAPY": "3.8",
            "stableBorrowAPY": "4.2",
            "totalLiquidity": "1000000000",
            "totalBorrowed": "600000000",
            "utilizationRate": "0.60",
            "liquidationThreshold": "0.85",
            "ltv": "0.80",
            "isActive": true,
            "isFrozen": false
        }
        """
        try:
            result = await self._client.call_tool(
                tool_name="mcp__aave__get_market_data",
                arguments={"asset": asset},
                timeout=self._timeout,
            )

            return MarketData(
                asset_address=result["asset"],
                supply_apy=Decimal(result["supplyAPY"]),
                borrow_apy_variable=Decimal(result["variableBorrowAPY"]),
                borrow_apy_stable=Decimal(result.get("stableBorrowAPY", "0")),
                total_supply=Decimal(result["totalLiquidity"]),
                total_borrowed=Decimal(result["totalBorrowed"]),
                utilization_rate=Decimal(result["utilizationRate"]),
                liquidation_threshold=Decimal(result["liquidationThreshold"]),
                ltv=Decimal(result["ltv"]),
                is_active=result["isActive"],
                is_frozen=result["isFrozen"],
                updated_at=datetime.utcnow(),
            )

        except httpx.ConnectError as e:
            raise McpServerUnreachableError(
                server="aave", url=self._base_url, original_error=e
            )

        except KeyError as e:
            raise McpToolError(
                tool="get_market_data",
                message=f"Unexpected response format: missing {e}",
            )

    async def get_user_account_data(self, wallet: str) -> UserAccountData:
        """
        Call: mcp__aave__get_user_account_data

        Example response:
        {
            "totalCollateralBase": "10000",
            "totalDebtBase": "5000",
            "availableBorrowsBase": "3000",
            "currentLiquidationThreshold": "8500",
            "ltv": "8000",
            "healthFactor": "1.7"
        }
        """
        result = await self._client.call_tool(
            tool_name="mcp__aave__get_user_account_data",
            arguments={"user_address": wallet},
            timeout=self._timeout,
        )

        return UserAccountData(
            wallet_address=wallet,
            total_collateral_base=Decimal(result["totalCollateralBase"]),
            total_debt_base=Decimal(result["totalDebtBase"]),
            available_borrow_base=Decimal(result["availableBorrowsBase"]),
            current_liquidation_threshold=Decimal(result["currentLiquidationThreshold"]) / 10000,
            ltv=Decimal(result["ltv"]) / 10000,
            health_factor=Decimal(result["healthFactor"]),
            updated_at=datetime.utcnow(),
        )

    async def supply_asset(
        self, wallet: str, asset: str, amount: Decimal
    ) -> str:
        """
        Call: mcp__aave__supply_asset

        Arguments:
        - user_address: wallet address
        - asset: asset address
        - amount: amount in wei (string)
        - on_behalf_of: optional (defaults to user_address)
        - referral_code: optional (defaults to 0)

        Returns:
        {
            "tx_hash": "0x123abc...",
            "status": "pending"
        }
        """
        result = await self._client.call_tool(
            tool_name="mcp__aave__supply_asset",
            arguments={
                "user_address": wallet,
                "asset": asset,
                "amount": str(amount),
            },
            timeout=self._timeout,
        )

        return result["tx_hash"]

    async def borrow_asset(
        self,
        wallet: str,
        asset: str,
        amount: Decimal,
        rate_mode: str = "variable",
    ) -> str:
        """
        Call: mcp__aave__borrow_asset

        Arguments:
        - user_address: wallet address
        - asset: asset address
        - amount: amount to borrow (wei string)
        - interest_rate_mode: 1 (stable) or 2 (variable)
        - on_behalf_of: optional
        - referral_code: optional
        """
        # Convert rate_mode to Aave's integer format
        rate_mode_int = 2 if rate_mode == "variable" else 1

        result = await self._client.call_tool(
            tool_name="mcp__aave__borrow_asset",
            arguments={
                "user_address": wallet,
                "asset": asset,
                "amount": str(amount),
                "interest_rate_mode": rate_mode_int,
            },
            timeout=self._timeout,
        )

        return result["tx_hash"]

    async def health_check(self) -> bool:
        """Check if Aave MCP server is reachable"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._base_url}/health", timeout=5
                )
                return response.status_code == 200
        except httpx.ConnectError:
            return False
```

### 1.4 Configuration (TOML)
```toml
# config/local/.secrets.toml
[mcp_servers.aave]
base_url = "http://localhost:8085"
timeout = 30
cache_ttl = 60  # Cache market data for 60 seconds
retry_attempts = 3
retry_delay = 2  # seconds
```

---

## 2. Morpho MCP Adapter Pattern

### 2.1 Available Tools (6 Total)
```python
# Tool inventory from Morpho MCP Server (port 8088)
MORPHO_TOOLS = {
    # Vault Discovery
    "mcp__morpho__morpho_get_vaults": "List all Morpho vaults with APY and TVL",
    "mcp__morpho__morpho_get_vault_data": "Get detailed vault data (APY, cap, utilization)",

    # User Positions
    "mcp__morpho__morpho_get_user_position": "Get user's position in a vault",

    # Supply Operations
    "mcp__morpho__morpho_supply": "Supply assets to a vault",
    "mcp__morpho__morpho_withdraw": "Withdraw assets from a vault",

    # Borrow Operations
    "mcp__morpho__morpho_borrow": "Borrow from a vault",
}
```

### 2.2 Morpho-Specific Adapter
```python
# src/app/infrastructure/adapters/lending/morpho_mcp_adapter.py
from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime

@dataclass(frozen=True)
class MorphoVault:
    """Morpho vault metadata"""
    vault_address: str
    name: str
    asset_address: str
    asset_symbol: str
    supply_apy: Decimal
    borrow_apy: Decimal
    tvl: Decimal  # Total Value Locked
    utilization_rate: Decimal
    capacity: Optional[Decimal]  # Maximum TVL
    is_active: bool

class MorphoMcpAdapter:
    """Adapter for Morpho protocol via MCP server"""

    def __init__(
        self,
        mcp_client: McpClient,
        base_url: str = "http://localhost:8088",
        timeout: int = 30,
    ):
        self._client = mcp_client
        self._base_url = base_url
        self._timeout = timeout

    async def get_vaults(
        self, asset: Optional[str] = None
    ) -> List[MorphoVault]:
        """
        Call: mcp__morpho__morpho_get_vaults

        Example response:
        {
            "vaults": [
                {
                    "address": "0xabc...",
                    "name": "Morpho USDC Vault",
                    "asset": "0xA0b...",
                    "assetSymbol": "USDC",
                    "supplyAPY": "5.2",
                    "borrowAPY": "6.8",
                    "tvl": "50000000",
                    "utilizationRate": "0.75",
                    "capacity": "100000000",
                    "isActive": true
                }
            ]
        }
        """
        result = await self._client.call_tool(
            tool_name="mcp__morpho__morpho_get_vaults",
            arguments={"asset": asset} if asset else {},
            timeout=self._timeout,
        )

        return [
            MorphoVault(
                vault_address=vault["address"],
                name=vault["name"],
                asset_address=vault["asset"],
                asset_symbol=vault["assetSymbol"],
                supply_apy=Decimal(vault["supplyAPY"]),
                borrow_apy=Decimal(vault["borrowAPY"]),
                tvl=Decimal(vault["tvl"]),
                utilization_rate=Decimal(vault["utilizationRate"]),
                capacity=Decimal(vault["capacity"]) if vault.get("capacity") else None,
                is_active=vault["isActive"],
            )
            for vault in result["vaults"]
        ]

    async def supply_to_vault(
        self, wallet: str, vault_address: str, amount: Decimal
    ) -> str:
        """
        Call: mcp__morpho__morpho_supply

        Arguments:
        - user_address: wallet address
        - vault: vault address
        - assets: amount to supply (wei string)
        - shares: optional (defaults to 0, meaning calculate from assets)
        - receiver: optional (defaults to user_address)
        """
        result = await self._client.call_tool(
            tool_name="mcp__morpho__morpho_supply",
            arguments={
                "user_address": wallet,
                "vault": vault_address,
                "assets": str(amount),
            },
            timeout=self._timeout,
        )

        return result["tx_hash"]
```

---

## 3. Cross-Protocol Comparison Logic

### 3.1 Protocol Comparator Service (Domain Layer)
```python
# src/app/domain/services/protocol_comparator.py
from typing import List, Literal
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class ProtocolComparison:
    """Comparison of lending rates across protocols"""
    asset_address: str
    asset_symbol: str

    # Aave data
    aave_supply_apy: Decimal
    aave_borrow_apy: Decimal
    aave_utilization: Decimal

    # Morpho data
    morpho_supply_apy: Decimal
    morpho_borrow_apy: Decimal
    morpho_utilization: Decimal

    # Comparison
    best_supply_protocol: Literal["aave", "morpho"]
    best_borrow_protocol: Literal["aave", "morpho"]
    supply_apy_difference: Decimal
    borrow_apy_difference: Decimal

class ProtocolComparator:
    """Domain service for comparing protocols"""

    def compare(
        self,
        aave_data: MarketData,
        morpho_vault: MorphoVault,
    ) -> ProtocolComparison:
        """Compare Aave and Morpho for the same asset"""

        # Determine best supply rate
        if morpho_vault.supply_apy > aave_data.supply_apy:
            best_supply = "morpho"
            supply_diff = morpho_vault.supply_apy - aave_data.supply_apy
        else:
            best_supply = "aave"
            supply_diff = aave_data.supply_apy - morpho_vault.supply_apy

        # Determine best borrow rate (LOWER is better)
        if morpho_vault.borrow_apy < aave_data.borrow_apy_variable:
            best_borrow = "morpho"
            borrow_diff = aave_data.borrow_apy_variable - morpho_vault.borrow_apy
        else:
            best_borrow = "aave"
            borrow_diff = morpho_vault.borrow_apy - aave_data.borrow_apy_variable

        return ProtocolComparison(
            asset_address=aave_data.asset_address,
            asset_symbol=morpho_vault.asset_symbol,
            aave_supply_apy=aave_data.supply_apy,
            aave_borrow_apy=aave_data.borrow_apy_variable,
            aave_utilization=aave_data.utilization_rate,
            morpho_supply_apy=morpho_vault.supply_apy,
            morpho_borrow_apy=morpho_vault.borrow_apy,
            morpho_utilization=morpho_vault.utilization_rate,
            best_supply_protocol=best_supply,
            best_borrow_protocol=best_borrow,
            supply_apy_difference=supply_diff,
            borrow_apy_difference=borrow_diff,
        )
```

### 3.2 Comparison Query Interactor (Application Layer)
```python
# src/app/application/lending/queries/compare_protocols_query.py
from dataclasses import dataclass
from typing import Optional
import asyncio

@dataclass(frozen=True)
class CompareProtocolsQuery:
    asset_address: str

class CompareProtocolsInteractor:
    def __init__(
        self,
        aave_adapter: AaveMcpAdapter,
        morpho_adapter: MorphoMcpAdapter,
        comparator: ProtocolComparator,
    ):
        self._aave = aave_adapter
        self._morpho = morpho_adapter
        self._comparator = comparator

    async def execute(
        self, query: CompareProtocolsQuery
    ) -> Optional[ProtocolComparison]:
        """Compare Aave and Morpho rates for an asset"""

        # Fetch data in parallel
        aave_data, morpho_vaults = await asyncio.gather(
            self._aave.get_market_data(query.asset_address),
            self._morpho.get_vaults(asset=query.asset_address),
            return_exceptions=True,
        )

        # Handle failures gracefully
        if isinstance(aave_data, Exception):
            logger.error(f"Aave fetch failed: {aave_data}")
            aave_data = None

        if isinstance(morpho_vaults, Exception):
            logger.error(f"Morpho fetch failed: {morpho_vaults}")
            morpho_vaults = None

        # Need both to compare
        if aave_data is None or not morpho_vaults:
            return None

        # Compare with first Morpho vault for this asset
        morpho_vault = morpho_vaults[0]

        return self._comparator.compare(aave_data, morpho_vault)
```

---

## 4. Balance Checking Before Transaction Submission

### 4.1 Balance Validator Port (Domain Layer)
```python
# src/app/domain/ports/balance_validator.py
from typing import Protocol
from decimal import Decimal

class IBalanceValidator(Protocol):
    async def get_balance(self, wallet: str, asset: str) -> Decimal:
        """Get current token balance for wallet"""
        ...

    async def has_sufficient_balance(
        self, wallet: str, asset: str, required_amount: Decimal
    ) -> bool:
        """Check if wallet has enough balance"""
        ...

    async def get_native_balance(self, wallet: str) -> Decimal:
        """Get native token (ETH) balance for gas"""
        ...
```

### 4.2 Web3 Balance Adapter (Infrastructure Layer)
```python
# src/app/infrastructure/adapters/balance/web3_balance_adapter.py
from web3 import Web3
from decimal import Decimal
from eth_typing import ChecksumAddress

class Web3BalanceValidator(IBalanceValidator):
    """Check balances via Web3 (direct RPC calls)"""

    def __init__(self, web3: Web3, erc20_abi: List[Dict[str, Any]]):
        self._web3 = web3
        self._erc20_abi = erc20_abi

    async def get_balance(self, wallet: str, asset: str) -> Decimal:
        """Get ERC20 token balance"""
        # Convert to checksum address
        wallet_checksum = Web3.to_checksum_address(wallet)
        asset_checksum = Web3.to_checksum_address(asset)

        # Create contract instance
        contract = self._web3.eth.contract(
            address=asset_checksum, abi=self._erc20_abi
        )

        # Call balanceOf
        balance_wei = await contract.functions.balanceOf(wallet_checksum).call()

        return Decimal(balance_wei)

    async def has_sufficient_balance(
        self, wallet: str, asset: str, required_amount: Decimal
    ) -> bool:
        """Check if balance >= required amount"""
        current_balance = await self.get_balance(wallet, asset)
        return current_balance >= required_amount

    async def get_native_balance(self, wallet: str) -> Decimal:
        """Get ETH balance"""
        wallet_checksum = Web3.to_checksum_address(wallet)
        balance_wei = await self._web3.eth.get_balance(wallet_checksum)
        return Decimal(balance_wei)
```

### 4.3 Pre-Transaction Validation (Application Layer)
```python
# src/app/application/lending/commands/supply_asset.py
class SupplyAssetInteractor:
    def __init__(
        self,
        lending_gateway: ILendingProtocolGateway,
        balance_validator: IBalanceValidator,
        gas_estimator: IGasEstimator,
    ):
        self._lending_gateway = lending_gateway
        self._balance_validator = balance_validator
        self._gas_estimator = gas_estimator

    async def execute(self, command: SupplyAssetCommand) -> str:
        """Supply asset with comprehensive pre-checks"""

        # 1. Check token balance
        has_balance = await self._balance_validator.has_sufficient_balance(
            command.wallet_address,
            command.asset_address,
            command.amount,
        )

        if not has_balance:
            current_balance = await self._balance_validator.get_balance(
                command.wallet_address, command.asset_address
            )
            raise InsufficientBalanceError(
                asset=command.asset_address,
                required=command.amount,
                available=current_balance,
            )

        # 2. Check gas balance
        gas_estimate = await self._gas_estimator.estimate_supply_gas(
            command.asset_address, command.amount
        )
        gas_cost = gas_estimate.total_cost_wei

        native_balance = await self._balance_validator.get_native_balance(
            command.wallet_address
        )

        if native_balance < gas_cost:
            raise InsufficientGasBalanceError(
                required=gas_cost,
                available=native_balance,
            )

        # 3. Execute transaction
        tx_hash = await self._lending_gateway.supply_asset(
            wallet=command.wallet_address,
            asset=command.asset_address,
            amount=command.amount,
        )

        return tx_hash
```

---

## 5. Transaction Status Monitoring

### 5.1 Transaction Tracker (Infrastructure Layer)
```python
# src/app/infrastructure/adapters/blockchain/tx_tracker.py
from enum import Enum
from web3 import Web3

class TxStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    DROPPED = "dropped"

class TransactionTracker:
    """Monitor transaction status on blockchain"""

    def __init__(self, web3: Web3, confirmations_required: int = 3):
        self._web3 = web3
        self._confirmations_required = confirmations_required

    async def get_status(self, tx_hash: str) -> TxStatus:
        """Get current transaction status"""
        try:
            # Get transaction receipt
            receipt = await self._web3.eth.get_transaction_receipt(tx_hash)

            if receipt is None:
                # Not mined yet
                return TxStatus.PENDING

            # Check if transaction succeeded
            if receipt["status"] == 0:
                return TxStatus.FAILED

            # Check confirmations
            current_block = await self._web3.eth.block_number
            confirmations = current_block - receipt["blockNumber"]

            if confirmations >= self._confirmations_required:
                return TxStatus.CONFIRMED
            else:
                return TxStatus.PENDING

        except Exception as e:
            logger.error(f"Failed to get tx status: {e}")
            return TxStatus.DROPPED

    async def wait_for_confirmation(
        self, tx_hash: str, timeout: int = 300
    ) -> TxStatus:
        """Wait for transaction confirmation (max timeout seconds)"""
        start_time = datetime.utcnow()

        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            status = await self.get_status(tx_hash)

            if status in (TxStatus.CONFIRMED, TxStatus.FAILED, TxStatus.DROPPED):
                return status

            # Poll every 5 seconds
            await asyncio.sleep(5)

        return TxStatus.PENDING  # Timed out
```

### 5.2 Background Monitoring Task (Celery)
```python
# src/app/infrastructure/tasks/lending_tasks.py
from celery import shared_task
from app.infrastructure.persistence_sqla.models import LendingTransaction

@shared_task
async def monitor_pending_transactions():
    """Background task to update pending transaction statuses"""

    # Find all pending transactions
    pending_txs = await db.query(LendingTransaction).filter(
        LendingTransaction.status == TxStatus.PENDING
    ).all()

    for tx in pending_txs:
        # Check current status
        status = await tx_tracker.get_status(tx.tx_hash)

        if status == TxStatus.CONFIRMED:
            # Update lending position
            tx.status = status
            await lending_service.finalize_position(tx)

            # Emit event
            await event_bus.publish(
                LendingPositionConfirmed(
                    user_id=tx.user_id,
                    tx_hash=tx.tx_hash,
                    operation=tx.operation,
                )
            )

        elif status == TxStatus.FAILED:
            tx.status = status

            # Notify user
            await notification_service.send_transaction_failed(tx)

        await db.commit()

# Schedule every 30 seconds
@celery.task(schedule=crontab(minute="*/1"))
async def schedule_tx_monitoring():
    await monitor_pending_transactions()
```

---

## 6. Event-Driven Updates for Position Changes

### 6.1 Domain Events (Domain Layer)
```python
# src/app/domain/events/lending_events.py
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

@dataclass(frozen=True)
class LendingPositionCreated:
    """Emitted when user creates a new lending position"""
    user_id: UUID
    position_id: UUID
    protocol: str  # 'aave' | 'morpho'
    operation: str  # 'supply' | 'borrow'
    asset_address: str
    amount: Decimal
    tx_hash: str
    occurred_at: datetime

@dataclass(frozen=True)
class LendingPositionConfirmed:
    """Emitted when transaction is confirmed on-chain"""
    user_id: UUID
    position_id: UUID
    tx_hash: str
    confirmations: int
    occurred_at: datetime

@dataclass(frozen=True)
class HealthFactorCritical:
    """Emitted when health factor drops below critical threshold"""
    user_id: UUID
    wallet_address: str
    current_health_factor: Decimal
    threshold: Decimal  # e.g., 1.2
    collateral_needed: Decimal
    occurred_at: datetime
```

### 6.2 Event Bus (Infrastructure Layer)
```python
# src/app/infrastructure/events/event_bus.py
from typing import Dict, List, Callable, Any
from app.domain.events.base import DomainEvent

class EventBus:
    """Simple in-memory event bus (can be replaced with Redis pub/sub)"""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe a handler to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent):
        """Publish an event to all subscribers"""
        event_type = type(event).__name__

        if event_type not in self._handlers:
            return

        for handler in self._handlers[event_type]:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler failed: {e}")
```

### 6.3 Event Handlers (Application Layer)
```python
# src/app/application/lending/event_handlers/position_confirmed_handler.py
class PositionConfirmedHandler:
    """Handle LendingPositionConfirmed event"""

    def __init__(
        self,
        notification_service: INotificationService,
        analytics_service: IAnalyticsService,
    ):
        self._notifications = notification_service
        self._analytics = analytics_service

    async def handle(self, event: LendingPositionConfirmed):
        """Process confirmed position"""

        # 1. Send user notification
        await self._notifications.send_transaction_confirmed(
            user_id=event.user_id,
            tx_hash=event.tx_hash,
        )

        # 2. Track analytics
        await self._analytics.track_event(
            user_id=event.user_id,
            event_name="lending_position_confirmed",
            properties={
                "protocol": event.protocol,
                "operation": event.operation,
                "asset": event.asset_address,
            },
        )

# Register handler with event bus
event_bus.subscribe(
    "LendingPositionConfirmed",
    position_confirmed_handler.handle,
)
```

---

## 7. Caching Strategy

### 7.1 Multi-Level Cache
```python
# src/app/infrastructure/adapters/lending/cached_aave_adapter.py
from typing import Optional
import redis.asyncio as redis
import json

class CachedAaveMcpAdapter(ILendingProtocolGateway):
    """Aave adapter with Redis caching"""

    def __init__(
        self,
        base_adapter: AaveMcpAdapter,
        redis_client: redis.Redis,
        cache_ttl: int = 60,
    ):
        self._adapter = base_adapter
        self._redis = redis_client
        self._cache_ttl = cache_ttl

    async def get_market_data(self, asset: str) -> MarketData:
        """Get market data with caching"""

        # Check cache
        cache_key = f"aave:market_data:{asset}"
        cached = await self._redis.get(cache_key)

        if cached:
            # Deserialize from cache
            data = json.loads(cached)
            return MarketData(**data)

        # Fetch fresh data
        market_data = await self._adapter.get_market_data(asset)

        # Store in cache
        await self._redis.setex(
            cache_key,
            self._cache_ttl,
            json.dumps(market_data.__dict__),
        )

        return market_data

    async def get_user_account_data(self, wallet: str) -> UserAccountData:
        """Get user data with shorter cache (critical data)"""

        cache_key = f"aave:account:{wallet}"
        cached = await self._redis.get(cache_key)

        if cached:
            data = json.loads(cached)
            return UserAccountData(**data)

        account_data = await self._adapter.get_user_account_data(wallet)

        # Cache for only 30 seconds (frequently changes)
        await self._redis.setex(
            cache_key,
            30,
            json.dumps(account_data.__dict__),
        )

        return account_data
```

---

## 8. Testing MCP Integrations

### 8.1 Mock MCP Client for Unit Tests
```python
# tests/unit/mocks/mock_mcp_client.py
class MockMcpClient:
    """Mock MCP client for testing"""

    def __init__(self):
        self._responses: Dict[str, Any] = {}

    def mock_tool_response(self, tool_name: str, response: Dict[str, Any]):
        """Set mock response for a tool"""
        self._responses[tool_name] = response

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any], timeout: int = 30
    ) -> Dict[str, Any]:
        """Return mocked response"""
        if tool_name not in self._responses:
            raise ValueError(f"No mock configured for {tool_name}")

        return self._responses[tool_name]

# Usage in tests
@pytest.mark.asyncio
async def test_aave_get_market_data():
    mock_client = MockMcpClient()
    mock_client.mock_tool_response(
        "mcp__aave__get_market_data",
        {
            "asset": "0xA0b...",
            "supplyAPY": "2.5",
            "variableBorrowAPY": "3.8",
            "totalLiquidity": "1000000",
            "isActive": True,
        },
    )

    adapter = AaveMcpAdapter(mock_client)
    market_data = await adapter.get_market_data("0xA0b...")

    assert market_data.supply_apy == Decimal("2.5")
```

---

## Sign-Off

- [ ] **MCP Integration**: @integration-specialist
- [ ] **Caching Strategy**: @performance-optimizer
- [ ] **Event Architecture**: @software-engineering-expert
- [ ] **Testing Patterns**: @test-automation-expert

**Final Approval**: @code-reviewer
