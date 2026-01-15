"""User portfolio domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass
class ProtocolExposure:
    """User's exposure to a specific protocol."""

    protocol_id: UUID
    protocol_name: str
    value_usd: Decimal
    percentage: float  # Of total portfolio
    chain: str
    position_type: str  # supply/borrow/stake/lp
    entry_date: datetime
    current_apy: Optional[float] = None
    risk_score: Optional[float] = None


@dataclass
class UserPortfolio:
    """User's DeFi portfolio with protocol exposures."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default=None)
    protocols: List[ProtocolExposure] = field(default_factory=list)
    chains: List[str] = field(default_factory=list)
    total_value_usd: Decimal = field(default=Decimal("0"))
    risk_profile: str = "moderate"  # conservative/moderate/aggressive
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_exposure(self, exposure: ProtocolExposure) -> None:
        """Add protocol exposure to portfolio."""
        self.protocols.append(exposure)
        self._recalculate()

    def remove_exposure(self, protocol_id: UUID) -> bool:
        """Remove protocol exposure from portfolio."""
        initial_len = len(self.protocols)
        self.protocols = [p for p in self.protocols if p.protocol_id != protocol_id]
        if len(self.protocols) < initial_len:
            self._recalculate()
            return True
        return False

    def get_exposure(self, protocol_id: UUID) -> Optional[ProtocolExposure]:
        """Get exposure for a specific protocol."""
        for exposure in self.protocols:
            if exposure.protocol_id == protocol_id:
                return exposure
        return None

    def _recalculate(self) -> None:
        """Recalculate total value and percentages."""
        self.total_value_usd = sum(p.value_usd for p in self.protocols)

        # Update percentages
        if self.total_value_usd > 0:
            for protocol in self.protocols:
                protocol.percentage = float(
                    (protocol.value_usd / self.total_value_usd) * 100
                )

        # Update chains
        self.chains = list({p.chain for p in self.protocols})
        self.updated_at = datetime.now(UTC)

    def get_chain_allocation(self) -> dict[str, Decimal]:
        """Get portfolio allocation by chain."""
        allocation = {}
        for protocol in self.protocols:
            if protocol.chain not in allocation:
                allocation[protocol.chain] = Decimal("0")
            allocation[protocol.chain] += protocol.value_usd
        return allocation

    def get_position_type_allocation(self) -> dict[str, Decimal]:
        """Get portfolio allocation by position type."""
        allocation = {}
        for protocol in self.protocols:
            if protocol.position_type not in allocation:
                allocation[protocol.position_type] = Decimal("0")
            allocation[protocol.position_type] += protocol.value_usd
        return allocation
