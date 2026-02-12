"""
Asset Sentiment Provider port.

Provides optional Hunter-style sentiment for assets (e.g. USDC, ETH)
for use in money market and other workflow responses.
"""

from typing import Protocol


class AssetSentimentProvider(Protocol):
    """
    Provides best-effort sentiment for an asset symbol.

    Used to enrich money market (and other) responses with
    Hunter sentiment analysis. Returns None on failure or timeout.
    """

    async def get_sentiment(self, asset_symbol: str) -> dict | None:
        """
        Get aggregated sentiment for an asset.

        Args:
            asset_symbol: Token symbol (e.g. USDC, ETH, USD).

        Returns:
            Dict with score (0-100), classification (bullish/bearish/neutral),
            token_symbol; or None if unavailable.
        """
        ...
