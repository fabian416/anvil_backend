"""
Leverage loop execution domain entity.

Tracks leverage loop executions with multi-step state management.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

__slots__ = (
    "id",
    "user_id",
    "protocol",
    "chain",
    "asset_address",
    "asset_symbol",
    "initial_amount",
    "target_leverage",
    "actual_leverage",
    "total_steps",
    "current_step",
    "steps_completed",
    "status",
    "final_health_factor",
    "final_collateral_usd",
    "final_debt_usd",
    "total_gas_used",
    "total_cost_usd",
    "error_message",
    "metadata",
    "created_at",
    "updated_at",
    "completed_at",
)


@dataclass(slots=True, frozen=True)
class LeverageLoopExecution:
    """
    Domain entity representing a leverage loop execution.

    Attributes:
        id: Unique identifier
        user_id: Reference to chat_users
        protocol: Lending protocol ('aave' or 'morpho')
        chain: Blockchain network
        asset_address: Asset contract address
        asset_symbol: Asset symbol (e.g., 'ETH', 'WBTC')
        initial_amount: Initial collateral amount
        target_leverage: Target leverage multiplier
        actual_leverage: Actual achieved leverage
        total_steps: Total number of steps required
        current_step: Current step number (0-indexed)
        steps_completed: Array of completed transaction hashes
        status: Execution status ('pending', 'in_progress', 'completed', 'failed', 'cancelled')
        final_health_factor: Final health factor after completion
        final_collateral_usd: Final collateral value in USD
        final_debt_usd: Final debt value in USD
        total_gas_used: Total gas consumed across all steps
        total_cost_usd: Total cost in USD (gas + fees)
        error_message: Error message if failed
        metadata: Additional execution metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        completed_at: Completion timestamp
    """

    id: UUID
    user_id: UUID
    protocol: str  # 'aave' or 'morpho'
    chain: str
    asset_address: str
    asset_symbol: str
    initial_amount: Decimal
    target_leverage: Decimal
    actual_leverage: Optional[Decimal]
    total_steps: int
    current_step: int
    steps_completed: List[str]  # Array of transaction hashes
    status: str  # 'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    final_health_factor: Optional[Decimal]
    final_collateral_usd: Optional[Decimal]
    final_debt_usd: Optional[Decimal]
    total_gas_used: Optional[Decimal]
    total_cost_usd: Optional[Decimal]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        valid_statuses = ("pending", "in_progress", "completed", "failed", "cancelled")
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {self.status}. "
                f"Must be one of {valid_statuses}."
            )

        if self.total_steps < 1:
            raise ValueError(
                f"Invalid total_steps: {self.total_steps}. "
                "Must be >= 1."
            )

        if self.current_step < 0 or self.current_step > self.total_steps:
            raise ValueError(
                f"Invalid current_step: {self.current_step}. "
                f"Must be between 0 and {self.total_steps}."
            )

        if self.target_leverage < Decimal("1.0"):
            raise ValueError(
                f"Invalid target_leverage: {self.target_leverage}. "
                "Must be >= 1.0."
            )

    @property
    def is_pending(self) -> bool:
        """Check if execution is pending."""
        return self.status == "pending"

    @property
    def is_in_progress(self) -> bool:
        """Check if execution is in progress."""
        return self.status == "in_progress"

    @property
    def is_completed(self) -> bool:
        """Check if execution is completed."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self.status == "failed"

    @property
    def is_cancelled(self) -> bool:
        """Check if execution was cancelled."""
        return self.status == "cancelled"

    @property
    def is_terminal(self) -> bool:
        """Check if execution is in terminal state (completed, failed, or cancelled)."""
        return self.status in ("completed", "failed", "cancelled")

    @property
    def progress_percentage(self) -> Decimal:
        """Calculate execution progress percentage."""
        if self.total_steps == 0:
            return Decimal("0")
        return (Decimal(self.current_step) / Decimal(self.total_steps)) * Decimal("100")

    @property
    def steps_remaining(self) -> int:
        """Calculate remaining steps."""
        return self.total_steps - self.current_step

    @property
    def leverage_efficiency(self) -> Optional[Decimal]:
        """Calculate leverage efficiency (actual vs target)."""
        if self.actual_leverage is None or self.target_leverage == Decimal("0"):
            return None
        return (self.actual_leverage / self.target_leverage) * Decimal("100")
