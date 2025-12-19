"""Sentiment analysis value objects.

Domain value objects for Hunter AI sentiment analysis.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class SentimentScore(str, Enum):
    """Sentiment classification."""

    VERY_BEARISH = "very_bearish"  # 0-20
    BEARISH = "bearish"  # 20-40
    NEUTRAL = "neutral"  # 40-60
    BULLISH = "bullish"  # 60-80
    VERY_BULLISH = "very_bullish"  # 80-100


class SentimentSource(str, Enum):
    """Source of sentiment data."""

    TWITTER = "twitter"
    REDDIT = "reddit"
    DISCORD = "discord"
    NEWS = "news"
    AGGREGATED = "aggregated"


@dataclass(frozen=True)
class SentimentReading:
    """Individual sentiment reading from a source.

    Immutable value object representing a single sentiment measurement.
    """

    source: SentimentSource
    score: float  # 0-100
    confidence: float  # 0-1
    timestamp: datetime
    token_symbol: str
    metadata: dict

    def __post_init__(self):
        """Validate sentiment reading values."""
        if not 0 <= self.score <= 100:
            raise ValueError(f"Score must be 0-100, got {self.score}")
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")

    @property
    def classification(self) -> SentimentScore:
        """Get sentiment classification from score.

        Returns:
            SentimentScore enum based on score value
        """
        if self.score < 20:
            return SentimentScore.VERY_BEARISH
        elif self.score < 40:
            return SentimentScore.BEARISH
        elif self.score < 60:
            return SentimentScore.NEUTRAL
        elif self.score < 80:
            return SentimentScore.BULLISH
        else:
            return SentimentScore.VERY_BULLISH

    @property
    def is_bullish(self) -> bool:
        """Check if sentiment is bullish (score >= 60)."""
        return self.score >= 60

    @property
    def is_bearish(self) -> bool:
        """Check if sentiment is bearish (score < 40)."""
        return self.score < 40

    @property
    def is_high_confidence(self) -> bool:
        """Check if reading has high confidence (>= 0.75)."""
        return self.confidence >= 0.75


@dataclass(frozen=True)
class AggregatedSentiment:
    """Aggregated sentiment across multiple sources.

    Weighted average of sentiment readings from different sources.
    """

    token_symbol: str
    overall_score: float  # 0-100 (weighted average)
    overall_confidence: float  # 0-1 (average confidence)
    timestamp: datetime
    readings: tuple[SentimentReading, ...]  # Immutable
    weights: dict[SentimentSource, float]  # Source weights

    def __post_init__(self):
        """Validate aggregated sentiment values."""
        if not 0 <= self.overall_score <= 100:
            raise ValueError(f"Score must be 0-100, got {self.overall_score}")
        if not 0 <= self.overall_confidence <= 1:
            raise ValueError(f"Confidence must be 0-1, got {self.overall_confidence}")

    @property
    def classification(self) -> SentimentScore:
        """Get overall sentiment classification."""
        if self.overall_score < 20:
            return SentimentScore.VERY_BEARISH
        elif self.overall_score < 40:
            return SentimentScore.BEARISH
        elif self.overall_score < 60:
            return SentimentScore.NEUTRAL
        elif self.overall_score < 80:
            return SentimentScore.BULLISH
        else:
            return SentimentScore.VERY_BULLISH

    @property
    def signal_strength(self) -> str:
        """Get trading signal strength.

        Returns:
            "strong", "moderate", or "weak" based on confidence
        """
        if self.overall_confidence >= 0.8:
            return "strong"
        elif self.overall_confidence >= 0.6:
            return "moderate"
        else:
            return "weak"

    @property
    def source_count(self) -> int:
        """Get number of sources contributing to sentiment."""
        return len(self.readings)

    def get_source_score(self, source: SentimentSource) -> Optional[float]:
        """Get sentiment score for specific source.

        Args:
            source: Source to get score for

        Returns:
            Score for source, or None if not found
        """
        for reading in self.readings:
            if reading.source == source:
                return reading.score
        return None


@dataclass(frozen=True)
class SentimentTrend:
    """Sentiment trend over time.

    Tracks changes in sentiment over a time period.
    """

    token_symbol: str
    current_score: float
    previous_score: float
    change_percent: float
    period_hours: int
    timestamp: datetime

    @property
    def direction(self) -> str:
        """Get trend direction.

        Returns:
            "increasing", "decreasing", or "stable"
        """
        if abs(self.change_percent) < 5:
            return "stable"
        elif self.change_percent > 0:
            return "increasing"
        else:
            return "decreasing"

    @property
    def is_significant(self) -> bool:
        """Check if change is significant (>10%)."""
        return abs(self.change_percent) > 10

    @property
    def momentum(self) -> str:
        """Get momentum strength.

        Returns:
            "strong", "moderate", or "weak"
        """
        abs_change = abs(self.change_percent)
        if abs_change >= 20:
            return "strong"
        elif abs_change >= 10:
            return "moderate"
        else:
            return "weak"
