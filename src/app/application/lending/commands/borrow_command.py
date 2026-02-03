"""
Borrow Command for Lending Operations.

Defines the command pattern for borrow operations following CQRS principles.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class BorrowCommand:
    """
    Command to borrow assets from a lending protocol.

    Following CQRS pattern, this is the immutable input contract for the
    borrow use case. Borrow operations require health factor validation.

    Attributes:
        user_id: User's unique identifier (UUID)
        protocol: Lending protocol ("aave" only - Morpho doesn't support borrowing)
        asset: Asset symbol to borrow (e.g., "USDC", "USDT", "DAI")
        amount: Amount in asset units (e.g., 2000.0 for 2000 USDC)
        chain: Blockchain network (ethereum, base, arbitrum, etc.)
        rate_mode: Borrow rate mode ("variable" or "stable", default: "variable")
        min_health_factor: Minimum acceptable health factor (default: 1.5)

    Business Rules:
        - Health factor must remain >= min_health_factor after borrow
        - User must have sufficient collateral
        - Borrow capacity must be available
        - Minimum recommended health factor: 1.5
        - Critical safety threshold: 1.2
        - Liquidation occurs at health factor < 1.0

    Example:
        >>> command = BorrowCommand(
        ...     user_id=UUID("..."),
        ...     protocol="aave",
        ...     asset="USDC",
        ...     amount=Decimal("2000.0"),
        ...     chain="ethereum",
        ...     rate_mode="variable",
        ...     min_health_factor=Decimal("1.5"),
        ... )
    """

    user_id: UUID
    protocol: str  # "aave" (only protocol supporting borrows)
    asset: str
    amount: Decimal
    chain: str
    rate_mode: str = "variable"  # "variable" or "stable"
    min_health_factor: Decimal = Decimal("1.5")

    def __post_init__(self) -> None:
        """
        Validate command invariants.

        Raises:
            ValueError: If command validation fails
        """
        # Validate amount
        if self.amount <= 0:
            raise ValueError(f"Borrow amount must be positive, got: {self.amount}")

        # Validate protocol (only Aave supports borrowing)
        if self.protocol.lower() != "aave":
            raise ValueError(
                f"Only Aave protocol supports borrowing, got: {self.protocol}"
            )

        # Validate asset symbol
        if not self.asset or len(self.asset) < 2:
            raise ValueError(f"Invalid asset symbol: {self.asset}")

        # Validate rate mode
        if self.rate_mode.lower() not in ("variable", "stable"):
            raise ValueError(
                f"Rate mode must be 'variable' or 'stable', got: {self.rate_mode}"
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
                f"recommended threshold of 1.5 - increased liquidation risk"
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
class BorrowResult:
    """
    Result of borrow command execution.

    Contains transaction data and health factor analysis for safe borrowing.

    Attributes:
        transaction_hash: Transaction hash (None if awaiting signature)
        position_id: UUID of updated lending position
        health_factor_current: Current health factor before borrow
        health_factor_projected: Projected health factor after borrow
        risk_level: Risk level classification (SAFE, CAUTION, DANGER, CRITICAL, LIQUIDATABLE)
        liquidation_price: Price at which liquidation would occur (if applicable)
        max_safe_borrow_usd: Maximum safe borrow amount in USD
        execute_data: Transaction data for Privy SDK execution
        protocol: Protocol used (aave)
        asset: Asset borrowed
        amount: Amount borrowed
        chain: Blockchain network
        rate_mode: Borrow rate mode (variable or stable)
        borrow_apy: Current borrow APY
        status: Transaction status ("awaiting_signature", "pending", "confirmed")
        message: Human-readable message with health factor warning

    Example:
        >>> result = BorrowResult(
        ...     transaction_hash=None,
        ...     position_id=UUID("..."),
        ...     health_factor_current=Decimal("3.5"),
        ...     health_factor_projected=Decimal("2.1"),
        ...     risk_level="CAUTION",
        ...     liquidation_price=Decimal("3200.50"),
        ...     max_safe_borrow_usd=Decimal("3500.00"),
        ...     execute_data={...},
        ...     protocol="aave",
        ...     asset="USDC",
        ...     amount=Decimal("2000.0"),
        ...     chain="ethereum",
        ...     rate_mode="variable",
        ...     borrow_apy=Decimal("4.2"),
        ...     status="awaiting_signature",
        ...     message="⚠️ CAUTION - Health Factor 3.5 → 2.1",
        ... )
    """

    transaction_hash: Optional[str]
    position_id: UUID
    health_factor_current: Decimal
    health_factor_projected: Decimal
    risk_level: str
    liquidation_price: Optional[Decimal]
    max_safe_borrow_usd: Decimal
    execute_data: dict
    protocol: str
    asset: str
    amount: Decimal
    chain: str
    rate_mode: str
    borrow_apy: Decimal
    status: str
    message: str

    def to_dict(self) -> dict:
        """
        Convert result to dictionary for JSON serialization.

        Returns:
            Dictionary representation of result
        """
        return {
            "transaction_hash": self.transaction_hash,
            "position_id": str(self.position_id),
            "health_factor": {
                "current": str(self.health_factor_current),
                "projected": str(self.health_factor_projected),
                "risk_level": self.risk_level,
                "liquidation_price": str(self.liquidation_price)
                if self.liquidation_price
                else None,
                "max_safe_borrow_usd": str(self.max_safe_borrow_usd),
            },
            "execute_data": self.execute_data,
            "protocol": self.protocol,
            "asset": self.asset,
            "amount": str(self.amount),
            "chain": self.chain,
            "rate_mode": self.rate_mode,
            "borrow_apy": str(self.borrow_apy),
            "status": self.status,
            "message": self.message,
        }
