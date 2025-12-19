"""MEV Protection & Execution API endpoints.

REST API for MEV-protected arbitrage execution.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from decimal import Decimal

from app.application.ultra.mev_protection import (
    MEVProtection,
    Transaction,
    ProtectionLevel,
)
from app.application.ultra.arbitrage_executor import ArbitrageExecutor
from app.application.ultra.arbitrage_discovery import ArbitrageDiscovery


class ExecuteRequest(BaseModel):
    """Request model for arbitrage execution."""

    opportunity_id: str = Field(..., description="Opportunity ID to execute")
    use_mev_protection: bool = Field(
        True, description="Use MEV protection (recommended)"
    )

    class Config:
        json_schema_extra = {
            "example": {"opportunity_id": "ARB-1638360000-0001", "use_mev_protection": True}
        }


class ExecutionResponse(BaseModel):
    """Response model for execution result."""

    execution_id: str = Field(..., description="Execution ID")
    opportunity_id: str = Field(..., description="Opportunity ID")
    status: str = Field(..., description="Execution status")
    expected_profit: str = Field(..., description="Expected profit USD")
    realized_profit: Optional[str] = Field(None, description="Realized profit USD")
    gas_cost: str = Field(..., description="Gas cost USD")


class BundleStatusResponse(BaseModel):
    """Response model for bundle status."""

    bundle_id: str = Field(..., description="Bundle ID")
    status: str = Field(..., description="Bundle status")
    block_number: Optional[int] = Field(None, description="Block number")
    profit_realized: Optional[str] = Field(None, description="Realized profit")


def create_mev_router() -> APIRouter:
    """Create MEV protection router.

    Returns:
        Configured FastAPI router
    """
    router = APIRouter(prefix="/user/ultra/mev", tags=["ultra-mev"])

    # Global instances
    _mev_protection = MEVProtection()
    _executor = ArbitrageExecutor(mev_protection=_mev_protection)
    _discovery = ArbitrageDiscovery()
    _discovered_opportunities = []

    @router.post(
        "/execute",
        response_model=ExecutionResponse,
        summary="Execute arbitrage with MEV protection",
        description="Execute discovered arbitrage opportunity with MEV protection",
    )
    async def execute_arbitrage(request: ExecuteRequest) -> ExecutionResponse:
        """Execute arbitrage opportunity.

        Executes a discovered arbitrage opportunity with:
        - Flash loan acquisition
        - MEV-protected transaction bundling
        - Flashbots relay submission
        - Profit tracking

        Args:
            request: Execution request

        Returns:
            Execution result

        Example:
            POST /api/v1/ultra/mev/execute
            Body:
            {
                "opportunity_id": "ARB-1638360000-0001",
                "use_mev_protection": true
            }

            Response:
            {
                "execution_id": "EXEC-1638360100-0001",
                "opportunity_id": "ARB-1638360000-0001",
                "status": "success",
                "expected_profit": "145.50",
                "realized_profit": "143.20",
                "gas_cost": "25.00"
            }
        """
        try:
            # Find opportunity (in production, would fetch from database)
            opportunity = None
            for opp in _discovered_opportunities:
                if opp.opportunity_id == request.opportunity_id:
                    opportunity = opp
                    break

            if not opportunity:
                # Try discovering new opportunities
                opportunities = await _discovery.discover_all_opportunities(
                    Decimal("10000")
                )
                _discovered_opportunities.extend(opportunities)

                for opp in opportunities:
                    if opp.opportunity_id == request.opportunity_id:
                        opportunity = opp
                        break

            if not opportunity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Opportunity not found: {request.opportunity_id}",
                )

            # Execute
            result = await _executor.execute_opportunity(
                opportunity, use_mev_protection=request.use_mev_protection
            )

            return ExecutionResponse(**result.to_dict())

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Execution failed: {str(e)}",
            )

    @router.get(
        "/bundles/{bundle_id}",
        response_model=BundleStatusResponse,
        summary="Check bundle status",
        description="Get status of submitted MEV bundle",
    )
    async def get_bundle_status(bundle_id: str) -> BundleStatusResponse:
        """Check bundle status.

        Returns the current status of a submitted MEV bundle.

        Args:
            bundle_id: Bundle ID

        Returns:
            Bundle status

        Example:
            GET /api/v1/ultra/mev/bundles/BUNDLE-1638360000-0001

            Response:
            {
                "bundle_id": "BUNDLE-1638360000-0001",
                "status": "included",
                "block_number": 18000001,
                "profit_realized": "145.50"
            }
        """
        try:
            status_result = await _mev_protection.check_bundle_status(bundle_id)

            if not status_result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bundle not found: {bundle_id}",
                )

            return BundleStatusResponse(**status_result.to_dict())

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get bundle status: {str(e)}",
            )

    @router.get(
        "/statistics",
        response_model=Dict,
        summary="Get MEV statistics",
        description="Get statistics about MEV-protected executions",
    )
    async def get_statistics() -> Dict:
        """Get MEV statistics.

        Returns statistics about all MEV-protected executions.

        Returns:
            Statistics dictionary

        Example:
            GET /api/v1/ultra/mev/statistics

            Response:
            {
                "total_bundles": 25,
                "by_status": {
                    "included": 20,
                    "failed": 5
                },
                "success_rate": 80.0,
                "total_profit": "2450.00"
            }
        """
        try:
            return await _mev_protection.get_bundle_statistics()

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get statistics: {str(e)}",
            )

    @router.get(
        "/protection-info",
        response_model=Dict,
        summary="Get protection configuration",
        description="Get current MEV protection configuration",
    )
    async def get_protection_info() -> Dict:
        """Get protection configuration.

        Returns current MEV protection settings.

        Returns:
            Protection configuration

        Example:
            GET /api/v1/ultra/mev/protection-info

            Response:
            {
                "protection_level": "advanced",
                "use_flashbots": true,
                "use_private_relay": true,
                "use_mev_share": false,
                "max_gas_price_gwei": 150,
                "simulation_enabled": true
            }
        """
        try:
            return _mev_protection.get_protection_info()

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get protection info: {str(e)}",
            )

    return router
