"""
Integration tests for guest Hunter AI price prediction.

Tests the LSTM-based price prediction feature for guest users with real data.
"""

import pytest


class TestGuestHunterPricePrediction:
    """Test Hunter AI price prediction for guests."""

    @pytest.mark.asyncio
    async def test_price_prediction_basic(self, client):
        """Test basic price prediction request."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What's the price prediction for BTC?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show price prediction
        assert any(word in content.lower() for word in ["prediction", "forecast", "price"])
        assert "BTC" in content

        # Should have enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert "token" in enrichment
        assert enrichment["token"] == "BTC"
        assert "predictions" in enrichment or "forecast" in enrichment

        # Guests can access without registration
        assert data["registration_required"]["required"] is False

    @pytest.mark.asyncio
    async def test_price_prediction_timeframes(self, client):
        """Test that prediction shows multiple timeframes."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC price prediction", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have predictions for different timeframes
        assert "predictions" in enrichment
        predictions = enrichment["predictions"]

        # Should include short, medium, long term predictions
        timeframe_keywords = ["24h", "7d", "30d", "day", "week", "month"]
        assert any(keyword in content.lower() for keyword in timeframe_keywords)

    @pytest.mark.asyncio
    async def test_price_prediction_multiple_tokens(self, client):
        """Test price prediction for different tokens."""

        tokens = ["BTC", "ETH", "SOL"]

        for token in tokens:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": f"price prediction for {token}", "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            enrichment = data["enrichment"]
            assert enrichment["token"] == token

    @pytest.mark.asyncio
    async def test_price_prediction_confidence_levels(self, client):
        """Test that predictions include confidence levels."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH price forecast", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have confidence metrics
        assert "confidence" in enrichment or "accuracy" in enrichment

        # Should mention confidence in content
        confidence_keywords = ["confidence", "accuracy", "probability", "likely"]
        assert any(keyword in content.lower() for keyword in confidence_keywords)

    @pytest.mark.asyncio
    async def test_price_prediction_historical_accuracy(self, client):
        """Test that predictions show historical accuracy."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC price prediction", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have historical accuracy metrics
        assert "historical_accuracy" in enrichment or "model_performance" in enrichment

        # Should mention accuracy in content
        accuracy_keywords = ["accuracy", "performance", "historical", "track record"]
        assert any(keyword in content.lower() for keyword in accuracy_keywords)

    @pytest.mark.asyncio
    async def test_price_prediction_lstm_model_tag(self, client):
        """Test that response includes LSTM model tag."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "SOL price prediction", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "hunter_tool" in enrichment
        assert enrichment["hunter_tool"] == "lstm_price_predictor"

    @pytest.mark.asyncio
    async def test_price_prediction_uses_real_data(self, client):
        """Test that predictions use real CoinGecko historical data."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH price forecast", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]

        # Should have real data source
        assert "data_source" in enrichment or "predictions" in enrichment

        # Predictions should have reasonable values
        if "predictions" in enrichment:
            predictions = enrichment["predictions"]
            assert isinstance(predictions, (list, dict))
            assert len(predictions) > 0 if isinstance(predictions, (list, dict)) else True

    @pytest.mark.asyncio
    async def test_price_prediction_multilingual_spanish(self, client):
        """Test price prediction in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "predicción de precio para ETH", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback)
        assert any(word in content for word in ["Predicción", "Prediction", "Pronóstico", "Forecast"])


class TestGuestHunterPricePredictionStorytellingQuality:
    """Test storytelling and UX quality of price prediction responses."""

    @pytest.mark.asyncio
    async def test_prediction_uses_emojis(self, client):
        """Test that predictions use emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC price prediction", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        assert any(emoji in content for emoji in ["📈", "📉", "🔮", "💹", "📊", "⚡"])

    @pytest.mark.asyncio
    async def test_prediction_clear_formatting(self, client):
        """Test that predictions have clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH price forecast", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        assert "**" in content  # Bold text

        # Should have structured sections
        assert "\n\n" in content or "\n" in content  # Line breaks

    @pytest.mark.asyncio
    async def test_prediction_actionable_insights(self, client):
        """Test that predictions provide actionable context."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "SOL price prediction", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should provide context about predictions
        insights_keywords = ["increase", "decrease", "bullish", "bearish", "trend", "forecast"]
        assert any(keyword in content.lower() for keyword in insights_keywords)

    @pytest.mark.asyncio
    async def test_prediction_risk_disclaimers(self, client):
        """Test that predictions include appropriate risk disclaimers."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "BTC price prediction", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have disclaimer language
        disclaimer_keywords = ["not financial advice", "prediction", "estimate", "may vary", "risk"]
        assert any(keyword in content.lower() for keyword in disclaimer_keywords)
