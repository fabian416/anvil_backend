"""News sentiment analysis service.

Analyzes cryptocurrency news articles for sentiment.
Uses real RSS feeds from crypto news sources (no auth required).
"""

import logging
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.domain.common.datetime_utils import utc_now
from dataclasses import dataclass

from app.domain.value_objects.sentiment import (
    SentimentReading,
    SentimentSource,
)
from app.infrastructure.adapters.external.rss_news_client import RSSNewsClient

logger = logging.getLogger(__name__)


@dataclass
class NewsConfig:
    """Configuration for news sentiment analysis."""

    # Feature flags
    enabled: bool = True

    # News sources
    rss_feeds: List[str] = None
    crypto_news_apis: List[str] = None

    # API limits
    rate_limit: int = 60  # requests/hour
    max_articles_per_query: int = 50

    # Analysis thresholds
    min_article_length: int = 100  # characters
    high_confidence_threshold: float = 0.75

    # Cache settings
    cache_ttl_minutes: int = 30

    # Quality filters
    trusted_sources_only: bool = False
    min_source_authority: float = 0.5  # 0-1

    def __post_init__(self):
        """Initialize default news sources if not provided."""
        if self.rss_feeds is None:
            self.rss_feeds = [
                "https://cointelegraph.com/rss",
                "https://decrypt.co/feed",
                "https://cryptoslate.com/feed/",
                "https://theblock.co/rss",
                "https://coindesk.com/arc/outboundfeeds/rss/",
            ]

        if self.crypto_news_apis is None:
            self.crypto_news_apis = [
                "cryptocompare",
                "newsapi",
                "cryptopanic",
            ]


class NewsSentimentAnalyzer:
    """Analyzes news sentiment for cryptocurrency tokens.

    Uses RSS feeds and crypto news APIs to analyze:
    - Article headlines
    - Article content
    - Source authority
    - Publication patterns
    """

    def __init__(self, config: NewsConfig = None, rss_client: RSSNewsClient = None):
        """Initialize news sentiment analyzer.

        Args:
            config: Configuration for news analysis
            rss_client: RSS client (optional, creates one if not provided)
        """
        self.config = config or NewsConfig()
        self._rss_client = rss_client
        self._bullish_keywords = self._load_bullish_keywords()
        self._bearish_keywords = self._load_bearish_keywords()
        self._bullish_phrases = self._load_bullish_phrases()
        self._bearish_phrases = self._load_bearish_phrases()
        self._source_authority = self._load_source_authority()

    def _load_bullish_keywords(self) -> set:
        """Load bullish keywords for news analysis."""
        return {
            "surge",
            "rally",
            "gains",
            "growth",
            "adoption",
            "partnership",
            "integration",
            "upgrade",
            "launch",
            "breakthrough",
            "innovation",
            "institutional",
            "investment",
            "bullish",
            "positive",
            "optimistic",
            "outperform",
            "momentum",
            "breakthrough",
            "milestone",
            "expansion",
            "approval",
        }

    def _load_bearish_keywords(self) -> set:
        """Load bearish keywords for news analysis."""
        return {
            "crash",
            "plunge",
            "decline",
            "fall",
            "drop",
            "losses",
            "bearish",
            "negative",
            "concern",
            "warning",
            "risk",
            "vulnerability",
            "exploit",
            "hack",
            "breach",
            "scam",
            "fraud",
            "regulation",
            "ban",
            "crackdown",
            "investigation",
            "lawsuit",
        }

    def _load_bullish_phrases(self) -> set:
        """Load bullish multi-word phrases."""
        return {
            "all time high",
            "record high",
            "breaking out",
            "strong momentum",
            "institutional adoption",
            "positive outlook",
            "bullish trend",
            "major partnership",
            "technical upgrade",
            "network growth",
        }

    def _load_bearish_phrases(self) -> set:
        """Load bearish multi-word phrases."""
        return {
            "all time low",
            "breaking down",
            "negative outlook",
            "bearish trend",
            "regulatory pressure",
            "security breach",
            "major concern",
            "losing support",
            "market decline",
            "investor concern",
        }

    def _load_source_authority(self) -> Dict[str, float]:
        """Load authority scores for news sources.

        Returns:
            Dictionary mapping source domain to authority score (0-1)
        """
        return {
            "cointelegraph.com": 0.85,
            "coindesk.com": 0.90,
            "theblock.co": 0.88,
            "decrypt.co": 0.82,
            "cryptoslate.com": 0.75,
            "bloomberg.com": 0.95,
            "reuters.com": 0.95,
            "wsj.com": 0.93,
            "ft.com": 0.92,
            "unknown": 0.50,  # Default for unknown sources
        }

    async def analyze_token_sentiment(
        self, token_symbol: str, hours: int = 24
    ) -> SentimentReading:
        """Analyze news sentiment for a token.

        Args:
            token_symbol: Token symbol (e.g., "ETH")
            hours: Hours of historical data to analyze

        Returns:
            SentimentReading with news sentiment analysis

        Example:
            >>> analyzer = NewsSentimentAnalyzer()
            >>> sentiment = await analyzer.analyze_token_sentiment("ETH", hours=24)
            >>> print(f"ETH news sentiment: {sentiment.score}/100")
        """
        # In production, this would call news APIs and parse RSS feeds
        # For now, simulate with mock data
        articles = await self._fetch_articles(token_symbol, hours)

        if not articles:
            return self._create_neutral_reading(token_symbol)

        # Analyze articles
        scores = [self._analyze_article(article) for article in articles]

        # Calculate weighted average based on source authority
        weighted_score = self._calculate_weighted_sentiment(articles, scores)

        # Calculate confidence based on sample size and source quality
        confidence = self._calculate_confidence(articles, scores)

        return SentimentReading(
            source=SentimentSource.NEWS,
            score=weighted_score,
            confidence=confidence,
            timestamp=utc_now(),
            token_symbol=token_symbol,
            metadata={
                "article_count": len(articles),
                "time_period_hours": hours,
                "sources": len(set(a.get("source") for a in articles)),
                "avg_authority": sum(
                    self._source_authority.get(a.get("source", "unknown"), 0.5)
                    for a in articles
                )
                / len(articles)
                if articles
                else 0,
            },
        )

    async def _fetch_articles(
        self, token_symbol: str, hours: int
    ) -> List[Dict]:
        """Fetch news articles mentioning token.

        Uses real RSS feeds from crypto news sources.

        Args:
            token_symbol: Token symbol
            hours: Hours of history

        Returns:
            List of article dictionaries
        """
        # Map common symbols to full names for better matching
        token_names = {
            "ETH": "Ethereum",
            "BTC": "Bitcoin",
            "SOL": "Solana",
            "MATIC": "Polygon",
            "AVAX": "Avalanche",
            "ARB": "Arbitrum",
            "OP": "Optimism",
            "LINK": "Chainlink",
            "UNI": "Uniswap",
            "AAVE": "Aave",
        }
        token_name = token_names.get(token_symbol.upper(), token_symbol)

        try:
            # Create client if not provided
            client = self._rss_client or RSSNewsClient()
            should_close = self._rss_client is None

            try:
                # Fetch articles about the token
                articles = await client.get_token_news(
                    token_symbol=token_symbol,
                    token_name=token_name,
                    limit=self.config.max_articles_per_query,
                )

                # Filter by time window
                cutoff_time = utc_now() - timedelta(hours=hours)
                recent_articles = [
                    a for a in articles
                    if a.published.replace(tzinfo=None) > cutoff_time.replace(tzinfo=None)
                ]

                # Convert to dict format for analysis
                result = []
                for article in recent_articles:
                    content = article.description
                    # Filter by minimum length
                    if len(content) >= self.config.min_article_length:
                        result.append({
                            "title": article.title,
                            "content": content,
                            "source": article.source,
                            "published": article.published,
                            "url": article.link,
                            "categories": article.categories,
                        })

                logger.info(
                    f"Fetched {len(result)} news articles for {token_symbol} "
                    f"(from {len(articles)} total)"
                )

                return result

            finally:
                if should_close:
                    await client.close()

        except Exception as e:
            logger.warning(f"Error fetching news for {token_symbol}: {e}")
            # Return empty list on error - will create neutral reading
            return []

    def _analyze_article(self, article: Dict) -> float:
        """Analyze individual news article sentiment.

        Args:
            article: Article dictionary

        Returns:
            Sentiment score (0-100)
        """
        title = article["title"].lower()
        content = article.get("content", "").lower()
        combined_text = f"{title} {content}"

        score = 50.0  # Neutral baseline

        # Keyword analysis (weighted more heavily for news)
        bullish_count = sum(1 for kw in self._bullish_keywords if kw in combined_text)
        bearish_count = sum(1 for kw in self._bearish_keywords if kw in combined_text)

        # News keywords carry more weight (7 points per keyword)
        score += bullish_count * 7
        score -= bearish_count * 7

        # Phrase analysis (even stronger signal in news)
        bullish_phrase_count = sum(
            1 for phrase in self._bullish_phrases if phrase in combined_text
        )
        bearish_phrase_count = sum(
            1 for phrase in self._bearish_phrases if phrase in combined_text
        )

        score += bullish_phrase_count * 10
        score -= bearish_phrase_count * 10

        # Title sentiment carries extra weight (headlines matter)
        title_bullish = sum(1 for kw in self._bullish_keywords if kw in title)
        title_bearish = sum(1 for kw in self._bearish_keywords if kw in title)

        score += title_bullish * 3
        score -= title_bearish * 3

        # Question marks in headlines indicate uncertainty
        if "?" in title:
            score *= 0.92

        # Clamp to 0-100
        return max(0, min(100, score))

    def _calculate_weighted_sentiment(
        self, articles: List[Dict], scores: List[float]
    ) -> float:
        """Calculate weighted sentiment based on source authority.

        Args:
            articles: List of articles
            scores: Corresponding sentiment scores

        Returns:
            Weighted average sentiment score
        """
        if not articles:
            return 50.0

        total_weight = 0.0
        weighted_sum = 0.0

        for article, score in zip(articles, scores):
            # Get source authority
            source = article.get("source", "unknown")
            authority = self._source_authority.get(source, 0.5)

            # Weight by source authority
            weight = authority

            total_weight += weight
            weighted_sum += score * weight

        return weighted_sum / total_weight if total_weight > 0 else 50.0

    def _calculate_confidence(
        self, articles: List[Dict], scores: List[float]
    ) -> float:
        """Calculate confidence in sentiment analysis.

        Args:
            articles: List of articles
            scores: Corresponding sentiment scores

        Returns:
            Confidence score (0-1)
        """
        if not articles:
            return 0.0

        # Base confidence from sample size
        sample_confidence = min(len(articles) / 30, 1.0)  # Max at 30 articles

        # Consistency: how similar are the scores?
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            std_dev = variance**0.5
            consistency = 1.0 - (std_dev / 50)
        else:
            consistency = 0.5

        # Source authority boost
        avg_authority = sum(
            self._source_authority.get(a.get("source", "unknown"), 0.5)
            for a in articles
        ) / len(articles)
        authority_boost = avg_authority * 0.2

        # Combine factors
        confidence = (sample_confidence * 0.4) + (consistency * 0.4) + authority_boost

        return max(0.0, min(1.0, confidence))

    def _create_neutral_reading(self, token_symbol: str) -> SentimentReading:
        """Create neutral sentiment reading when no data available."""
        return SentimentReading(
            source=SentimentSource.NEWS,
            score=50.0,
            confidence=0.0,
            timestamp=utc_now(),
            token_symbol=token_symbol,
            metadata={
                "article_count": 0,
                "reason": "no_data",
            },
        )

    async def get_top_headlines(
        self, limit: int = 10
    ) -> List[Dict]:
        """Get top cryptocurrency news headlines.

        Args:
            limit: Maximum number of headlines to return

        Returns:
            List of top headlines

        Example:
            >>> analyzer = NewsSentimentAnalyzer()
            >>> headlines = await analyzer.get_top_headlines(limit=5)
        """
        # In production: aggregate from multiple news sources
        # For now, return simulated data
        headlines = [
            {
                "title": "Bitcoin Reaches New All-Time High",
                "source": "coindesk.com",
                "sentiment": 85.0,
                "published": utc_now() - timedelta(hours=1),
            },
            {
                "title": "Ethereum Network Sees Record Activity",
                "source": "cointelegraph.com",
                "sentiment": 78.5,
                "published": utc_now() - timedelta(hours=2),
            },
            {
                "title": "Regulatory Concerns Impact Crypto Markets",
                "source": "bloomberg.com",
                "sentiment": 35.0,
                "published": utc_now() - timedelta(hours=3),
            },
        ]

        return headlines[:limit]

    def get_source_authority(self, source: str) -> float:
        """Get authority score for news source.

        Args:
            source: Source domain (e.g., "coindesk.com")

        Returns:
            Authority score (0-1)

        Example:
            >>> analyzer = NewsSentimentAnalyzer()
            >>> authority = analyzer.get_source_authority("coindesk.com")
            >>> # Returns: 0.90 (high authority)
        """
        return self._source_authority.get(source, 0.5)
