"""Pattern recognition API endpoints.

REST API for technical pattern detection and analysis.
"""

from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List

from app.application.hunter.pattern_recognition import PatternRecognizer


class DetectedPatternResponse(BaseModel):
    """Response model for detected pattern."""

    pattern_type: str = Field(..., description="Chart pattern type")
    signal: str = Field(..., description="Signal direction (bullish/bearish/neutral)")
    confidence: float = Field(..., description="Pattern confidence (0-1)")
    start_date: str = Field(..., description="Pattern start date")
    end_date: str = Field(..., description="Pattern end date")
    key_levels: Dict[str, float] = Field(..., description="Key price levels")
    description: str = Field(..., description="Pattern description")

    class Config:
        json_schema_extra = {
            "example": {
                "pattern_type": "head_and_shoulders",
                "signal": "bearish",
                "confidence": 0.75,
                "start_date": "2025-11-15T00:00:00Z",
                "end_date": "2025-12-03T00:00:00Z",
                "key_levels": {
                    "left_shoulder": 2050.0,
                    "head": 2100.0,
                    "right_shoulder": 2045.0,
                    "neckline": 1980.0,
                    "target": 1860.0,
                },
                "description": "Head and shoulders pattern indicates bearish reversal",
            }
        }


class CandlestickSignalResponse(BaseModel):
    """Response model for candlestick pattern."""

    pattern: str = Field(..., description="Candlestick pattern type")
    signal: str = Field(..., description="Signal direction")
    confidence: float = Field(..., description="Pattern confidence")
    date: str = Field(..., description="Pattern date")
    price: float = Field(..., description="Price at pattern")
    description: str = Field(..., description="Pattern description")

    class Config:
        json_schema_extra = {
            "example": {
                "pattern": "bullish_engulfing",
                "signal": "bullish",
                "confidence": 0.8,
                "date": "2025-12-03T00:00:00Z",
                "price": 2000.0,
                "description": "Bullish engulfing indicates strong buying pressure",
            }
        }


class SupportResistanceLevelResponse(BaseModel):
    """Response model for support/resistance level."""

    level: float = Field(..., description="Price level")
    level_type: str = Field(..., description="Level type (support/resistance)")
    strength: float = Field(..., description="Level strength (0-1)")
    touches: int = Field(..., description="Number of touches")
    first_touch: str = Field(..., description="First touch date")
    last_touch: str = Field(..., description="Last touch date")


def create_patterns_router() -> APIRouter:
    """Create pattern recognition router.

    Returns:
        Configured FastAPI router
    """
    router = APIRouter(prefix="/hunter/patterns", tags=["hunter-patterns"])

    @router.get(
        "/chart/{token_symbol}",
        response_model=List[DetectedPatternResponse],
        summary="Detect chart patterns",
        description="Detect technical chart patterns (head & shoulders, triangles, flags, etc.)",
    )
    async def detect_chart_patterns(
        token_symbol: str,
        min_confidence: float = Query(0.6, ge=0.0, le=1.0, description="Minimum pattern confidence"),
    ) -> List[DetectedPatternResponse]:
        """Detect chart patterns.

        Analyzes price history to identify:
        - Reversal patterns (head & shoulders, double/triple tops/bottoms)
        - Continuation patterns (triangles, flags, pennants, wedges)

        Args:
            token_symbol: Token symbol (e.g., BTC, ETH)
            min_confidence: Minimum confidence threshold

        Returns:
            List of detected patterns with key levels and targets

        Example:
            GET /api/v1/hunter/patterns/chart/BTC?min_confidence=0.7

            Response:
            [
                {
                    "pattern_type": "head_and_shoulders",
                    "signal": "bearish",
                    "confidence": 0.75,
                    "key_levels": {
                        "neckline": 1980.0,
                        "target": 1860.0
                    }
                }
            ]
        """
        try:
            recognizer = PatternRecognizer()
            patterns = await recognizer.detect_chart_patterns(token_symbol.upper())

            # Filter by confidence
            patterns = [p for p in patterns if p.confidence >= min_confidence]

            return [DetectedPatternResponse(**p.to_dict()) for p in patterns]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pattern detection failed: {str(e)}",
            )

    @router.get(
        "/candlestick/{token_symbol}",
        response_model=List[CandlestickSignalResponse],
        summary="Detect candlestick patterns",
        description="Detect candlestick patterns (doji, hammer, engulfing, harami, stars, etc.)",
    )
    async def detect_candlestick_patterns(
        token_symbol: str,
        min_confidence: float = Query(0.6, ge=0.0, le=1.0, description="Minimum pattern confidence"),
    ) -> List[CandlestickSignalResponse]:
        """Detect candlestick patterns.

        Analyzes recent candlesticks to identify:
        - Single candle patterns (doji, hammer, shooting star)
        - Two candle patterns (engulfing, harami)
        - Three candle patterns (morning/evening star, soldiers/crows)

        Args:
            token_symbol: Token symbol
            min_confidence: Minimum confidence threshold

        Returns:
            List of detected candlestick patterns

        Example:
            GET /api/v1/hunter/patterns/candlestick/ETH

            Response:
            [
                {
                    "pattern": "bullish_engulfing",
                    "signal": "bullish",
                    "confidence": 0.8,
                    "price": 2000.0
                }
            ]
        """
        try:
            recognizer = PatternRecognizer()
            signals = await recognizer.detect_candlestick_patterns(token_symbol.upper())

            # Filter by confidence
            signals = [s for s in signals if s.confidence >= min_confidence]

            return [CandlestickSignalResponse(**s.to_dict()) for s in signals]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Candlestick pattern detection failed: {str(e)}",
            )

    @router.get(
        "/support-resistance/{token_symbol}",
        response_model=Dict[str, List[SupportResistanceLevelResponse]],
        summary="Find support and resistance levels",
        description="Identify key support and resistance price levels",
    )
    async def find_support_resistance(
        token_symbol: str,
    ) -> Dict[str, List[SupportResistanceLevelResponse]]:
        """Find support and resistance levels.

        Analyzes historical price action to identify:
        - Support levels (price floors where buying pressure emerges)
        - Resistance levels (price ceilings where selling pressure emerges)

        Each level includes:
        - Strength score (based on number of touches)
        - Number of times price tested the level
        - Historical touch dates

        Args:
            token_symbol: Token symbol

        Returns:
            Dictionary with "support" and "resistance" level lists

        Example:
            GET /api/v1/hunter/patterns/support-resistance/SOL

            Response:
            {
                "support": [
                    {
                        "level": 95.50,
                        "strength": 0.8,
                        "touches": 4,
                        "level_type": "support"
                    }
                ],
                "resistance": [
                    {
                        "level": 105.75,
                        "strength": 0.9,
                        "touches": 5,
                        "level_type": "resistance"
                    }
                ]
            }
        """
        try:
            recognizer = PatternRecognizer()
            levels = await recognizer.find_support_resistance(token_symbol.upper())

            return {
                "support": [SupportResistanceLevelResponse(**l.to_dict()) for l in levels["support"]],
                "resistance": [SupportResistanceLevelResponse(**l.to_dict()) for l in levels["resistance"]],
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Support/resistance detection failed: {str(e)}",
            )

    @router.get(
        "/analysis/{token_symbol}",
        response_model=Dict,
        summary="Comprehensive pattern analysis",
        description="Get all pattern types in one request",
    )
    async def comprehensive_pattern_analysis(
        token_symbol: str,
    ) -> Dict:
        """Comprehensive pattern analysis.

        Returns all pattern analysis types:
        - Chart patterns
        - Candlestick patterns
        - Support/resistance levels

        Args:
            token_symbol: Token symbol

        Returns:
            Dictionary with all pattern analysis

        Example:
            GET /api/v1/hunter/patterns/analysis/BTC

            Response:
            {
                "chart_patterns": [...],
                "candlestick_patterns": [...],
                "support_resistance": {
                    "support": [...],
                    "resistance": [...]
                }
            }
        """
        try:
            recognizer = PatternRecognizer()

            chart_patterns = await recognizer.detect_chart_patterns(token_symbol.upper())
            candlestick_patterns = await recognizer.detect_candlestick_patterns(token_symbol.upper())
            levels = await recognizer.find_support_resistance(token_symbol.upper())

            return {
                "chart_patterns": [p.to_dict() for p in chart_patterns],
                "candlestick_patterns": [s.to_dict() for s in candlestick_patterns],
                "support_resistance": {
                    "support": [l.to_dict() for l in levels["support"]],
                    "resistance": [l.to_dict() for l in levels["resistance"]],
                },
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pattern analysis failed: {str(e)}",
            )

    return router
