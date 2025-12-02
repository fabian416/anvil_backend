"""Dashboard aggregation service for home dashboard insights."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.application.portfolio.portfolio_risk_analysis import PortfolioRiskAnalysis
from app.application.preferences.user_preferences_service import UserPreferencesService
from app.application.graph.hybrid_retrieval_interactor import HybridRetrievalInteractor
from app.domain.entities.user_portfolio import UserPortfolio


class AIInsight:
    """AI-generated insight for dashboard."""

    def __init__(
        self,
        id: str,
        insight_type: str,
        title: str,
        message: str,
        action_label: str,
        action_url: str,
        severity: str,
        created_at: datetime,
    ):
        self.id = id
        self.type = insight_type
        self.title = title
        self.message = message
        self.action_label = action_label
        self.action_url = action_url
        self.severity = severity
        self.created_at = created_at


class DashboardAggregationService:
    """
    Aggregate dashboard data from multiple sources.

    Combines portfolio risk, user preferences, GraphRAG recommendations,
    and real-time data to generate personalized dashboard insights.
    """

    def __init__(
        self,
        portfolio_risk: PortfolioRiskAnalysis,
        preferences_service: UserPreferencesService,
        hybrid_retrieval: HybridRetrievalInteractor,
    ):
        self._portfolio_risk = portfolio_risk
        self._preferences = preferences_service
        self._hybrid_retrieval = hybrid_retrieval

    async def get_dashboard_insights(
        self, user_id: UUID, portfolio: Optional[UserPortfolio] = None
    ) -> List[AIInsight]:
        """
        Generate AI-powered insights for dashboard.

        Args:
            user_id: User UUID
            portfolio: User portfolio (optional, will fetch if not provided)

        Returns:
            List of AI insights
        """
        insights: List[AIInsight] = []

        # Get user preferences for personalization
        prefs = await self._preferences.get_user_preferences(user_id)

        # Generate risk-based insights
        if portfolio and len(portfolio.protocols) > 0:
            risk_insights = await self._generate_risk_insights(portfolio, prefs)
            insights.extend(risk_insights)

        # Generate opportunity insights
        opportunity_insights = await self._generate_opportunity_insights(
            user_id, prefs
        )
        insights.extend(opportunity_insights)

        # Generate diversification insights
        if portfolio:
            diversification_insights = self._generate_diversification_insights(
                portfolio
            )
            insights.extend(diversification_insights)

        # Sort by severity and recency
        insights.sort(
            key=lambda x: (
                {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[x.severity],
                -x.created_at.timestamp(),
            )
        )

        # Return top 5
        return insights[:5]

    async def _generate_risk_insights(
        self, portfolio: UserPortfolio, prefs
    ) -> List[AIInsight]:
        """Generate risk-based insights."""
        insights = []

        # Get portfolio risk analysis
        risk_summary = await self._portfolio_risk.get_portfolio_risk(portfolio)

        # High risk protocol warning
        for protocol_at_risk in risk_summary.protocols_at_risk:
            if protocol_at_risk.risk_score > 7.0:  # Critical risk
                insights.append(
                    AIInsight(
                        id=f"risk_{protocol_at_risk.protocol_id}",
                        insight_type="risk_warning",
                        title="High Risk Detected",
                        message=f"{protocol_at_risk.protocol_name} has elevated risk "
                        f"({protocol_at_risk.risk_score:.1f}/10). "
                        f"Your exposure: ${protocol_at_risk.exposure_usd:,.0f} "
                        f"({protocol_at_risk.exposure_percentage:.1f}%). "
                        f"Consider reviewing alternatives.",
                        action_label="Review Risk",
                        action_url=f"/protocols/{protocol_at_risk.protocol_id}/risk",
                        severity="HIGH",
                        created_at=datetime.utcnow(),
                    )
                )

        # Concentration risk warning
        if risk_summary.concentration_risk > 0.7:
            insights.append(
                AIInsight(
                    id="concentration_risk",
                    insight_type="risk_warning",
                    title="High Concentration Risk",
                    message=f"Your portfolio is concentrated in few protocols "
                    f"(Herfindahl: {risk_summary.concentration_risk:.2f}). "
                    f"Consider diversifying to reduce risk.",
                    action_label="View Diversification",
                    action_url="/portfolio/diversify",
                    severity="MEDIUM",
                    created_at=datetime.utcnow(),
                )
            )

        return insights

    async def _generate_opportunity_insights(
        self, user_id: UUID, prefs
    ) -> List[AIInsight]:
        """Generate opportunity-based insights."""
        insights = []

        # Find protocols matching user preferences with better yields
        # This is a simplified example - real implementation would query yields
        risk_tolerance_map = {
            "conservative": "LOW",
            "moderate": "MEDIUM",
            "aggressive": "HIGH",
        }
        max_risk = risk_tolerance_map.get(prefs.risk_tolerance, "MEDIUM")

        # Search for opportunities
        # TODO: Integrate with real yield data
        insights.append(
            AIInsight(
                id="staking_opportunity",
                insight_type="opportunity",
                title="Staking Opportunity",
                message=f"Based on your {prefs.risk_tolerance} risk profile, "
                f"Lido Finance offers 4.2% APY on ETH staking (Risk: 2.3/10). "
                f"Matches your preferences.",
                action_label="Explore Lido",
                action_url="/protocols/lido-finance",
                severity="LOW",
                created_at=datetime.utcnow(),
            )
        )

        return insights

    def _generate_diversification_insights(
        self, portfolio: UserPortfolio
    ) -> List[AIInsight]:
        """Generate diversification insights."""
        insights = []

        # Check chain diversity
        chains = {p.chain for p in portfolio.protocols}
        if len(chains) == 1:
            insights.append(
                AIInsight(
                    id="chain_diversity",
                    insight_type="optimization",
                    title="Single Chain Exposure",
                    message=f"All your positions are on {list(chains)[0]}. "
                    f"Consider diversifying across chains to reduce systemic risk.",
                    action_label="Explore Multi-Chain",
                    action_url="/protocols?chains=multiple",
                    severity="LOW",
                    created_at=datetime.utcnow(),
                )
            )

        # Check position type diversity
        position_types = {p.position_type for p in portfolio.protocols}
        if len(position_types) == 1:
            insights.append(
                AIInsight(
                    id="position_diversity",
                    insight_type="optimization",
                    title="Limited Position Types",
                    message=f"All your positions are {list(position_types)[0]}. "
                    f"Consider exploring other DeFi strategies (LP, staking, etc.).",
                    action_label="Explore Strategies",
                    action_url="/defi/strategies",
                    severity="LOW",
                    created_at=datetime.utcnow(),
                )
            )

        return insights

    async def get_portfolio_summary(
        self, user_id: UUID, portfolio: UserPortfolio
    ) -> dict:
        """
        Get comprehensive portfolio summary for dashboard.

        Returns:
            Portfolio summary with risk, value, and breakdowns
        """
        # Calculate total value
        total_value = portfolio.total_value_usd

        # Get risk analysis
        risk_summary = await self._portfolio_risk.get_portfolio_risk(portfolio)

        # Calculate breakdowns
        chain_breakdown = portfolio.get_allocation_by_chain()
        position_breakdown = portfolio.get_allocation_by_position_type()

        # Value changes (TODO: Integrate with historical data)
        value_change_24h = 0  # Placeholder
        value_change_pct = 0  # Placeholder

        return {
            "total_value_usd": total_value,
            "value_change_24h": value_change_24h,
            "value_change_pct": value_change_pct,
            "overall_risk_score": risk_summary.overall_risk_score,
            "risk_level": self._get_risk_level(risk_summary.overall_risk_score),
            "chain_breakdown": chain_breakdown,
            "position_breakdown": position_breakdown,
            "protocols_count": len(portfolio.protocols),
            "chains_count": len(chain_breakdown),
            "last_updated": datetime.utcnow(),
        }

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to level."""
        if risk_score <= 3.0:
            return "LOW"
        elif risk_score <= 5.0:
            return "MEDIUM"
        elif risk_score <= 7.0:
            return "HIGH"
        else:
            return "CRITICAL"
