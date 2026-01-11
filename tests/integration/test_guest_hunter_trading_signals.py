"""
Integration tests for guest Hunter AI trading signals.

Tests the buy/sell signal recommendation feature for guest users with real data.
"""

import pytest


class TestGuestHunterTradingSignals:
    """Test Hunter AI trading signals for guests."""

    @pytest.mark.asyncio
    async def test_trading_signals_basic(self, client):
        """Test basic trading signals request."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What are the trading signals for BTC?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show trading signals
        assert any(word in content.lower() for word in ["signal", "buy", "sell", "trading", "trade"])
        assert "BTC" in content

        # Should have enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert "token" in enrichment
        assert enrichment["token"] == "BTC"
        assert "signal" in enrichment or "recommendation" in enrichment

        # Guests can access without registration
        assert data["registration_required"]["required"] is False

    @pytest.mark.asyncio
    async def test_trading_signals_signal_types(self, client):
        """Test that trading signals show valid signal types."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH trading signals", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have signal classification
        assert "signal" in enrichment

        # Should be one of: buy, sell, hold, neutral
        valid_signals = ["buy", "sell", "hold", "neutral"]
        assert enrichment["signal"].lower() in valid_signals

        # Should mention signal in content
        assert any(signal in content.lower() for signal in valid_signals)

    @pytest.mark.asyncio
    async def test_trading_signals_strength_levels(self, client):
        """Test that trading signals show strength levels."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC trading recommendations", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have signal strength
        assert "strength" in enrichment or "confidence" in enrichment

        # Should mention strength in content
        strength_keywords = ["strong", "weak", "moderate", "confidence", "strength"]
        assert any(keyword in content.lower() for keyword in strength_keywords)

    @pytest.mark.asyncio
    async def test_trading_signals_multiple_tokens(self, client):
        """Test trading signals for different tokens."""

        tokens = ["BTC", "ETH", "SOL"]

        for token in tokens:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": f"trading signals for {token}", "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            enrichment = data["enrichment"]
            assert enrichment["token"] == token
            assert "signal" in enrichment

    @pytest.mark.asyncio
    async def test_trading_signals_technical_indicators(self, client):
        """Test that signals include technical indicators."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH buy sell signals", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have technical indicators
        assert "indicators" in enrichment or "technical" in enrichment

        # Should mention technical analysis
        ta_keywords = ["rsi", "macd", "moving average", "support", "resistance", "indicator"]
        assert any(keyword in content.lower() for keyword in ta_keywords)

    @pytest.mark.asyncio
    async def test_trading_signals_entry_exit_points(self, client):
        """Test that signals provide entry/exit recommendations."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC trading signals", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have entry/exit points
        assert "entry_point" in enrichment or "exit_point" in enrichment or "price_target" in enrichment

        # Should mention price levels
        price_keywords = ["entry", "exit", "target", "level", "price", "zone"]
        assert any(keyword in content.lower() for keyword in price_keywords)

    @pytest.mark.asyncio
    async def test_trading_signals_stop_loss_recommendations(self, client):
        """Test that signals include risk management."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "SOL trading recommendations", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have risk management suggestions
        assert "stop_loss" in enrichment or "risk_management" in enrichment

        # Should mention risk management
        risk_keywords = ["stop loss", "risk", "protect", "limit", "manage"]
        assert any(keyword in content.lower() for keyword in risk_keywords)

    @pytest.mark.asyncio
    async def test_trading_signals_hunter_tool_tag(self, client):
        """Test that response includes hunter_tool tag."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC trading signals", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "hunter_tool" in enrichment
        assert enrichment["hunter_tool"] == "trading_signal_generator"

    @pytest.mark.asyncio
    async def test_trading_signals_uses_real_data(self, client):
        """Test that signals use real price and volume data."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH buy sell signals", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]

        # Should have real market data
        assert "current_price" in enrichment or "market_data" in enrichment
        assert isinstance(enrichment.get("signal"), str)

    @pytest.mark.asyncio
    async def test_trading_signals_multilingual_spanish(self, client):
        """Test trading signals in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "señales de trading para BTC", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback)
        assert any(word in content for word in ["Señal", "Signal", "Compra", "Buy", "Venta", "Sell"])


class TestGuestHunterTradingSignalsStorytellingQuality:
    """Test storytelling and UX quality of trading signal responses."""

    @pytest.mark.asyncio
    async def test_trading_signals_uses_emojis(self, client):
        """Test that trading signals use emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC trading signals", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert any(emoji in content for emoji in ["📊", "📈", "📉", "🟢", "🔴", "💹", "⚡"])

    @pytest.mark.asyncio
    async def test_trading_signals_clear_formatting(self, client):
        """Test that trading signals have clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH buy sell signals", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        assert "**" in content  # Bold text

        # Should have structured sections
        assert "\n\n" in content or "\n" in content  # Line breaks

    @pytest.mark.asyncio
    async def test_trading_signals_clear_recommendations(self, client):
        """Test that recommendations are clearly stated."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "SOL trading signals", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have clear action verbs
        action_keywords = ["buy", "sell", "hold", "enter", "exit", "consider"]
        assert any(keyword in content.lower() for keyword in action_keywords)

    @pytest.mark.asyncio
    async def test_trading_signals_disclaimers(self, client):
        """Test that signals include appropriate disclaimers."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC trading signals", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have disclaimer language
        disclaimer_keywords = ["not financial advice", "dyor", "research", "risk", "own decision"]
        assert any(keyword in content.lower() for keyword in disclaimer_keywords)

    @pytest.mark.asyncio
    async def test_trading_signals_educational_context(self, client):
        """Test that signals provide educational context."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH trading recommendations", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should explain the reasoning
        reasoning_keywords = ["because", "due to", "based on", "indicates", "suggests"]
        assert any(keyword in content.lower() for keyword in reasoning_keywords)
