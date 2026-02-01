"""Integration tests for Hunter AI sentiment analysis.

Tests sentiment analysis domain models, Twitter analyzer, and aggregation.
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from app.domain.value_objects.sentiment import (
    SentimentScore,
    SentimentSource,
    SentimentReading,
    AggregatedSentiment,
    SentimentTrend,
)
from app.domain.entities.sentiment_analysis import (
    SentimentAnalysis,
    SentimentSnapshot,
)
from app.application.hunter.twitter_sentiment import (
    TwitterSentimentAnalyzer,
    TwitterConfig,
)
from app.application.hunter.sentiment_aggregator import SentimentAggregator


class TestSentimentValueObjects:
    """Test sentiment value objects."""

    def test_sentiment_reading_creation(self):
        """Test creating sentiment reading."""
        reading = SentimentReading(
            source=SentimentSource.TWITTER,
            score=75.0,
            confidence=0.85,
            timestamp=datetime.utcnow(),
            token_symbol="ETH",
            metadata={"tweet_count": 100},
        )

        assert reading.source == SentimentSource.TWITTER
        assert reading.score == 75.0
        assert reading.confidence == 0.85
        assert reading.token_symbol == "ETH"

    def test_sentiment_reading_classification(self):
        """Test sentiment classification from score."""
        # Very bearish
        reading = SentimentReading(
            source=SentimentSource.TWITTER,
            score=15.0,
            confidence=0.8,
            timestamp=datetime.utcnow(),
            token_symbol="ETH",
            metadata={},
        )
        assert reading.classification == SentimentScore.VERY_BEARISH

        # Bullish
        reading = SentimentReading(
            source=SentimentSource.TWITTER,
            score=70.0,
            confidence=0.8,
            timestamp=datetime.utcnow(),
            token_symbol="ETH",
            metadata={},
        )
        assert reading.classification == SentimentScore.BULLISH

    def test_sentiment_reading_validation(self):
        """Test sentiment reading validation."""
        # Invalid score
        with pytest.raises(ValueError):
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=150.0,  # > 100
                confidence=0.8,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            )

        # Invalid confidence
        with pytest.raises(ValueError):
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=75.0,
                confidence=1.5,  # > 1
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            )

    def test_sentiment_reading_properties(self):
        """Test sentiment reading computed properties."""
        # Bullish reading
        reading = SentimentReading(
            source=SentimentSource.TWITTER,
            score=75.0,
            confidence=0.85,
            timestamp=datetime.utcnow(),
            token_symbol="ETH",
            metadata={},
        )

        assert reading.is_bullish is True
        assert reading.is_bearish is False
        assert reading.is_high_confidence is True

        # Bearish reading
        reading = SentimentReading(
            source=SentimentSource.TWITTER,
            score=35.0,
            confidence=0.65,
            timestamp=datetime.utcnow(),
            token_symbol="BTC",
            metadata={},
        )

        assert reading.is_bullish is False
        assert reading.is_bearish is True
        assert reading.is_high_confidence is False

    def test_aggregated_sentiment_creation(self):
        """Test creating aggregated sentiment."""
        readings = (
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=75.0,
                confidence=0.85,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
            SentimentReading(
                source=SentimentSource.REDDIT,
                score=68.0,
                confidence=0.75,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
        )

        aggregated = AggregatedSentiment(
            token_symbol="ETH",
            overall_score=72.0,
            overall_confidence=0.80,
            timestamp=datetime.utcnow(),
            readings=readings,
            weights={
                SentimentSource.TWITTER: 0.35,
                SentimentSource.REDDIT: 0.25,
            },
        )

        assert aggregated.token_symbol == "ETH"
        assert aggregated.overall_score == 72.0
        assert aggregated.source_count == 2

    def test_aggregated_sentiment_properties(self):
        """Test aggregated sentiment computed properties."""
        readings = (
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=75.0,
                confidence=0.85,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
        )

        aggregated = AggregatedSentiment(
            token_symbol="ETH",
            overall_score=72.0,
            overall_confidence=0.85,
            timestamp=datetime.utcnow(),
            readings=readings,
            weights={SentimentSource.TWITTER: 0.35},
        )

        assert aggregated.classification == SentimentScore.BULLISH
        assert aggregated.signal_strength == "strong"

    def test_sentiment_trend_creation(self):
        """Test creating sentiment trend."""
        trend = SentimentTrend(
            token_symbol="ETH",
            current_score=75.0,
            previous_score=65.0,
            change_percent=15.38,
            period_hours=24,
            timestamp=datetime.utcnow(),
        )

        assert trend.direction == "increasing"
        assert trend.is_significant is True
        assert trend.momentum == "moderate"


class TestSentimentEntities:
    """Test sentiment entities."""

    def test_sentiment_analysis_creation(self):
        """Test creating sentiment analysis entity."""
        readings = (
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=75.0,
                confidence=0.85,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
        )

        aggregated = AggregatedSentiment(
            token_symbol="ETH",
            overall_score=75.0,
            overall_confidence=0.85,
            timestamp=datetime.utcnow(),
            readings=readings,
            weights={SentimentSource.TWITTER: 0.35},
        )

        analysis = SentimentAnalysis.create(
            token_symbol="ETH",
            aggregated_sentiment=aggregated,
        )

        assert analysis.token_symbol == "ETH"
        assert analysis.overall_score == 75.0
        assert analysis.total_data_points == 1

    def test_sentiment_analysis_update(self):
        """Test updating sentiment analysis."""
        analysis = SentimentAnalysis(token_symbol="ETH")

        readings = (
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=75.0,
                confidence=0.85,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
        )

        aggregated = AggregatedSentiment(
            token_symbol="ETH",
            overall_score=75.0,
            overall_confidence=0.85,
            timestamp=datetime.utcnow(),
            readings=readings,
            weights={SentimentSource.TWITTER: 0.35},
        )

        analysis.update_sentiment(aggregated)

        assert analysis.overall_score == 75.0
        assert analysis.total_data_points == 1

    def test_sentiment_snapshot_from_analysis(self):
        """Test creating snapshot from analysis."""
        readings = (
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=75.0,
                confidence=0.85,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
        )

        aggregated = AggregatedSentiment(
            token_symbol="ETH",
            overall_score=75.0,
            overall_confidence=0.85,
            timestamp=datetime.utcnow(),
            readings=readings,
            weights={SentimentSource.TWITTER: 0.35},
        )

        analysis = SentimentAnalysis.create(
            token_symbol="ETH",
            aggregated_sentiment=aggregated,
        )

        snapshot = SentimentSnapshot.from_analysis(analysis)

        assert snapshot is not None
        assert snapshot.token_symbol == "ETH"
        assert snapshot.score == 75.0


class TestTwitterSentimentAnalyzer:
    """Test Twitter sentiment analyzer."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_analyze_token_sentiment(self):
        """Test analyzing token sentiment from Twitter."""
        config = TwitterConfig(enabled=True)
        analyzer = TwitterSentimentAnalyzer(config)

        reading = await analyzer.analyze_token_sentiment("ETH", hours=24)

        assert reading.source == SentimentSource.TWITTER
        assert 0 <= reading.score <= 100
        assert 0 <= reading.confidence <= 1
        assert reading.token_symbol == "ETH"
        assert "tweet_count" in reading.metadata

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_trending_tokens(self):
        """Test getting trending tokens."""
        analyzer = TwitterSentimentAnalyzer()

        trending = await analyzer.get_trending_tokens(limit=5)

        assert len(trending) <= 5
        assert all("symbol" in t for t in trending)
        assert all("mentions" in t for t in trending)
        assert all("sentiment" in t for t in trending)

    def test_keyword_analysis(self):
        """Test keyword sentiment analysis."""
        analyzer = TwitterSentimentAnalyzer()

        # Bullish tweet
        tweet = {
            "text": "ETH to the moon! 🚀 Buying more. Bullish!",
            "likes": 100,
            "retweets": 30,
            "verified": True,
            "timestamp": datetime.utcnow(),
        }

        score = analyzer._analyze_tweet(tweet)
        assert score > 50, "Bullish tweet should have score > 50"

        # Bearish tweet
        tweet = {
            "text": "ETH dump incoming. Selling everything. Bearish!",
            "likes": 50,
            "retweets": 15,
            "verified": False,
            "timestamp": datetime.utcnow(),
        }

        score = analyzer._analyze_tweet(tweet)
        assert score < 50, "Bearish tweet should have score < 50"


class TestSentimentAggregator:
    """Test sentiment aggregator."""

    def test_aggregate_multiple_sources(self):
        """Test aggregating sentiment from multiple sources."""
        readings = [
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=75.0,
                confidence=0.85,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
            SentimentReading(
                source=SentimentSource.REDDIT,
                score=68.0,
                confidence=0.75,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
        ]

        aggregator = SentimentAggregator()
        aggregated = aggregator.aggregate(readings, "ETH")

        assert aggregated.token_symbol == "ETH"
        assert 0 <= aggregated.overall_score <= 100
        assert 0 <= aggregated.overall_confidence <= 1
        assert aggregated.source_count == 2

    def test_weighted_aggregation(self):
        """Test weighted sentiment aggregation."""
        # Twitter (weight=0.35): score=100, confidence=1.0
        # Reddit (weight=0.25): score=0, confidence=1.0
        # Expected weighted: (100*0.35*1.0 + 0*0.25*1.0) / (0.35*1.0 + 0.25*1.0)
        # = 35 / 0.6 = 58.33

        readings = [
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=100.0,
                confidence=1.0,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
            SentimentReading(
                source=SentimentSource.REDDIT,
                score=0.0,
                confidence=1.0,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
        ]

        aggregator = SentimentAggregator()
        aggregated = aggregator.aggregate(readings, "ETH")

        # Should be closer to Twitter (higher weight)
        assert 50 < aggregated.overall_score < 70

    def test_consensus_calculation(self):
        """Test consensus calculation."""
        aggregator = SentimentAggregator()

        # High consensus (all scores similar)
        readings = [
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=70.0,
                confidence=0.8,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
            SentimentReading(
                source=SentimentSource.REDDIT,
                score=72.0,
                confidence=0.8,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
        ]

        consensus = aggregator.calculate_consensus(readings)
        assert consensus > 0.9, "Similar scores should have high consensus"

        # Low consensus (scores divergent)
        readings = [
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=80.0,
                confidence=0.8,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
            SentimentReading(
                source=SentimentSource.REDDIT,
                score=20.0,
                confidence=0.8,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
        ]

        consensus = aggregator.calculate_consensus(readings)
        assert consensus < 0.7, "Divergent scores should have low consensus"

    def test_divergence_detection(self):
        """Test divergence detection between sources."""
        # Divergent signals (bullish vs bearish)
        readings = [
            SentimentReading(
                source=SentimentSource.TWITTER,
                score=75.0,  # Bullish
                confidence=0.8,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
            SentimentReading(
                source=SentimentSource.REDDIT,
                score=35.0,  # Bearish
                confidence=0.8,
                timestamp=datetime.utcnow(),
                token_symbol="ETH",
                metadata={},
            ),
        ]

        aggregated = AggregatedSentiment(
            token_symbol="ETH",
            overall_score=55.0,
            overall_confidence=0.8,
            timestamp=datetime.utcnow(),
            readings=tuple(readings),
            weights={
                SentimentSource.TWITTER: 0.35,
                SentimentSource.REDDIT: 0.25,
            },
        )

        aggregator = SentimentAggregator()
        divergence = aggregator.identify_divergence(aggregated)

        assert divergence["has_divergence"] is True
        assert len(divergence["bullish_sources"]) == 1
        assert len(divergence["bearish_sources"]) == 1


class TestSentimentIntegration:
    """Integration tests for complete sentiment analysis flow."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_end_to_end_sentiment_analysis(self):
        """Test complete sentiment analysis flow."""
        # 1. Analyze Twitter sentiment
        twitter_analyzer = TwitterSentimentAnalyzer()
        twitter_reading = await twitter_analyzer.analyze_token_sentiment("ETH", hours=24)

        assert twitter_reading.source == SentimentSource.TWITTER
        assert twitter_reading.token_symbol == "ETH"

        # 2. Create aggregated sentiment (Twitter only for now)
        aggregator = SentimentAggregator()
        aggregated = aggregator.aggregate([twitter_reading], "ETH")

        assert aggregated.token_symbol == "ETH"
        assert aggregated.source_count == 1

        # 3. Create sentiment analysis entity
        analysis = aggregator.create_analysis([twitter_reading], "ETH")

        assert analysis.token_symbol == "ETH"
        assert analysis.overall_score is not None
        assert analysis.total_data_points == 1

        # 4. Create snapshot for historical tracking
        snapshot = SentimentSnapshot.from_analysis(analysis)

        assert snapshot is not None
        assert snapshot.token_symbol == "ETH"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multi_source_analysis(self):
        """Test sentiment analysis with multiple sources."""
        twitter_analyzer = TwitterSentimentAnalyzer()
        aggregator = SentimentAggregator()

        # Analyze multiple tokens
        tokens = ["ETH", "BTC"]
        results = {}

        for token in tokens:
            reading = await twitter_analyzer.analyze_token_sentiment(token, hours=24)
            aggregated = aggregator.aggregate([reading], token)
            analysis = aggregator.create_analysis([reading], token)
            results[token] = analysis

        assert len(results) == 2
        assert "ETH" in results
        assert "BTC" in results
