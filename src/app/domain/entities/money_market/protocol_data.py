"""
Money market protocol data domain entity.

Stores cached protocol rate data with TTL-based cache invalidation.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

__slots__ = (
    "id",
    "protocol_id",
    "asset",
    "chain",
    "supply_apy",
    "borrow_apy_variable",
    "borrow_apy_stable",
    "total_supplied_usd",
    "total_borrowed_usd",
    "utilization_rate",
    "liquidity_available",
    "data_source",
    "valid_until",
    "created_at",
)


@dataclass(slots=True, frozen=True)
class MoneyMarketProtocolData:
    """
    Domain entity representing a money market protocol's cached rate data.

    Attributes:
        id: Unique identifier
        protocol_id: Protocol identifier ('aave_v3', 'compound_v3')
        asset: Asset symbol (USDC, USDT, DAI, WETH, WBTC)
        chain: Blockchain network (ethereum, arbitrum, polygon, etc.)
        supply_apy: Supply APY as Decimal (percentage)
        borrow_apy_variable: Variable borrow APY as Decimal
        borrow_apy_stable: Stable borrow APY as Decimal (optional, Aave only)
        total_supplied_usd: Total supplied in USD
        total_borrowed_usd: Total borrowed in USD
        utilization_rate: Protocol utilization rate (0-1)
        liquidity_available: Available liquidity in USD
        data_source: Source of data ('on_chain', 'api', 'graph', 'estimated')
        valid_until: Cache expiration timestamp
        created_at: Creation timestamp
    """

    id: UUID
    protocol_id: str
    asset: str
    chain: str
    supply_apy: Decimal
    borrow_apy_variable: Decimal
    borrow_apy_stable: Optional[Decimal]
    total_supplied_usd: Decimal
    total_borrowed_usd: Decimal
    utilization_rate: Decimal
    liquidity_available: Decimal
    data_source: str
    valid_until: datetime
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        # Validate protocol_id
        valid_protocols = ("aave_v3", "compound_v3")
        if self.protocol_id not in valid_protocols:
            raise ValueError(
                f"Invalid protocol_id: {self.protocol_id}. "
                f"Must be one of {valid_protocols}."
            )

        # Validate asset symbol
        if not self.asset or len(self.asset.strip()) == 0:
            raise ValueError("Asset symbol cannot be empty.")
        if not self.asset.isupper():
            raise ValueError(f"Asset symbol must be uppercase: {self.asset}")

        # Validate chain
        if not self.chain or len(self.chain.strip()) == 0:
            raise ValueError("Chain cannot be empty.")

        # Validate APY values (must be >= 0 and <= 100%)
        if self.supply_apy < Decimal("0") or self.supply_apy > Decimal("100"):
            raise ValueError(
                f"Invalid supply_apy: {self.supply_apy}. Must be between 0 and 100%."
            )
        if self.borrow_apy_variable < Decimal(
            "0"
        ) or self.borrow_apy_variable > Decimal("100"):
            raise ValueError(
                f"Invalid borrow_apy_variable: {self.borrow_apy_variable}. "
                "Must be between 0 and 100%."
            )
        if self.borrow_apy_stable is not None:
            if self.borrow_apy_stable < Decimal(
                "0"
            ) or self.borrow_apy_stable > Decimal("100"):
                raise ValueError(
                    f"Invalid borrow_apy_stable: {self.borrow_apy_stable}. "
                    "Must be between 0 and 100%."
                )

        # Validate utilization rate (must be between 0-1)
        if self.utilization_rate < Decimal("0") or self.utilization_rate > Decimal("1"):
            raise ValueError(
                f"Invalid utilization_rate: {self.utilization_rate}. "
                "Must be between 0 and 1."
            )

        # Validate USD values (must be >= 0)
        if self.total_supplied_usd < Decimal("0"):
            raise ValueError("total_supplied_usd cannot be negative.")
        if self.total_borrowed_usd < Decimal("0"):
            raise ValueError("total_borrowed_usd cannot be negative.")
        if self.liquidity_available < Decimal("0"):
            raise ValueError("liquidity_available cannot be negative.")

        # Validate data_source
        valid_sources = ("on_chain", "api", "graph", "estimated")
        if self.data_source not in valid_sources:
            raise ValueError(
                f"Invalid data_source: {self.data_source}. "
                f"Must be one of {valid_sources}."
            )

        # Validate valid_until is in the future
        if self.valid_until <= self.created_at:
            raise ValueError(
                "valid_until must be after created_at. "
                f"Got valid_until={self.valid_until}, created_at={self.created_at}."
            )

    @property
    def is_valid(self) -> bool:
        """Check if cached data is still valid (not expired)."""
        return datetime.now(timezone.utc) < self.valid_until

    @property
    def is_expired(self) -> bool:
        """Check if cached data has expired."""
        return not self.is_valid

    @property
    def is_real_data(self) -> bool:
        """Check if data comes from real on-chain sources."""
        return self.data_source in ("on_chain", "graph")

    @property
    def is_estimated(self) -> bool:
        """Check if data is estimated (not real on-chain data)."""
        return self.data_source == "estimated"

    @property
    def is_api_data(self) -> bool:
        """Check if data comes from external API."""
        return self.data_source == "api"

    @property
    def time_until_expiry(self) -> timedelta:
        """Calculate remaining time until cache expiration."""
        return self.valid_until - datetime.now(timezone.utc)

    @property
    def seconds_until_expiry(self) -> int:
        """Calculate remaining seconds until cache expiration."""
        delta = self.time_until_expiry
        return max(0, int(delta.total_seconds()))

    @property
    def is_aave(self) -> bool:
        """Check if protocol is Aave V3."""
        return self.protocol_id == "aave_v3"

    @property
    def is_compound(self) -> bool:
        """Check if protocol is Compound V3."""
        return self.protocol_id == "compound_v3"

    @property
    def has_stable_borrow(self) -> bool:
        """Check if protocol supports stable borrow rates (Aave only)."""
        return self.borrow_apy_stable is not None

    @property
    def utilization_percentage(self) -> Decimal:
        """Get utilization rate as percentage (0-100)."""
        return self.utilization_rate * Decimal("100")

    @property
    def is_high_utilization(self) -> bool:
        """Check if protocol has high utilization (>80%)."""
        return self.utilization_rate > Decimal("0.8")

    @property
    def is_low_liquidity(self) -> bool:
        """Check if protocol has low liquidity (<$1M)."""
        return self.liquidity_available < Decimal("1000000")
