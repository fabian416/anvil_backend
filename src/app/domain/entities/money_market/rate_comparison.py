"""
Money market rate comparison domain entity.

Logs every user rate comparison request for analytics and optimization.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

__slots__ = (
    "id",
    "user_id",
    "guest_session_id",
    "asset",
    "chain",
    "protocols_compared",
    "best_supply_protocol",
    "best_supply_apy",
    "best_borrow_protocol",
    "best_borrow_apy",
    "latency_ms",
    "language",
    "created_at",
)


@dataclass(slots=True, frozen=True)
class MoneyMarketRateComparison:
    """
    Domain entity representing a user's rate comparison request.

    Logs every comparison for analytics purposes to track:
    - Popular asset/chain combinations
    - Average response times
    - Best protocol recommendations
    - User engagement patterns

    Attributes:
        id: Unique identifier
        user_id: Reference to chat_users (nullable for guests)
        guest_session_id: Guest session identifier (nullable)
        asset: Asset symbol compared (USDC, USDT, DAI, WETH, WBTC)
        chain: Chain compared on (ethereum, arbitrum, polygon, etc.)
        protocols_compared: List of protocol comparison results (JSONB)
        best_supply_protocol: Protocol with best supply APY
        best_supply_apy: Best supply APY found (Decimal as string)
        best_borrow_protocol: Protocol with best borrow APY
        best_borrow_apy: Best borrow APY found (Decimal as string)
        latency_ms: Response time in milliseconds
        language: Response language (ISO code)
        created_at: Timestamp
    """

    id: UUID
    user_id: Optional[UUID]
    guest_session_id: Optional[str]
    asset: str
    chain: str
    protocols_compared: List[Dict[str, Any]]
    best_supply_protocol: str
    best_supply_apy: str
    best_borrow_protocol: str
    best_borrow_apy: str
    latency_ms: int
    language: str
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        # Must have either user_id OR guest_session_id (not both, not neither)
        if self.user_id is None and self.guest_session_id is None:
            raise ValueError(
                "Must provide either user_id or guest_session_id."
            )
        if self.user_id is not None and self.guest_session_id is not None:
            raise ValueError(
                "Cannot provide both user_id and guest_session_id. "
                "Use one or the other."
            )

        # Validate asset symbol
        if not self.asset or len(self.asset.strip()) == 0:
            raise ValueError("Asset symbol cannot be empty.")
        if not self.asset.isupper():
            raise ValueError(f"Asset symbol must be uppercase: {self.asset}")

        # Validate chain
        if not self.chain or len(self.chain.strip()) == 0:
            raise ValueError("Chain cannot be empty.")

        # Validate protocols_compared
        if not self.protocols_compared or len(self.protocols_compared) == 0:
            raise ValueError(
                "protocols_compared must contain at least one protocol."
            )

        # Validate best_supply_protocol
        if not self.best_supply_protocol or len(self.best_supply_protocol.strip()) == 0:
            raise ValueError("best_supply_protocol cannot be empty.")

        # Validate best_borrow_protocol
        if not self.best_borrow_protocol or len(self.best_borrow_protocol.strip()) == 0:
            raise ValueError("best_borrow_protocol cannot be empty.")

        # Validate latency_ms (must be positive)
        if self.latency_ms <= 0:
            raise ValueError(
                f"latency_ms must be positive. Got: {self.latency_ms}"
            )

        # Validate language (must be valid ISO code)
        valid_languages = ("en", "es", "pt", "zh", "ja", "ko", "fr", "de", "ru")
        if self.language not in valid_languages:
            raise ValueError(
                f"Invalid language: {self.language}. "
                f"Must be one of {valid_languages}."
            )

    @property
    def is_guest_comparison(self) -> bool:
        """Check if comparison was made by guest user."""
        return self.guest_session_id is not None

    @property
    def is_authenticated_comparison(self) -> bool:
        """Check if comparison was made by authenticated user."""
        return self.user_id is not None

    @property
    def comparison_count(self) -> int:
        """Get number of protocols compared."""
        return len(self.protocols_compared)

    @property
    def is_fast_response(self) -> bool:
        """Check if response was fast (<500ms)."""
        return self.latency_ms < 500

    @property
    def is_slow_response(self) -> bool:
        """Check if response was slow (>2000ms)."""
        return self.latency_ms > 2000

    @property
    def is_english(self) -> bool:
        """Check if response language is English."""
        return self.language == "en"

    @property
    def is_spanish(self) -> bool:
        """Check if response language is Spanish."""
        return self.language == "es"

    @property
    def is_portuguese(self) -> bool:
        """Check if response language is Portuguese."""
        return self.language == "pt"

    @property
    def is_chinese(self) -> bool:
        """Check if response language is Chinese."""
        return self.language == "zh"

    @property
    def latency_seconds(self) -> float:
        """Get latency in seconds."""
        return self.latency_ms / 1000.0

    @property
    def is_stablecoin(self) -> bool:
        """Check if asset is a stablecoin."""
        stablecoins = ("USDC", "USDT", "DAI", "BUSD", "FRAX", "LUSD")
        return self.asset in stablecoins

    @property
    def is_ethereum_mainnet(self) -> bool:
        """Check if chain is Ethereum mainnet."""
        return self.chain.lower() in ("ethereum", "mainnet", "eth")

    @property
    def is_layer2(self) -> bool:
        """Check if chain is a Layer 2 network."""
        layer2_chains = (
            "arbitrum",
            "optimism",
            "base",
            "polygon",
            "zksync",
            "scroll",
        )
        return self.chain.lower() in layer2_chains
