"""Trading signals API endpoints.

REST API for AI-powered trading signal generation.
"""

from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional

from app.application.hunter.trading_signal_generator import (
    TradingSignalGenerator,
    SignalConfig,
    Timeframe,
    SignalType,
)


class TradingSignalResponse(BaseModel):
    """Response model for trading signal."""

    token_symbol: str = Field(..., description="Token symbol")
    signal_type: str = Field(..., description="Signal type: BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL")
    signal_strength: float = Field(..., description="Signal strength (0-100)", ge=0, le=100)
    confidence: float = Field(..., description="Signal confidence (0-1)", ge=0, le=1)

    entry_price: Optional[float] = Field(None, description="Recommended entry price")
    stop_loss_price: Optional[float] = Field(None, description="Stop-loss price")
    take_profit_price: Optional[float] = Field(None, description="Take-profit target")

    sentiment_score: float = Field(..., description="Sentiment contribution (0-100)")
    prediction_score: float = Field(..., description="Price prediction contribution (0-100)")
    risk_score: float = Field(..., description="Risk-adjusted score (0-100)")

    timeframe: str = Field(..., description="Timeframe (1h, 4h, 1d, 1w, 1M)")
    generated_at: str = Field(..., description="Signal generation timestamp")
    recommendation: str = Field(..., description="Human-readable recommendation")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "token_symbol": "ETH",
                "signal_type": "BUY",
                "signal_strength": 72.5,
                "confidence": 0.78,
                "entry_price": 2450.00,
                "stop_loss_price": 2327.50,
                "take_profit_price": 2695.00,
                "sentiment_score": 68.0,
                "prediction_score": 75.0,
                "risk_score": 75.0,
                "timeframe": "1d",
                "generated_at": "2025-12-03T18:00:00Z",
                "recommendation": "BUY signal (strength: 72.5/100)...",
            }
        })


class MultiTimeframeAnalysisResponse(BaseModel):
    """Response model for multi-timeframe analysis."""

    token_symbol: str = Field(..., description="Token symbol")
    signals: Dict[str, TradingSignalResponse] = Field(..., description="Signals by timeframe")
    consensus_signal: str = Field(..., description="Consensus signal across timeframes")
    alignment_score: float = Field(..., description="Timeframe alignment (0-1)", ge=0, le=1)
    trend_direction: str = Field(..., description="Overall trend: bullish, bearish, neutral")
    generated_at: str = Field(..., description="Analysis timestamp")

    model_config = ConfigDict(json_schema_extra={
            "example": {
                "token_symbol": "ETH",
                "signals": {
                    "4h": {"signal_type": "BUY", "signal_strength": 70.0},
                    "1d": {"signal_type": "BUY", "signal_strength": 72.5},
                    "1w": {"signal_type": "HOLD", "signal_strength": 55.0},
                },
                "consensus_signal": "BUY",
                "alignment_score": 0.67,
                "trend_direction": "bullish",
                "generated_at": "2025-12-03T18:00:00Z",
            }
        })


def create_trading_signals_router() -> APIRouter:
    """Create trading signals router.

    Returns:
        Configured FastAPI router
    """
    router = APIRouter(prefix="/user/hunter/signals", tags=["hunter-signals"])

    @router.get(
        "/generate/{token_symbol}",
        response_model=TradingSignalResponse,
        summary="Generate trading signal",
        description="Generate AI-powered trading signal combining sentiment, price prediction, and risk analysis",
    )
    async def generate_trading_signal(
        token_symbol: str,
        timeframe: str = Query("1d", description="Timeframe: 1h, 4h, 1d, 1w, 1M"),
    ) -> TradingSignalResponse:
        """Generate trading signal for a token.

        Combines:
        - Sentiment analysis (4 sources)
        - LSTM price prediction
        - ML risk assessment (4 factors)

        Returns:
        - Signal type (BUY/SELL/HOLD)
        - Entry/exit prices
        - Stop-loss/take-profit levels
        - Position sizing recommendation

        Args:
            token_symbol: Token to analyze
            timeframe: Trading timeframe

        Returns:
            Complete trading signal with recommendations

        Example:
            GET /api/v1/hunter/signals/generate/ETH?timeframe=1d

            Response:
            {
                "token_symbol": "ETH",
                "signal_type": "BUY",
                "signal_strength": 72.5,
                "confidence": 0.78,
                "entry_price": 2450.00,
                "stop_loss_price": 2327.50,
                "take_profit_price": 2695.00,
                "recommendation": "BUY signal..."
            }
        """
        try:
            # Validate timeframe
            try:
                tf = Timeframe(timeframe)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid timeframe. Must be one of: 1h, 4h, 1d, 1w, 1M",
                )

            generator = TradingSignalGenerator()
            signal = await generator.generate_signal(token_symbol, tf)

            return TradingSignalResponse(**signal.to_dict())

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Signal generation failed: {str(e)}",
            )

    @router.get(
        "/multi-timeframe/{token_symbol}",
        response_model=MultiTimeframeAnalysisResponse,
        summary="Multi-timeframe analysis",
        description="Analyze token across multiple timeframes (4h, 1d, 1w) and generate consensus signal",
    )
    async def multi_timeframe_analysis(
        token_symbol: str,
    ) -> MultiTimeframeAnalysisResponse:
        """Generate signals across multiple timeframes.

        Analyzes token on:
        - 4-hour timeframe (short-term)
        - 1-day timeframe (medium-term)
        - 1-week timeframe (long-term)

        Provides:
        - Individual signals per timeframe
        - Consensus signal
        - Alignment score
        - Trend direction

        Args:
            token_symbol: Token to analyze

        Returns:
            Multi-timeframe analysis with consensus

        Example:
            GET /api/v1/hunter/signals/multi-timeframe/ETH

            Response:
            {
                "token_symbol": "ETH",
                "signals": {
                    "4h": {...},
                    "1d": {...},
                    "1w": {...}
                },
                "consensus_signal": "BUY",
                "alignment_score": 0.67,
                "trend_direction": "bullish"
            }
        """
        try:
            generator = TradingSignalGenerator()
            analysis = await generator.generate_multi_timeframe_analysis(token_symbol)

            # Convert to response format
            signals_response = {}
            for tf, signal in analysis.signals.items():
                signals_response[tf.value] = TradingSignalResponse(**signal.to_dict())

            return MultiTimeframeAnalysisResponse(
                token_symbol=analysis.token_symbol,
                signals=signals_response,
                consensus_signal=analysis.consensus_signal.value,
                alignment_score=analysis.alignment_score,
                trend_direction=analysis.trend_direction,
                generated_at=analysis.generated_at.isoformat(),
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Multi-timeframe analysis failed: {str(e)}",
            )

    @router.get(
        "/batch",
        response_model=Dict[str, TradingSignalResponse],
        summary="Batch signal generation",
        description="Generate signals for multiple tokens simultaneously",
    )
    async def batch_generate_signals(
        tokens: str = Query(..., description="Comma-separated token symbols (e.g., ETH,BTC,SOL)"),
        timeframe: str = Query("1d", description="Timeframe: 1h, 4h, 1d, 1w, 1M"),
    ) -> Dict[str, TradingSignalResponse]:
        """Generate signals for multiple tokens.

        Args:
            tokens: Comma-separated token list
            timeframe: Trading timeframe

        Returns:
            Dictionary of signals keyed by token symbol

        Example:
            GET /api/v1/hunter/signals/batch?tokens=ETH,BTC,SOL&timeframe=1d

            Response:
            {
                "ETH": {...},
                "BTC": {...},
                "SOL": {...}
            }
        """
        try:
            # Validate timeframe
            try:
                tf = Timeframe(timeframe)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid timeframe. Must be one of: 1h, 4h, 1d, 1w, 1M",
                )

            # Parse token list
            token_list = [t.strip().upper() for t in tokens.split(",")]

            if len(token_list) > 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum 10 tokens per batch request",
                )

            # Generate signals
            generator = TradingSignalGenerator()
            results = {}

            for token in token_list:
                try:
                    signal = await generator.generate_signal(token, tf)
                    results[token] = TradingSignalResponse(**signal.to_dict())
                except Exception as e:
                    # Continue with other tokens if one fails
                    results[token] = {
                        "error": f"Failed to generate signal: {str(e)}"
                    }

            return results

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Batch signal generation failed: {str(e)}",
            )

    @router.get(
        "/top-signals",
        response_model=list[TradingSignalResponse],
        summary="Get top trading signals",
        description="Get strongest BUY or SELL signals from a watchlist",
    )
    async def get_top_signals(
        signal_type: str = Query("BUY", description="Signal type filter: BUY or SELL"),
        limit: int = Query(5, ge=1, le=20, description="Number of signals to return"),
    ) -> list[TradingSignalResponse]:
        """Get top trading signals from watchlist.

        Args:
            signal_type: Filter by signal type (BUY or SELL)
            limit: Number of results

        Returns:
            List of top signals sorted by strength

        Example:
            GET /api/v1/hunter/signals/top-signals?signal_type=BUY&limit=5

            Response:
            [
                {"token_symbol": "ETH", "signal_type": "STRONG_BUY", "signal_strength": 85.0},
                {"token_symbol": "BTC", "signal_type": "BUY", "signal_strength": 72.5},
                ...
            ]
        """
        try:
            # Validate signal type
            if signal_type not in ["BUY", "SELL"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="signal_type must be BUY or SELL",
                )

            # Watchlist of popular tokens
            watchlist = ["BTC", "ETH", "SOL", "AVAX", "BNB", "ADA", "DOT", "MATIC"]

            generator = TradingSignalGenerator()
            signals = []

            # Generate signals for watchlist
            for token in watchlist:
                try:
                    signal = await generator.generate_signal(token, Timeframe.DAY_1)

                    # Filter by signal type
                    if signal_type == "BUY" and signal.signal_type in [
                        SignalType.BUY,
                        SignalType.STRONG_BUY,
                    ]:
                        signals.append(signal)
                    elif signal_type == "SELL" and signal.signal_type in [
                        SignalType.SELL,
                        SignalType.STRONG_SELL,
                    ]:
                        signals.append(signal)
                except Exception:
                    # Skip failed tokens
                    continue

            # Sort by signal strength
            signals.sort(key=lambda s: s.signal_strength, reverse=True)

            # Return top N
            top_signals = signals[:limit]

            return [TradingSignalResponse(**s.to_dict()) for s in top_signals]

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Top signals generation failed: {str(e)}",
            )

    return router
