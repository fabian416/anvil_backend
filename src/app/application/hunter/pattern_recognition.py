"""Technical pattern recognition for chart and candlestick analysis.

Implements detection of:
- Chart patterns (head & shoulders, triangles, flags, etc.)
- Candlestick patterns (doji, hammer, engulfing, etc.)
- Support/resistance levels
- Breakout identification

Based on Hunter AI Bot's pattern recognition module.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy as np

from app.application.hunter.price_data_service import PriceDataService, PricePoint


class PatternType(str, Enum):
    """Chart pattern types."""

    # Reversal patterns
    HEAD_SHOULDERS = "head_and_shoulders"
    INVERSE_HEAD_SHOULDERS = "inverse_head_and_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_TOP = "triple_top"
    TRIPLE_BOTTOM = "triple_bottom"

    # Continuation patterns
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRICAL_TRIANGLE = "symmetrical_triangle"
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    PENNANT = "pennant"
    RISING_WEDGE = "rising_wedge"
    FALLING_WEDGE = "falling_wedge"


class CandlestickPattern(str, Enum):
    """Candlestick pattern types."""

    # Single candle patterns
    DOJI = "doji"
    DRAGONFLY_DOJI = "dragonfly_doji"
    GRAVESTONE_DOJI = "gravestone_doji"
    HAMMER = "hammer"
    HANGING_MAN = "hanging_man"
    SHOOTING_STAR = "shooting_star"
    INVERTED_HAMMER = "inverted_hammer"

    # Two candle patterns
    BULLISH_ENGULFING = "bullish_engulfing"
    BEARISH_ENGULFING = "bearish_engulfing"
    BULLISH_HARAMI = "bullish_harami"
    BEARISH_HARAMI = "bearish_harami"
    PIERCING_LINE = "piercing_line"
    DARK_CLOUD_COVER = "dark_cloud_cover"

    # Three candle patterns
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"
    THREE_WHITE_SOLDIERS = "three_white_soldiers"
    THREE_BLACK_CROWS = "three_black_crows"


class SignalDirection(str, Enum):
    """Pattern signal direction."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class PatternConfig:
    """Configuration for pattern recognition."""

    # Lookback periods
    chart_pattern_window: int = 60  # Days for chart patterns
    candlestick_window: int = 20  # Days for candlestick patterns
    support_resistance_window: int = 90  # Days for S/R levels

    # Thresholds
    min_pattern_confidence: float = 0.6  # Minimum confidence to report
    price_tolerance: float = 0.02  # 2% tolerance for level matching
    volume_multiplier: float = 1.5  # Volume spike threshold


@dataclass
class DetectedPattern:
    """Detected chart pattern."""

    pattern_type: PatternType
    signal: SignalDirection
    confidence: float  # 0-1
    start_date: datetime
    end_date: datetime
    key_levels: Dict[str, float]  # e.g., {"neckline": 2000, "target": 2100}
    description: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "pattern_type": self.pattern_type.value,
            "signal": self.signal.value,
            "confidence": round(self.confidence, 2),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "key_levels": {k: round(v, 2) for k, v in self.key_levels.items()},
            "description": self.description,
        }


@dataclass
class CandlestickSignal:
    """Detected candlestick pattern."""

    pattern: CandlestickPattern
    signal: SignalDirection
    confidence: float
    date: datetime
    price: float
    description: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "pattern": self.pattern.value,
            "signal": self.signal.value,
            "confidence": round(self.confidence, 2),
            "date": self.date.isoformat(),
            "price": round(self.price, 2),
            "description": self.description,
        }


@dataclass
class SupportResistanceLevel:
    """Support or resistance level."""

    level: float
    level_type: str  # "support" or "resistance"
    strength: float  # 0-1
    touches: int  # Number of times price touched this level
    first_touch: datetime
    last_touch: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "level": round(self.level, 2),
            "level_type": self.level_type,
            "strength": round(self.strength, 2),
            "touches": self.touches,
            "first_touch": self.first_touch.isoformat(),
            "last_touch": self.last_touch.isoformat(),
        }


class PatternRecognizer:
    """Technical pattern recognition engine.

    Detects chart patterns, candlestick patterns, and support/resistance levels.
    """

    def __init__(
        self,
        config: PatternConfig = None,
        price_service: PriceDataService = None,
    ):
        """Initialize pattern recognizer.

        Args:
            config: Pattern recognition configuration
            price_service: Price data service
        """
        self.config = config or PatternConfig()
        self.price_service = price_service or PriceDataService()

    async def detect_chart_patterns(
        self, token_symbol: str
    ) -> List[DetectedPattern]:
        """Detect chart patterns.

        Args:
            token_symbol: Token symbol

        Returns:
            List of detected patterns

        Example:
            >>> recognizer = PatternRecognizer()
            >>> patterns = await recognizer.detect_chart_patterns("BTC")
            >>> for p in patterns:
            ...     print(f"{p.pattern_type}: {p.signal} (confidence: {p.confidence})")
        """
        # Fetch price data
        prices = await self.price_service.fetch_historical_prices(
            token_symbol, days=self.config.chart_pattern_window
        )

        patterns = []

        # Detect reversal patterns
        patterns.extend(self._detect_head_shoulders(prices))
        patterns.extend(self._detect_double_patterns(prices))
        patterns.extend(self._detect_triple_patterns(prices))

        # Detect continuation patterns
        patterns.extend(self._detect_triangles(prices))
        patterns.extend(self._detect_flags(prices))
        patterns.extend(self._detect_wedges(prices))

        # Filter by minimum confidence
        patterns = [
            p for p in patterns if p.confidence >= self.config.min_pattern_confidence
        ]

        return patterns

    async def detect_candlestick_patterns(
        self, token_symbol: str
    ) -> List[CandlestickSignal]:
        """Detect candlestick patterns.

        Args:
            token_symbol: Token symbol

        Returns:
            List of detected candlestick patterns

        Example:
            >>> recognizer = PatternRecognizer()
            >>> signals = await recognizer.detect_candlestick_patterns("ETH")
            >>> for s in signals:
            ...     print(f"{s.pattern}: {s.signal}")
        """
        # Fetch recent price data
        prices = await self.price_service.fetch_historical_prices(
            token_symbol, days=self.config.candlestick_window
        )

        signals = []

        # Single candle patterns
        signals.extend(self._detect_doji_patterns(prices))
        signals.extend(self._detect_hammer_patterns(prices))

        # Two candle patterns
        signals.extend(self._detect_engulfing_patterns(prices))
        signals.extend(self._detect_harami_patterns(prices))

        # Three candle patterns
        signals.extend(self._detect_star_patterns(prices))
        signals.extend(self._detect_soldier_crow_patterns(prices))

        # Filter by confidence
        signals = [
            s for s in signals if s.confidence >= self.config.min_pattern_confidence
        ]

        return signals

    async def find_support_resistance(
        self, token_symbol: str
    ) -> Dict[str, List[SupportResistanceLevel]]:
        """Find support and resistance levels.

        Args:
            token_symbol: Token symbol

        Returns:
            Dictionary with "support" and "resistance" level lists

        Example:
            >>> recognizer = PatternRecognizer()
            >>> levels = await recognizer.find_support_resistance("SOL")
            >>> print(f"Support: {levels['support']}")
            >>> print(f"Resistance: {levels['resistance']}")
        """
        # Fetch price data
        prices = await self.price_service.fetch_historical_prices(
            token_symbol, days=self.config.support_resistance_window
        )

        # Find local extrema
        highs = self._find_local_maxima(prices)
        lows = self._find_local_minima(prices)

        # Cluster resistance levels
        resistance_levels = self._cluster_levels(highs, "resistance")

        # Cluster support levels
        support_levels = self._cluster_levels(lows, "support")

        return {
            "support": support_levels,
            "resistance": resistance_levels,
        }

    def _detect_head_shoulders(self, prices: List[PricePoint]) -> List[DetectedPattern]:
        """Detect head and shoulders patterns."""
        patterns = []

        if len(prices) < 30:
            return patterns

        # Simplified detection: Look for 5 peaks with middle highest (head)
        highs = [p.high for p in prices]
        closes = [p.close for p in prices]

        # Find peaks
        peaks = []
        for i in range(5, len(highs) - 5):
            if highs[i] > max(highs[i-5:i]) and highs[i] > max(highs[i+1:i+6]):
                peaks.append((i, highs[i]))

        # Look for H&S pattern in peaks
        if len(peaks) >= 3:
            for i in range(len(peaks) - 2):
                left_shoulder = peaks[i]
                head = peaks[i + 1]
                right_shoulder = peaks[i + 2]

                # Head should be higher than shoulders
                if head[1] > left_shoulder[1] and head[1] > right_shoulder[1]:
                    # Shoulders should be roughly equal
                    shoulder_diff = abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1]

                    if shoulder_diff < 0.05:  # Within 5%
                        # Neckline is the low between shoulders
                        neckline = min(closes[left_shoulder[0]:right_shoulder[0]])

                        confidence = 0.7 - (shoulder_diff * 2)  # Adjust for symmetry

                        patterns.append(DetectedPattern(
                            pattern_type=PatternType.HEAD_SHOULDERS,
                            signal=SignalDirection.BEARISH,
                            confidence=confidence,
                            start_date=prices[left_shoulder[0]].timestamp,
                            end_date=prices[right_shoulder[0]].timestamp,
                            key_levels={
                                "left_shoulder": left_shoulder[1],
                                "head": head[1],
                                "right_shoulder": right_shoulder[1],
                                "neckline": neckline,
                                "target": neckline - (head[1] - neckline),
                            },
                            description="Head and shoulders pattern indicates bearish reversal",
                        ))

        return patterns

    def _detect_double_patterns(self, prices: List[PricePoint]) -> List[DetectedPattern]:
        """Detect double top/bottom patterns."""
        patterns = []

        if len(prices) < 20:
            return patterns

        highs = [p.high for p in prices]
        lows = [p.low for p in prices]

        # Find peaks for double top
        peaks = []
        for i in range(3, len(highs) - 3):
            if highs[i] > max(highs[i-3:i]) and highs[i] > max(highs[i+1:i+4]):
                peaks.append((i, highs[i]))

        # Check for double top
        if len(peaks) >= 2:
            for i in range(len(peaks) - 1):
                peak1 = peaks[i]
                peak2 = peaks[i + 1]

                price_diff = abs(peak1[1] - peak2[1]) / peak1[1]

                if price_diff < 0.03:  # Within 3%
                    neckline = min(lows[peak1[0]:peak2[0]])
                    confidence = 0.75 - (price_diff * 5)

                    patterns.append(DetectedPattern(
                        pattern_type=PatternType.DOUBLE_TOP,
                        signal=SignalDirection.BEARISH,
                        confidence=confidence,
                        start_date=prices[peak1[0]].timestamp,
                        end_date=prices[peak2[0]].timestamp,
                        key_levels={
                            "peak1": peak1[1],
                            "peak2": peak2[1],
                            "neckline": neckline,
                            "target": neckline - (peak1[1] - neckline),
                        },
                        description="Double top pattern indicates bearish reversal",
                    ))

        return patterns

    def _detect_triple_patterns(self, prices: List[PricePoint]) -> List[DetectedPattern]:
        """Detect triple top/bottom patterns."""
        # Similar to double patterns but with 3 peaks/troughs
        # Simplified for now
        return []

    def _detect_triangles(self, prices: List[PricePoint]) -> List[DetectedPattern]:
        """Detect triangle patterns (ascending, descending, symmetrical)."""
        patterns = []

        if len(prices) < 30:
            return patterns

        highs = [p.high for p in prices[-30:]]
        lows = [p.low for p in prices[-30:]]

        # Fit trend lines
        x = np.arange(len(highs))
        upper_slope = np.polyfit(x, highs, 1)[0]
        lower_slope = np.polyfit(x, lows, 1)[0]

        # Ascending triangle: flat resistance, rising support
        if abs(upper_slope) < 0.01 and lower_slope > 0.02:
            patterns.append(DetectedPattern(
                pattern_type=PatternType.ASCENDING_TRIANGLE,
                signal=SignalDirection.BULLISH,
                confidence=0.7,
                start_date=prices[-30].timestamp,
                end_date=prices[-1].timestamp,
                key_levels={
                    "resistance": max(highs),
                    "support_start": lows[0],
                    "support_end": lows[-1],
                },
                description="Ascending triangle indicates bullish breakout potential",
            ))

        # Descending triangle: falling resistance, flat support
        elif upper_slope < -0.02 and abs(lower_slope) < 0.01:
            patterns.append(DetectedPattern(
                pattern_type=PatternType.DESCENDING_TRIANGLE,
                signal=SignalDirection.BEARISH,
                confidence=0.7,
                start_date=prices[-30].timestamp,
                end_date=prices[-1].timestamp,
                key_levels={
                    "support": min(lows),
                    "resistance_start": highs[0],
                    "resistance_end": highs[-1],
                },
                description="Descending triangle indicates bearish breakdown potential",
            ))

        # Symmetrical triangle: converging trend lines
        elif upper_slope < -0.01 and lower_slope > 0.01:
            patterns.append(DetectedPattern(
                pattern_type=PatternType.SYMMETRICAL_TRIANGLE,
                signal=SignalDirection.NEUTRAL,
                confidence=0.65,
                start_date=prices[-30].timestamp,
                end_date=prices[-1].timestamp,
                key_levels={
                    "apex": (highs[-1] + lows[-1]) / 2,
                },
                description="Symmetrical triangle indicates potential breakout in either direction",
            ))

        return patterns

    def _detect_flags(self, prices: List[PricePoint]) -> List[DetectedPattern]:
        """Detect flag and pennant patterns."""
        # Simplified implementation
        return []

    def _detect_wedges(self, prices: List[PricePoint]) -> List[DetectedPattern]:
        """Detect rising and falling wedge patterns."""
        # Simplified implementation
        return []

    def _detect_doji_patterns(self, prices: List[PricePoint]) -> List[CandlestickSignal]:
        """Detect doji candlestick patterns."""
        signals = []

        for i in range(len(prices)):
            candle = prices[i]
            body_size = abs(candle.close - candle.open)
            full_range = candle.high - candle.low

            if full_range == 0:
                continue

            body_pct = body_size / full_range

            # Standard doji: very small body
            if body_pct < 0.1:
                upper_shadow = candle.high - max(candle.open, candle.close)
                lower_shadow = min(candle.open, candle.close) - candle.low

                # Dragonfly doji: long lower shadow
                if lower_shadow > 2 * upper_shadow:
                    signals.append(CandlestickSignal(
                        pattern=CandlestickPattern.DRAGONFLY_DOJI,
                        signal=SignalDirection.BULLISH,
                        confidence=0.7,
                        date=candle.timestamp,
                        price=candle.close,
                        description="Dragonfly doji indicates potential bullish reversal",
                    ))

                # Gravestone doji: long upper shadow
                elif upper_shadow > 2 * lower_shadow:
                    signals.append(CandlestickSignal(
                        pattern=CandlestickPattern.GRAVESTONE_DOJI,
                        signal=SignalDirection.BEARISH,
                        confidence=0.7,
                        date=candle.timestamp,
                        price=candle.close,
                        description="Gravestone doji indicates potential bearish reversal",
                    ))

                # Standard doji
                else:
                    signals.append(CandlestickSignal(
                        pattern=CandlestickPattern.DOJI,
                        signal=SignalDirection.NEUTRAL,
                        confidence=0.6,
                        date=candle.timestamp,
                        price=candle.close,
                        description="Doji indicates market indecision",
                    ))

        return signals

    def _detect_hammer_patterns(self, prices: List[PricePoint]) -> List[CandlestickSignal]:
        """Detect hammer and hanging man patterns."""
        signals = []

        for i in range(len(prices)):
            candle = prices[i]
            body_size = abs(candle.close - candle.open)
            full_range = candle.high - candle.low

            if full_range == 0:
                continue

            upper_shadow = candle.high - max(candle.open, candle.close)
            lower_shadow = min(candle.open, candle.close) - candle.low

            # Hammer: small body, long lower shadow, small upper shadow
            if lower_shadow > 2 * body_size and upper_shadow < body_size * 0.5:
                # Context matters: hammer at bottom, hanging man at top
                is_downtrend = i > 5 and prices[i-5].close > candle.close

                if is_downtrend:
                    signals.append(CandlestickSignal(
                        pattern=CandlestickPattern.HAMMER,
                        signal=SignalDirection.BULLISH,
                        confidence=0.75,
                        date=candle.timestamp,
                        price=candle.close,
                        description="Hammer indicates potential bullish reversal",
                    ))

        return signals

    def _detect_engulfing_patterns(self, prices: List[PricePoint]) -> List[CandlestickSignal]:
        """Detect engulfing patterns."""
        signals = []

        for i in range(1, len(prices)):
            prev = prices[i - 1]
            curr = prices[i]

            prev_body = abs(prev.close - prev.open)
            curr_body = abs(curr.close - curr.open)

            # Bullish engulfing: small red candle followed by large green
            if prev.close < prev.open and curr.close > curr.open:
                if curr.open <= prev.close and curr.close >= prev.open:
                    if curr_body > prev_body * 1.5:
                        signals.append(CandlestickSignal(
                            pattern=CandlestickPattern.BULLISH_ENGULFING,
                            signal=SignalDirection.BULLISH,
                            confidence=0.8,
                            date=curr.timestamp,
                            price=curr.close,
                            description="Bullish engulfing indicates strong buying pressure",
                        ))

            # Bearish engulfing: small green candle followed by large red
            elif prev.close > prev.open and curr.close < curr.open:
                if curr.open >= prev.close and curr.close <= prev.open:
                    if curr_body > prev_body * 1.5:
                        signals.append(CandlestickSignal(
                            pattern=CandlestickPattern.BEARISH_ENGULFING,
                            signal=SignalDirection.BEARISH,
                            confidence=0.8,
                            date=curr.timestamp,
                            price=curr.close,
                            description="Bearish engulfing indicates strong selling pressure",
                        ))

        return signals

    def _detect_harami_patterns(self, prices: List[PricePoint]) -> List[CandlestickSignal]:
        """Detect harami patterns."""
        signals = []

        for i in range(1, len(prices)):
            prev = prices[i - 1]
            curr = prices[i]

            prev_body_top = max(prev.open, prev.close)
            prev_body_bottom = min(prev.open, prev.close)
            curr_body_top = max(curr.open, curr.close)
            curr_body_bottom = min(curr.open, curr.close)

            # Harami: small candle inside previous large candle
            if curr_body_top < prev_body_top and curr_body_bottom > prev_body_bottom:
                # Bullish harami: large red followed by small green
                if prev.close < prev.open and curr.close > curr.open:
                    signals.append(CandlestickSignal(
                        pattern=CandlestickPattern.BULLISH_HARAMI,
                        signal=SignalDirection.BULLISH,
                        confidence=0.7,
                        date=curr.timestamp,
                        price=curr.close,
                        description="Bullish harami indicates potential reversal",
                    ))

                # Bearish harami: large green followed by small red
                elif prev.close > prev.open and curr.close < curr.open:
                    signals.append(CandlestickSignal(
                        pattern=CandlestickPattern.BEARISH_HARAMI,
                        signal=SignalDirection.BEARISH,
                        confidence=0.7,
                        date=curr.timestamp,
                        price=curr.close,
                        description="Bearish harami indicates potential reversal",
                    ))

        return signals

    def _detect_star_patterns(self, prices: List[PricePoint]) -> List[CandlestickSignal]:
        """Detect morning and evening star patterns."""
        signals = []

        for i in range(2, len(prices)):
            first = prices[i - 2]
            star = prices[i - 1]
            third = prices[i]

            first_body = abs(first.close - first.open)
            star_body = abs(star.close - star.open)
            third_body = abs(third.close - third.open)

            # Morning star: large red, small body (gap down), large green
            if (first.close < first.open and
                star_body < first_body * 0.3 and
                third.close > third.open and
                third_body > first_body * 0.8):

                signals.append(CandlestickSignal(
                    pattern=CandlestickPattern.MORNING_STAR,
                    signal=SignalDirection.BULLISH,
                    confidence=0.85,
                    date=third.timestamp,
                    price=third.close,
                    description="Morning star indicates strong bullish reversal",
                ))

            # Evening star: large green, small body (gap up), large red
            elif (first.close > first.open and
                  star_body < first_body * 0.3 and
                  third.close < third.open and
                  third_body > first_body * 0.8):

                signals.append(CandlestickSignal(
                    pattern=CandlestickPattern.EVENING_STAR,
                    signal=SignalDirection.BEARISH,
                    confidence=0.85,
                    date=third.timestamp,
                    price=third.close,
                    description="Evening star indicates strong bearish reversal",
                ))

        return signals

    def _detect_soldier_crow_patterns(self, prices: List[PricePoint]) -> List[CandlestickSignal]:
        """Detect three white soldiers and three black crows."""
        # Simplified implementation
        return []

    def _find_local_maxima(self, prices: List[PricePoint]) -> List[Tuple[datetime, float]]:
        """Find local maxima (peaks) in price data."""
        maxima = []
        highs = [p.high for p in prices]

        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                maxima.append((prices[i].timestamp, highs[i]))

        return maxima

    def _find_local_minima(self, prices: List[PricePoint]) -> List[Tuple[datetime, float]]:
        """Find local minima (troughs) in price data."""
        minima = []
        lows = [p.low for p in prices]

        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                minima.append((prices[i].timestamp, lows[i]))

        return minima

    def _cluster_levels(
        self, extrema: List[Tuple[datetime, float]], level_type: str
    ) -> List[SupportResistanceLevel]:
        """Cluster price levels into support/resistance."""
        if not extrema:
            return []

        levels = []
        used = set()

        for i, (date1, price1) in enumerate(extrema):
            if i in used:
                continue

            # Find nearby prices (within tolerance)
            cluster = [(date1, price1)]
            for j, (date2, price2) in enumerate(extrema[i+1:], start=i+1):
                if abs(price2 - price1) / price1 < self.config.price_tolerance:
                    cluster.append((date2, price2))
                    used.add(j)

            if len(cluster) >= 2:  # At least 2 touches
                avg_price = np.mean([p for _, p in cluster])
                first_date = min(d for d, _ in cluster)
                last_date = max(d for d, _ in cluster)

                # Strength based on number of touches
                strength = min(len(cluster) / 5.0, 1.0)

                levels.append(SupportResistanceLevel(
                    level=float(avg_price),
                    level_type=level_type,
                    strength=strength,
                    touches=len(cluster),
                    first_touch=first_date,
                    last_touch=last_date,
                ))

        # Sort by strength
        levels.sort(key=lambda x: x.strength, reverse=True)

        return levels[:5]  # Return top 5
