"""Sentiment aggregation service.

Combines sentiment from multiple sources (Twitter, Reddit, Discord, News)
into a weighted aggregate score.
"""

from typing import List, Dict
from datetime import datetime

from app.domain.value_objects.sentiment import (
    SentimentReading,
    AggregatedSentiment,
    SentimentSource,
)
from app.domain.entities.sentiment_analysis import SentimentAnalysis


class SentimentAggregator:
    """Aggregates sentiment from multiple sources.

    Combines sentiment readings from Twitter, Reddit, Discord, and News
    using configurable weights to produce an overall sentiment score.
    """

    DEFAULT_WEIGHTS = {
        SentimentSource.TWITTER: 0.35,
        SentimentSource.REDDIT: 0.25,
        SentimentSource.DISCORD: 0.20,
        SentimentSource.NEWS: 0.20,
    }

    def __init__(self, custom_weights: Dict[SentimentSource, float] = None):
        """Initialize sentiment aggregator.

        Args:
            custom_weights: Custom weights for each source (must sum to 1.0)
        """
        self.weights = custom_weights or self.DEFAULT_WEIGHTS
        self._validate_weights()

    def _validate_weights(self) -> None:
        """Validate that weights sum to approximately 1.0."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def aggregate(
        self,
        readings: List[SentimentReading],
        token_symbol: str,
    ) -> AggregatedSentiment:
        """Aggregate multiple sentiment readings.

        Args:
            readings: List of sentiment readings from different sources
            token_symbol: Token symbol being analyzed

        Returns:
            AggregatedSentiment with weighted average score

        Example:
            >>> aggregator = SentimentAggregator()
            >>> readings = [
            ...     twitter_reading,  # score: 72, confidence: 0.85
            ...     reddit_reading,   # score: 65, confidence: 0.75
            ...     news_reading,     # score: 68, confidence: 0.90
            ... ]
            >>> aggregated = aggregator.aggregate(readings, "ETH")
            >>> print(f"Overall sentiment: {aggregated.overall_score}/100")
            >>> # Output: Overall sentiment: 69.05/100 (weighted average)
        """
        if not readings:
            return self._create_neutral_aggregate(token_symbol)

        # Calculate weighted score
        weighted_score = self._calculate_weighted_score(readings)

        # Calculate average confidence
        avg_confidence = sum(r.confidence for r in readings) / len(readings)

        return AggregatedSentiment(
            token_symbol=token_symbol,
            overall_score=weighted_score,
            overall_confidence=avg_confidence,
            timestamp=datetime.utcnow(),
            readings=tuple(readings),  # Immutable
            weights=self.weights.copy(),
        )

    def _calculate_weighted_score(self, readings: List[SentimentReading]) -> float:
        """Calculate weighted sentiment score.

        Args:
            readings: List of sentiment readings

        Returns:
            Weighted average score (0-100)
        """
        total_weight = 0.0
        weighted_sum = 0.0

        for reading in readings:
            # Get weight for this source (default to equal if not specified)
            weight = self.weights.get(
                reading.source, 1.0 / len(SentimentSource)
            )

            # Apply confidence as additional weighting factor
            effective_weight = weight * reading.confidence

            weighted_sum += reading.score * effective_weight
            total_weight += effective_weight

        if total_weight == 0:
            return 50.0  # Neutral if no confidence

        return weighted_sum / total_weight

    def _create_neutral_aggregate(self, token_symbol: str) -> AggregatedSentiment:
        """Create neutral aggregate when no readings available.

        Args:
            token_symbol: Token symbol

        Returns:
            Neutral aggregated sentiment
        """
        neutral_reading = SentimentReading(
            source=SentimentSource.AGGREGATED,
            score=50.0,
            confidence=0.0,
            timestamp=datetime.utcnow(),
            token_symbol=token_symbol,
            metadata={"reason": "no_data"},
        )

        return AggregatedSentiment(
            token_symbol=token_symbol,
            overall_score=50.0,
            overall_confidence=0.0,
            timestamp=datetime.utcnow(),
            readings=(neutral_reading,),
            weights=self.weights.copy(),
        )

    def create_analysis(
        self,
        readings: List[SentimentReading],
        token_symbol: str,
    ) -> SentimentAnalysis:
        """Create complete sentiment analysis entity.

        Args:
            readings: List of sentiment readings
            token_symbol: Token symbol

        Returns:
            SentimentAnalysis entity

        Example:
            >>> aggregator = SentimentAggregator()
            >>> readings = [twitter_reading, reddit_reading, news_reading]
            >>> analysis = aggregator.create_analysis(readings, "ETH")
            >>> print(analysis.to_dict())
        """
        aggregated = self.aggregate(readings, token_symbol)
        return SentimentAnalysis.create(
            token_symbol=token_symbol,
            aggregated_sentiment=aggregated,
        )

    def get_source_breakdown(
        self, aggregated: AggregatedSentiment
    ) -> Dict[str, Dict]:
        """Get detailed breakdown of sentiment by source.

        Args:
            aggregated: Aggregated sentiment

        Returns:
            Dictionary with per-source breakdown

        Example:
            >>> breakdown = aggregator.get_source_breakdown(aggregated)
            >>> print(breakdown["twitter"])
            >>> # {
            >>> #   "score": 72.0,
            >>> #   "confidence": 0.85,
            >>> #   "weight": 0.35,
            >>> #   "contribution": 25.2
            >>> # }
        """
        breakdown = {}

        for reading in aggregated.readings:
            source = reading.source.value
            weight = self.weights.get(reading.source, 0.0)
            contribution = reading.score * weight

            breakdown[source] = {
                "score": reading.score,
                "confidence": reading.confidence,
                "weight": weight,
                "contribution": contribution,
                "classification": reading.classification.value,
            }

        return breakdown

    def calculate_consensus(self, readings: List[SentimentReading]) -> float:
        """Calculate consensus level among sources.

        Args:
            readings: List of sentiment readings

        Returns:
            Consensus score (0-1), where 1 = perfect agreement

        Example:
            >>> # All sources bullish (scores: 70, 75, 72)
            >>> consensus = aggregator.calculate_consensus(readings)
            >>> # Returns: 0.95 (high consensus)
            >>>
            >>> # Mixed signals (scores: 70, 45, 60)
            >>> consensus = aggregator.calculate_consensus(readings)
            >>> # Returns: 0.65 (moderate consensus)
        """
        if len(readings) < 2:
            return 1.0  # Perfect consensus with single source

        scores = [r.score for r in readings]
        mean_score = sum(scores) / len(scores)

        # Calculate variance
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_dev = variance**0.5

        # Normalize: max possible std_dev is 50 (all scores at extremes)
        consensus = 1.0 - (std_dev / 50)

        return max(0.0, min(1.0, consensus))

    def identify_divergence(
        self, aggregated: AggregatedSentiment
    ) -> Dict[str, any]:
        """Identify divergence between sources.

        Args:
            aggregated: Aggregated sentiment

        Returns:
            Divergence analysis

        Example:
            >>> divergence = aggregator.identify_divergence(aggregated)
            >>> if divergence["has_divergence"]:
            ...     print(f"Divergence detected: {divergence['description']}")
            ...     print(f"Bullish sources: {divergence['bullish_sources']}")
            ...     print(f"Bearish sources: {divergence['bearish_sources']}")
        """
        bullish_sources = []
        bearish_sources = []

        for reading in aggregated.readings:
            if reading.is_bullish:
                bullish_sources.append(reading.source.value)
            elif reading.is_bearish:
                bearish_sources.append(reading.source.value)

        has_divergence = len(bullish_sources) > 0 and len(bearish_sources) > 0

        description = ""
        if has_divergence:
            description = (
                f"{len(bullish_sources)} sources bullish, "
                f"{len(bearish_sources)} sources bearish"
            )

        return {
            "has_divergence": has_divergence,
            "description": description,
            "bullish_sources": bullish_sources,
            "bearish_sources": bearish_sources,
            "consensus": self.calculate_consensus(list(aggregated.readings)),
        }
