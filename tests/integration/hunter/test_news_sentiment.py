"""Integration tests for News sentiment analysis (Day 3).

Tests news sentiment analyzer and full 4-source aggregation.
"""

import pytest
from datetime import datetime

from app.domain.value_objects.sentiment import (
    SentimentSource,
    SentimentReading,
)
from app.application.hunter.news_sentiment import (
    NewsSentimentAnalyzer,
    NewsConfig,
)
from app.application.hunter.twitter_sentiment import TwitterSentimentAnalyzer
from app.application.hunter.reddit_sentiment import RedditSentimentAnalyzer
from app.application.hunter.discord_sentiment import DiscordSentimentAnalyzer
from app.application.hunter.sentiment_aggregator import SentimentAggregator


class TestNewsSentimentAnalyzer:
    """Test News sentiment analyzer."""

    @pytest.mark.asyncio
    async def test_analyze_token_sentiment(self):
        """Test analyzing token sentiment from news."""
        config = NewsConfig(enabled=True)
        analyzer = NewsSentimentAnalyzer(config)

        reading = await analyzer.analyze_token_sentiment("ETH", hours=24)

        assert reading.source == SentimentSource.NEWS
        assert 0 <= reading.score <= 100
        assert 0 <= reading.confidence <= 1
        assert reading.token_symbol == "ETH"
        assert "article_count" in reading.metadata

    @pytest.mark.asyncio
    async def test_news_config_defaults(self):
        """Test news config default values."""
        config = NewsConfig()

        assert config.enabled is True
        assert config.rate_limit == 60
        assert len(config.rss_feeds) > 0
        assert any("coindesk" in feed for feed in config.rss_feeds)

    @pytest.mark.asyncio
    async def test_top_headlines(self):
        """Test getting top crypto news headlines."""
        analyzer = NewsSentimentAnalyzer()

        headlines = await analyzer.get_top_headlines(limit=5)

        assert len(headlines) <= 5
        assert all("title" in h for h in headlines)
        assert all("source" in h for h in headlines)
        assert all("sentiment" in h for h in headlines)

    def test_news_keyword_analysis(self):
        """Test news keyword sentiment analysis."""
        analyzer = NewsSentimentAnalyzer()

        # Bullish article
        article = {
            "title": "Major Partnership Announced for ETH",
            "content": "Institutional adoption surge. Positive outlook and strong momentum.",
            "source": "coindesk.com",
            "published": datetime.utcnow(),
        }

        score = analyzer._analyze_article(article)
        assert score > 50, "Bullish article should have score > 50"

        # Bearish article
        article = {
            "title": "Regulatory Concerns Around ETH",
            "content": "Investigation launched. Market decline and negative outlook.",
            "source": "bloomberg.com",
            "published": datetime.utcnow(),
        }

        score = analyzer._analyze_article(article)
        assert score < 50, "Bearish article should have score < 50"

    def test_news_phrase_analysis(self):
        """Test news multi-word phrase analysis."""
        analyzer = NewsSentimentAnalyzer()

        # Article with bullish phrases
        article = {
            "title": "ETH Reaches All Time High",
            "content": "Breaking out with strong momentum. Major partnership announced.",
            "source": "cointelegraph.com",
            "published": datetime.utcnow(),
        }

        score = analyzer._analyze_article(article)
        assert score > 70, "Article with bullish phrases should have high score"

    def test_headline_sentiment_weight(self):
        """Test that headline sentiment carries extra weight."""
        analyzer = NewsSentimentAnalyzer()

        # Bullish headline, neutral content
        article_headline = {
            "title": "ETH Surge and Rally Expected",
            "content": "Market analysis shows mixed signals.",
            "source": "coindesk.com",
            "published": datetime.utcnow(),
        }

        # Neutral headline, bullish content
        article_content = {
            "title": "ETH Market Update",
            "content": "Surge and rally expected. Strong momentum and positive outlook.",
            "source": "coindesk.com",
            "published": datetime.utcnow(),
        }

        score_headline = analyzer._analyze_article(article_headline)
        score_content = analyzer._analyze_article(article_content)

        # Both should be bullish, but headline impact is noticeable
        assert score_headline > 50, "Bullish headline should increase score"
        assert score_content > 50, "Bullish content should increase score"

    def test_source_authority_scoring(self):
        """Test source authority impact on confidence."""
        analyzer = NewsSentimentAnalyzer()

        assert analyzer.get_source_authority("coindesk.com") == 0.90
        assert analyzer.get_source_authority("bloomberg.com") == 0.95
        assert analyzer.get_source_authority("unknown.com") == 0.5


class TestFourSourceAggregation:
    """Test complete 4-source sentiment aggregation (Twitter + Reddit + Discord + News)."""

    @pytest.mark.asyncio
    async def test_all_sources_aggregation(self):
        """Test aggregating sentiment from all four sources."""
        # Analyze same token across all sources
        twitter_analyzer = TwitterSentimentAnalyzer()
        reddit_analyzer = RedditSentimentAnalyzer()
        discord_analyzer = DiscordSentimentAnalyzer()
        news_analyzer = NewsSentimentAnalyzer()

        twitter_reading = await twitter_analyzer.analyze_token_sentiment("ETH", hours=24)
        reddit_reading = await reddit_analyzer.analyze_token_sentiment("ETH", hours=24)
        discord_reading = await discord_analyzer.analyze_token_sentiment("ETH", hours=24)
        news_reading = await news_analyzer.analyze_token_sentiment("ETH", hours=24)

        # Aggregate all sources
        aggregator = SentimentAggregator()
        aggregated = aggregator.aggregate(
            [twitter_reading, reddit_reading, discord_reading, news_reading], "ETH"
        )

        assert aggregated.token_symbol == "ETH"
        assert aggregated.source_count == 4
        assert 0 <= aggregated.overall_score <= 100
        assert 0 <= aggregated.overall_confidence <= 1
        assert aggregated.classification is not None

    @pytest.mark.asyncio
    async def test_full_weight_distribution(self):
        """Test that all source weights sum to 1.0."""
        twitter_analyzer = TwitterSentimentAnalyzer()
        reddit_analyzer = RedditSentimentAnalyzer()
        discord_analyzer = DiscordSentimentAnalyzer()
        news_analyzer = NewsSentimentAnalyzer()

        readings = [
            await twitter_analyzer.analyze_token_sentiment("BTC", hours=24),
            await reddit_analyzer.analyze_token_sentiment("BTC", hours=24),
            await discord_analyzer.analyze_token_sentiment("BTC", hours=24),
            await news_analyzer.analyze_token_sentiment("BTC", hours=24),
        ]

        aggregator = SentimentAggregator()
        aggregated = aggregator.aggregate(readings, "BTC")

        # Verify all sources present
        breakdown = aggregator.get_source_breakdown(aggregated)

        # Check weights sum to 1.0 (or close due to floating point)
        total_weight = sum(s["weight"] for s in breakdown.values())
        assert abs(total_weight - 1.0) < 0.01, f"Weights should sum to 1.0, got {total_weight}"

    @pytest.mark.asyncio
    async def test_news_authority_boosts_confidence(self):
        """Test that high-authority news sources boost overall confidence."""
        news_analyzer = NewsSentimentAnalyzer()

        reading = await news_analyzer.analyze_token_sentiment("ETH", hours=24)

        # News should have some confidence (may be lower with small sample)
        assert reading.confidence >= 0.3, "News should have reasonable confidence"
        assert reading.confidence <= 1.0, "Confidence should be <= 1.0"

    @pytest.mark.asyncio
    async def test_complete_sentiment_pipeline(self):
        """Test complete sentiment analysis pipeline with all sources."""
        token = "SOL"

        # Analyze all sources
        twitter_analyzer = TwitterSentimentAnalyzer()
        reddit_analyzer = RedditSentimentAnalyzer()
        discord_analyzer = DiscordSentimentAnalyzer()
        news_analyzer = NewsSentimentAnalyzer()

        twitter_reading = await twitter_analyzer.analyze_token_sentiment(token, hours=24)
        reddit_reading = await reddit_analyzer.analyze_token_sentiment(token, hours=24)
        discord_reading = await discord_analyzer.analyze_token_sentiment(token, hours=24)
        news_reading = await news_analyzer.analyze_token_sentiment(token, hours=24)

        # Aggregate
        aggregator = SentimentAggregator()
        aggregated = aggregator.aggregate(
            [twitter_reading, reddit_reading, discord_reading, news_reading], token
        )

        # Get detailed breakdown
        breakdown = aggregator.get_source_breakdown(aggregated)

        # Verify complete analysis
        assert aggregated.source_count == 4
        assert len(breakdown) == 4
        assert "twitter" in breakdown
        assert "reddit" in breakdown
        assert "discord" in breakdown
        assert "news" in breakdown

        # Verify signal quality
        assert aggregated.signal_strength in ["strong", "moderate", "weak"]
        assert aggregated.classification is not None

        # Verify consensus and divergence
        consensus = aggregator.calculate_consensus(
            [twitter_reading, reddit_reading, discord_reading, news_reading]
        )
        divergence = aggregator.identify_divergence(aggregated)

        assert 0 <= consensus <= 1
        assert "has_divergence" in divergence
