"""
Supply Interactor for Lending Operations.

Orchestrates supply operations following hexagonal architecture principles.
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from app.application.lending.commands.supply_command import SupplyCommand, SupplyResult
from app.domain.ports.balance_checker import IBalanceChecker
from app.domain.ports.lending_repository import ILendingRepository
from app.domain.ports.aave_gateway import AaveGateway
from app.domain.ports.morpho_gateway import MorphoGateway

logger = logging.getLogger(__name__)


class BalanceInsufficientError(Exception):
    """
    Raised when user has insufficient balance for supply operation.

    This exception should be caught by the presentation layer and
    converted to a user-friendly error response with status 400.
    """

    def __init__(self, asset: str, required: Decimal, available: Decimal):
        self.asset = asset
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient {asset} balance. Required: {required}, Available: {available}"
        )


class ProtocolNotSupportedError(Exception):
    """Raised when protocol is not supported for operation."""

    pass


class SupplyInteractor:
    """
    Interactor for supply/deposit use case.

    Orchestrates:
    1. Balance validation (BEFORE execute_data generation)
    2. Protocol-specific supply logic (Aave vs Morpho)
    3. Execute data generation for Privy
    4. Position persistence

    This follows hexagonal architecture:
    - Domain: Business logic and validation rules
    - Application: Use case orchestration (this class)
    - Infrastructure: External calls via ports (balance, gateways, repos)

    Dependencies are injected via Dishka DI with REQUEST scope.
    """

    __slots__ = (
        "_balance_checker",
        "_aave_gateway",
        "_morpho_gateway",
        "_repository",
    )

    def __init__(
        self,
        balance_checker: IBalanceChecker,
        aave_gateway: AaveGateway,
        morpho_gateway: MorphoGateway,
        repository: ILendingRepository,
    ):
        """
        Initialize supply interactor.

        Args:
            balance_checker: Port for checking wallet balances
            aave_gateway: Port for Aave operations
            morpho_gateway: Port for Morpho operations
            repository: Port for position persistence
        """
        self._balance_checker = balance_checker
        self._aave_gateway = aave_gateway
        self._morpho_gateway = morpho_gateway
        self._repository = repository

    async def execute(
        self,
        command: SupplyCommand,
        wallet_address: str,
    ) -> SupplyResult:
        """
        Execute supply command with validation.

        Flow:
        1. Validate user balance (CRITICAL - prevents failed transactions)
        2. Fetch current APY from protocol
        3. Generate execute_data for Privy
        4. Save position to database
        5. Return result with execute_data

        Args:
            command: Supply command with operation details
            wallet_address: User's wallet address (from auth context)

        Returns:
            SupplyResult with execute_data for Privy signing

        Raises:
            BalanceInsufficientError: If user has insufficient balance
            ProtocolNotSupportedError: If protocol is invalid
            ValueError: If validation fails

        Example:
            >>> result = await interactor.execute(
            ...     command=SupplyCommand(
            ...         user_id=UUID("..."),
            ...         protocol="aave",
            ...         asset="USDC",
            ...         amount=Decimal("1000.0"),
            ...         chain="ethereum",
            ...     ),
            ...     wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            ... )
            >>> # Frontend receives execute_data and opens Privy modal
        """
        logger.info(
            f"Executing supply command: user={command.user_id}, "
            f"protocol={command.protocol}, asset={command.asset}, "
            f"amount={command.amount}, chain={command.chain}"
        )

        # STEP 1: CRITICAL BALANCE VALIDATION
        # This MUST happen BEFORE generating execute_data
        # to prevent showing approval UI for transactions user can't afford
        await self._validate_balance(
            wallet_address=wallet_address,
            asset=command.asset,
            amount=command.amount,
            chain=command.chain,
        )

        # STEP 2: Protocol-specific supply logic
        if command.protocol.lower() == "aave":
            result = await self._execute_aave_supply(command, wallet_address)
        elif command.protocol.lower() == "morpho":
            result = await self._execute_morpho_supply(command, wallet_address)
        else:
            raise ProtocolNotSupportedError(
                f"Protocol {command.protocol} not supported for supply operations"
            )

        logger.info(
            f"Supply command executed successfully: position_id={result.position_id}, "
            f"status={result.status}"
        )

        return result

    async def _validate_balance(
        self,
        wallet_address: str,
        asset: str,
        amount: Decimal,
        chain: str,
    ) -> None:
        """
        Validate user has sufficient balance for supply.

        Args:
            wallet_address: User's wallet address
            asset: Asset symbol
            amount: Required amount
            chain: Blockchain network

        Raises:
            BalanceInsufficientError: If insufficient balance
        """
        logger.debug(f"Validating balance: {amount} {asset} on {chain}")

        # Get token address for balance check
        # NOTE: This will be enhanced with a token registry in the future
        token_address = self._get_token_address(asset, chain)

        # Check balance
        current_balance = await self._balance_checker.get_balance(
            wallet_address=wallet_address,
            token_address=token_address,
            chain=chain,
        )

        logger.debug(
            f"Balance check result: required={amount}, available={current_balance}"
        )

        if current_balance < amount:
            raise BalanceInsufficientError(
                asset=asset,
                required=amount,
                available=current_balance,
            )

        # Also check gas balance
        has_gas = await self._balance_checker.check_gas_balance(
            wallet_address=wallet_address,
            chain=chain,
        )

        if not has_gas:
            chain_native = "ETH" if chain != "polygon" else "MATIC"
            raise BalanceInsufficientError(
                asset=chain_native,
                required=Decimal("0.01"),  # Approximate gas requirement
                available=Decimal("0"),
            )

    async def _execute_aave_supply(
        self,
        command: SupplyCommand,
        wallet_address: str,
    ) -> SupplyResult:
        """
        Execute Aave supply operation.

        Args:
            command: Supply command
            wallet_address: User's wallet address

        Returns:
            SupplyResult with Aave execute_data
        """
        logger.debug(f"Executing Aave supply: {command.asset} on {command.chain}")

        # Fetch current Aave market data for APY
        market_data = await self._aave_gateway.get_market_data(chain=command.chain)

        # Find asset in market data
        asset_market = next(
            (m for m in market_data if m.symbol.upper() == command.asset.upper()),
            None,
        )

        if not asset_market:
            raise ValueError(f"Asset {command.asset} not found in Aave market")

        # Get asset details
        apy = asset_market.supply_apy
        asset_address = asset_market.address

        # Generate execute_data for Privy
        # Following established pattern from SwapHandlerV2
        execute_data = {
            "action_type": "supply",
            "provider": "aave",
            "protocol": "aave_v3",
            "chain": command.chain,
            "asset_address": asset_address,
            "asset_symbol": command.asset,
            "amount": str(command.amount),
            "use_as_collateral": command.use_as_collateral,
            "expected_apy": float(apy),
            "pool_address": self._get_aave_pool_address(command.chain),
        }

        # Calculate USD value (approximate)
        amount_usd = command.amount * asset_market.price_usd if hasattr(asset_market, "price_usd") else command.amount

        # Save position to database
        position_id = await self._repository.save_supply_position(
            user_id=command.user_id,
            protocol="aave",
            asset=command.asset,
            amount=str(command.amount),
            amount_usd=str(amount_usd),
            apy=str(apy),
            chain=command.chain,
            transaction_hash=None,  # Awaiting signature
        )

        # Return result
        return SupplyResult(
            transaction_hash=None,
            position_id=position_id,
            apy=apy,
            execute_data=execute_data,
            protocol="aave",
            asset=command.asset,
            amount=command.amount,
            chain=command.chain,
            vault_name=None,
            status="awaiting_signature",
            message=f"Supply {command.amount} {command.asset} to Aave on {command.chain} at {apy:.2f}% APY",
        )

    async def _execute_morpho_supply(
        self,
        command: SupplyCommand,
        wallet_address: str,
    ) -> SupplyResult:
        """
        Execute Morpho vault supply operation.

        Args:
            command: Supply command
            wallet_address: User's wallet address

        Returns:
            SupplyResult with Morpho execute_data
        """
        logger.debug(
            f"Executing Morpho supply: {command.asset} on {command.chain}, "
            f"vault={command.vault_address}"
        )

        if not command.vault_address:
            raise ValueError("Morpho supply requires vault_address")

        # Fetch vault details
        vault = await self._morpho_gateway.get_vault_details(
            vault_address=command.vault_address,
            chain=command.chain,
        )

        # Validate asset matches vault
        if vault.asset.upper() != command.asset.upper():
            raise ValueError(
                f"Asset mismatch: command={command.asset}, vault={vault.asset}"
            )

        # Generate execute_data for Privy
        execute_data = {
            "action_type": "supply",
            "provider": "morpho",
            "protocol": "morpho",
            "chain": command.chain,
            "vault_address": vault.address,
            "asset_address": vault.asset_address,
            "asset_symbol": vault.asset,
            "amount": str(command.amount),
            "slippage": 0.5,
            "vault_name": vault.name,
            "vault_apy": float(vault.apy),
            "vault_tvl": float(vault.total_assets),
        }

        # Calculate USD value
        amount_usd = command.amount  # Assume 1:1 for stablecoins, enhance later

        # Save position to database
        position_id = await self._repository.save_supply_position(
            user_id=command.user_id,
            protocol="morpho",
            asset=command.asset,
            amount=str(command.amount),
            amount_usd=str(amount_usd),
            apy=str(vault.apy),
            chain=command.chain,
            vault_address=vault.address,
            vault_name=vault.name,
            transaction_hash=None,  # Awaiting signature
        )

        # Return result
        return SupplyResult(
            transaction_hash=None,
            position_id=position_id,
            apy=vault.apy,
            execute_data=execute_data,
            protocol="morpho",
            asset=command.asset,
            amount=command.amount,
            chain=command.chain,
            vault_name=vault.name,
            status="awaiting_signature",
            message=f"Supply {command.amount} {command.asset} to {vault.name} at {vault.apy:.2f}% APY",
        )

    def _get_token_address(self, asset: str, chain: str) -> str:
        """
        Get token contract address for asset.

        NOTE: This is a simplified implementation. In production, use a
        comprehensive token registry service.

        Args:
            asset: Asset symbol
            chain: Blockchain network

        Returns:
            Token contract address or "native" for native tokens
        """
        # Common token addresses by chain
        TOKEN_ADDRESSES = {
            "ethereum": {
                "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                "DAI": "0x6b175474e89094c44da98b954eedeac495271d0f",
                "WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
            },
            "base": {
                "USDC": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
                "WETH": "0x4200000000000000000000000000000000000006",
            },
        }

        # Check if native token
        if asset.upper() in ("ETH", "MATIC"):
            return "native"

        # Lookup token address
        chain_tokens = TOKEN_ADDRESSES.get(chain.lower(), {})
        return chain_tokens.get(asset.upper(), "native")

    def _get_aave_pool_address(self, chain: str) -> str:
        """
        Get Aave V3 Pool contract address for chain.

        Args:
            chain: Blockchain network

        Returns:
            Pool contract address
        """
        AAVE_POOLS = {
            "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            "base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
            "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "avalanche": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        }
        return AAVE_POOLS.get(chain.lower(), AAVE_POOLS["ethereum"])
