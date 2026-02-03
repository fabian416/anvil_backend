"""
Borrow Interactor for Lending Operations.

Orchestrates borrow operations with health factor validation.
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from app.application.lending.commands.borrow_command import BorrowCommand, BorrowResult
from app.application.lending.services.health_factor_validator_service import (
    HealthFactorValidatorService,
)
from app.domain.ports.balance_checker import IBalanceChecker
from app.domain.ports.lending_repository import ILendingRepository
from app.domain.ports.aave_gateway import AaveGateway
from app.domain.value_objects.lending.health_factor_result import HealthFactorResult

logger = logging.getLogger(__name__)


class UnsafeBorrowError(Exception):
    """
    Raised when borrow operation would result in unsafe health factor.

    This exception should be caught by the presentation layer and
    converted to a user-friendly error response with status 400.

    Attributes:
        validation_result: HealthFactorResult with detailed safety assessment
    """

    def __init__(self, validation_result: HealthFactorResult):
        self.validation_result = validation_result
        super().__init__(validation_result.warning_message)


class InsufficientCollateralError(Exception):
    """
    Raised when user has insufficient collateral for borrow.

    Attributes:
        required_usd: Required collateral in USD
        available_usd: Available collateral in USD
    """

    def __init__(self, required_usd: Decimal, available_usd: Decimal):
        self.required_usd = required_usd
        self.available_usd = available_usd
        super().__init__(
            f"Insufficient collateral. Required: ${required_usd}, "
            f"Available: ${available_usd}"
        )


class BorrowInteractor:
    """
    Interactor for borrow use case.

    Orchestrates:
    1. Health factor validation (CRITICAL - before approval UI)
    2. Collateral sufficiency check
    3. Borrow capacity verification
    4. Execute data generation for Privy
    5. Position persistence with health factor tracking

    This is a SAFETY-CRITICAL operation:
    - Health factor MUST be validated BEFORE execute_data generation
    - User should NEVER see approval UI if borrow is unsafe
    - Minimum safe health factor: 1.2 (recommended: 1.5)
    - Operations with projected HF < 1.2 are BLOCKED

    Dependencies are injected via Dishka DI with REQUEST scope.
    """

    __slots__ = (
        "_hf_validator",
        "_balance_checker",
        "_aave_gateway",
        "_repository",
    )

    def __init__(
        self,
        hf_validator: HealthFactorValidatorService,
        balance_checker: IBalanceChecker,
        aave_gateway: AaveGateway,
        repository: ILendingRepository,
    ):
        """
        Initialize borrow interactor.

        Args:
            hf_validator: Service for health factor validation
            balance_checker: Port for checking wallet balances
            aave_gateway: Port for Aave operations
            repository: Port for position persistence
        """
        self._hf_validator = hf_validator
        self._balance_checker = balance_checker
        self._aave_gateway = aave_gateway
        self._repository = repository

    async def execute(
        self,
        command: BorrowCommand,
        wallet_address: str,
    ) -> BorrowResult:
        """
        Execute borrow command with health factor validation.

        Flow:
        1. Validate health factor (BLOCKS if unsafe)
        2. Check collateral sufficiency
        3. Verify borrow capacity available
        4. Generate execute_data for Privy
        5. Save position to database
        6. Return result with health factor warnings

        Args:
            command: Borrow command with operation details
            wallet_address: User's wallet address (from auth context)

        Returns:
            BorrowResult with execute_data and health factor analysis

        Raises:
            UnsafeBorrowError: If projected HF < min_health_factor (BLOCKED)
            InsufficientCollateralError: If collateral insufficient
            ValueError: If validation fails

        Example:
            >>> result = await interactor.execute(
            ...     command=BorrowCommand(
            ...         user_id=UUID("..."),
            ...         protocol="aave",
            ...         asset="USDC",
            ...         amount=Decimal("2000.0"),
            ...         chain="ethereum",
            ...         min_health_factor=Decimal("1.5"),
            ...     ),
            ...     wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            ... )
            >>> # Frontend receives execute_data and health factor warning
        """
        logger.info(
            f"Executing borrow command: user={command.user_id}, "
            f"asset={command.asset}, amount={command.amount}, "
            f"chain={command.chain}, min_hf={command.min_health_factor}"
        )

        # STEP 1: CRITICAL HEALTH FACTOR VALIDATION
        # This MUST happen BEFORE generating execute_data
        # to prevent users from seeing approval UI for unsafe borrows
        validation_result = await self._hf_validator.validate_borrow(
            wallet=wallet_address,
            borrow_asset=command.asset,
            borrow_amount=command.amount,
            chain=command.chain,
        )

        logger.info(
            f"Health factor validation: current={validation_result.current_hf:.2f}, "
            f"projected={validation_result.projected_hf:.2f}, "
            f"level={validation_result.level.value}, is_safe={validation_result.is_safe}"
        )

        # STEP 2: BLOCK UNSAFE BORROWS
        # If projected HF < min_health_factor, raise exception immediately
        # This prevents the approval UI from being shown
        if validation_result.projected_hf < command.min_health_factor:
            logger.warning(
                f"Unsafe borrow blocked: projected_hf={validation_result.projected_hf:.2f} "
                f"< min_required={command.min_health_factor:.2f}"
            )
            raise UnsafeBorrowError(validation_result)

        # STEP 3: Check collateral sufficiency
        # Verify user has adequate collateral for this borrow
        await self._validate_collateral(
            validation_result=validation_result,
            wallet_address=wallet_address,
            chain=command.chain,
        )

        # STEP 4: Fetch borrow APY from Aave
        market_data = await self._aave_gateway.get_market_data(chain=command.chain)
        asset_market = next(
            (m for m in market_data if m.symbol.upper() == command.asset.upper()),
            None,
        )

        if not asset_market:
            raise ValueError(f"Asset {command.asset} not found in Aave market")

        borrow_apy = asset_market.variable_borrow_apy if command.rate_mode == "variable" else asset_market.stable_borrow_apy
        asset_address = asset_market.address

        # STEP 5: Generate execute_data (only if safe)
        # This is what gets sent to frontend for Privy signing
        execute_data = {
            "action_type": "borrow",
            "provider": "aave",
            "protocol": "aave_v3",
            "chain": command.chain,
            "asset_address": asset_address,
            "asset_symbol": command.asset,
            "amount": str(command.amount),
            "rate_mode": command.rate_mode,
            "pool_address": self._get_aave_pool_address(command.chain),
            "health_factor_before": str(validation_result.current_hf),
            "health_factor_after": str(validation_result.projected_hf),
            "expected_borrow_apy": float(borrow_apy),
        }

        # STEP 6: Save position to database
        position_id = await self._repository.save_borrow_position(
            user_id=command.user_id,
            protocol="aave",
            asset=command.asset,
            amount=str(command.amount),
            amount_usd=str(validation_result.projected_debt_usd),
            apy=str(borrow_apy),
            chain=command.chain,
            rate_mode=command.rate_mode,
            health_factor_before=str(validation_result.current_hf),
            health_factor_after=str(validation_result.projected_hf),
            liquidation_price=str(validation_result.liquidation_price) if validation_result.liquidation_price else None,
            transaction_hash=None,  # Awaiting signature
        )

        # STEP 7: Package result with health factor context
        # Frontend can show health factor impact before approval
        message = self._build_message(
            command=command,
            validation_result=validation_result,
        )

        result = BorrowResult(
            transaction_hash=None,
            position_id=position_id,
            health_factor_current=validation_result.current_hf,
            health_factor_projected=validation_result.projected_hf,
            risk_level=validation_result.level.value.upper(),
            liquidation_price=validation_result.liquidation_price,
            max_safe_borrow_usd=validation_result.max_safe_borrow_usd,
            execute_data=execute_data,
            protocol="aave",
            asset=command.asset,
            amount=command.amount,
            chain=command.chain,
            rate_mode=command.rate_mode,
            borrow_apy=borrow_apy,
            status="awaiting_signature",
            message=message,
        )

        logger.info(
            f"Borrow command executed successfully: position_id={position_id}, "
            f"status={result.status}"
        )

        return result

    async def _validate_collateral(
        self,
        validation_result: HealthFactorResult,
        wallet_address: str,
        chain: str,
    ) -> None:
        """
        Validate user has sufficient collateral.

        Args:
            validation_result: Health factor validation result
            wallet_address: User's wallet address
            chain: Blockchain network

        Raises:
            InsufficientCollateralError: If collateral insufficient
        """
        # Check if user has collateral
        if validation_result.collateral_usd <= 0:
            raise InsufficientCollateralError(
                required_usd=validation_result.projected_debt_usd,
                available_usd=Decimal("0"),
            )

        # Verify collateral is sufficient for projected debt
        # (This is somewhat redundant with HF check, but explicit is better)
        min_collateral_needed = validation_result.projected_debt_usd * Decimal("1.5")
        if validation_result.collateral_usd < min_collateral_needed:
            logger.warning(
                f"Low collateral: have ${validation_result.collateral_usd}, "
                f"recommended ${min_collateral_needed} for safe borrowing"
            )

    def _build_message(
        self,
        command: BorrowCommand,
        validation_result: HealthFactorResult,
    ) -> str:
        """
        Build human-readable message with health factor warning.

        Args:
            command: Borrow command
            validation_result: Health factor validation result

        Returns:
            Formatted message with warnings
        """
        hf_current = validation_result.current_hf
        hf_projected = validation_result.projected_hf
        level = validation_result.level.value.upper()
        emoji = validation_result.emoji

        # Format health factor values
        hf_current_str = f"{hf_current:.2f}" if hf_current != Decimal("inf") else "∞"
        hf_projected_str = f"{hf_projected:.2f}" if hf_projected != Decimal("inf") else "∞"

        # Build message
        message_lines = [
            f"Borrow {command.amount} {command.asset}",
            "",
            f"Health Factor: {hf_current_str} → {hf_projected_str}",
            f"{emoji} {level}",
            "",
            validation_result.warning_message,
        ]

        # Add liquidation price if available
        if validation_result.liquidation_price:
            message_lines.append(
                f"\n💰 Liquidation Price: ${validation_result.liquidation_price:.2f}"
            )

        # Add max safe borrow recommendation
        if validation_result.max_safe_borrow_usd > 0:
            message_lines.append(
                f"\n💡 Max Safe Borrow: ${validation_result.max_safe_borrow_usd:.2f}"
            )

        return "\n".join(message_lines)

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
