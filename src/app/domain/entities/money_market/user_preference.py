"""
Money market user preference domain entity.

Stores user-specific rate alert preferences and notification settings.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

__slots__ = (
    "id",
    "user_id",
    "enable_rate_alerts",
    "alert_threshold_apy_change",
    "watched_assets",
    "watched_chains",
    "preferred_protocol",
    "notification_enabled",
    "created_at",
    "updated_at",
)


@dataclass(slots=True, frozen=True)
class MoneyMarketUserPreference:
    """
    Domain entity representing user's money market preferences.

    Attributes:
        id: Unique identifier
        user_id: Reference to chat_users (unique constraint)
        enable_rate_alerts: Enable rate change notifications
        alert_threshold_apy_change: APY change threshold for alerts (Decimal, percentage)
        watched_assets: List of assets to watch (JSONB array)
        watched_chains: List of chains to watch (JSONB array)
        preferred_protocol: Preferred protocol ('aave_v3' or 'compound_v3')
        notification_enabled: Enable notifications
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID
    user_id: UUID
    enable_rate_alerts: bool
    alert_threshold_apy_change: Decimal
    watched_assets: List[str]
    watched_chains: List[str]
    preferred_protocol: Optional[str]
    notification_enabled: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        # Validate alert_threshold_apy_change (must be between 0.01% and 10%)
        if self.alert_threshold_apy_change < Decimal(
            "0.01"
        ) or self.alert_threshold_apy_change > Decimal("10.0"):
            raise ValueError(
                f"Invalid alert_threshold_apy_change: {self.alert_threshold_apy_change}. "
                "Must be between 0.01% and 10%."
            )

        # Validate watched_assets (must be uppercase if provided)
        for asset in self.watched_assets:
            if not asset or len(asset.strip()) == 0:
                raise ValueError("Watched asset cannot be empty.")
            if not asset.isupper():
                raise ValueError(f"Watched asset must be uppercase: {asset}")

        # Validate watched_chains (must be lowercase if provided)
        for chain in self.watched_chains:
            if not chain or len(chain.strip()) == 0:
                raise ValueError("Watched chain cannot be empty.")
            if not chain.islower():
                raise ValueError(f"Watched chain must be lowercase: {chain}")

        # Validate preferred_protocol (if provided)
        if self.preferred_protocol is not None:
            valid_protocols = ("aave_v3", "compound_v3")
            if self.preferred_protocol not in valid_protocols:
                raise ValueError(
                    f"Invalid preferred_protocol: {self.preferred_protocol}. "
                    f"Must be one of {valid_protocols}."
                )

    @property
    def has_rate_alerts(self) -> bool:
        """Check if rate alerts are enabled."""
        return self.enable_rate_alerts

    @property
    def should_notify(self) -> bool:
        """Check if notifications are enabled."""
        return self.notification_enabled

    @property
    def should_send_alerts(self) -> bool:
        """Check if user should receive alerts (both flags enabled)."""
        return self.enable_rate_alerts and self.notification_enabled

    @property
    def is_watching_assets(self) -> bool:
        """Check if user is watching any assets."""
        return len(self.watched_assets) > 0

    @property
    def is_watching_chains(self) -> bool:
        """Check if user is watching any chains."""
        return len(self.watched_chains) > 0

    @property
    def has_preferred_protocol(self) -> bool:
        """Check if user has set a preferred protocol."""
        return self.preferred_protocol is not None

    @property
    def prefers_aave(self) -> bool:
        """Check if user prefers Aave V3."""
        return self.preferred_protocol == "aave_v3"

    @property
    def prefers_compound(self) -> bool:
        """Check if user prefers Compound V3."""
        return self.preferred_protocol == "compound_v3"

    @property
    def watched_asset_count(self) -> int:
        """Get number of watched assets."""
        return len(self.watched_assets)

    @property
    def watched_chain_count(self) -> int:
        """Get number of watched chains."""
        return len(self.watched_chains)

    @property
    def alert_threshold_percentage(self) -> str:
        """Get alert threshold as formatted percentage string."""
        return f"{self.alert_threshold_apy_change:.2f}%"

    @property
    def is_sensitive_to_changes(self) -> bool:
        """Check if user has low alert threshold (<0.5%)."""
        return self.alert_threshold_apy_change < Decimal("0.5")

    @property
    def is_watching_stablecoins(self) -> bool:
        """Check if user is watching any stablecoins."""
        stablecoins = ("USDC", "USDT", "DAI", "BUSD", "FRAX", "LUSD")
        return any(asset in stablecoins for asset in self.watched_assets)

    @property
    def is_watching_ethereum(self) -> bool:
        """Check if user is watching Ethereum mainnet."""
        ethereum_names = ("ethereum", "mainnet", "eth")
        return any(chain in ethereum_names for chain in self.watched_chains)

    @property
    def is_watching_layer2(self) -> bool:
        """Check if user is watching any Layer 2 chains."""
        layer2_chains = (
            "arbitrum",
            "optimism",
            "base",
            "polygon",
            "zksync",
            "scroll",
        )
        return any(chain in layer2_chains for chain in self.watched_chains)

    def is_watching_asset(self, asset: str) -> bool:
        """Check if user is watching a specific asset."""
        return asset.upper() in self.watched_assets

    def is_watching_chain(self, chain: str) -> bool:
        """Check if user is watching a specific chain."""
        return chain.lower() in self.watched_chains

    def should_alert_for_change(self, apy_change_percent: Decimal) -> bool:
        """
        Check if APY change exceeds user's alert threshold.

        Args:
            apy_change_percent: Absolute value of APY change percentage

        Returns:
            True if change exceeds threshold
        """
        return abs(apy_change_percent) >= self.alert_threshold_apy_change
