"""
Example Borrow Command Integration with HealthFactorValidator.

This file demonstrates how to integrate the HealthFactorValidator
into a CQRS command following the hexagonal architecture pattern.

NOTE: This is an EXAMPLE for Week 1, Days 6-7 implementation.
The actual BorrowCommand will be implemented in Week 2.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.application.lending.services.health_factor_validator_service import (
    HealthFactorValidatorService,
)
from app.domain.value_objects.lending.health_factor_result import HealthFactorResult


class UnsafeBorrowError(Exception):
    """
    Raised when a borrow operation would result in unsafe health factor.

    This exception should be caught by the presentation layer and
    converted to a user-friendly error response with status 400.
    """

    def __init__(self, validation_result: HealthFactorResult):
        self.result = validation_result
        super().__init__(validation_result.warning_message)


@dataclass(frozen=True)
class BorrowCommand:
    """
    Command to borrow assets from a lending protocol.

    Following CQRS pattern, this is the input contract for the
    borrow use case.
    """

    user_id: int
    wallet: str
    protocol: str  # "aave" or "morpho"
    asset: str  # Asset to borrow (e.g., "USDC")
    amount: Decimal  # Amount in asset units
    chain: str = "ethereum"


@dataclass(frozen=True)
class BorrowResult:
    """
    Result of borrow command execution.

    Contains transaction data for frontend execution via Privy.
    """

    status: str  # "awaiting_signature"
    execute_data: dict  # Transaction calldata for Privy
    validation: HealthFactorResult  # Health factor validation result
    message: str


class IBalanceChecker(Protocol):
    """Port for checking user balances (Week 1, Days 1-2)."""

    async def check_sufficient_collateral(
        self,
        wallet: str,
        required_collateral_usd: Decimal,
        chain: str = "ethereum",
    ) -> bool:
        """Check if user has sufficient collateral for borrow."""
        ...


class IAaveExecutor(Protocol):
    """Port for generating Aave transaction calldata."""

    async def generate_borrow_calldata(
        self,
        wallet: str,
        asset: str,
        amount: Decimal,
        chain: str = "ethereum",
    ) -> dict:
        """Generate transaction calldata for Aave borrow."""
        ...


class BorrowInteractor:
    """
    Interactor for borrow use case.

    Orchestrates:
    1. Health factor validation (BEFORE approval)
    2. Balance checking
    3. Transaction calldata generation
    4. Result packaging for frontend

    This is a CRITICAL USER APPROVAL checkpoint - the user should
    NEVER see the approval UI if the borrow is unsafe.
    """

    def __init__(
        self,
        hf_validator: HealthFactorValidatorService,
        balance_checker: IBalanceChecker,
        aave_executor: IAaveExecutor,
    ):
        self._hf_validator = hf_validator
        self._balance = balance_checker
        self._aave = aave_executor

    async def execute(self, command: BorrowCommand) -> BorrowResult:
        """
        Execute borrow command with health factor validation.

        Flow:
        1. Validate health factor (BLOCKS if unsafe)
        2. Check collateral sufficiency
        3. Generate execute_data
        4. Return result with validation info

        Args:
            command: Borrow command

        Returns:
            BorrowResult with execute_data for Privy

        Raises:
            UnsafeBorrowError: If HF < 1.2 (blocked)
            ValueError: If insufficient collateral or invalid input

        Example:
            >>> result = await interactor.execute(BorrowCommand(
            ...     user_id=123,
            ...     wallet="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            ...     protocol="aave",
            ...     asset="USDC",
            ...     amount=Decimal("2000"),
            ...     chain="ethereum",
            ... ))
            >>> # Frontend receives execute_data and shows Privy modal
        """
        # STEP 1: CRITICAL HEALTH FACTOR VALIDATION
        # This MUST happen BEFORE generating execute_data
        # to prevent users from seeing approval UI for unsafe borrows
        validation_result = await self._hf_validator.validate_borrow(
            wallet=command.wallet,
            borrow_asset=command.asset,
            borrow_amount=command.amount,
            chain=command.chain,
        )

        # STEP 2: BLOCK UNSAFE BORROWS
        # If projected HF < 1.2, raise exception immediately
        # This prevents the approval UI from being shown
        if not validation_result.is_safe:
            raise UnsafeBorrowError(validation_result)

        # STEP 3: Check collateral sufficiency
        # (Implementation in Week 1, Days 1-2)
        has_collateral = await self._balance.check_sufficient_collateral(
            wallet=command.wallet,
            required_collateral_usd=validation_result.projected_debt_usd,
            chain=command.chain,
        )

        if not has_collateral:
            raise ValueError(
                f"Insufficient collateral for borrow.\n"
                f"Required: ${validation_result.projected_debt_usd}\n"
                f"Add collateral to proceed."
            )

        # STEP 4: Generate execute_data (only if safe)
        # This is what gets sent to frontend for Privy signing
        execute_data = await self._aave.generate_borrow_calldata(
            wallet=command.wallet,
            asset=command.asset,
            amount=command.amount,
            chain=command.chain,
        )

        # STEP 5: Package result with validation context
        # Frontend can show health factor impact before approval
        return BorrowResult(
            status="awaiting_signature",
            execute_data=execute_data,
            validation=validation_result,
            message=(
                f"Borrow {command.amount} {command.asset}\n\n"
                f"Health Factor: {validation_result.current_hf:.2f} → "
                f"{validation_result.projected_hf:.2f}\n"
                f"{validation_result.emoji} {validation_result.level.value.upper()}\n\n"
                f"{validation_result.warning_message}"
            ),
        )


# Example presentation layer integration (HTTP controller)
"""
# Location: src/app/presentation/http/controllers/lending/borrow_controller.py

from fastapi import APIRouter, Depends, HTTPException
from dishka.integrations.fastapi import FromDishka

router = APIRouter()

@router.post("/api/v1/lending/borrow")
async def borrow_asset(
    request: BorrowRequest,
    interactor: FromDishka[BorrowInteractor],
) -> BorrowResponse:
    '''Borrow asset from lending protocol.'''

    try:
        # Execute command - health factor validation happens here
        result = await interactor.execute(
            BorrowCommand(
                user_id=request.user_id,
                wallet=request.wallet,
                protocol=request.protocol,
                asset=request.asset,
                amount=request.amount,
                chain=request.chain,
            )
        )

        # Return execute_data for Privy signing
        return BorrowResponse(
            status=result.status,
            execute_data=result.execute_data,
            health_factor={
                "current": str(result.validation.current_hf),
                "projected": str(result.validation.projected_hf),
                "level": result.validation.level.value,
                "color": result.validation.color,
                "message": result.validation.warning_message,
            },
            message=result.message,
        )

    except UnsafeBorrowError as e:
        # Convert to HTTP 400 with detailed error
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsafe_borrow",
                "message": str(e),
                "health_factor": e.result.to_dict(),
                "recommendation": (
                    f"Maximum safe borrow: ${e.result.max_safe_borrow_usd}"
                ),
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
"""
