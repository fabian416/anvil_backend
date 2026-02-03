"""
Money market alert domain entity.

Stores rate change alerts triggered by user preferences.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

__slots__ = (
    "id",
    "user_id",
    "alert_type",
    "protocol",
    "asset",
    "chain",
    "previous_apy",
    "new_apy",
    "apy_change_percent",
    "severity",
    "message",
    "is_read",
    "notification_sent",
    "sent_at",
    "created_at",
)


@dataclass(slots=True, frozen=True)
class MoneyMarketAlert:
    """
    Domain entity representing a rate change alert.

    Triggered when monitored rate changes exceed user's threshold.

    Attributes:
        id: Unique identifier
        user_id: Reference to chat_users
        alert_type: Type of alert ('rate_increase', 'rate_decrease', 'new_best_rate')
        protocol: Protocol name ('aave_v3', 'compound_v3')
        asset: Asset symbol (USDC, USDT, DAI, WETH, WBTC)
        chain: Blockchain network (ethereum, arbitrum, polygon, etc.)
        previous_apy: Previous APY value
        new_apy: New APY value
        apy_change_percent: Percentage change (can be negative)
        severity: Alert severity ('info', 'warning')
        message: Alert message
        is_read: Whether alert was read
        notification_sent: Whether notification was sent
        sent_at: Notification sent timestamp
        created_at: Creation timestamp
    """

    id: UUID
    user_id: UUID
    alert_type: str
    protocol: str
    asset: str
    chain: str
    previous_apy: Decimal
    new_apy: Decimal
    apy_change_percent: Decimal
    severity: str
    message: str
    is_read: bool
    notification_sent: bool
    sent_at: Optional[datetime]
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        # Validate alert_type
        valid_types = ("rate_increase", "rate_decrease", "new_best_rate")
        if self.alert_type not in valid_types:
            raise ValueError(
                f"Invalid alert_type: {self.alert_type}. Must be one of {valid_types}."
            )

        # Validate protocol
        valid_protocols = ("aave_v3", "compound_v3")
        if self.protocol not in valid_protocols:
            raise ValueError(
                f"Invalid protocol: {self.protocol}. Must be one of {valid_protocols}."
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
        if self.previous_apy < Decimal("0") or self.previous_apy > Decimal("100"):
            raise ValueError(
                f"Invalid previous_apy: {self.previous_apy}. "
                "Must be between 0 and 100%."
            )
        if self.new_apy < Decimal("0") or self.new_apy > Decimal("100"):
            raise ValueError(
                f"Invalid new_apy: {self.new_apy}. Must be between 0 and 100%."
            )

        # Validate apy_change_percent matches calculation
        # Allow small floating point differences (0.001%)
        expected_change = (
            (self.new_apy - self.previous_apy) / self.previous_apy
        ) * Decimal("100")
        diff = abs(self.apy_change_percent - expected_change)
        if diff > Decimal("0.001"):
            raise ValueError(
                f"apy_change_percent mismatch. "
                f"Expected {expected_change:.4f}%, got {self.apy_change_percent:.4f}%. "
                f"Difference: {diff:.6f}%"
            )

        # Validate severity
        valid_severities = ("info", "warning")
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity: {self.severity}. Must be one of {valid_severities}."
            )

        # Validate message
        if not self.message or len(self.message.strip()) == 0:
            raise ValueError("Alert message cannot be empty.")

        # Validate notification logic
        if self.notification_sent and self.sent_at is None:
            raise ValueError(
                "notification_sent is True but sent_at is None. "
                "Must provide sent_at timestamp when notification is sent."
            )

    @property
    def is_unread(self) -> bool:
        """Check if alert is unread."""
        return not self.is_read

    @property
    def is_info(self) -> bool:
        """Check if alert is informational."""
        return self.severity == "info"

    @property
    def is_warning(self) -> bool:
        """Check if alert is a warning."""
        return self.severity == "warning"

    @property
    def was_notified(self) -> bool:
        """Check if notification was sent."""
        return self.notification_sent

    @property
    def was_not_notified(self) -> bool:
        """Check if notification was not sent."""
        return not self.notification_sent

    @property
    def apy_increased(self) -> bool:
        """Check if APY went up."""
        return self.new_apy > self.previous_apy

    @property
    def apy_decreased(self) -> bool:
        """Check if APY went down."""
        return self.new_apy < self.previous_apy

    @property
    def is_significant(self) -> bool:
        """Check if change is significant (>1%)."""
        return abs(self.apy_change_percent) > Decimal("1.0")

    @property
    def is_major_change(self) -> bool:
        """Check if change is major (>5%)."""
        return abs(self.apy_change_percent) > Decimal("5.0")

    @property
    def is_rate_increase(self) -> bool:
        """Check if alert type is rate_increase."""
        return self.alert_type == "rate_increase"

    @property
    def is_rate_decrease(self) -> bool:
        """Check if alert type is rate_decrease."""
        return self.alert_type == "rate_decrease"

    @property
    def is_new_best_rate(self) -> bool:
        """Check if alert type is new_best_rate."""
        return self.alert_type == "new_best_rate"

    @property
    def is_aave(self) -> bool:
        """Check if protocol is Aave V3."""
        return self.protocol == "aave_v3"

    @property
    def is_compound(self) -> bool:
        """Check if protocol is Compound V3."""
        return self.protocol == "compound_v3"

    @property
    def apy_change_absolute(self) -> Decimal:
        """Get absolute APY change value."""
        return abs(self.new_apy - self.previous_apy)

    @property
    def formatted_change(self) -> str:
        """Get formatted change string with +/- sign."""
        sign = "+" if self.apy_increased else ""
        return f"{sign}{self.apy_change_percent:.2f}%"

    @property
    def is_stablecoin(self) -> bool:
        """Check if alert is for a stablecoin."""
        stablecoins = ("USDC", "USDT", "DAI", "BUSD", "FRAX", "LUSD")
        return self.asset in stablecoins

    @property
    def is_ethereum_mainnet(self) -> bool:
        """Check if alert is for Ethereum mainnet."""
        return self.chain.lower() in ("ethereum", "mainnet", "eth")

    @property
    def is_layer2(self) -> bool:
        """Check if alert is for a Layer 2 network."""
        layer2_chains = (
            "arbitrum",
            "optimism",
            "base",
            "polygon",
            "zksync",
            "scroll",
        )
        return self.chain.lower() in layer2_chains

    @property
    def age_hours(self) -> float:
        """Get alert age in hours."""
        delta = datetime.utcnow() - self.created_at
        return delta.total_seconds() / 3600.0

    @property
    def is_recent(self) -> bool:
        """Check if alert is recent (<24 hours old)."""
        return self.age_hours < 24.0

    @property
    def is_old(self) -> bool:
        """Check if alert is old (>7 days old)."""
        return self.age_hours > (7 * 24.0)
