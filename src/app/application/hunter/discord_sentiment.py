"""Discord sentiment analysis service.

Analyzes Discord server messages for cryptocurrency sentiment.
Based on Hunter AI Bot's Discord integration.
"""

import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.domain.common.datetime_utils import utc_now
from dataclasses import dataclass

from app.domain.value_objects.sentiment import (
    SentimentReading,
    SentimentSource,
)


@dataclass
class DiscordConfig:
    """Configuration for Discord sentiment analysis."""

    # Feature flags
    enabled: bool = True

    # API limits
    rate_limit: int = 300  # requests/hour
    max_messages_per_query: int = 500

    # Servers to monitor
    target_servers: List[str] = None

    # Analysis thresholds
    min_reactions: int = 3  # Min message reactions
    high_confidence_threshold: float = 0.75

    # Cache settings
    cache_ttl_minutes: int = 10  # More frequent for real-time chat

    # Quality filters
    min_message_length: int = 10
    bot_filter: bool = True  # Filter out bot messages

    def __post_init__(self):
        """Initialize default servers if not provided."""
        if self.target_servers is None:
            self.target_servers = [
                "ethereum",
                "defi",
                "uniswap",
                "aave",
                "compound",
            ]


class DiscordSentimentAnalyzer:
    """Analyzes Discord sentiment for cryptocurrency tokens.

    Uses Discord API to analyze messages from crypto Discord servers:
    - Message content
    - Reaction counts and types
    - User activity patterns
    - Channel-specific sentiment
    """

    def __init__(self, config: DiscordConfig = None):
        """Initialize Discord sentiment analyzer.

        Args:
            config: Configuration for Discord analysis
        """
        self.config = config or DiscordConfig()
        self._bullish_keywords = self._load_bullish_keywords()
        self._bearish_keywords = self._load_bearish_keywords()
        self._positive_reactions = {"🚀", "👍", "💎", "🔥", "⬆️", "✅", "💰", "🌙"}
        self._negative_reactions = {"👎", "📉", "⬇️", "❌", "💩", "😢"}

    def _load_bullish_keywords(self) -> set:
        """Load bullish keywords for sentiment analysis."""
        return {
            "gm",  # Good morning (crypto greeting)
            "wagmi",  # We're all gonna make it
            "lfg",  # Let's go
            "moon",
            "bullish",
            "pump",
            "buy",
            "buying",
            "accumulate",
            "long",
            "hodl",
            "hold",
            "gem",
            "alpha",
            "dyor",  # Do your own research (often bullish context)
            "gains",
            "profit",
            "breakout",
            "rally",
            "surge",
        }

    def _load_bearish_keywords(self) -> set:
        """Load bearish keywords for sentiment analysis."""
        return {
            "dump",
            "dumping",
            "bearish",
            "sell",
            "selling",
            "short",
            "rekt",
            "liquidated",
            "crash",
            "falling",
            "drop",
            "fud",
            "ngmi",  # Not gonna make it
            "rug",
            "rugpull",
            "scam",
            "exit",
            "panic",
            "fear",
        }

    async def analyze_token_sentiment(
        self, token_symbol: str, hours: int = 24
    ) -> SentimentReading:
        """Analyze Discord sentiment for a token.

        Args:
            token_symbol: Token symbol (e.g., "ETH")
            hours: Hours of historical data to analyze

        Returns:
            SentimentReading with Discord sentiment analysis

        Example:
            >>> analyzer = DiscordSentimentAnalyzer()
            >>> sentiment = await analyzer.analyze_token_sentiment("ETH", hours=24)
            >>> print(f"ETH Discord sentiment: {sentiment.score}/100")
        """
        # In production, this would call Discord API
        # For now, simulate with mock data
        messages = await self._fetch_messages(token_symbol, hours)

        if not messages:
            return self._create_neutral_reading(token_symbol)

        # Analyze messages
        scores = [self._analyze_message(msg) for msg in messages]

        # Calculate weighted average based on reactions
        weighted_score = self._calculate_weighted_sentiment(messages, scores)

        # Calculate confidence based on sample size and activity
        confidence = self._calculate_confidence(messages, scores)

        return SentimentReading(
            source=SentimentSource.DISCORD,
            score=weighted_score,
            confidence=confidence,
            timestamp=utc_now(),
            token_symbol=token_symbol,
            metadata={
                "message_count": len(messages),
                "time_period_hours": hours,
                "servers": len(set(m.get("server") for m in messages)),
                "total_reactions": sum(m.get("reactions", 0) for m in messages),
                "avg_reactions": sum(m.get("reactions", 0) for m in messages)
                / len(messages)
                if messages
                else 0,
            },
        )

    async def _fetch_messages(
        self, token_symbol: str, hours: int
    ) -> List[Dict]:
        """Fetch Discord messages mentioning token.

        In production, this would call Discord API.
        For now, returns simulated data.

        Args:
            token_symbol: Token symbol
            hours: Hours of history

        Returns:
            List of message dictionaries
        """
        # Simulate Discord API response
        # In production: use discord.py library
        # client = discord.Client(...)
        # messages = await channel.history(limit=500).flatten()

        # Simulated messages for testing
        simulated_messages = [
            {
                "content": f"gm everyone! ${token_symbol} looking strong today 🚀",
                "reactions": 12,
                "reaction_breakdown": {"🚀": 8, "👍": 4},
                "server": "ethereum",
                "channel": "general",
                "timestamp": utc_now() - timedelta(minutes=30),
            },
            {
                "content": f"Is ${token_symbol} dumping? Not looking good...",
                "reactions": 5,
                "reaction_breakdown": {"👎": 3, "📉": 2},
                "server": "defi",
                "channel": "trading",
                "timestamp": utc_now() - timedelta(hours=2),
            },
            {
                "content": f"${token_symbol} breakout imminent. LFG! 💎🙌",
                "reactions": 18,
                "reaction_breakdown": {"🚀": 10, "💎": 5, "👍": 3},
                "server": "uniswap",
                "channel": "alpha",
                "timestamp": utc_now() - timedelta(hours=4),
            },
            {
                "content": f"WAGMI ${token_symbol} holders! Bullish AF 🔥",
                "reactions": 15,
                "reaction_breakdown": {"🔥": 8, "🚀": 4, "👍": 3},
                "server": "ethereum",
                "channel": "price-talk",
                "timestamp": utc_now() - timedelta(hours=6),
            },
            {
                "content": f"Just bought more ${token_symbol}. Accumulation phase.",
                "reactions": 9,
                "reaction_breakdown": {"👍": 6, "💰": 3},
                "server": "aave",
                "channel": "general",
                "timestamp": utc_now() - timedelta(hours=8),
            },
            {
                "content": f"${token_symbol} FUD spreading. Don't panic sell.",
                "reactions": 7,
                "reaction_breakdown": {"👍": 4, "💎": 3},
                "server": "compound",
                "channel": "discussion",
                "timestamp": utc_now() - timedelta(hours=10),
            },
        ]

        # Filter by message length and reactions
        filtered = [
            m
            for m in simulated_messages
            if len(m["content"]) >= self.config.min_message_length
            and m["reactions"] >= self.config.min_reactions
        ]

        return filtered

    def _analyze_message(self, message: Dict) -> float:
        """Analyze individual Discord message sentiment.

        Args:
            message: Message dictionary

        Returns:
            Sentiment score (0-100)
        """
        content = message["content"].lower()
        score = 50.0  # Neutral baseline

        # Keyword analysis
        bullish_count = sum(1 for kw in self._bullish_keywords if kw in content)
        bearish_count = sum(1 for kw in self._bearish_keywords if kw in content)

        # Adjust score based on keywords (5 points per keyword)
        score += bullish_count * 5
        score -= bearish_count * 5

        # Reaction analysis (strong signal in Discord)
        reaction_breakdown = message.get("reaction_breakdown", {})

        positive_reactions = sum(
            count
            for emoji, count in reaction_breakdown.items()
            if emoji in self._positive_reactions
        )
        negative_reactions = sum(
            count
            for emoji, count in reaction_breakdown.items()
            if emoji in self._negative_reactions
        )

        # Reactions are weighted higher (10 points per reaction)
        score += positive_reactions * 10
        score -= negative_reactions * 10

        # Caps and exclamation marks indicate strong sentiment
        if content.isupper():
            # ALL CAPS amplifies sentiment
            if score > 50:
                score *= 1.2
            else:
                score *= 0.8

        exclamations = content.count("!")
        if score > 50:
            score += exclamations * 3
        else:
            score -= exclamations * 3

        # Question marks indicate uncertainty
        if "?" in content:
            score *= 0.92

        # Clamp to 0-100
        return max(0, min(100, score))

    def _calculate_weighted_sentiment(
        self, messages: List[Dict], scores: List[float]
    ) -> float:
        """Calculate weighted sentiment based on reactions.

        Args:
            messages: List of messages
            scores: Corresponding sentiment scores

        Returns:
            Weighted average sentiment score
        """
        if not messages:
            return 50.0

        total_weight = 0.0
        weighted_sum = 0.0

        for message, score in zip(messages, scores):
            # Calculate weight based on reactions
            reactions = message.get("reactions", 0)
            # Weight = reactions + 1 (to avoid zero weight)
            weight = reactions + 1

            total_weight += weight
            weighted_sum += score * weight

        return weighted_sum / total_weight if total_weight > 0 else 50.0

    def _calculate_confidence(
        self, messages: List[Dict], scores: List[float]
    ) -> float:
        """Calculate confidence in sentiment analysis.

        Args:
            messages: List of messages
            scores: Corresponding sentiment scores

        Returns:
            Confidence score (0-1)
        """
        if not messages:
            return 0.0

        # Base confidence from sample size
        sample_confidence = min(len(messages) / 100, 1.0)  # Max at 100 messages

        # Consistency: how similar are the scores?
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            std_dev = variance**0.5
            consistency = 1.0 - (std_dev / 50)
        else:
            consistency = 0.5

        # Activity boost (more reactions = higher confidence)
        avg_reactions = sum(m.get("reactions", 0) for m in messages) / len(messages)
        activity_boost = min(avg_reactions / 20, 0.2)  # Max 0.2 boost

        # Combine factors
        confidence = (sample_confidence * 0.5) + (consistency * 0.3) + activity_boost

        return max(0.0, min(1.0, confidence))

    def _create_neutral_reading(self, token_symbol: str) -> SentimentReading:
        """Create neutral sentiment reading when no data available."""
        return SentimentReading(
            source=SentimentSource.DISCORD,
            score=50.0,
            confidence=0.0,
            timestamp=utc_now(),
            token_symbol=token_symbol,
            metadata={
                "message_count": 0,
                "reason": "no_data",
            },
        )

    async def get_server_activity(
        self, server_id: str = None
    ) -> Dict:
        """Get activity metrics for Discord servers.

        Args:
            server_id: Specific server ID (optional)

        Returns:
            Server activity metrics

        Example:
            >>> analyzer = DiscordSentimentAnalyzer()
            >>> activity = await analyzer.get_server_activity()
        """
        # In production: analyze server activity
        # For now, return simulated data
        return {
            "active_users": 1250,
            "messages_24h": 3840,
            "avg_sentiment": 68.5,
            "top_tokens": ["ETH", "BTC", "SOL"],
        }
