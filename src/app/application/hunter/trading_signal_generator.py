"""AI-powered trading signal generation.

Combines sentiment analysis, price predictions, and risk scoring to generate
actionable trading signals with entry/exit recommendations.

Based on Hunter AI Bot's signal generation module.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from app.domain.common.datetime_utils import utc_now
from enum import Enum
import numpy as np

from app.application.hunter.sentiment_aggregator import SentimentAggregator
from app.application.hunter.twitter_sentiment import TwitterSentimentAnalyzer
from app.application.hunter.reddit_sentiment import RedditSentimentAnalyzer
from app.application.hunter.discord_sentiment import DiscordSentimentAnalyzer
from app.application.hunter.news_sentiment import NewsSentimentAnalyzer
from app.application.hunter.lstm_price_predictor import LSTMPricePredictor
from app.application.hunter.risk_analyzer import RiskAnalyzer
from app.application.hunter.price_data_service import PriceDataService


class SignalType(str, Enum):
    """Trading signal types."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class Timeframe(str, Enum):
    """Trading timeframes."""

    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


@dataclass
class SignalConfig:
    """Configuration for signal generation."""

    # Signal strength thresholds (0-100)
    strong_buy_threshold: float = 75.0
    buy_threshold: float = 60.0
    hold_threshold: float = 40.0
    sell_threshold: float = 25.0

    # Factor weights (must sum to 1.0)
    sentiment_weight: float = 0.35
    prediction_weight: float = 0.35
    risk_weight: float = 0.30

    # Risk management
    max_risk_score_for_buy: float = 60.0  # Don't buy high-risk assets
    min_confidence_for_signal: float = 0.50  # Min confidence to generate signal

    # Stop-loss/take-profit settings
    stop_loss_pct: float = 0.05  # 5% default stop-loss
    take_profit_multiplier: float = 2.0  # 2:1 reward:risk ratio


@dataclass
class TradingSignal:
    """Complete trading signal with recommendations."""

    token_symbol: str
    signal_type: SignalType
    signal_strength: float  # 0-100
    confidence: float  # 0-1

    # Entry/Exit recommendations
    entry_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None

    # Factor contributions
    sentiment_score: float = 0.0
    prediction_score: float = 0.0
    risk_score: float = 0.0

    # Metadata
    timeframe: Timeframe = Timeframe.DAY_1
    generated_at: datetime = None
    recommendation: str = ""

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = utc_now()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "token_symbol": self.token_symbol,
            "signal_type": self.signal_type.value,
            "signal_strength": round(self.signal_strength, 2),
            "confidence": round(self.confidence, 2),
            "entry_price": round(self.entry_price, 2) if self.entry_price else None,
            "stop_loss_price": round(self.stop_loss_price, 2) if self.stop_loss_price else None,
            "take_profit_price": round(self.take_profit_price, 2) if self.take_profit_price else None,
            "sentiment_score": round(self.sentiment_score, 2),
            "prediction_score": round(self.prediction_score, 2),
            "risk_score": round(self.risk_score, 2),
            "timeframe": self.timeframe.value,
            "generated_at": self.generated_at.isoformat(),
            "recommendation": self.recommendation,
        }


@dataclass
class MultiTimeframeAnalysis:
    """Analysis across multiple timeframes."""

    token_symbol: str
    signals: Dict[Timeframe, TradingSignal]
    consensus_signal: SignalType
    alignment_score: float  # 0-1, how aligned timeframes are
    trend_direction: str  # "bullish", "bearish", "neutral"
    generated_at: datetime = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = utc_now()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "token_symbol": self.token_symbol,
            "signals": {tf.value: sig.to_dict() for tf, sig in self.signals.items()},
            "consensus_signal": self.consensus_signal.value,
            "alignment_score": round(self.alignment_score, 2),
            "trend_direction": self.trend_direction,
            "generated_at": self.generated_at.isoformat(),
        }


class TradingSignalGenerator:
    """AI-powered trading signal generator.

    Combines multiple data sources to generate actionable trading signals:
    - Sentiment analysis (4 sources)
    - Price predictions (LSTM)
    - Risk assessment (4 factors)
    """

    def __init__(
        self,
        config: SignalConfig = None,
        price_service: PriceDataService = None,
    ):
        """Initialize signal generator.

        Args:
            config: Signal generation configuration
            price_service: Price data service
        """
        self.config = config or SignalConfig()
        self.price_service = price_service or PriceDataService()

        # Initialize analysis services
        self.sentiment_aggregator = SentimentAggregator()
        self.twitter_analyzer = TwitterSentimentAnalyzer()
        self.reddit_analyzer = RedditSentimentAnalyzer()
        self.discord_analyzer = DiscordSentimentAnalyzer()
        self.news_analyzer = NewsSentimentAnalyzer()
        self.predictor = LSTMPricePredictor()
        self.risk_analyzer = RiskAnalyzer()

    async def generate_signal(
        self,
        token_symbol: str,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> TradingSignal:
        """Generate trading signal for a token.

        Args:
            token_symbol: Token to analyze
            timeframe: Trading timeframe

        Returns:
            Complete trading signal with recommendations

        Example:
            >>> generator = TradingSignalGenerator()
            >>> signal = await generator.generate_signal("ETH", Timeframe.DAY_1)
            >>> print(f"{signal.signal_type}: {signal.recommendation}")
        """
        # 1. Gather all analysis factors
        sentiment_reading = await self._get_sentiment_score(token_symbol)
        prediction_score, prediction_confidence = await self._get_prediction_score(
            token_symbol, timeframe
        )
        risk_assessment = await self.risk_analyzer.analyze_comprehensive_risk(
            token_symbol
        )

        # 2. Calculate composite signal strength
        sentiment_score = self._normalize_sentiment(sentiment_reading)
        risk_score_normalized = 100 - risk_assessment.overall_risk_score  # Invert (lower risk = higher score)

        # Weighted combination
        signal_strength = (
            sentiment_score * self.config.sentiment_weight
            + prediction_score * self.config.prediction_weight
            + risk_score_normalized * self.config.risk_weight
        )

        # 3. Calculate overall confidence
        confidence = (sentiment_reading.overall_confidence + prediction_confidence) / 2

        # 4. Determine signal type
        signal_type = self._determine_signal_type(
            signal_strength, risk_assessment.overall_risk_score, confidence
        )

        # 5. Calculate entry/exit prices
        current_price = await self._get_current_price(token_symbol)
        entry_price, stop_loss, take_profit = self._calculate_entry_exit(
            current_price, signal_type, risk_assessment.overall_risk_score
        )

        # 6. Generate recommendation
        recommendation = self._generate_recommendation(
            signal_type,
            signal_strength,
            sentiment_score,
            prediction_score,
            risk_score_normalized,
            risk_assessment,
        )

        return TradingSignal(
            token_symbol=token_symbol,
            signal_type=signal_type,
            signal_strength=signal_strength,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
            sentiment_score=sentiment_score,
            prediction_score=prediction_score,
            risk_score=risk_score_normalized,
            timeframe=timeframe,
            recommendation=recommendation,
        )

    async def generate_multi_timeframe_analysis(
        self, token_symbol: str
    ) -> MultiTimeframeAnalysis:
        """Generate signals across multiple timeframes.

        Args:
            token_symbol: Token to analyze

        Returns:
            Multi-timeframe analysis with consensus

        Example:
            >>> generator = TradingSignalGenerator()
            >>> analysis = await generator.generate_multi_timeframe_analysis("ETH")
            >>> print(f"Consensus: {analysis.consensus_signal}")
        """
        # Generate signals for multiple timeframes
        timeframes = [
            Timeframe.HOUR_4,
            Timeframe.DAY_1,
            Timeframe.WEEK_1,
        ]

        signals = {}
        for tf in timeframes:
            signal = await self.generate_signal(token_symbol, tf)
            signals[tf] = signal

        # Calculate consensus
        consensus = self._calculate_consensus(signals)
        alignment = self._calculate_alignment(signals)
        trend = self._determine_trend(signals)

        return MultiTimeframeAnalysis(
            token_symbol=token_symbol,
            signals=signals,
            consensus_signal=consensus,
            alignment_score=alignment,
            trend_direction=trend,
        )

    async def _get_sentiment_score(self, token_symbol: str) -> any:
        """Get aggregated sentiment score."""
        # Analyze across all sources
        twitter_reading = await self.twitter_analyzer.analyze_token_sentiment(
            token_symbol
        )
        reddit_reading = await self.reddit_analyzer.analyze_token_sentiment(
            token_symbol
        )
        discord_reading = await self.discord_analyzer.analyze_token_sentiment(
            token_symbol
        )
        news_reading = await self.news_analyzer.analyze_token_sentiment(token_symbol)

        # Aggregate
        readings = [twitter_reading, reddit_reading, discord_reading, news_reading]
        aggregated = self.sentiment_aggregator.aggregate(readings, token_symbol)

        return aggregated

    async def _get_prediction_score(
        self, token_symbol: str, timeframe: Timeframe
    ) -> Tuple[float, float]:
        """Get price prediction score.

        Returns:
            (score 0-100, confidence 0-1)
        """
        # Map timeframe to prediction horizon
        horizon_map = {
            Timeframe.HOUR_1: 1,
            Timeframe.HOUR_4: 4,
            Timeframe.DAY_1: 24,
            Timeframe.WEEK_1: 168,
            Timeframe.MONTH_1: 720,
        }

        horizon = horizon_map.get(timeframe, 24)
        prediction = await self.predictor.predict(token_symbol, horizon)

        # Convert prediction to score
        # Positive prediction = high score, negative = low score
        if prediction.direction == "up":
            score = 50 + (prediction.change_percent * 2)  # Scale to 0-100
        else:
            score = 50 - (abs(prediction.change_percent) * 2)

        score = max(0, min(100, score))  # Clamp to 0-100

        return score, prediction.confidence

    async def _get_current_price(self, token_symbol: str) -> float:
        """Get current token price."""
        prices = await self.price_service.fetch_historical_prices(token_symbol, days=1)
        return prices[-1].close if prices else 100.0  # Fallback

    def _normalize_sentiment(self, sentiment: any) -> float:
        """Normalize sentiment score to 0-100.

        Args:
            sentiment: Aggregated sentiment reading

        Returns:
            Score 0-100 (0=very bearish, 50=neutral, 100=very bullish)
        """
        # Sentiment overall_score is already 0-100
        # Just return it directly
        return sentiment.overall_score

    def _determine_signal_type(
        self, signal_strength: float, risk_score: float, confidence: float
    ) -> SignalType:
        """Determine signal type from strength and risk.

        Args:
            signal_strength: Composite signal strength (0-100)
            risk_score: Overall risk score (0-100)
            confidence: Signal confidence (0-1)

        Returns:
            Signal type
        """
        # Don't generate strong signals if confidence is low
        if confidence < self.config.min_confidence_for_signal:
            return SignalType.HOLD

        # Don't buy high-risk assets
        if risk_score > self.config.max_risk_score_for_buy:
            if signal_strength < 50:
                return SignalType.SELL
            return SignalType.HOLD

        # Determine signal based on strength
        if signal_strength >= self.config.strong_buy_threshold:
            return SignalType.STRONG_BUY
        elif signal_strength >= self.config.buy_threshold:
            return SignalType.BUY
        elif signal_strength <= self.config.sell_threshold:
            return SignalType.STRONG_SELL
        elif signal_strength <= self.config.hold_threshold:
            return SignalType.SELL
        else:
            return SignalType.HOLD

    def _calculate_entry_exit(
        self, current_price: float, signal_type: SignalType, risk_score: float
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate entry, stop-loss, and take-profit prices.

        Args:
            current_price: Current token price
            signal_type: Signal type
            risk_score: Risk score (affects stop-loss tightness)

        Returns:
            (entry_price, stop_loss, take_profit)
        """
        if signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            entry = current_price
            # Tighter stop-loss for higher risk
            stop_loss_pct = self.config.stop_loss_pct * (1 + risk_score / 200)
            stop_loss = entry * (1 - stop_loss_pct)
            take_profit = entry * (
                1 + stop_loss_pct * self.config.take_profit_multiplier
            )
            return entry, stop_loss, take_profit

        elif signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            # Short position (inverse logic)
            entry = current_price
            stop_loss_pct = self.config.stop_loss_pct * (1 + risk_score / 200)
            stop_loss = entry * (1 + stop_loss_pct)
            take_profit = entry * (
                1 - stop_loss_pct * self.config.take_profit_multiplier
            )
            return entry, stop_loss, take_profit

        return None, None, None

    def _generate_recommendation(
        self,
        signal_type: SignalType,
        signal_strength: float,
        sentiment_score: float,
        prediction_score: float,
        risk_score: float,
        risk_assessment: any,
    ) -> str:
        """Generate human-readable recommendation.

        Args:
            signal_type: Signal type
            signal_strength: Signal strength
            sentiment_score: Sentiment contribution
            prediction_score: Prediction contribution
            risk_score: Risk contribution
            risk_assessment: Full risk assessment

        Returns:
            Recommendation string
        """
        if signal_type == SignalType.STRONG_BUY:
            return (
                f"STRONG BUY signal (strength: {signal_strength:.1f}/100). "
                f"High conviction long opportunity. "
                f"Sentiment: {sentiment_score:.1f}, Prediction: {prediction_score:.1f}, Risk: {risk_score:.1f}. "
                f"Consider 30-50% of planned position size."
            )
        elif signal_type == SignalType.BUY:
            return (
                f"BUY signal (strength: {signal_strength:.1f}/100). "
                f"Favorable entry opportunity. "
                f"Sentiment: {sentiment_score:.1f}, Prediction: {prediction_score:.1f}, Risk: {risk_score:.1f}. "
                f"Consider 20-30% of planned position size."
            )
        elif signal_type == SignalType.SELL:
            return (
                f"SELL signal (strength: {100 - signal_strength:.1f}/100). "
                f"Consider reducing exposure or taking profits. "
                f"Sentiment: {sentiment_score:.1f}, Prediction: {prediction_score:.1f}, Risk: {risk_score:.1f}."
            )
        elif signal_type == SignalType.STRONG_SELL:
            return (
                f"STRONG SELL signal (strength: {100 - signal_strength:.1f}/100). "
                f"High conviction short or exit signal. "
                f"Sentiment: {sentiment_score:.1f}, Prediction: {prediction_score:.1f}, Risk: {risk_score:.1f}. "
                f"Consider full position exit."
            )
        else:  # HOLD
            return (
                f"HOLD signal (strength: {signal_strength:.1f}/100). "
                f"No clear directional bias. Wait for better setup. "
                f"Risk level: {risk_assessment.overall_risk_level}."
            )

    def _calculate_consensus(self, signals: Dict[Timeframe, TradingSignal]) -> SignalType:
        """Calculate consensus signal across timeframes."""
        # Count signal types
        signal_counts = {}
        for signal in signals.values():
            signal_counts[signal.signal_type] = (
                signal_counts.get(signal.signal_type, 0) + 1
            )

        # Return most common signal
        return max(signal_counts, key=signal_counts.get)

    def _calculate_alignment(self, signals: Dict[Timeframe, TradingSignal]) -> float:
        """Calculate alignment score (0-1).

        Higher score = more timeframes agree.
        """
        consensus = self._calculate_consensus(signals)
        agreement_count = sum(
            1 for sig in signals.values() if sig.signal_type == consensus
        )
        return agreement_count / len(signals)

    def _determine_trend(self, signals: Dict[Timeframe, TradingSignal]) -> str:
        """Determine overall trend direction."""
        buy_signals = sum(
            1
            for sig in signals.values()
            if sig.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]
        )
        sell_signals = sum(
            1
            for sig in signals.values()
            if sig.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]
        )

        if buy_signals > sell_signals:
            return "bullish"
        elif sell_signals > buy_signals:
            return "bearish"
        else:
            return "neutral"
