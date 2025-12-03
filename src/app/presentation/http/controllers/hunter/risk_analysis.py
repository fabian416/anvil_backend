"""Risk analysis API endpoints.

REST API for ML-based risk assessment.
"""

from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Optional

from app.application.hunter.risk_analyzer import (
    RiskAnalyzer,
    RiskConfig,
)


class RiskFactorResponse(BaseModel):
    """Response model for individual risk factor."""

    factor: str = Field(..., description="Risk factor name")
    score: float = Field(..., description="Risk score (0-100)", ge=0, le=100)
    level: str = Field(..., description="Risk level: low, medium, high, extreme")
    details: Dict = Field(..., description="Detailed metrics for this factor")
    timestamp: str = Field(..., description="Analysis timestamp")


class CompositeRiskResponse(BaseModel):
    """Response model for comprehensive risk assessment."""

    token_symbol: str = Field(..., description="Token symbol")
    overall_risk_score: float = Field(..., description="Overall risk score (0-100)", ge=0, le=100)
    overall_risk_level: str = Field(..., description="Overall risk level")
    risk_factors: Dict[str, RiskFactorResponse] = Field(..., description="Individual risk factors")
    recommendation: str = Field(..., description="Trading recommendation")
    timestamp: str = Field(..., description="Analysis timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "token_symbol": "ETH",
                "overall_risk_score": 32.5,
                "overall_risk_level": "medium",
                "risk_factors": {
                    "volatility": {
                        "factor": "volatility",
                        "score": 35.2,
                        "level": "medium",
                        "details": {
                            "historical_volatility": 3.5,
                            "max_drawdown_pct": -15.2,
                        },
                        "timestamp": "2025-12-03T17:00:00Z",
                    }
                },
                "recommendation": "Moderate risk profile. Suitable for balanced portfolios.",
                "timestamp": "2025-12-03T17:00:00Z",
            }
        }


def create_risk_analysis_router() -> APIRouter:
    """Create risk analysis router.

    Returns:
        Configured FastAPI router
    """
    router = APIRouter(prefix="/hunter/risk", tags=["hunter-risk"])

    @router.get(
        "/analyze/{token_symbol}",
        response_model=CompositeRiskResponse,
        summary="Comprehensive risk analysis",
        description="Analyze token risk across 4 factors: volatility, liquidity, smart contract, and market correlation",
    )
    async def analyze_comprehensive_risk(
        token_symbol: str = Field(..., description="Token symbol (e.g., ETH, BTC)"),
    ) -> CompositeRiskResponse:
        """Perform comprehensive risk analysis.

        Analyzes:
        - Volatility Risk (price stability)
        - Liquidity Risk (trading volume)
        - Smart Contract Risk (code security)
        - Market Correlation Risk (systemic exposure)

        Args:
            token_symbol: Token to analyze

        Returns:
            Complete risk assessment with recommendations

        Example:
            GET /api/v1/hunter/risk/analyze/ETH

            Response:
            {
                "token_symbol": "ETH",
                "overall_risk_score": 32.5,
                "overall_risk_level": "medium",
                "risk_factors": {
                    "volatility": {...},
                    "liquidity": {...},
                    "smart_contract": {...},
                    "correlation": {...}
                },
                "recommendation": "Moderate risk profile..."
            }
        """
        try:
            analyzer = RiskAnalyzer()
            assessment = await analyzer.analyze_comprehensive_risk(token_symbol)

            # Convert to response format
            risk_factors_response = {
                name: RiskFactorResponse(**risk.to_dict())
                for name, risk in assessment.risk_factors.items()
            }

            return CompositeRiskResponse(
                token_symbol=assessment.token_symbol,
                overall_risk_score=assessment.overall_risk_score,
                overall_risk_level=assessment.overall_risk_level,
                risk_factors=risk_factors_response,
                recommendation=assessment.recommendation,
                timestamp=assessment.timestamp.isoformat(),
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Risk analysis failed: {str(e)}",
            )

    @router.get(
        "/volatility/{token_symbol}",
        response_model=RiskFactorResponse,
        summary="Volatility risk analysis",
        description="Analyze token price volatility risk",
    )
    async def analyze_volatility_risk(
        token_symbol: str = Field(..., description="Token symbol"),
        window_days: int = Query(30, ge=7, le=90, description="Analysis window in days"),
    ) -> RiskFactorResponse:
        """Analyze volatility risk only.

        Args:
            token_symbol: Token to analyze
            window_days: Historical window for analysis

        Returns:
            Volatility risk assessment

        Example:
            GET /api/v1/hunter/risk/volatility/ETH?window_days=30

            Response:
            {
                "factor": "volatility",
                "score": 35.2,
                "level": "medium",
                "details": {
                    "historical_volatility": 3.5,
                    "avg_daily_range_pct": 4.2,
                    "max_drawdown_pct": -15.2,
                    "sharp_movements": 3
                }
            }
        """
        try:
            config = RiskConfig(volatility_window=window_days)
            analyzer = RiskAnalyzer(config=config)
            risk = await analyzer.analyze_volatility_risk(token_symbol)

            return RiskFactorResponse(**risk.to_dict())

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Volatility analysis failed: {str(e)}",
            )

    @router.get(
        "/liquidity/{token_symbol}",
        response_model=RiskFactorResponse,
        summary="Liquidity risk analysis",
        description="Analyze token liquidity risk based on trading volume",
    )
    async def analyze_liquidity_risk(
        token_symbol: str = Field(..., description="Token symbol"),
    ) -> RiskFactorResponse:
        """Analyze liquidity risk only.

        Args:
            token_symbol: Token to analyze

        Returns:
            Liquidity risk assessment

        Example:
            GET /api/v1/hunter/risk/liquidity/ETH

            Response:
            {
                "factor": "liquidity",
                "score": 25.0,
                "level": "low",
                "details": {
                    "avg_daily_volume_usd": 15000000,
                    "volume_consistency": 0.85,
                    "estimated_spread_pct": 0.20
                }
            }
        """
        try:
            analyzer = RiskAnalyzer()
            risk = await analyzer.analyze_liquidity_risk(token_symbol)

            return RiskFactorResponse(**risk.to_dict())

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Liquidity analysis failed: {str(e)}",
            )

    @router.get(
        "/smart-contract/{token_symbol}",
        response_model=RiskFactorResponse,
        summary="Smart contract risk analysis",
        description="Analyze token smart contract security risk",
    )
    async def analyze_smart_contract_risk(
        token_symbol: str = Field(..., description="Token symbol"),
    ) -> RiskFactorResponse:
        """Analyze smart contract risk only.

        Args:
            token_symbol: Token to analyze

        Returns:
            Smart contract risk assessment

        Example:
            GET /api/v1/hunter/risk/smart-contract/ETH

            Response:
            {
                "factor": "smart_contract",
                "score": 15.0,
                "level": "low",
                "details": {
                    "audit_status": "complete",
                    "bug_bounty": "active",
                    "code_quality": "high",
                    "centralization_risk": "low"
                }
            }
        """
        try:
            analyzer = RiskAnalyzer()
            risk = await analyzer.analyze_smart_contract_risk(token_symbol)

            return RiskFactorResponse(**risk.to_dict())

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Smart contract analysis failed: {str(e)}",
            )

    @router.get(
        "/correlation/{token_symbol}",
        response_model=RiskFactorResponse,
        summary="Market correlation risk analysis",
        description="Analyze token correlation with market benchmark (BTC)",
    )
    async def analyze_correlation_risk(
        token_symbol: str = Field(..., description="Token symbol"),
    ) -> RiskFactorResponse:
        """Analyze market correlation risk only.

        Args:
            token_symbol: Token to analyze

        Returns:
            Correlation risk assessment

        Example:
            GET /api/v1/hunter/risk/correlation/ETH

            Response:
            {
                "factor": "correlation",
                "score": 75.0,
                "level": "high",
                "details": {
                    "correlation_with_btc": 0.85,
                    "beta": 1.2,
                    "systemic_risk_exposure": "high"
                }
            }
        """
        try:
            analyzer = RiskAnalyzer()
            risk = await analyzer.analyze_market_correlation_risk(token_symbol)

            return RiskFactorResponse(**risk.to_dict())

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Correlation analysis failed: {str(e)}",
            )

    return router
