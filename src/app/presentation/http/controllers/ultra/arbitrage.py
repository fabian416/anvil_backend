"""Arbitrage Discovery API endpoints.

REST API for arbitrage opportunity discovery and simulation.
"""

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from decimal import Decimal

from app.application.ultra.arbitrage_discovery import (
    ArbitrageDiscovery,
    ArbitrageType,
    DEX,
)


class ArbitrageOpportunityResponse(BaseModel):
    """Response model for arbitrage opportunity."""

    opportunity_id: str = Field(..., description="Unique opportunity ID")
    type: str = Field(..., description="Arbitrage type")
    path: List[Dict] = Field(..., description="Trading path")
    expected_profit_usd: str = Field(..., description="Expected profit USD")
    profit_percentage: float = Field(..., description="Profit percentage")
    required_capital: str = Field(..., description="Required capital USD")
    estimated_gas_cost: str = Field(..., description="Estimated gas cost USD")
    confidence_score: float = Field(..., description="Confidence score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "opportunity_id": "ARB-1638360000-0001",
                "type": "2hop",
                "path": [
                    {
                        "dex": "uniswap_v2",
                        "token_in": "WETH",
                        "token_out": "USDC",
                        "amount_in": "10000",
                        "amount_out": "20000000",
                        "price": "2000.0",
                    }
                ],
                "expected_profit_usd": "95.50",
                "profit_percentage": 0.955,
                "required_capital": "10000",
                "estimated_gas_cost": "15.00",
                "confidence_score": 0.85,
            }
        }


class SimulationRequest(BaseModel):
    """Request model for opportunity simulation."""

    opportunity_id: str = Field(..., description="Opportunity ID to simulate")

    class Config:
        json_schema_extra = {"example": {"opportunity_id": "ARB-1638360000-0001"}}


class SimulationResponse(BaseModel):
    """Response model for simulation result."""

    opportunity_id: str = Field(..., description="Opportunity ID")
    type: str = Field(..., description="Arbitrage type")
    expected_profit: str = Field(..., description="Expected profit USD")
    simulated_profit: str = Field(..., description="Simulated profit with slippage")
    slippage_impact: str = Field(..., description="Slippage impact USD")
    success_probability: float = Field(..., description="Success probability (0-1)")
    recommendation: str = Field(..., description="Execute or Skip")

    class Config:
        json_schema_extra = {
            "example": {
                "opportunity_id": "ARB-1638360000-0001",
                "type": "2hop",
                "expected_profit": "95.50",
                "simulated_profit": "94.55",
                "slippage_impact": "0.95",
                "success_probability": 0.85,
                "recommendation": "Execute",
            }
        }


def create_arbitrage_router() -> APIRouter:
    """Create arbitrage discovery router.

    Returns:
        Configured FastAPI router
    """
    router = APIRouter(prefix="/user/ultra/arbitrage", tags=["ultra-arbitrage"])

    # In-memory storage for discovered opportunities (would be Redis in production)
    _discovered_opportunities = []

    @router.get(
        "/discover",
        response_model=List[ArbitrageOpportunityResponse],
        summary="Discover arbitrage opportunities",
        description="Scan all DEXes for profitable arbitrage opportunities",
    )
    async def discover_opportunities(
        capital: float = Query(
            10000, ge=100, le=1000000, description="Starting capital USD"
        ),
        type: Optional[str] = Query(
            None, description="Filter by type: 2hop, 3hop, triangle"
        ),
        min_profit: Optional[float] = Query(
            None, ge=0, description="Minimum profit USD filter"
        ),
    ) -> List[ArbitrageOpportunityResponse]:
        """Discover arbitrage opportunities.

        Scans all supported DEXes for profitable arbitrage opportunities including:
        - 2-hop: Cross-DEX price differences
        - 3-hop: Multi-token circular paths
        - Triangle: Same-DEX triangular arbitrage

        Args:
            capital: Starting capital in USD
            type: Filter by arbitrage type (optional)
            min_profit: Minimum profit threshold (optional)

        Returns:
            List of discovered opportunities sorted by profit

        Example:
            GET /api/v1/ultra/arbitrage/discover?capital=10000&type=2hop&min_profit=100

            Response:
            [
                {
                    "opportunity_id": "ARB-1638360000-0001",
                    "type": "2hop",
                    "path": [
                        {
                            "dex": "uniswap_v2",
                            "token_in": "WETH",
                            "token_out": "USDC",
                            "price": "2000.0"
                        },
                        {
                            "dex": "sushiswap",
                            "token_in": "USDC",
                            "token_out": "WETH",
                            "price": "0.000505"
                        }
                    ],
                    "expected_profit_usd": "95.50",
                    "profit_percentage": 0.955,
                    "confidence_score": 0.85
                }
            ]
        """
        try:
            discovery = ArbitrageDiscovery()
            capital_decimal = Decimal(str(capital))

            # Discover opportunities
            opportunities = await discovery.discover_all_opportunities(capital_decimal)

            # Store for later retrieval
            nonlocal _discovered_opportunities
            _discovered_opportunities = opportunities

            # Filter by type if specified
            if type:
                try:
                    arb_type = ArbitrageType(type)
                    opportunities = [
                        opp for opp in opportunities if opp.type == arb_type
                    ]
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid type: {type}. Must be: 2hop, 3hop, triangle",
                    )

            # Filter by minimum profit if specified
            if min_profit is not None:
                min_profit_decimal = Decimal(str(min_profit))
                opportunities = [
                    opp
                    for opp in opportunities
                    if opp.expected_profit_usd >= min_profit_decimal
                ]

            return [
                ArbitrageOpportunityResponse(**opp.to_dict()) for opp in opportunities
            ]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Discovery failed: {str(e)}",
            )

    @router.get(
        "/opportunities",
        response_model=List[ArbitrageOpportunityResponse],
        summary="List discovered opportunities",
        description="Get list of previously discovered opportunities",
    )
    async def list_opportunities(
        limit: int = Query(10, ge=1, le=100, description="Maximum results"),
        sort_by: str = Query(
            "profit", description="Sort by: profit, confidence, timestamp"
        ),
    ) -> List[ArbitrageOpportunityResponse]:
        """List discovered opportunities.

        Returns previously discovered opportunities from the cache.

        Args:
            limit: Maximum number of results
            sort_by: Sort field (profit, confidence, timestamp)

        Returns:
            List of opportunities

        Example:
            GET /api/v1/ultra/arbitrage/opportunities?limit=5&sort_by=profit

            Response:
            [
                {
                    "opportunity_id": "ARB-1638360000-0001",
                    "expected_profit_usd": "150.00",
                    ...
                }
            ]
        """
        try:
            opportunities = _discovered_opportunities.copy()

            # Sort
            if sort_by == "profit":
                opportunities.sort(
                    key=lambda x: x.expected_profit_usd, reverse=True
                )
            elif sort_by == "confidence":
                opportunities.sort(key=lambda x: x.confidence_score, reverse=True)
            elif sort_by == "timestamp":
                opportunities.sort(key=lambda x: x.timestamp, reverse=True)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid sort_by: {sort_by}",
                )

            # Limit results
            opportunities = opportunities[:limit]

            return [
                ArbitrageOpportunityResponse(**opp.to_dict()) for opp in opportunities
            ]

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list opportunities: {str(e)}",
            )

    @router.post(
        "/simulate",
        response_model=SimulationResponse,
        summary="Simulate opportunity execution",
        description="Simulate execution of an arbitrage opportunity",
    )
    async def simulate_opportunity(request: SimulationRequest) -> SimulationResponse:
        """Simulate opportunity execution.

        Simulates the execution of an arbitrage opportunity including:
        - Slippage impact
        - Success probability
        - Net profit after costs
        - Execution recommendation

        Args:
            request: Simulation request with opportunity ID

        Returns:
            Simulation result

        Example:
            POST /api/v1/ultra/arbitrage/simulate
            Body:
            {
                "opportunity_id": "ARB-1638360000-0001"
            }

            Response:
            {
                "opportunity_id": "ARB-1638360000-0001",
                "type": "2hop",
                "expected_profit": "95.50",
                "simulated_profit": "94.55",
                "slippage_impact": "0.95",
                "success_probability": 0.85,
                "recommendation": "Execute"
            }
        """
        try:
            # Find opportunity
            opportunity = None
            for opp in _discovered_opportunities:
                if opp.opportunity_id == request.opportunity_id:
                    opportunity = opp
                    break

            if not opportunity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Opportunity not found: {request.opportunity_id}",
                )

            # Simulate
            discovery = ArbitrageDiscovery()
            result = await discovery.simulate_opportunity(opportunity)

            return SimulationResponse(**result)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Simulation failed: {str(e)}",
            )

    @router.get(
        "/statistics",
        response_model=Dict,
        summary="Get arbitrage statistics",
        description="Get statistics about discovered opportunities",
    )
    async def get_statistics() -> Dict:
        """Get arbitrage statistics.

        Returns statistics about all discovered opportunities.

        Returns:
            Statistics dictionary

        Example:
            GET /api/v1/ultra/arbitrage/statistics

            Response:
            {
                "total_opportunities": 15,
                "by_type": {
                    "2hop": 8,
                    "3hop": 5,
                    "triangle": 2
                },
                "total_potential_profit": "1250.00",
                "average_profit": "83.33",
                "best_opportunity": {
                    "id": "ARB-1638360000-0001",
                    "profit": "150.00"
                }
            }
        """
        try:
            if not _discovered_opportunities:
                return {
                    "total_opportunities": 0,
                    "by_type": {},
                    "total_potential_profit": "0",
                    "average_profit": "0",
                    "best_opportunity": None,
                }

            # Calculate statistics
            by_type = {}
            total_profit = Decimal("0")

            for opp in _discovered_opportunities:
                # Count by type
                type_str = opp.type.value
                by_type[type_str] = by_type.get(type_str, 0) + 1

                # Sum profit
                total_profit += opp.expected_profit_usd

            # Find best
            best = max(_discovered_opportunities, key=lambda x: x.expected_profit_usd)

            return {
                "total_opportunities": len(_discovered_opportunities),
                "by_type": by_type,
                "total_potential_profit": str(total_profit),
                "average_profit": str(
                    total_profit / len(_discovered_opportunities)
                ),
                "best_opportunity": {
                    "id": best.opportunity_id,
                    "type": best.type.value,
                    "profit": str(best.expected_profit_usd),
                },
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get statistics: {str(e)}",
            )

    return router
