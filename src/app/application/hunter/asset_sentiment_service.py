"""
Asset sentiment service for workflow enrichment.

Implements AssetSentimentProvider using Hunter news sentiment (and optional
aggregation). Best-effort, non-blocking; returns None on failure or timeout.
"""

import asyncio
import logging
from typing import Any

from app.application.hunter.news_sentiment import (
    NewsConfig,
    NewsSentimentAnalyzer,
)
from app.application.hunter.sentiment_aggregator import SentimentAggregator

logger = logging.getLogger(__name__)

# Map display symbols to news-friendly token for sentiment
ASSET_TO_SENTIMENT_SYMBOL = {
    "USD": "USDC",
    "USDC": "USDC",
    "USDT": "USDT",
    "DAI": "DAI",
    "ETH": "ETH",
    "WETH": "ETH",
    "BTC": "BTC",
    "WBTC": "BTC",
}


class AssetSentimentService:
    """
    Best-effort sentiment for assets (USDC, ETH, etc.) for money market enrichment.

    Uses news sentiment only by default (fast, no social auth). Returns None
    on any failure so workflows degrade gracefully.
    """

    def __init__(self, timeout_seconds: float = 5.0):
        self._timeout = timeout_seconds
        self._news = NewsSentimentAnalyzer(NewsConfig(enabled=True))
        self._aggregator = SentimentAggregator()

    async def get_sentiment(self, asset_symbol: str) -> dict[str, Any] | None:
        """
        Get aggregated sentiment for an asset (best-effort).

        Args:
            asset_symbol: Token symbol (e.g. USDC, ETH, USD).

        Returns:
            Dict with score (0-100), classification (bullish/bearish/neutral),
            token_symbol; or None if unavailable.
        """
        symbol = (asset_symbol or "").strip().upper() or "USDC"
        lookup = ASSET_TO_SENTIMENT_SYMBOL.get(symbol, symbol)
        try:
            return await asyncio.wait_for(
                self._fetch_sentiment(lookup),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            logger.debug(
                "[AssetSentiment] Timeout for %s (%.1fs)", symbol, self._timeout
            )
            return None
        except Exception as e:
            logger.debug("[AssetSentiment] Error for %s: %s", symbol, e)
            return None

    async def _fetch_sentiment(self, token_symbol: str) -> dict[str, Any] | None:
        """Fetch news sentiment and return simple dict."""
        try:
            reading = await self._news.analyze_token_sentiment(
                token_symbol, hours=24
            )
        except Exception as e:
            logger.debug(
                "[AssetSentiment] News analysis failed for %s: %s",
                token_symbol,
                e,
            )
            return None
        aggregated = self._aggregator.aggregate([reading], token_symbol)
        score = aggregated.overall_score
        classification = self._score_to_classification(score)
        interpretation = self._score_to_interpretation(score)
        confidence = getattr(aggregated, "overall_confidence", None)
        return {
            "score": round(score, 1),
            "classification": classification,
            "token_symbol": token_symbol,
            "interpretation": interpretation,
            "confidence": round(confidence, 2) if confidence is not None else None,
            "time_horizon": "24h",
            "source": "news",
        }

    @staticmethod
    def _score_to_classification(score: float) -> str:
        """Map 0-100 score to bullish/bearish/neutral."""
        if score >= 60:
            return "bullish"
        if score <= 40:
            return "bearish"
        return "neutral"

    @staticmethod
    def _score_to_interpretation(score: float) -> str:
        """
        Plain-language interpretation for new and mid-level traders.

        Enterprise-grade: avoids jargon, clear for decision context.
        """
        if score >= 80:
            return "strongly positive"
        if score >= 60:
            return "moderately positive"
        if score >= 40:
            return "neutral"
        if score >= 20:
            return "moderately negative"
        return "strongly negative"
