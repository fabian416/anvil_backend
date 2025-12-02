"""
Portfolio router for risk analysis endpoints.
"""

from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status, Security
from fastapi.exceptions import HTTPException

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.common.services.current_user import CurrentUserService
from app.presentation.http.schemas.portfolio import (
    PortfolioRiskResponse,
    CascadeSimulationRequest,
    CascadeSimulationResponse,
)
from app.application.portfolio import PortfolioRiskAnalysis
from app.domain.entities.user_portfolio import UserPortfolio


def create_portfolio_router() -> APIRouter:
    router = APIRouter(
        prefix="/portfolio",
        tags=["portfolio"],
    )

    @router.get(
        "/risk",
        status_code=status.HTTP_200_OK,
        response_model=PortfolioRiskResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_portfolio_risk(
        current_user: FromDishka[CurrentUserService],
        risk_analysis: FromDishka[PortfolioRiskAnalysis],
    ) -> PortfolioRiskResponse:
        """
        Get comprehensive risk analysis for user's portfolio.

        Returns:
        - Overall risk score (weighted by exposure)
        - Risk distribution by level
        - Protocols at elevated risk
        - Dependency risks
        - Systemic risk score
        - Concentration risk
        - Chain-specific risks
        - Actionable recommendations
        """
        user = await current_user.get_current_user()

        # TODO: Get actual portfolio from repository
        # For now, create mock portfolio for demonstration
        portfolio = UserPortfolio(user_id=UUID(str(user.id)))
        
        # In production, would load from:
        # portfolio = await portfolio_repo.get_by_user_id(user.id)
        
        if not portfolio.protocols:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No portfolio found. Add protocols to your portfolio first.",
            )

        # Get risk analysis
        risk_summary = await risk_analysis.get_portfolio_risk(portfolio)

        return PortfolioRiskResponse(
            user_id=str(risk_summary.user_id),
            overall_risk_score=risk_summary.overall_risk_score,
            risk_distribution=risk_summary.risk_distribution,
            protocols_at_risk=[
                {
                    "protocol_id": str(p.protocol_id),
                    "protocol_name": p.protocol_name,
                    "exposure_usd": float(p.exposure_usd),
                    "exposure_percentage": p.exposure_percentage,
                    "risk_score": p.risk_score,
                    "risk_level": p.risk_level,
                    "risk_trend": p.risk_trend,
                    "contributing_factors": p.contributing_factors,
                    "value_at_risk_usd": float(p.value_at_risk_usd),
                }
                for p in risk_summary.protocols_at_risk
            ],
            dependency_risks=[
                {
                    "dependency_protocol_id": str(d.dependency_protocol_id),
                    "dependency_protocol_name": d.dependency_protocol_name,
                    "dependent_protocols": d.dependent_protocols,
                    "impact_if_failure": d.impact_if_failure,
                    "total_exposure_usd": float(d.total_exposure_usd),
                    "risk_score": d.risk_score,
                }
                for d in risk_summary.dependency_risks
            ],
            systemic_risk_score=risk_summary.systemic_risk_score,
            concentration_risk=risk_summary.concentration_risk,
            chain_risk_distribution=risk_summary.chain_risk_distribution,
            recommendations=risk_summary.recommendations,
            total_value_at_risk_usd=float(risk_summary.total_value_at_risk_usd),
            last_updated=risk_summary.last_updated.isoformat(),
        )

    @router.post(
        "/risk/simulate-cascade",
        status_code=status.HTTP_200_OK,
        response_model=CascadeSimulationResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def simulate_cascade(
        request: CascadeSimulationRequest,
        current_user: FromDishka[CurrentUserService],
        risk_analysis: FromDishka[PortfolioRiskAnalysis],
    ) -> CascadeSimulationResponse:
        """
        Simulate cascade failure impact on portfolio.

        Simulates what would happen if a specific protocol in the
        portfolio fails, showing direct and indirect impacts via
        network contagion.

        Args:
            origin_protocol_id: Protocol that fails

        Returns:
        - Cascade impacts (direct/indirect)
        - Worst case loss (USD and %)
        - Protocols to exit immediately
        - Protocols to reduce exposure
        - Safe protocols (unaffected)
        """
        user = await current_user.get_current_user()

        # TODO: Get actual portfolio
        portfolio = UserPortfolio(user_id=UUID(str(user.id)))

        if not portfolio.protocols:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No portfolio found",
            )

        # Check if protocol is in portfolio
        origin_id = UUID(request.origin_protocol_id)
        if not portfolio.get_exposure(origin_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Protocol not in your portfolio",
            )

        # Run simulation
        cascade_result = await risk_analysis.simulate_portfolio_cascade(
            portfolio, origin_id
        )

        return CascadeSimulationResponse(
            user_id=str(cascade_result.user_id),
            cascade_impacts=[
                {
                    "origin_protocol_id": str(c.origin_protocol_id),
                    "origin_protocol_name": c.origin_protocol_name,
                    "directly_affected": c.directly_affected,
                    "indirectly_affected": c.indirectly_affected,
                    "total_exposure_at_risk_usd": float(c.total_exposure_at_risk_usd),
                    "cascade_probability": c.cascade_probability,
                    "time_to_impact": c.time_to_impact,
                }
                for c in cascade_result.cascade_impacts
            ],
            worst_case_loss_usd=float(cascade_result.worst_case_loss_usd),
            worst_case_loss_percentage=cascade_result.worst_case_loss_percentage,
            protocols_to_exit=cascade_result.protocols_to_exit,
            protocols_to_reduce=cascade_result.protocols_to_reduce,
            safe_protocols=cascade_result.safe_protocols,
        )

    return router
