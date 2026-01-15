"""Sentiment analysis domain entity.

Domain entity for persisting and managing sentiment analysis data.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID, uuid4

from app.domain.value_objects.sentiment import (
    SentimentReading,
    AggregatedSentiment,
    SentimentSource,
    SentimentScore,
)


@dataclass
class SentimentAnalysis:
    """Sentiment analysis entity.

    Represents a complete sentiment analysis for a token at a point in time.
    """

    id: UUID = field(default_factory=uuid4)
    token_symbol: str = field(default="")
    aggregated_sentiment: Optional[AggregatedSentiment] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Analysis metadata
    analysis_version: str = "1.0"
    sources_analyzed: list[SentimentSource] = field(default_factory=list)
    total_data_points: int = 0

    def update_sentiment(self, aggregated: AggregatedSentiment) -> None:
        """Update sentiment analysis with new data.

        Args:
            aggregated: New aggregated sentiment data
        """
        self.aggregated_sentiment = aggregated
        self.updated_at = datetime.now(UTC)
        self.sources_analyzed = [r.source for r in aggregated.readings]
        self.total_data_points = len(aggregated.readings)

    @property
    def is_stale(self, max_age_minutes: int = 30) -> bool:
        """Check if analysis is stale.

        Args:
            max_age_minutes: Maximum age in minutes

        Returns:
            True if analysis is older than max_age_minutes
        """
        age = datetime.now(UTC) - self.updated_at
        return age.total_seconds() / 60 > max_age_minutes

    @property
    def overall_score(self) -> Optional[float]:
        """Get overall sentiment score."""
        if self.aggregated_sentiment:
            return self.aggregated_sentiment.overall_score
        return None

    @property
    def overall_classification(self) -> Optional[SentimentScore]:
        """Get overall sentiment classification."""
        if self.aggregated_sentiment:
            return self.aggregated_sentiment.classification
        return None

    @property
    def signal_strength(self) -> Optional[str]:
        """Get signal strength."""
        if self.aggregated_sentiment:
            return self.aggregated_sentiment.signal_strength
        return None

    @classmethod
    def create(
        cls,
        token_symbol: str,
        aggregated_sentiment: AggregatedSentiment,
    ) -> "SentimentAnalysis":
        """Factory method to create sentiment analysis.

        Args:
            token_symbol: Token symbol (e.g., "ETH")
            aggregated_sentiment: Aggregated sentiment data

        Returns:
            New SentimentAnalysis entity
        """
        analysis = cls(
            token_symbol=token_symbol,
            aggregated_sentiment=aggregated_sentiment,
            sources_analyzed=[r.source for r in aggregated_sentiment.readings],
            total_data_points=len(aggregated_sentiment.readings),
        )
        return analysis

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "id": str(self.id),
            "token_symbol": self.token_symbol,
            "overall_score": self.overall_score,
            "classification": self.overall_classification.value
            if self.overall_classification
            else None,
            "confidence": self.aggregated_sentiment.overall_confidence
            if self.aggregated_sentiment
            else None,
            "signal_strength": self.signal_strength,
            "sources_analyzed": [s.value for s in self.sources_analyzed],
            "total_data_points": self.total_data_points,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SentimentSnapshot:
    """Snapshot of sentiment at a specific time.

    Used for historical tracking and trend analysis.
    """

    id: UUID = field(default_factory=uuid4)
    token_symbol: str = field(default="")
    score: float = 0.0
    confidence: float = 0.0
    classification: SentimentScore = SentimentScore.NEUTRAL
    source: SentimentSource = SentimentSource.AGGREGATED
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Metadata
    data_points: int = 0
    sources: list[SentimentSource] = field(default_factory=list)

    @classmethod
    def from_analysis(
        cls, analysis: SentimentAnalysis
    ) -> Optional["SentimentSnapshot"]:
        """Create snapshot from sentiment analysis.

        Args:
            analysis: SentimentAnalysis entity

        Returns:
            SentimentSnapshot or None if analysis is incomplete
        """
        if not analysis.aggregated_sentiment:
            return None

        return cls(
            token_symbol=analysis.token_symbol,
            score=analysis.aggregated_sentiment.overall_score,
            confidence=analysis.aggregated_sentiment.overall_confidence,
            classification=analysis.aggregated_sentiment.classification,
            source=SentimentSource.AGGREGATED,
            data_points=analysis.total_data_points,
            sources=analysis.sources_analyzed,
            timestamp=analysis.updated_at,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "token_symbol": self.token_symbol,
            "score": self.score,
            "confidence": self.confidence,
            "classification": self.classification.value,
            "source": self.source.value,
            "data_points": self.data_points,
            "sources": [s.value for s in self.sources],
            "timestamp": self.timestamp.isoformat(),
        }
