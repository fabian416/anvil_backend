"""
Integration tests for guest Hunter AI pattern detection.

Tests the chart pattern detection and analysis feature for guest users with real data.
"""

import pytest


class TestGuestHunterPatterns:
    """Test Hunter AI pattern detection for guests."""

    @pytest.mark.asyncio
    async def test_pattern_detection_basic(self, client):
        """Test basic pattern detection request."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What patterns do you see in BTC chart?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show pattern analysis
        assert any(word in content.lower() for word in ["pattern", "chart", "formation", "trend"])
        assert "BTC" in content

        # Should have enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert "token" in enrichment
        assert enrichment["token"] == "BTC"
        assert "patterns" in enrichment or "detected_patterns" in enrichment

        # Guests can access without registration
        assert data["registration_required"]["required"] is False

    @pytest.mark.asyncio
    async def test_pattern_types_classification(self, client):
        """Test that patterns are properly classified."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH chart patterns", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have pattern classifications
        assert "patterns" in enrichment

        # Should mention common pattern types
        pattern_types = ["head and shoulders", "double top", "double bottom", "triangle",
                        "wedge", "flag", "pennant", "channel", "support", "resistance"]
        assert any(pattern in content.lower() for pattern in pattern_types)

    @pytest.mark.asyncio
    async def test_pattern_detection_multiple_tokens(self, client):
        """Test pattern detection for different tokens."""

        tokens = ["BTC", "ETH", "SOL"]

        for token in tokens:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": f"chart patterns for {token}", "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            enrichment = data["enrichment"]
            assert enrichment["token"] == token

    @pytest.mark.asyncio
    async def test_pattern_timeframe_analysis(self, client):
        """Test that patterns show timeframe context."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC chart analysis", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have timeframe information
        assert "timeframe" in enrichment or "patterns" in enrichment

        # Should mention timeframes
        timeframe_keywords = ["1h", "4h", "1d", "hourly", "daily", "weekly", "timeframe"]
        assert any(keyword in content.lower() for keyword in timeframe_keywords)

    @pytest.mark.asyncio
    async def test_pattern_confidence_scores(self, client):
        """Test that patterns include confidence scores."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH chart patterns", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have confidence metrics
        patterns = enrichment.get("patterns", [])
        if patterns and len(patterns) > 0:
            # At least one pattern should have confidence
            assert any("confidence" in p or "strength" in p for p in patterns if isinstance(p, dict))

        # Should mention confidence in content
        confidence_keywords = ["confidence", "strong", "weak", "likely", "probability"]
        assert any(keyword in content.lower() for keyword in confidence_keywords)

    @pytest.mark.asyncio
    async def test_pattern_bullish_bearish_signals(self, client):
        """Test that patterns indicate bullish/bearish implications."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "SOL chart patterns", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have sentiment implications
        assert "sentiment" in enrichment or "implication" in enrichment or "patterns" in enrichment

        # Should mention bullish/bearish context
        sentiment_keywords = ["bullish", "bearish", "reversal", "continuation", "breakout"]
        assert any(keyword in content.lower() for keyword in sentiment_keywords)

    @pytest.mark.asyncio
    async def test_pattern_price_targets(self, client):
        """Test that patterns provide price target projections."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC pattern analysis", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have price targets or projections
        assert "price_targets" in enrichment or "projections" in enrichment or "patterns" in enrichment

        # Should mention targets
        target_keywords = ["target", "projection", "level", "resistance", "support"]
        assert any(keyword in content.lower() for keyword in target_keywords)

    @pytest.mark.asyncio
    async def test_pattern_hunter_tool_tag(self, client):
        """Test that response includes hunter_tool tag."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH chart patterns", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "hunter_tool" in enrichment
        assert enrichment["hunter_tool"] == "pattern_detector"

    @pytest.mark.asyncio
    async def test_pattern_uses_real_chart_data(self, client):
        """Test that patterns use real chart data."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC patterns", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]

        # Should have real chart data or patterns
        assert "patterns" in enrichment or "detected_patterns" in enrichment
        patterns = enrichment.get("patterns") or enrichment.get("detected_patterns")
        assert isinstance(patterns, (list, dict))

    @pytest.mark.asyncio
    async def test_pattern_multilingual_spanish(self, client):
        """Test pattern detection in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "patrones de gráfico para ETH", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback)
        assert any(word in content for word in ["Patrón", "Pattern", "Gráfico", "Chart", "Formación", "Formation"])


class TestGuestHunterPatternsStorytellingQuality:
    """Test storytelling and UX quality of pattern detection responses."""

    @pytest.mark.asyncio
    async def test_pattern_uses_emojis(self, client):
        """Test that pattern analysis uses emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC chart patterns", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert any(emoji in content for emoji in ["📊", "📈", "📉", "🔺", "🔻", "📐", "⚡"])

    @pytest.mark.asyncio
    async def test_pattern_clear_formatting(self, client):
        """Test that patterns have clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH pattern analysis", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        assert "**" in content  # Bold text

        # Should have structured sections
        assert "\n\n" in content or "\n" in content  # Line breaks

    @pytest.mark.asyncio
    async def test_pattern_visual_descriptions(self, client):
        """Test that patterns are described visually."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "SOL chart patterns", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have visual language
        visual_keywords = ["shape", "formation", "line", "level", "peak", "trough", "forming"]
        assert any(keyword in content.lower() for keyword in visual_keywords)

    @pytest.mark.asyncio
    async def test_pattern_actionable_insights(self, client):
        """Test that patterns provide actionable insights."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC patterns", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should provide trading context
        action_keywords = ["watch", "monitor", "breakout", "confirmation", "entry", "exit"]
        assert any(keyword in content.lower() for keyword in action_keywords)

    @pytest.mark.asyncio
    async def test_pattern_educational_context(self, client):
        """Test that patterns include educational explanations."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH chart analysis", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should explain what patterns mean
        educational_keywords = ["typically", "usually", "indicates", "suggests", "means", "signals"]
        assert any(keyword in content.lower() for keyword in educational_keywords)
