"""Integration tests for Pattern Recognition (Weeks 7-8).

Tests chart patterns, candlestick patterns, and support/resistance detection.
"""

import pytest

from app.application.hunter.pattern_recognition import (
    PatternRecognizer,
    PatternConfig,
    PatternType,
    CandlestickPattern,
    SignalDirection,
    DetectedPattern,
    CandlestickSignal,
    SupportResistanceLevel,
)


class TestPatternConfig:
    """Test pattern recognition configuration."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = PatternConfig()

        assert config.chart_pattern_window == 60
        assert config.candlestick_window == 20
        assert config.support_resistance_window == 90
        assert config.min_pattern_confidence == 0.6
        assert config.price_tolerance == 0.02


class TestChartPatterns:
    """Test chart pattern detection."""

    @pytest.mark.asyncio
    async def test_detect_chart_patterns(self):
        """Test chart pattern detection."""
        recognizer = PatternRecognizer()

        patterns = await recognizer.detect_chart_patterns("BTC")

        assert isinstance(patterns, list)
        for pattern in patterns:
            assert isinstance(pattern, DetectedPattern)
            assert pattern.confidence >= 0.6

    @pytest.mark.asyncio
    async def test_pattern_has_required_fields(self):
        """Test that detected patterns have all required fields."""
        recognizer = PatternRecognizer()

        patterns = await recognizer.detect_chart_patterns("ETH")

        if patterns:  # If any patterns detected
            pattern = patterns[0]
            assert hasattr(pattern, "pattern_type")
            assert hasattr(pattern, "signal")
            assert hasattr(pattern, "confidence")
            assert hasattr(pattern, "start_date")
            assert hasattr(pattern, "end_date")
            assert hasattr(pattern, "key_levels")
            assert hasattr(pattern, "description")

    @pytest.mark.asyncio
    async def test_pattern_signal_direction(self):
        """Test that patterns have valid signal directions."""
        recognizer = PatternRecognizer()

        patterns = await recognizer.detect_chart_patterns("SOL")

        valid_signals = [SignalDirection.BULLISH, SignalDirection.BEARISH, SignalDirection.NEUTRAL]

        for pattern in patterns:
            assert pattern.signal in valid_signals


class TestCandlestickPatterns:
    """Test candlestick pattern detection."""

    @pytest.mark.asyncio
    async def test_detect_candlestick_patterns(self):
        """Test candlestick pattern detection."""
        recognizer = PatternRecognizer()

        signals = await recognizer.detect_candlestick_patterns("BTC")

        assert isinstance(signals, list)
        for signal in signals:
            assert isinstance(signal, CandlestickSignal)
            assert signal.confidence >= 0.6

    @pytest.mark.asyncio
    async def test_doji_patterns(self):
        """Test doji pattern detection."""
        recognizer = PatternRecognizer()

        signals = await recognizer.detect_candlestick_patterns("ETH")

        # Filter to doji patterns
        doji_signals = [
            s for s in signals
            if s.pattern in [
                CandlestickPattern.DOJI,
                CandlestickPattern.DRAGONFLY_DOJI,
                CandlestickPattern.GRAVESTONE_DOJI,
            ]
        ]

        # Doji patterns should exist in typical market data
        # (Not asserting existence as it depends on market conditions)
        for signal in doji_signals:
            assert signal.confidence > 0

    @pytest.mark.asyncio
    async def test_engulfing_patterns(self):
        """Test engulfing pattern detection."""
        recognizer = PatternRecognizer()

        signals = await recognizer.detect_candlestick_patterns("SOL")

        # Filter to engulfing patterns
        engulfing_signals = [
            s for s in signals
            if s.pattern in [
                CandlestickPattern.BULLISH_ENGULFING,
                CandlestickPattern.BEARISH_ENGULFING,
            ]
        ]

        for signal in engulfing_signals:
            assert signal.signal in [SignalDirection.BULLISH, SignalDirection.BEARISH]
            assert signal.confidence >= 0.6


class TestSupportResistance:
    """Test support and resistance level detection."""

    @pytest.mark.asyncio
    async def test_find_support_resistance(self):
        """Test support/resistance detection."""
        recognizer = PatternRecognizer()

        levels = await recognizer.find_support_resistance("BTC")

        assert "support" in levels
        assert "resistance" in levels
        assert isinstance(levels["support"], list)
        assert isinstance(levels["resistance"], list)

    @pytest.mark.asyncio
    async def test_support_level_structure(self):
        """Test support level structure."""
        recognizer = PatternRecognizer()

        levels = await recognizer.find_support_resistance("ETH")

        for support in levels["support"]:
            assert isinstance(support, SupportResistanceLevel)
            assert support.level_type == "support"
            assert 0 <= support.strength <= 1
            assert support.touches >= 2  # At least 2 touches to be a level

    @pytest.mark.asyncio
    async def test_resistance_level_structure(self):
        """Test resistance level structure."""
        recognizer = PatternRecognizer()

        levels = await recognizer.find_support_resistance("SOL")

        for resistance in levels["resistance"]:
            assert isinstance(resistance, SupportResistanceLevel)
            assert resistance.level_type == "resistance"
            assert 0 <= resistance.strength <= 1
            assert resistance.touches >= 2


class TestPatternSerialization:
    """Test pattern serialization."""

    @pytest.mark.asyncio
    async def test_chart_pattern_to_dict(self):
        """Test chart pattern serialization."""
        recognizer = PatternRecognizer()

        patterns = await recognizer.detect_chart_patterns("BTC")

        if patterns:
            data = patterns[0].to_dict()

            # Verify structure
            assert "pattern_type" in data
            assert "signal" in data
            assert "confidence" in data
            assert "start_date" in data
            assert "end_date" in data
            assert "key_levels" in data
            assert "description" in data

    @pytest.mark.asyncio
    async def test_candlestick_signal_to_dict(self):
        """Test candlestick signal serialization."""
        recognizer = PatternRecognizer()

        signals = await recognizer.detect_candlestick_patterns("ETH")

        if signals:
            data = signals[0].to_dict()

            # Verify structure
            assert "pattern" in data
            assert "signal" in data
            assert "confidence" in data
            assert "date" in data
            assert "price" in data
            assert "description" in data

    @pytest.mark.asyncio
    async def test_support_resistance_to_dict(self):
        """Test support/resistance serialization."""
        recognizer = PatternRecognizer()

        levels = await recognizer.find_support_resistance("SOL")

        if levels["support"]:
            data = levels["support"][0].to_dict()

            # Verify structure
            assert "level" in data
            assert "level_type" in data
            assert "strength" in data
            assert "touches" in data
            assert "first_touch" in data
            assert "last_touch" in data


class TestPatternConfidence:
    """Test pattern confidence scoring."""

    @pytest.mark.asyncio
    async def test_confidence_filtering(self):
        """Test that patterns are filtered by confidence."""
        config = PatternConfig(min_pattern_confidence=0.8)
        recognizer = PatternRecognizer(config=config)

        patterns = await recognizer.detect_chart_patterns("BTC")

        # All patterns should meet minimum confidence
        for pattern in patterns:
            assert pattern.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_confidence_range(self):
        """Test that confidence is in valid range."""
        recognizer = PatternRecognizer()

        patterns = await recognizer.detect_chart_patterns("ETH")
        signals = await recognizer.detect_candlestick_patterns("ETH")

        for pattern in patterns:
            assert 0 <= pattern.confidence <= 1

        for signal in signals:
            assert 0 <= signal.confidence <= 1


class TestPatternTypes:
    """Test different pattern type detections."""

    @pytest.mark.asyncio
    async def test_reversal_patterns(self):
        """Test reversal pattern detection."""
        recognizer = PatternRecognizer()

        patterns = await recognizer.detect_chart_patterns("BTC")

        reversal_types = [
            PatternType.HEAD_SHOULDERS,
            PatternType.INVERSE_HEAD_SHOULDERS,
            PatternType.DOUBLE_TOP,
            PatternType.DOUBLE_BOTTOM,
        ]

        reversal_patterns = [p for p in patterns if p.pattern_type in reversal_types]

        # Reversal patterns should have bullish or bearish signal
        for pattern in reversal_patterns:
            assert pattern.signal in [SignalDirection.BULLISH, SignalDirection.BEARISH]

    @pytest.mark.asyncio
    async def test_continuation_patterns(self):
        """Test continuation pattern detection."""
        recognizer = PatternRecognizer()

        patterns = await recognizer.detect_chart_patterns("ETH")

        continuation_types = [
            PatternType.ASCENDING_TRIANGLE,
            PatternType.DESCENDING_TRIANGLE,
            PatternType.SYMMETRICAL_TRIANGLE,
        ]

        continuation_patterns = [p for p in patterns if p.pattern_type in continuation_types]

        # Continuation patterns exist
        # (Not asserting count as it depends on market conditions)
        for pattern in continuation_patterns:
            assert pattern.confidence > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_patterns_handling(self):
        """Test handling when no patterns detected."""
        recognizer = PatternRecognizer()

        # With very high confidence threshold, might get empty list
        config = PatternConfig(min_pattern_confidence=0.99)
        recognizer_strict = PatternRecognizer(config=config)

        patterns = await recognizer_strict.detect_chart_patterns("BTC")

        # Should return empty list, not error
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_multiple_token_analysis(self):
        """Test analyzing multiple tokens."""
        recognizer = PatternRecognizer()

        tokens = ["BTC", "ETH", "SOL"]

        for token in tokens:
            patterns = await recognizer.detect_chart_patterns(token)
            signals = await recognizer.detect_candlestick_patterns(token)
            levels = await recognizer.find_support_resistance(token)

            # Should complete without error
            assert isinstance(patterns, list)
            assert isinstance(signals, list)
            assert isinstance(levels, dict)
