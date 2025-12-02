"""
Unit tests for Dashboard Aggregation Service.

Tests AI-powered insight generation, portfolio summaries,
and risk/opportunity/diversification analysis.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.application.dashboard.dashboard_aggregation_service import (
    DashboardAggregationService,
    AIInsight,
)
from app.domain.entities.user_portfolio import UserPortfolio, ProtocolExposure
from app.domain.entities.user_preferences import UserPreferences


@pytest.fixture
def mock_preferences_service():
    """Mock user preferences service."""
    service = AsyncMock()
    service.get_user_preferences.return_value = UserPreferences(
        user_id=uuid4(),
        risk_tolerance="moderate",
        preferred_chains=["ethereum", "arbitrum"],
    )
    return service


@pytest.fixture
def mock_portfolio_service():
    """Mock portfolio risk service."""
    service = AsyncMock()
    return service


@pytest.fixture
def dashboard_service(mock_preferences_service, mock_portfolio_service):
    """Create dashboard aggregation service."""
    return DashboardAggregationService(
        preferences=mock_preferences_service,
        portfolio_risk=mock_portfolio_service,
    )


@pytest.fixture
def sample_portfolio():
    """Sample user portfolio with multiple protocols."""
    return UserPortfolio(
        user_id=uuid4(),
        protocols=[
            ProtocolExposure(
                protocol_id=uuid4(),
                protocol_name="Aave V3",
                chain="ethereum",
                exposure_usd=50000,
                risk_score=2.1,
                risk_level="LOW",
            ),
            ProtocolExposure(
                protocol_id=uuid4(),
                protocol_name="High Risk Protocol",
                chain="ethereum",
                exposure_usd=5000,
                risk_score=8.5,
                risk_level="CRITICAL",
            ),
            ProtocolExposure(
                protocol_id=uuid4(),
                protocol_name="Compound",
                chain="ethereum",
                exposure_usd=30000,
                risk_score=2.5,
                risk_level="LOW",
            ),
        ],
        total_value_usd=85000,
        weighted_risk_score=3.2,
    )


class TestDashboardAggregation:
    """Test suite for Dashboard Aggregation Service."""

    @pytest.mark.asyncio
    async def test_generate_risk_insights(self, dashboard_service, sample_portfolio):
        """Test risk insight generation from portfolio."""
        user_id = uuid4()
        prefs = await dashboard_service._preferences.get_user_preferences(user_id)
        
        insights = await dashboard_service._generate_risk_insights(
            sample_portfolio, prefs
        )
        
        # Should detect critical risk protocol
        assert len(insights) > 0
        critical_insights = [i for i in insights if i.severity == "CRITICAL"]
        assert len(critical_insights) > 0
        
        # Should mention the high-risk protocol
        assert any(
            "High Risk Protocol" in i.message or i.risk_score >= 8.0
            for i in critical_insights
        )

    @pytest.mark.asyncio
    async def test_generate_opportunity_insights(self, dashboard_service):
        """Test opportunity insight generation."""
        user_id = uuid4()
        prefs = await dashboard_service._preferences.get_user_preferences(user_id)
        
        insights = await dashboard_service._generate_opportunity_insights(
            user_id, prefs
        )
        
        # Should generate opportunities based on preferences
        assert isinstance(insights, list)
        # Opportunities should have MEDIUM or LOW severity
        for insight in insights:
            assert insight.severity in ["MEDIUM", "LOW"]

    @pytest.mark.asyncio
    async def test_diversification_insights(self, dashboard_service, sample_portfolio):
        """Test diversification analysis."""
        insights = dashboard_service._generate_diversification_insights(
            sample_portfolio
        )
        
        # Should detect concentration risk (only Ethereum)
        assert len(insights) > 0
        chain_insights = [i for i in insights if "chain" in i.message.lower()]
        assert len(chain_insights) > 0

    @pytest.mark.asyncio
    async def test_insights_prioritization(self, dashboard_service, sample_portfolio):
        """Test that insights are correctly prioritized by severity."""
        user_id = uuid4()
        
        insights = await dashboard_service.get_dashboard_insights(
            user_id, sample_portfolio
        )
        
        # Should return max 5 insights
        assert len(insights) <= 5
        
        # Should be sorted by severity (CRITICAL first)
        if len(insights) >= 2:
            for i in range(len(insights) - 1):
                severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
                curr_priority = severity_order[insights[i].severity]
                next_priority = severity_order[insights[i + 1].severity]
                assert curr_priority <= next_priority

    @pytest.mark.asyncio
    async def test_portfolio_summary(self, dashboard_service, sample_portfolio):
        """Test portfolio summary generation."""
        user_id = uuid4()
        
        summary = await dashboard_service.get_portfolio_summary(
            user_id, sample_portfolio
        )
        
        # Should include key metrics
        assert summary["total_value_usd"] == 85000
        assert summary["protocol_count"] == 3
        assert summary["weighted_risk_score"] == 3.2
        assert "chain_distribution" in summary
        assert "risk_distribution" in summary
        
        # Chain distribution should show Ethereum dominance
        assert summary["chain_distribution"]["ethereum"] == 100.0

    @pytest.mark.asyncio
    async def test_empty_portfolio(self, dashboard_service):
        """Test handling of empty portfolio."""
        user_id = uuid4()
        empty_portfolio = UserPortfolio(
            user_id=user_id,
            protocols=[],
            total_value_usd=0,
            weighted_risk_score=0,
        )
        
        insights = await dashboard_service.get_dashboard_insights(
            user_id, empty_portfolio
        )
        
        # Should still generate opportunity insights
        assert isinstance(insights, list)
        # Should not crash with empty portfolio
        assert len(insights) >= 0

    @pytest.mark.asyncio
    async def test_insight_structure(self, dashboard_service, sample_portfolio):
        """Test that AI insights have correct structure."""
        user_id = uuid4()
        
        insights = await dashboard_service.get_dashboard_insights(
            user_id, sample_portfolio
        )
        
        for insight in insights:
            # Verify all required fields
            assert isinstance(insight, AIInsight)
            assert hasattr(insight, "type")
            assert hasattr(insight, "severity")
            assert hasattr(insight, "message")
            assert hasattr(insight, "action")
            assert hasattr(insight, "created_at")
            
            # Verify field types
            assert insight.type in ["risk", "opportunity", "diversification"]
            assert insight.severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            assert isinstance(insight.message, str)
            assert len(insight.message) > 0

    @pytest.mark.asyncio
    async def test_risk_tolerance_respected(self, dashboard_service, sample_portfolio):
        """Test that insights respect user risk tolerance."""
        user_id = uuid4()
        
        # Mock conservative user
        conservative_prefs = UserPreferences(
            user_id=user_id,
            risk_tolerance="conservative",
        )
        dashboard_service._preferences.get_user_preferences.return_value = (
            conservative_prefs
        )
        
        insights = await dashboard_service._generate_risk_insights(
            sample_portfolio, conservative_prefs
        )
        
        # Conservative users should get warnings about moderate risks
        # Should flag protocols with risk > 2.0
        assert len(insights) > 0
