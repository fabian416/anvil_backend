"""
Health Check Query for Lending Operations.

Defines the query pattern for health factor monitoring following CQRS principles.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from uuid import UUID


@dataclass(frozen=True)
class HealthCheckQuery:
    """
    Query to check user's lending health factor.

    Following CQRS pattern, this is the immutable input contract for the
    health check query. Queries represent read-only operations.

    Attributes:
        user_id: User's unique identifier (UUID)
        protocol: Lending protocol ("aave" - Morpho doesn't have health factor)
        chain: Blockchain network (ethereum, base, arbitrum, etc.)

    Example:
        >>> query = HealthCheckQuery(
        ...     user_id=UUID("..."),
        ...     protocol="aave",
        ...     chain="ethereum",
        ... )
    """

    user_id: UUID
    protocol: str  # "aave" (only Aave has health factor concept)
    chain: str

    def __post_init__(self) -> None:
        """
        Validate query invariants.

        Raises:
            ValueError: If query validation fails
        """
        # Validate protocol (only Aave has health factor)
        if self.protocol.lower() != "aave":
            raise ValueError(
                f"Health check only available for Aave protocol, got: {self.protocol}"
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
class PositionSummary:
    """
    Summary of a single lending position.

    Attributes:
        asset: Asset symbol (e.g., "USDC", "ETH")
        type: Position type ("supply" or "borrow")
        amount: Amount in asset units
        amount_usd: Amount in USD
        apy: Annual percentage yield
        is_collateral: Whether asset is used as collateral (supplies only)
    """

    asset: str
    type: str  # "supply" or "borrow"
    amount: Decimal
    amount_usd: Decimal
    apy: Decimal
    is_collateral: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "asset": self.asset,
            "type": self.type,
            "amount": str(self.amount),
            "amount_usd": str(self.amount_usd),
            "apy": str(self.apy),
            "is_collateral": self.is_collateral,
        }


@dataclass(frozen=True)
class HealthCheckResult:
    """
    Result of health check query.

    Contains comprehensive health factor analysis and position details.

    Attributes:
        current_hf: Current health factor
        level: Risk level (SAFE, CAUTION, DANGER, CRITICAL, LIQUIDATABLE)
        emoji: Emoji representing risk level (✅, ⚠️, 🔶, 🔴, ❌)
        color: Color code for UI (#00CC66, #FFB84D, #FF6B35, #DC143C, #8B0000)
        positions: List of all positions (supplies and borrows)
        total_collateral_usd: Total collateral value in USD
        total_debt_usd: Total debt value in USD
        available_to_borrow_usd: Additional borrowing capacity in USD
        liquidation_threshold: Weighted average liquidation threshold
        liquidation_price: Price at which liquidation occurs (if applicable)
        warning_message: Human-readable health factor warning
        recommendations: List of recommended actions
        protocol: Protocol ("aave")
        chain: Blockchain network

    Example:
        >>> result = HealthCheckResult(
        ...     current_hf=Decimal("2.5"),
        ...     level="SAFE",
        ...     emoji="✅",
        ...     color="#00CC66",
        ...     positions=[...],
        ...     total_collateral_usd=Decimal("5000.00"),
        ...     total_debt_usd=Decimal("2000.00"),
        ...     available_to_borrow_usd=Decimal("1000.00"),
        ...     liquidation_threshold=Decimal("0.825"),
        ...     liquidation_price=Decimal("3200.50"),
        ...     warning_message="✅ SAFE - Your position is well-collateralized",
        ...     recommendations=[],
        ...     protocol="aave",
        ...     chain="ethereum",
        ... )
    """

    current_hf: Decimal
    level: str
    emoji: str
    color: str
    positions: List[PositionSummary]
    total_collateral_usd: Decimal
    total_debt_usd: Decimal
    available_to_borrow_usd: Decimal
    liquidation_threshold: Decimal
    liquidation_price: Optional[Decimal]
    warning_message: str
    recommendations: List[str]
    protocol: str
    chain: str

    def to_dict(self) -> dict:
        """
        Convert result to dictionary for JSON serialization.

        Returns:
            Dictionary representation of result
        """
        return {
            "health_factor": {
                "value": str(self.current_hf)
                if self.current_hf != Decimal("inf")
                else "infinity",
                "level": self.level,
                "emoji": self.emoji,
                "color": self.color,
                "warning": self.warning_message,
            },
            "positions": [pos.to_dict() for pos in self.positions],
            "summary": {
                "total_collateral_usd": str(self.total_collateral_usd),
                "total_debt_usd": str(self.total_debt_usd),
                "available_to_borrow_usd": str(self.available_to_borrow_usd),
                "liquidation_threshold": str(self.liquidation_threshold),
                "liquidation_price": str(self.liquidation_price)
                if self.liquidation_price
                else None,
            },
            "recommendations": self.recommendations,
            "protocol": self.protocol,
            "chain": self.chain,
        }
