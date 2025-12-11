"""
GetCollectionStats Query.

Application query for retrieving collection market statistics.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.exceptions.nft import CollectionNotFoundError
from app.domain.ports.nft_marketplace_gateway import NFTMarketplaceGateway
from app.domain.value_objects.nft.collection_stats import CollectionStats


@dataclass
class GetCollectionStatsRequest:
    """Request parameters for GetCollectionStats query."""

    collection_slug: str


@dataclass
class CollectionStatsResponse:
    """Response for collection stats query."""

    stats: CollectionStats
    market_sentiment: str  # BULLISH, BEARISH, NEUTRAL
    floor_change_alert: str | None = None  # SIGNIFICANT_DROP, SIGNIFICANT_RISE


class GetCollectionStats:
    """
    Query to get collection statistics with market analysis.

    Analyzes sentiment based on 24h price change and alerts
    on significant floor price movements.
    """

    # Sentiment thresholds
    BULLISH_THRESHOLD = Decimal("10")  # >10% = bullish
    BEARISH_THRESHOLD = Decimal("-10")  # <-10% = bearish

    # Alert thresholds
    DROP_THRESHOLD = Decimal("-20")  # <-20% = significant drop
    RISE_THRESHOLD = Decimal("30")  # >30% = significant rise

    def __init__(self, gateway: NFTMarketplaceGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetCollectionStatsRequest) -> CollectionStatsResponse:
        """Execute query to get collection stats."""
        stats = await self._gateway.get_collection_stats(request.collection_slug)

        if not stats:
            raise CollectionNotFoundError(request.collection_slug)

        sentiment = self._analyze_sentiment(stats)
        alert = self._check_floor_alert(stats)

        return CollectionStatsResponse(
            stats=stats,
            market_sentiment=sentiment,
            floor_change_alert=alert,
        )

    def _analyze_sentiment(self, stats: CollectionStats) -> str:
        """Analyze market sentiment based on 24h change."""
        if stats.one_day_change > self.BULLISH_THRESHOLD:
            return "BULLISH"
        elif stats.one_day_change < self.BEARISH_THRESHOLD:
            return "BEARISH"
        return "NEUTRAL"

    def _check_floor_alert(self, stats: CollectionStats) -> str | None:
        """Check for significant floor price movements."""
        if stats.one_day_change < self.DROP_THRESHOLD:
            return "SIGNIFICANT_DROP"
        elif stats.one_day_change > self.RISE_THRESHOLD:
            return "SIGNIFICANT_RISE"
        return None
