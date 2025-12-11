"""
Portfolio Snapshot and Token Holding domain entities.

These entities represent a point-in-time capture of a wallet's holdings,
including native tokens and ERC-20 tokens with their USD values.

Designed to work with the transaction confirmation worker to automatically
capture snapshots when transactions are confirmed on-chain.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from app.domain.entities.base import Entity
from app.domain.entities.wallet import WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.value_objects.base import ValueObject
from app.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, repr=False)
class PortfolioSnapshotId(ValueObject):
    """Value object for portfolio snapshot ID."""

    value: int


@dataclass(frozen=True, repr=False)
class TokenHoldingId(ValueObject):
    """Value object for token holding ID."""

    value: int


@dataclass
class TokenHolding:
    """
    Represents a single token holding within a portfolio snapshot.

    This can be a native token (ETH, MATIC, etc.) or an ERC-20 token.
    When token_address is None, it represents the native token of the chain.
    """

    id_: TokenHoldingId
    snapshot_id: PortfolioSnapshotId
    token_address: str | None  # None for native token
    symbol: str
    name: str
    decimals: int
    amount: Decimal  # Raw amount in token units
    usd_value: Decimal | None  # USD value (None if price unavailable)
    usd_price: Decimal | None  # Price per token in USD
    percentage: float = 0.0  # Percentage of total portfolio

    @classmethod
    def create_native(
        cls,
        snapshot_id: PortfolioSnapshotId,
        chain: ChainType,
        amount: Decimal,
        usd_value: Decimal | None = None,
        usd_price: Decimal | None = None,
    ) -> "TokenHolding":
        """Create a native token holding."""
        native_symbols = {
            ChainType.ETHEREUM: ("ETH", "Ethereum"),
            ChainType.BASE: ("ETH", "Ethereum"),
            ChainType.ARBITRUM: ("ETH", "Ethereum"),
            ChainType.OPTIMISM: ("ETH", "Ethereum"),
            ChainType.POLYGON: ("MATIC", "Polygon"),
        }
        symbol, name = native_symbols.get(chain, ("ETH", "Ethereum"))

        return cls(
            id_=TokenHoldingId(0),  # ID assigned by DB
            snapshot_id=snapshot_id,
            token_address=None,
            symbol=symbol,
            name=name,
            decimals=18,
            amount=amount,
            usd_value=usd_value,
            usd_price=usd_price,
        )

    @classmethod
    def create_erc20(
        cls,
        snapshot_id: PortfolioSnapshotId,
        token_address: str,
        symbol: str,
        name: str,
        decimals: int,
        amount: Decimal,
        usd_value: Decimal | None = None,
        usd_price: Decimal | None = None,
    ) -> "TokenHolding":
        """Create an ERC-20 token holding."""
        return cls(
            id_=TokenHoldingId(0),  # ID assigned by DB
            snapshot_id=snapshot_id,
            token_address=token_address.lower(),
            symbol=symbol,
            name=name,
            decimals=decimals,
            amount=amount,
            usd_value=usd_value,
            usd_price=usd_price,
        )


@dataclass(eq=False, kw_only=True)
class PortfolioSnapshot(Entity[PortfolioSnapshotId]):
    """
    Represents a point-in-time snapshot of a wallet's portfolio.

    This captures:
    - Total USD value of all holdings
    - Individual token holdings with amounts and values
    - Chain information for multi-chain portfolios

    Snapshots are created:
    - On-demand when user requests portfolio data
    - Automatically when transactions are confirmed
    """

    wallet_id: WalletId
    chain: ChainType
    total_usd: Decimal
    native_balance: Decimal
    native_usd_value: Decimal | None
    captured_at: datetime
    created_at: CreatedAt
    holdings: list[TokenHolding] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        wallet_id: WalletId,
        chain: ChainType,
        native_balance: Decimal,
        native_usd_value: Decimal | None = None,
    ) -> "PortfolioSnapshot":
        """
        Create a new portfolio snapshot.

        Args:
            wallet_id: The wallet this snapshot belongs to.
            chain: The blockchain network.
            native_balance: Native token balance.
            native_usd_value: USD value of native balance.

        Returns:
            A new PortfolioSnapshot instance.
        """
        now = datetime.now(UTC)
        return cls(
            id_=PortfolioSnapshotId(0),  # ID assigned by DB
            wallet_id=wallet_id,
            chain=chain,
            total_usd=native_usd_value or Decimal("0"),
            native_balance=native_balance,
            native_usd_value=native_usd_value,
            captured_at=now,
            created_at=CreatedAt(now),
            holdings=[],
        )

    def add_holding(self, holding: TokenHolding) -> None:
        """Add a token holding to this snapshot."""
        self.holdings.append(holding)
        self._recalculate_totals()

    def _recalculate_totals(self) -> None:
        """Recalculate total USD and percentages."""
        # Calculate total from all holdings
        total = self.native_usd_value or Decimal("0")
        for holding in self.holdings:
            if holding.usd_value is not None:
                total += holding.usd_value

        self.total_usd = total

        # Update percentages
        if self.total_usd > 0:
            for holding in self.holdings:
                if holding.usd_value is not None:
                    holding.percentage = float(
                        (holding.usd_value / self.total_usd) * 100
                    )

    def get_holding_by_symbol(self, symbol: str) -> TokenHolding | None:
        """Get a specific token holding by symbol."""
        for holding in self.holdings:
            if holding.symbol.upper() == symbol.upper():
                return holding
        return None

    def get_holding_by_address(self, token_address: str) -> TokenHolding | None:
        """Get a specific token holding by address."""
        address_lower = token_address.lower()
        for holding in self.holdings:
            if holding.token_address and holding.token_address.lower() == address_lower:
                return holding
        return None

    @property
    def token_count(self) -> int:
        """Number of token holdings (excluding native)."""
        return len(self.holdings)

    @property
    def has_value(self) -> bool:
        """Check if portfolio has any USD value."""
        return self.total_usd > 0
