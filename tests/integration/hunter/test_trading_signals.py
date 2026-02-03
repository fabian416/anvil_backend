"""Integration tests for AI Trading Signals (Weeks 3-4).

Tests signal generation, multi-timeframe analysis, and trading recommendations.
"""

import pytest

from app.application.hunter.trading_signal_generator import (
    TradingSignalGenerator,
    SignalConfig,
    SignalType,
    Timeframe,
    TradingSignal,
    MultiTimeframeAnalysis,
)


class TestSignalConfig:
    """Test signal configuration."""

    def test_signal_config_defaults(self):
        """Test default configuration values."""
        config = SignalConfig()

        assert config.strong_buy_threshold == 75.0
        assert config.buy_threshold == 60.0
        assert config.hold_threshold == 40.0
        assert config.sell_threshold == 25.0

        # Weights sum to 1.0
        assert (
            config.sentiment_weight + config.prediction_weight + config.risk_weight
            == 1.0
        )

    def test_signal_config_custom(self):
        """Test custom configuration."""
        config = SignalConfig(
            strong_buy_threshold=80.0,
            sentiment_weight=0.40,
            prediction_weight=0.30,
            risk_weight=0.30,
        )

        assert config.strong_buy_threshold == 80.0
        assert config.sentiment_weight == 0.40


class TestSignalGeneration:
    """Test basic signal generation."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_generate_signal_eth(self):
        """Test generating signal for ETH."""
        generator = TradingSignalGenerator()

        signal = await generator.generate_signal("ETH", Timeframe.DAY_1)

        assert isinstance(signal, TradingSignal)
        assert signal.token_symbol == "ETH"
        assert signal.signal_type in [
            SignalType.BUY,
            SignalType.SELL,
            SignalType.HOLD,
            SignalType.STRONG_BUY,
            SignalType.STRONG_SELL,
        ]
        assert 0 <= signal.signal_strength <= 100
        assert 0 <= signal.confidence <= 1

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_generate_signal_btc(self):
        """Test generating signal for BTC."""
        generator = TradingSignalGenerator()

        signal = await generator.generate_signal("BTC", Timeframe.DAY_1)

        assert signal.token_symbol == "BTC"
        assert signal.timeframe == Timeframe.DAY_1
        assert signal.generated_at is not None

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_signal_has_all_factors(self):
        """Test that signal includes all factor scores."""
        generator = TradingSignalGenerator()

        signal = await generator.generate_signal("SOL", Timeframe.DAY_1)

        # All factors should be present
        assert 0 <= signal.sentiment_score <= 100
        assert 0 <= signal.prediction_score <= 100
        assert 0 <= signal.risk_score <= 100


class TestEntryExitPrices:
    """Test entry/exit price calculations."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_buy_signal_has_prices(self):
        """Test that BUY signals include entry/exit prices."""
        generator = TradingSignalGenerator()

        # Generate multiple signals to find a BUY
        for token in ["ETH", "BTC", "SOL", "AVAX"]:
            signal = await generator.generate_signal(token, Timeframe.DAY_1)

            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                assert signal.entry_price is not None
                assert signal.stop_loss_price is not None
                assert signal.take_profit_price is not None

                # Stop-loss should be below entry
                assert signal.stop_loss_price < signal.entry_price

                # Take-profit should be above entry
                assert signal.take_profit_price > signal.entry_price
                break

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_hold_signal_no_prices(self):
        """Test that HOLD signals don't have entry/exit prices."""
        generator = TradingSignalGenerator()

        # Generate signals until we find a HOLD
        for token in ["ETH", "BTC", "SOL", "AVAX", "BNB"]:
            signal = await generator.generate_signal(token, Timeframe.DAY_1)

            if signal.signal_type == SignalType.HOLD:
                # HOLD signals should not have prices
                assert signal.entry_price is None
                assert signal.stop_loss_price is None
                assert signal.take_profit_price is None
                break


class TestMultiTimeframeAnalysis:
    """Test multi-timeframe analysis."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multi_timeframe_analysis(self):
        """Test generating multi-timeframe analysis."""
        generator = TradingSignalGenerator()

        analysis = await generator.generate_multi_timeframe_analysis("ETH")

        assert isinstance(analysis, MultiTimeframeAnalysis)
        assert analysis.token_symbol == "ETH"
        assert len(analysis.signals) == 3  # 4h, 1d, 1w

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multi_timeframe_has_all_timeframes(self):
        """Test that analysis includes all expected timeframes."""
        generator = TradingSignalGenerator()

        analysis = await generator.generate_multi_timeframe_analysis("BTC")

        expected_timeframes = [Timeframe.HOUR_4, Timeframe.DAY_1, Timeframe.WEEK_1]

        for tf in expected_timeframes:
            assert tf in analysis.signals
            assert isinstance(analysis.signals[tf], TradingSignal)

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_consensus_signal_valid(self):
        """Test that consensus signal is valid."""
        generator = TradingSignalGenerator()

        analysis = await generator.generate_multi_timeframe_analysis("SOL")

        assert analysis.consensus_signal in [
            SignalType.BUY,
            SignalType.SELL,
            SignalType.HOLD,
            SignalType.STRONG_BUY,
            SignalType.STRONG_SELL,
        ]

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_alignment_score_valid(self):
        """Test that alignment score is between 0 and 1."""
        generator = TradingSignalGenerator()

        analysis = await generator.generate_multi_timeframe_analysis("AVAX")

        assert 0 <= analysis.alignment_score <= 1

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_trend_direction_valid(self):
        """Test that trend direction is valid."""
        generator = TradingSignalGenerator()

        analysis = await generator.generate_multi_timeframe_analysis("BNB")

        assert analysis.trend_direction in ["bullish", "bearish", "neutral"]


class TestSignalRecommendations:
    """Test signal recommendations."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_signal_has_recommendation(self):
        """Test that signals include human-readable recommendation."""
        generator = TradingSignalGenerator()

        signal = await generator.generate_signal("ETH", Timeframe.DAY_1)

        assert isinstance(signal.recommendation, str)
        assert len(signal.recommendation) > 20  # Should be meaningful

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_recommendation_mentions_signal_type(self):
        """Test that recommendation mentions the signal type."""
        generator = TradingSignalGenerator()

        signal = await generator.generate_signal("BTC", Timeframe.DAY_1)

        # Recommendation should mention the signal type
        recommendation_lower = signal.recommendation.lower()
        signal_type_lower = signal.signal_type.value.lower()

        assert signal_type_lower in recommendation_lower


class TestSignalSerialization:
    """Test signal serialization."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_signal_to_dict(self):
        """Test signal serialization to dictionary."""
        generator = TradingSignalGenerator()

        signal = await generator.generate_signal("ETH", Timeframe.DAY_1)
        data = signal.to_dict()

        # Verify structure
        assert "token_symbol" in data
        assert "signal_type" in data
        assert "signal_strength" in data
        assert "confidence" in data
        assert "sentiment_score" in data
        assert "prediction_score" in data
        assert "risk_score" in data
        assert "timeframe" in data
        assert "recommendation" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multi_timeframe_to_dict(self):
        """Test multi-timeframe analysis serialization."""
        generator = TradingSignalGenerator()

        analysis = await generator.generate_multi_timeframe_analysis("BTC")
        data = analysis.to_dict()

        # Verify structure
        assert "token_symbol" in data
        assert "signals" in data
        assert "consensus_signal" in data
        assert "alignment_score" in data
        assert "trend_direction" in data

        # Verify nested signals
        for tf_value, signal_data in data["signals"].items():
            assert "signal_type" in signal_data
            assert "signal_strength" in signal_data


class TestSignalIntegration:
    """Integration tests for complete signal flow."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multiple_token_signals(self):
        """Test generating signals for multiple tokens."""
        generator = TradingSignalGenerator()

        tokens = ["ETH", "BTC", "SOL"]
        signals = {}

        for token in tokens:
            signal = await generator.generate_signal(token, Timeframe.DAY_1)
            signals[token] = signal

        # Verify all signals generated
        assert len(signals) == 3
        for token, signal in signals.items():
            assert signal.token_symbol == token

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_different_timeframes(self):
        """Test signal generation across different timeframes."""
        generator = TradingSignalGenerator()

        timeframes = [Timeframe.HOUR_4, Timeframe.DAY_1, Timeframe.WEEK_1]
        signals = {}

        for tf in timeframes:
            signal = await generator.generate_signal("ETH", tf)
            signals[tf] = signal

        # Verify all timeframes generated
        assert len(signals) == 3
        for tf, signal in signals.items():
            assert signal.timeframe == tf

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_signal_consistency(self):
        """Test that multiple runs produce consistent results."""
        generator = TradingSignalGenerator()

        # Generate twice
        signal1 = await generator.generate_signal("BTC", Timeframe.DAY_1)
        signal2 = await generator.generate_signal("BTC", Timeframe.DAY_1)

        # Should be identical (deterministic with same data)
        assert signal1.signal_type == signal2.signal_type
