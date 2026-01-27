"""
Leverage Loop Command for Lending Operations.

Defines the command pattern for leverage loop operations following CQRS principles.
A leverage loop creates leveraged positions through iterative supply → borrow → supply cycles.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class LeverageLoopCommand:
    """
    Command to create a leveraged position through iterative supply-borrow-swap cycles.

    A leverage loop multiplies exposure to an asset by:
    1. Supply collateral → Borrow stablecoin → Swap to collateral → Supply again
    2. Repeat 2-4 times to achieve 2x-4x leverage
    3. Each iteration requires separate user signature (NO batch processing)

    Example 3x Leverage:
    - Start: 10 ETH
    - Iteration 1: Supply 10 ETH, borrow 7 ETH worth of USDC, swap to 7 ETH
    - Iteration 2: Supply 7 ETH, borrow 4.9 ETH worth of USDC, swap to 4.9 ETH
    - Iteration 3: Supply 4.9 ETH, borrow 3.43 ETH worth of USDC, swap to 3.43 ETH
    - Result: 25.33 ETH exposure from 10 ETH (2.53x leverage)

    CRITICAL: This is a MULTI-STEP operation requiring 3 separate signatures per iteration.
    Each step (supply, borrow, swap) MUST be approved individually by the user.

    Attributes:
        user_id: User's unique identifier (UUID)
        asset: Asset to leverage (ETH, WETH, wstETH only)
        initial_amount: Initial collateral amount to start loop
        target_leverage: Desired leverage multiplier (2.0 to 4.0)
        protocol: Lending protocol ("aave" - only protocol supporting borrowing)
        chain: Blockchain network (ethereum, base, arbitrum, etc.)
        max_iterations: Maximum number of loop iterations (default: 4)
        min_health_factor: Minimum acceptable health factor (default: 1.5)
        slippage_tolerance: Acceptable slippage for swaps (default: 0.01 = 1%)

    Business Rules:
        - Only ETH, WETH, wstETH are supported (high liquidity, accepted collateral)
        - Target leverage must be 2.0 to 4.0 (safety limits)
        - Health factor must remain >= min_health_factor after EVERY borrow
        - Each step requires separate user approval (NO batching)
        - Loop stops if health factor would drop below threshold
        - Minimum recommended health factor: 1.5
        - Critical safety threshold: 1.2

    Example:
        >>> command = LeverageLoopCommand(
        ...     user_id=UUID("..."),
        ...     asset="ETH",
        ...     initial_amount=Decimal("10.0"),
        ...     target_leverage=Decimal("3.0"),
        ...     protocol="aave",
        ...     chain="ethereum",
        ...     min_health_factor=Decimal("1.5"),
        ... )
    """

    user_id: UUID
    asset: str  # ETH, WETH, wstETH only
    initial_amount: Decimal
    target_leverage: Decimal  # 2.0 to 4.0
    protocol: Literal["aave"] = "aave"  # Only Aave supports borrowing
    chain: str = "ethereum"
    max_iterations: int = 4
    min_health_factor: Decimal = Decimal("1.5")  # Safety threshold
    slippage_tolerance: Decimal = Decimal("0.01")  # 1% default

    def __post_init__(self) -> None:
        """
        Validate command invariants.

        Raises:
            ValueError: If command validation fails
        """
        # Validate initial amount
        if self.initial_amount <= 0:
            raise ValueError(
                f"Initial amount must be positive, got: {self.initial_amount}"
            )

        # Validate asset (only high-liquidity collateral assets)
        supported_assets = {"ETH", "WETH", "wstETH"}
        if self.asset.upper() not in supported_assets:
            raise ValueError(
                f"Asset {self.asset} not supported for leverage loops. "
                f"Supported: {supported_assets}"
            )

        # Validate target leverage
        if not (Decimal("2.0") <= self.target_leverage <= Decimal("4.0")):
            raise ValueError(
                f"Target leverage must be between 2.0 and 4.0, got: {self.target_leverage}"
            )

        # Validate protocol (only Aave supports borrowing)
        if self.protocol.lower() != "aave":
            raise ValueError(
                f"Only Aave protocol supports borrowing, got: {self.protocol}"
            )

        # Validate minimum health factor
        if self.min_health_factor < Decimal("1.0"):
            raise ValueError(
                f"Minimum health factor must be >= 1.0, got: {self.min_health_factor}"
            )

        # Warn if health factor below recommended threshold
        if self.min_health_factor < Decimal("1.5"):
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Minimum health factor {self.min_health_factor} is below "
                f"recommended threshold of 1.5 - increased liquidation risk in leverage loops"
            )

        # Validate max iterations
        if not (1 <= self.max_iterations <= 10):
            raise ValueError(
                f"Max iterations must be between 1 and 10, got: {self.max_iterations}"
            )

        # Validate slippage tolerance
        if not (Decimal("0") <= self.slippage_tolerance <= Decimal("0.05")):
            raise ValueError(
                f"Slippage tolerance must be between 0 and 0.05 (5%), "
                f"got: {self.slippage_tolerance}"
            )

        # Validate chain
        supported_chains = {
            "ethereum",
            "base",
            "arbitrum",
            "polygon",
            "optimism",
            "avalanche",
        }
        if self.chain.lower() not in supported_chains:
            raise ValueError(
                f"Unsupported chain: {self.chain}. Supported: {supported_chains}"
            )


@dataclass(frozen=True)
class LeverageLoopStep:
    """
    Single step in the leverage loop execution.

    Each step represents one action that requires user approval:
    - supply: Supply collateral to Aave
    - borrow: Borrow stablecoin against collateral
    - swap: Swap borrowed stablecoin back to collateral

    Attributes:
        step_number: Step sequence number (1-based)
        action: Type of action (supply, borrow, swap)
        asset_in: Input asset symbol
        asset_out: Output asset symbol
        amount_in: Input amount
        amount_out: Expected output amount
        health_factor_after: Projected health factor after this step
        execute_data: Transaction data for Privy execution
        requires_approval: Whether this step needs user signature (always True)
    """

    step_number: int
    action: Literal["supply", "borrow", "swap"]
    asset_in: str
    asset_out: str
    amount_in: Decimal
    amount_out: Decimal
    health_factor_after: Decimal
    execute_data: dict
    requires_approval: bool = True

    def to_dict(self) -> dict:
        """Convert step to dictionary for JSON serialization."""
        return {
            "step_number": self.step_number,
            "action": self.action,
            "asset_in": self.asset_in,
            "asset_out": self.asset_out,
            "amount_in": str(self.amount_in),
            "amount_out": str(self.amount_out),
            "health_factor_after": str(self.health_factor_after),
            "execute_data": self.execute_data,
            "requires_approval": self.requires_approval,
        }


@dataclass(frozen=True)
class LeverageLoopResult:
    """
    Result of leverage loop calculation with multi-step execution plan.

    CRITICAL: This is a PLAN, not an execution. The user must approve
    each step individually. NO automatic batch processing.

    Attributes:
        loop_id: Unique identifier for this loop execution
        total_steps: Total number of steps requiring approval
        steps: List of all steps in execution order
        initial_collateral: Initial collateral amount
        final_exposure: Projected final collateral exposure
        actual_leverage: Actual leverage achieved (may differ from target)
        final_health_factor: Projected final health factor
        estimated_apy: Estimated net APY (supply APY - borrow APY)
        total_cost_usd: Estimated total cost (gas + swap fees)
        warnings: List of warning messages for user
        current_step: Current step index for resumable workflow (0 = not started)
    """

    loop_id: UUID
    total_steps: int
    steps: list[LeverageLoopStep]
    initial_collateral: Decimal
    final_exposure: Decimal
    actual_leverage: Decimal  # May differ from target
    final_health_factor: Decimal
    estimated_apy: Decimal
    total_cost_usd: Decimal  # Gas + swap fees
    warnings: list[str]
    current_step: int = 0  # For resumable workflows

    def to_dict(self) -> dict:
        """
        Convert result to dictionary for JSON serialization.

        Returns:
            Dictionary representation of result
        """
        return {
            "loop_id": str(self.loop_id),
            "total_steps": self.total_steps,
            "steps": [step.to_dict() for step in self.steps],
            "initial_collateral": str(self.initial_collateral),
            "final_exposure": str(self.final_exposure),
            "actual_leverage": str(self.actual_leverage),
            "final_health_factor": str(self.final_health_factor),
            "estimated_apy": str(self.estimated_apy),
            "total_cost_usd": str(self.total_cost_usd),
            "warnings": self.warnings,
            "current_step": self.current_step,
        }

    @property
    def is_complete(self) -> bool:
        """Check if all steps have been completed."""
        return self.current_step >= self.total_steps

    @property
    def next_step(self) -> LeverageLoopStep | None:
        """Get the next step to execute."""
        if self.is_complete:
            return None
        return self.steps[self.current_step]
