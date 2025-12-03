"""Portfolio optimization API endpoints.

REST API for Modern Portfolio Theory (MPT) portfolio optimization.
"""

from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from app.application.hunter.portfolio_optimizer import (
    PortfolioOptimizer,
    PortfolioConfig,
)


class OptimizedPortfolioResponse(BaseModel):
    """Response model for optimized portfolio."""

    weights: Dict[str, float] = Field(..., description="Asset weights (as percentages)")
    metrics: Dict = Field(..., description="Portfolio performance metrics")
    timestamp: str = Field(..., description="Optimization timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "weights": {"BTC": 40.0, "ETH": 35.0, "SOL": 25.0},
                "metrics": {
                    "expected_return": 45.2,
                    "volatility": 32.8,
                    "sharpe_ratio": 1.28,
                },
                "timestamp": "2025-12-03T20:00:00Z",
            }
        }


class EfficientFrontierResponse(BaseModel):
    """Response model for efficient frontier."""

    returns: List[float] = Field(..., description="Expected returns")
    risks: List[float] = Field(..., description="Volatilities")
    sharpe_ratios: List[float] = Field(..., description="Sharpe ratios")
    max_sharpe_portfolio: Dict = Field(..., description="Maximum Sharpe ratio portfolio")
    min_volatility_portfolio: Dict = Field(..., description="Minimum volatility portfolio")

    class Config:
        json_schema_extra = {
            "example": {
                "returns": [25.0, 30.0, 35.0],
                "risks": [20.0, 25.0, 30.0],
                "sharpe_ratios": [1.1, 1.15, 1.08],
                "max_sharpe_portfolio": {"return": 30.0, "risk": 25.0, "sharpe": 1.15},
                "min_volatility_portfolio": {"return": 25.0, "risk": 20.0, "sharpe": 1.1},
            }
        }


class RebalancingPlanResponse(BaseModel):
    """Response model for rebalancing plan."""

    current_weights: Dict[str, float] = Field(..., description="Current portfolio weights")
    target_weights: Dict[str, float] = Field(..., description="Target portfolio weights")
    changes: Dict[str, float] = Field(..., description="Weight changes needed")
    trades: List[Dict] = Field(..., description="Trade recommendations")
    estimated_cost: float = Field(..., description="Estimated trading cost")
    timestamp: str = Field(..., description="Plan timestamp")


def create_portfolio_router() -> APIRouter:
    """Create portfolio optimization router.

    Returns:
        Configured FastAPI router
    """
    router = APIRouter(prefix="/hunter/portfolio", tags=["hunter-portfolio"])

    @router.post(
        "/optimize",
        response_model=OptimizedPortfolioResponse,
        summary="Optimize portfolio",
        description="Optimize portfolio allocation using Modern Portfolio Theory (MPT)",
    )
    async def optimize_portfolio(
        tokens: str = Query(..., description="Comma-separated token symbols (e.g., BTC,ETH,SOL)"),
        risk_tolerance: float = Query(0.5, ge=0.0, le=1.0, description="Risk tolerance (0=conservative, 1=aggressive)"),
    ) -> OptimizedPortfolioResponse:
        """Optimize portfolio allocation.

        Uses MPT to find optimal asset weights based on risk tolerance:
        - Conservative (0-0.33): Minimize variance
        - Balanced (0.33-0.67): Maximize Sharpe ratio
        - Aggressive (0.67-1.0): Maximize return

        Args:
            tokens: Comma-separated token list
            risk_tolerance: Risk tolerance level

        Returns:
            Optimized portfolio with weights and metrics

        Example:
            POST /api/v1/hunter/portfolio/optimize?tokens=BTC,ETH,SOL&risk_tolerance=0.5

            Response:
            {
                "weights": {"BTC": 40.0, "ETH": 35.0, "SOL": 25.0},
                "metrics": {
                    "expected_return": 45.2,
                    "volatility": 32.8,
                    "sharpe_ratio": 1.28
                }
            }
        """
        try:
            # Parse token list
            token_list = [t.strip().upper() for t in tokens.split(",")]

            if len(token_list) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least 2 tokens required for portfolio optimization",
                )

            if len(token_list) > 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum 10 tokens allowed",
                )

            optimizer = PortfolioOptimizer()
            portfolio = await optimizer.optimize_portfolio(token_list, risk_tolerance)

            return OptimizedPortfolioResponse(**portfolio.to_dict())

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Portfolio optimization failed: {str(e)}",
            )

    @router.get(
        "/efficient-frontier",
        response_model=EfficientFrontierResponse,
        summary="Calculate efficient frontier",
        description="Calculate efficient frontier showing risk-return tradeoffs",
    )
    async def calculate_efficient_frontier(
        tokens: str = Query(..., description="Comma-separated token symbols"),
    ) -> EfficientFrontierResponse:
        """Calculate efficient frontier.

        Shows the set of optimal portfolios offering the highest expected return
        for each level of risk.

        Args:
            tokens: Comma-separated token list

        Returns:
            Efficient frontier data with max Sharpe and min volatility portfolios

        Example:
            GET /api/v1/hunter/portfolio/efficient-frontier?tokens=BTC,ETH,SOL

            Response:
            {
                "returns": [25.0, 30.0, 35.0, 40.0],
                "risks": [20.0, 25.0, 30.0, 35.0],
                "max_sharpe_portfolio": {...},
                "min_volatility_portfolio": {...}
            }
        """
        try:
            # Parse token list
            token_list = [t.strip().upper() for t in tokens.split(",")]

            if len(token_list) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least 2 tokens required",
                )

            optimizer = PortfolioOptimizer()
            frontier = await optimizer.calculate_efficient_frontier(token_list)

            return EfficientFrontierResponse(**frontier.to_dict())

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Efficient frontier calculation failed: {str(e)}",
            )

    @router.post(
        "/analyze",
        response_model=Dict,
        summary="Analyze portfolio",
        description="Analyze existing portfolio allocation and calculate metrics",
    )
    async def analyze_portfolio(
        portfolio: Dict[str, float] = Query(..., description="Portfolio weights (e.g., {\"BTC\": 0.6, \"ETH\": 0.4})"),
    ) -> Dict:
        """Analyze existing portfolio.

        Calculates comprehensive metrics for a given portfolio allocation.

        Args:
            portfolio: Portfolio weights (token: weight as decimal)

        Returns:
            Portfolio metrics

        Example:
            POST /api/v1/hunter/portfolio/analyze
            Body: {"BTC": 0.6, "ETH": 0.4}

            Response:
            {
                "expected_return": 42.5,
                "volatility": 35.2,
                "sharpe_ratio": 1.12,
                "sortino_ratio": 1.45,
                "max_drawdown": -28.5,
                "diversification_score": 0.72
            }
        """
        try:
            # Validate weights sum to 1.0
            total_weight = sum(portfolio.values())
            if not (0.99 <= total_weight <= 1.01):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Weights must sum to 1.0 (current: {total_weight:.2f})",
                )

            optimizer = PortfolioOptimizer()
            metrics = await optimizer.analyze_portfolio(portfolio)

            return metrics.to_dict()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Portfolio analysis failed: {str(e)}",
            )

    @router.post(
        "/rebalance",
        response_model=RebalancingPlanResponse,
        summary="Generate rebalancing plan",
        description="Suggest portfolio rebalancing to optimal allocation",
    )
    async def suggest_rebalancing(
        current_portfolio: Dict[str, float] = Query(..., description="Current portfolio weights"),
        risk_tolerance: float = Query(0.5, ge=0.0, le=1.0, description="Risk tolerance"),
    ) -> RebalancingPlanResponse:
        """Generate rebalancing plan.

        Compares current portfolio to optimal allocation and suggests trades.

        Args:
            current_portfolio: Current portfolio weights
            risk_tolerance: Risk tolerance level

        Returns:
            Rebalancing plan with trade recommendations

        Example:
            POST /api/v1/hunter/portfolio/rebalance?risk_tolerance=0.5
            Body: {"BTC": 0.7, "ETH": 0.3}

            Response:
            {
                "current_weights": {"BTC": 70.0, "ETH": 30.0},
                "target_weights": {"BTC": 55.0, "ETH": 45.0},
                "changes": {"BTC": -15.0, "ETH": +15.0},
                "trades": [
                    {"token": "BTC", "action": "SELL", "change_pct": -15.0},
                    {"token": "ETH", "action": "BUY", "change_pct": +15.0}
                ]
            }
        """
        try:
            # Validate weights
            total_weight = sum(current_portfolio.values())
            if not (0.99 <= total_weight <= 1.01):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Weights must sum to 1.0 (current: {total_weight:.2f})",
                )

            optimizer = PortfolioOptimizer()
            plan = await optimizer.suggest_rebalancing(current_portfolio, risk_tolerance)

            return RebalancingPlanResponse(**plan.to_dict())

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rebalancing plan generation failed: {str(e)}",
            )

    return router
