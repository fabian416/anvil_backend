"""
Dashboard aggregation router.
"""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status, Security

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.common.services.current_user import CurrentUserService
from app.application.dashboard.dashboard_aggregation_service import (
    DashboardAggregationService,
)
from app.domain.entities.user_portfolio import UserPortfolio, ProtocolExposure


def create_dashboard_router() -> APIRouter:
    router = APIRouter(
        prefix="/dashboard",
        tags=["dashboard"],
    )

    @router.get(
        "/insights",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_dashboard_insights(
        current_user: FromDishka[CurrentUserService],
        dashboard_service: FromDishka[DashboardAggregationService],
    ) -> dict:
        """
        Get AI-powered dashboard insights.

        Returns personalized insights including:
        - Risk warnings
        - Optimization opportunities
        - Diversification suggestions
        - Market opportunities
        """
        user = await current_user.get_current_user()
        user_id = UUID(str(user.id))

        # TODO: Fetch real portfolio from repository
        # For now, create mock portfolio
        mock_portfolio = UserPortfolio(
            user_id=user_id,
            protocols=[
                ProtocolExposure(
                    protocol_id=UUID("00000000-0000-0000-0000-000000000001"),
                    protocol_name="Aave V3",
                    chain="Ethereum",
                    position_type="supplied",
                    amount_usd=8200,
                ),
                ProtocolExposure(
                    protocol_id=UUID("00000000-0000-0000-0000-000000000002"),
                    protocol_name="Euler Finance",
                    chain="Ethereum",
                    position_type="supplied",
                    amount_usd=2450,
                ),
            ],
        )

        insights = await dashboard_service.get_dashboard_insights(
            user_id, mock_portfolio
        )

        return {
            "insights": [
                {
                    "id": insight.id,
                    "type": insight.type,
                    "title": insight.title,
                    "message": insight.message,
                    "action_label": insight.action_label,
                    "action_url": insight.action_url,
                    "severity": insight.severity,
                    "created_at": insight.created_at.isoformat(),
                }
                for insight in insights
            ],
            "personalized": True,
        }

    @router.get(
        "/summary",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_dashboard_summary(
        current_user: FromDishka[CurrentUserService],
        dashboard_service: FromDishka[DashboardAggregationService],
    ) -> dict:
        """
        Get comprehensive dashboard summary.

        Returns:
        - Total portfolio value
        - 24h change
        - Risk score
        - Chain breakdown
        - Position breakdown
        """
        user = await current_user.get_current_user()
        user_id = UUID(str(user.id))

        # TODO: Fetch real portfolio
        mock_portfolio = UserPortfolio(
            user_id=user_id,
            protocols=[
                ProtocolExposure(
                    protocol_id=UUID("00000000-0000-0000-0000-000000000001"),
                    protocol_name="Aave V3",
                    chain="Ethereum",
                    position_type="supplied",
                    amount_usd=8200,
                ),
                ProtocolExposure(
                    protocol_id=UUID("00000000-0000-0000-0000-000000000002"),
                    protocol_name="Lido Finance",
                    chain="Ethereum",
                    position_type="staked",
                    amount_usd=12000,
                ),
            ],
        )

        summary = await dashboard_service.get_portfolio_summary(user_id, mock_portfolio)

        return summary

    return router
