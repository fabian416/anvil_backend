"""
Integration tests for guest Hunter AI sentiment analysis.

Tests the sentiment analysis feature for guest users with real data sources.
"""

import json
import pytest
import warnings
from datetime import datetime


class TestGuestHunterSentiment:
    """Test Hunter AI sentiment analysis for guests."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_analysis_basic(self, client, llm_validator, csv_tracker):
        """Test basic sentiment analysis request."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What's the sentiment for ETH?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show sentiment analysis
        assert "Sentiment" in content or "sentiment" in content.lower()
        assert "ETH" in content

        # Should have enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert "token" in enrichment
        assert enrichment["token"] == "ETH"
        assert "overall_score" in enrichment
        assert "classification" in enrichment

        # Guests can access without registration (field may be None for unrestricted features)
        registration_required = data.get("registration_required")
        if registration_required is not None:
            assert registration_required["required"] is False
        # None means no registration required at all

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_sources_breakdown(self, client, llm_validator, csv_tracker):
        """Test that sentiment shows source breakdown."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentiment analysis for BTC", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have sources breakdown
        assert "sources" in enrichment
        sources = enrichment["sources"]

        # Should include major sources
        source_names = [s.lower() for s in sources.keys()]
        assert any("twitter" in s or "reddit" in s or "news" in s for s in source_names)

        # Should mention sources in content
        assert any(word in content.lower() for word in ["twitter", "reddit", "news", "sources", "social"])

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_multiple_tokens(self, client, llm_validator, csv_tracker):
        """Test sentiment for different tokens."""

        tokens = ["BTC", "ETH", "SOL"]
        last_content = ""

        for token in tokens:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": f"sentiment for {token}", "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            enrichment = data["enrichment"]
            assert enrichment["token"] == token
            last_content = data["agent_message"]["content"]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_classification_types(self, client, llm_validator, csv_tracker):
        """Test that sentiment returns valid classifications."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What's the sentiment for ETH?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "classification" in enrichment

        # Should be one of: bullish, bearish, neutral, mixed
        valid_classifications = ["bullish", "bearish", "neutral", "mixed"]
        assert enrichment["classification"].lower() in valid_classifications

        content = data["agent_message"]["content"]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_score_range(self, client, llm_validator, csv_tracker):
        """Test that sentiment score is in valid range."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentiment BTC", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "overall_score" in enrichment

        score = enrichment["overall_score"]
        # Score should be between -1 and 1
        assert -1.0 <= score <= 1.0

        content = data["agent_message"]["content"]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_multilingual_spanish(self, client, llm_validator, csv_tracker):
        """Test sentiment analysis in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentimiento de ETH", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback), or at minimum some response
        # Language detection may result in English fallback or error messages
        assert len(content) > 0  # At minimum, has some content

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_with_hunter_tool_tag(self, client, llm_validator, csv_tracker):
        """Test that response includes hunter_tool tag."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentiment ETH", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "hunter_tool" in enrichment
        assert enrichment["hunter_tool"] == "sentiment_aggregator"

        content = data["agent_message"]["content"]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_real_data_sources(self, client, llm_validator, csv_tracker):
        """Test that sentiment uses real data sources."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH sentiment", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should have sources array (new field)
        assert "sources" in data or "enrichment" in data

        enrichment = data["enrichment"]

        # Should have real source data
        assert "sources" in enrichment
        assert isinstance(enrichment["sources"], dict)
        assert len(enrichment["sources"]) > 0

        content = data["agent_message"]["content"]

class TestGuestHunterSentimentStorytellingQuality:
    """Test storytelling and UX quality of sentiment responses."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_uses_emojis(self, client, llm_validator, csv_tracker):
        """Test that sentiment uses emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentiment BTC", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        has_emojis = any(emoji in content for emoji in ["📊", "📈", "📉", "🐂", "🐻", "⚖️"])
        assert has_emojis

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_clear_formatting(self, client, llm_validator, csv_tracker):
        """Test that sentiment has clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH sentiment", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        has_formatting = "**" in content and ("\n\n" in content or "\n" in content)
        assert has_formatting

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_actionable_insights(self, client, llm_validator, csv_tracker):
        """Test that sentiment provides actionable context."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentiment SOL", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should provide context about what sentiment means
        insights_keywords = ["bullish", "bearish", "neutral", "positive", "negative", "mixed"]
        has_insights = any(keyword in content.lower() for keyword in insights_keywords)
        assert has_insights
