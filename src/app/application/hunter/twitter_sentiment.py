"""Twitter sentiment analysis service.

Analyzes Twitter posts for cryptocurrency sentiment using NLP and ML.
Based on Hunter AI Bot's sentiment analysis module.
"""

import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.domain.value_objects.sentiment import (
    SentimentReading,
    SentimentSource,
)


@dataclass
class TwitterConfig:
    """Configuration for Twitter sentiment analysis."""

    # Feature flags
    enabled: bool = True

    # API limits
    rate_limit: int = 100  # requests/hour
    max_tweets_per_query: int = 100

    # Analysis thresholds
    min_engagement: int = 10  # Min likes/retweets
    high_confidence_threshold: float = 0.75
    verified_accounts_only: bool = False

    # Cache settings
    cache_ttl_minutes: int = 15

    # Quality filters
    min_followers: int = 100
    min_account_age_days: int = 30


class TwitterSentimentAnalyzer:
    """Analyzes Twitter sentiment for cryptocurrency tokens.

    Uses NLP techniques to extract sentiment from tweets:
    - Keyword analysis
    - Emoji sentiment
    - Engagement metrics
    - Influencer weighting
    """

    def __init__(self, config: TwitterConfig = None):
        """Initialize Twitter sentiment analyzer.

        Args:
            config: Configuration for Twitter analysis
        """
        self.config = config or TwitterConfig()
        self._bullish_keywords = self._load_bullish_keywords()
        self._bearish_keywords = self._load_bearish_keywords()
        self._bullish_emojis = {"🚀", "🌙", "💎", "🙌", "📈", "💰", "🔥", "⬆️"}
        self._bearish_emojis = {"📉", "⬇️", "💩", "🐻", "😢", "😭", "🔴"}

    def _load_bullish_keywords(self) -> set:
        """Load bullish keywords for sentiment analysis."""
        return {
            "moon",
            "mooning",
            "bullish",
            "pump",
            "pumping",
            "breakout",
            "rally",
            "surge",
            "rocket",
            "gains",
            "profit",
            "buy",
            "buying",
            "accumulate",
            "accumulating",
            "hodl",
            "hold",
            "diamond hands",
            "to the moon",
            "ath",
            "all time high",
            "green",
            "up",
            "rising",
            "explosive",
            "bullrun",
        }

    def _load_bearish_keywords(self) -> set:
        """Load bearish keywords for sentiment analysis."""
        return {
            "dump",
            "dumping",
            "bearish",
            "crash",
            "crashing",
            "falling",
            "drop",
            "dropping",
            "sell",
            "selling",
            "exit",
            "exiting",
            "red",
            "down",
            "paper hands",
            "fear",
            "fud",
            "panic",
            "liquidation",
            "liquidated",
            "rekt",
            "scam",
            "rug",
            "rugpull",
            "avoid",
        }

    async def analyze_token_sentiment(
        self, token_symbol: str, hours: int = 24
    ) -> SentimentReading:
        """Analyze Twitter sentiment for a token.

        Args:
            token_symbol: Token symbol (e.g., "ETH")
            hours: Hours of historical data to analyze

        Returns:
            SentimentReading with Twitter sentiment analysis

        Example:
            >>> analyzer = TwitterSentimentAnalyzer()
            >>> sentiment = await analyzer.analyze_token_sentiment("ETH", hours=24)
            >>> print(f"ETH Twitter sentiment: {sentiment.score}/100")
            >>> print(f"Classification: {sentiment.classification.value}")
        """
        # In production, this would call Twitter API
        # For now, simulate with mock data
        tweets = await self._fetch_tweets(token_symbol, hours)

        if not tweets:
            # No data available
            return self._create_neutral_reading(token_symbol)

        # Analyze tweets
        scores = [self._analyze_tweet(tweet) for tweet in tweets]

        # Calculate weighted average based on engagement
        weighted_score = self._calculate_weighted_sentiment(tweets, scores)

        # Calculate confidence based on sample size and consistency
        confidence = self._calculate_confidence(tweets, scores)

        return SentimentReading(
            source=SentimentSource.TWITTER,
            score=weighted_score,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            token_symbol=token_symbol,
            metadata={
                "tweet_count": len(tweets),
                "time_period_hours": hours,
                "verified_accounts": sum(1 for t in tweets if t.get("verified", False)),
                "total_engagement": sum(
                    t.get("likes", 0) + t.get("retweets", 0) for t in tweets
                ),
            },
        )

    async def _fetch_tweets(
        self, token_symbol: str, hours: int
    ) -> List[Dict]:
        """Fetch tweets mentioning token.

        In production, this would call Twitter API v2.
        For now, returns simulated data.

        Args:
            token_symbol: Token symbol
            hours: Hours of history

        Returns:
            List of tweet dictionaries
        """
        # Simulate Twitter API response
        # In production: use Twitter API v2 with bearer token
        # search_query = f"${token_symbol} OR #{token_symbol}"
        # tweets = twitter_api.search_recent_tweets(query=search_query, ...)

        # Simulated tweets for testing
        simulated_tweets = [
            {
                "text": f"${token_symbol} to the moon! 🚀🌙 Great project!",
                "likes": 150,
                "retweets": 45,
                "verified": True,
                "timestamp": datetime.utcnow() - timedelta(hours=1),
            },
            {
                "text": f"Bearish on ${token_symbol} right now. Selling my bags.",
                "likes": 30,
                "retweets": 8,
                "verified": False,
                "timestamp": datetime.utcnow() - timedelta(hours=3),
            },
            {
                "text": f"${token_symbol} looking strong! Accumulating more. 💎🙌",
                "likes": 200,
                "retweets": 67,
                "verified": True,
                "timestamp": datetime.utcnow() - timedelta(hours=5),
            },
            {
                "text": f"Just bought more ${token_symbol}. HODL! 🚀",
                "likes": 95,
                "retweets": 22,
                "verified": False,
                "timestamp": datetime.utcnow() - timedelta(hours=8),
            },
            {
                "text": f"${token_symbol} dump incoming. Be careful.",
                "likes": 45,
                "retweets": 12,
                "verified": False,
                "timestamp": datetime.utcnow() - timedelta(hours=12),
            },
        ]

        # Filter by engagement threshold
        filtered = [
            t
            for t in simulated_tweets
            if (t["likes"] + t["retweets"]) >= self.config.min_engagement
        ]

        return filtered

    def _analyze_tweet(self, tweet: Dict) -> float:
        """Analyze individual tweet sentiment.

        Args:
            tweet: Tweet dictionary

        Returns:
            Sentiment score (0-100)
        """
        text = tweet["text"].lower()
        score = 50.0  # Neutral baseline

        # Keyword analysis
        bullish_count = sum(1 for kw in self._bullish_keywords if kw in text)
        bearish_count = sum(1 for kw in self._bearish_keywords if kw in text)

        # Adjust score based on keywords (5 points per keyword)
        score += bullish_count * 5
        score -= bearish_count * 5

        # Emoji analysis
        for emoji in self._bullish_emojis:
            if emoji in tweet["text"]:
                score += 3

        for emoji in self._bearish_emojis:
            if emoji in tweet["text"]:
                score -= 3

        # Question marks indicate uncertainty (reduce confidence)
        if "?" in text:
            score *= 0.9

        # Exclamation marks indicate strong sentiment
        exclamations = text.count("!")
        if score > 50:
            score += exclamations * 2
        else:
            score -= exclamations * 2

        # Clamp to 0-100
        return max(0, min(100, score))

    def _calculate_weighted_sentiment(
        self, tweets: List[Dict], scores: List[float]
    ) -> float:
        """Calculate weighted sentiment based on engagement.

        Args:
            tweets: List of tweets
            scores: Corresponding sentiment scores

        Returns:
            Weighted average sentiment score
        """
        if not tweets:
            return 50.0

        total_weight = 0.0
        weighted_sum = 0.0

        for tweet, score in zip(tweets, scores):
            # Calculate weight based on engagement
            engagement = tweet["likes"] + tweet["retweets"]
            verified_boost = 2.0 if tweet.get("verified", False) else 1.0

            weight = engagement * verified_boost
            total_weight += weight
            weighted_sum += score * weight

        return weighted_sum / total_weight if total_weight > 0 else 50.0

    def _calculate_confidence(
        self, tweets: List[Dict], scores: List[float]
    ) -> float:
        """Calculate confidence in sentiment analysis.

        Args:
            tweets: List of tweets
            scores: Corresponding sentiment scores

        Returns:
            Confidence score (0-1)
        """
        if not tweets:
            return 0.0

        # Base confidence from sample size
        sample_confidence = min(len(tweets) / 100, 1.0)  # Max at 100 tweets

        # Consistency: how similar are the scores?
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            std_dev = variance**0.5
            consistency = 1.0 - (std_dev / 50)  # Normalize by max possible std dev
        else:
            consistency = 0.5

        # Verified account boost
        verified_ratio = sum(1 for t in tweets if t.get("verified", False)) / len(
            tweets
        )
        verified_boost = 0.2 * verified_ratio

        # Combine factors
        confidence = (sample_confidence * 0.5) + (consistency * 0.3) + verified_boost

        return max(0.0, min(1.0, confidence))

    def _create_neutral_reading(self, token_symbol: str) -> SentimentReading:
        """Create neutral sentiment reading when no data available.

        Args:
            token_symbol: Token symbol

        Returns:
            Neutral sentiment reading with low confidence
        """
        return SentimentReading(
            source=SentimentSource.TWITTER,
            score=50.0,
            confidence=0.0,
            timestamp=datetime.utcnow(),
            token_symbol=token_symbol,
            metadata={
                "tweet_count": 0,
                "reason": "no_data",
            },
        )

    async def get_trending_tokens(self, limit: int = 10) -> List[Dict]:
        """Get trending cryptocurrency tokens on Twitter.

        Args:
            limit: Maximum number of tokens to return

        Returns:
            List of trending tokens with mention counts

        Example:
            >>> analyzer = TwitterSentimentAnalyzer()
            >>> trending = await analyzer.get_trending_tokens(limit=5)
            >>> for token in trending:
            ...     print(f"{token['symbol']}: {token['mentions']} mentions")
        """
        # In production: analyze Twitter trends API
        # For now, return simulated data
        trending = [
            {"symbol": "BTC", "mentions": 12450, "sentiment": 68.5},
            {"symbol": "ETH", "mentions": 8920, "sentiment": 72.3},
            {"symbol": "SOL", "mentions": 5670, "sentiment": 65.8},
            {"symbol": "AVAX", "mentions": 3240, "sentiment": 71.2},
            {"symbol": "MATIC", "mentions": 2890, "sentiment": 58.9},
        ]

        return trending[:limit]
