"""Integration tests for LSTM price prediction (Days 4-5).

Tests price data service, LSTM model, and prediction API.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from app.application.hunter.price_data_service import (
    PriceDataService,
    PriceDataConfig,
    PricePoint,
)
from app.application.hunter.lstm_price_predictor import (
    LSTMPricePredictor,
    LSTMConfig,
)


class TestPriceDataService:
    """Test price data service."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_fetch_historical_prices(self):
        """Test fetching historical price data."""
        service = PriceDataService()

        prices = await service.fetch_historical_prices("ETH", days=30)

        assert len(prices) > 0
        assert all(isinstance(p, PricePoint) for p in prices)
        assert all(p.close > 0 for p in prices)
        assert all(p.volume > 0 for p in prices)

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_price_data_config_defaults(self):
        """Test price data config defaults."""
        config = PriceDataConfig()

        assert config.primary_source == "coingecko"
        assert config.default_interval == "1h"
        assert config.default_lookback_days == 90
        assert config.include_volume is True

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_latest_price(self):
        """Test getting latest price."""
        service = PriceDataService()

        latest = await service.get_latest_price("ETH")

        assert latest is not None
        assert isinstance(latest, PricePoint)
        assert latest.close > 0

    def test_preprocess_for_lstm(self):
        """Test LSTM data preprocessing."""
        service = PriceDataService()

        # Create sample prices
        prices = [
            PricePoint(
                timestamp=datetime.utcnow() - timedelta(hours=i),
                open=2000.0 + i,
                high=2010.0 + i,
                low=1990.0 + i,
                close=2005.0 + i,
                volume=1000000.0,
            )
            for i in range(100)
        ]

        X, y, scaler = service.preprocess_for_lstm(prices, sequence_length=10)

        assert X.shape[0] == len(prices) - 10
        assert X.shape[1] == 10  # sequence_length
        assert X.shape[2] == 5  # OHLCV features
        assert y.shape[0] == len(prices) - 10
        assert "min" in scaler
        assert "max" in scaler

    def test_denormalize_prediction(self):
        """Test denormalizing predictions."""
        service = PriceDataService()

        scaler_params = {
            "min": np.array([1900, 1950, 1850, 1920, 500000]),
            "max": np.array([2100, 2150, 2050, 2080, 2000000]),
        }

        # Normalize and denormalize
        original_value = 2000.0
        normalized = (original_value - scaler_params["min"][3]) / (
            scaler_params["max"][3] - scaler_params["min"][3] + 1e-8
        )
        denormalized = service.denormalize_prediction(
            normalized, scaler_params, target_column="close"
        )

        assert abs(denormalized - original_value) < 1.0

    def test_calculate_technical_indicators(self):
        """Test technical indicator calculation."""
        service = PriceDataService()

        # Create sample prices
        prices = [
            PricePoint(
                timestamp=datetime.utcnow() - timedelta(hours=i),
                open=2000.0 + i,
                high=2010.0 + i,
                low=1990.0 + i,
                close=2005.0 + i * 0.5,  # Slight uptrend
                volume=1000000.0,
            )
            for i in range(100)
        ]

        indicators = service.calculate_technical_indicators(prices)

        assert "sma_7" in indicators
        assert "sma_25" in indicators
        assert "ema_12" in indicators
        assert "rsi" in indicators
        assert "macd" in indicators

        # Verify indicator lengths
        assert len(indicators["sma_7"]) == len(prices)
        assert len(indicators["rsi"]) == len(prices)


class TestLSTMPricePredictor:
    """Test LSTM price predictor."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lstm_model_initialization(self):
        """Test LSTM model initialization."""
        config = LSTMConfig(epochs=2)  # Reduced for testing
        predictor = LSTMPricePredictor(config=config)

        assert predictor.model is not None
        assert predictor.is_trained is False

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lstm_training(self):
        """Test LSTM model training."""
        config = LSTMConfig(epochs=2, batch_size=16)  # Fast training for tests
        predictor = LSTMPricePredictor(config=config)

        metrics = await predictor.train("ETH", days=30)

        assert "token_symbol" in metrics
        assert metrics["token_symbol"] == "ETH"
        assert "final_train_loss" in metrics
        assert "final_val_loss" in metrics
        assert metrics["epochs"] == 2
        assert predictor.is_trained is True

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lstm_prediction(self):
        """Test LSTM price prediction."""
        config = LSTMConfig(epochs=2)  # Fast training
        predictor = LSTMPricePredictor(config=config)

        # Train first
        await predictor.train("ETH", days=30)

        # Predict
        prediction = await predictor.predict("ETH", horizon_hours=24)

        assert prediction.token_symbol == "ETH"
        assert prediction.predicted_price > 0
        assert 0 <= prediction.confidence <= 1
        assert prediction.direction in ["up", "down", "neutral"]
        assert prediction.horizon_hours == 24

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lstm_multi_horizon_prediction(self):
        """Test multi-horizon predictions."""
        config = LSTMConfig(epochs=2)
        predictor = LSTMPricePredictor(config=config)

        predictions = await predictor.predict_multi_horizon("ETH")

        assert "24h" in predictions
        assert "7d" in predictions
        assert predictions["24h"].horizon_hours == 24
        assert predictions["7d"].horizon_hours == 168

    def test_get_model_info(self):
        """Test getting model information."""
        predictor = LSTMPricePredictor()

        info = predictor.get_model_info()

        assert info["architecture"] == "LSTM"
        assert info["layers"] == 3
        assert info["hidden_size"] == 128
        assert "total_parameters" in info
        assert info["device"] in ["cpu", "cuda"]


class TestLSTMConfig:
    """Test LSTM configuration."""

    def test_lstm_config_defaults(self):
        """Test LSTM config default values."""
        config = LSTMConfig()

        assert config.input_size == 5  # OHLCV
        assert config.hidden_size == 128
        assert config.num_layers == 3
        assert config.dropout == 0.2
        assert config.sequence_length == 60
        assert config.batch_size == 32
        assert config.learning_rate == 0.001
        assert config.epochs == 50

    def test_lstm_config_custom(self):
        """Test LSTM config with custom values."""
        config = LSTMConfig(
            hidden_size=64,
            num_layers=2,
            epochs=10,
            batch_size=16,
        )

        assert config.hidden_size == 64
        assert config.num_layers == 2
        assert config.epochs == 10
        assert config.batch_size == 16


class TestPricePredictionIntegration:
    """Integration tests for complete prediction flow."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_end_to_end_prediction_flow(self):
        """Test complete prediction pipeline."""
        # Create service and predictor
        config = LSTMConfig(epochs=2)  # Fast for testing
        predictor = LSTMPricePredictor(config=config)

        # Train
        train_metrics = await predictor.train("ETH", days=30)
        assert train_metrics["token_symbol"] == "ETH"
        assert predictor.is_trained is True

        # Predict 24h
        prediction_24h = await predictor.predict("ETH", horizon_hours=24)
        assert prediction_24h.current_price > 0
        assert prediction_24h.predicted_price > 0
        assert prediction_24h.confidence > 0

        # Predict 7d
        prediction_7d = await predictor.predict("ETH", horizon_hours=168)
        assert prediction_7d.horizon_hours == 168

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_prediction_without_training(self):
        """Test prediction automatically trains if needed."""
        config = LSTMConfig(epochs=2)
        predictor = LSTMPricePredictor(config=config)

        assert predictor.is_trained is False

        # Predict should auto-train
        prediction = await predictor.predict("BTC", horizon_hours=24)

        assert predictor.is_trained is True
        assert prediction.token_symbol == "BTC"
        assert prediction.predicted_price > 0

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_prediction_accuracy_metrics(self):
        """Test prediction includes accuracy metrics."""
        config = LSTMConfig(epochs=2)
        predictor = LSTMPricePredictor(config=config)

        prediction = await predictor.predict("ETH", horizon_hours=24)

        # Verify all expected fields
        assert hasattr(prediction, "token_symbol")
        assert hasattr(prediction, "current_price")
        assert hasattr(prediction, "predicted_price")
        assert hasattr(prediction, "confidence")
        assert hasattr(prediction, "change_percent")
        assert hasattr(prediction, "direction")

        # Verify confidence is reasonable
        assert 0 < prediction.confidence < 1

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multiple_token_predictions(self):
        """Test predicting multiple tokens."""
        config = LSTMConfig(epochs=2)

        tokens = ["ETH", "BTC", "SOL"]
        predictions = {}

        for token in tokens:
            predictor = LSTMPricePredictor(config=config)
            pred = await predictor.predict(token, horizon_hours=24)
            predictions[token] = pred

        # Verify all predictions
        assert len(predictions) == 3
        for token, pred in predictions.items():
            assert pred.token_symbol == token
