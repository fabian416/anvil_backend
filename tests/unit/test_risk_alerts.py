"""
Unit tests for Risk Alert Service.

Tests alert creation, subscription management,
and alert monitoring.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock

from app.application.alerts.risk_alert_service import RiskAlertService
from app.domain.entities.user_portfolio import UserPortfolio, ProtocolExposure


@pytest.fixture
def mock_portfolio_service():
    """Mock portfolio risk service."""
    service = AsyncMock()
    return service


@pytest.fixture
def alert_service(mock_portfolio_service):
    """Create risk alert service."""
    return RiskAlertService(portfolio_risk=mock_portfolio_service)


@pytest.fixture
def user_id():
    """Sample user ID."""
    return uuid4()


@pytest.fixture
def sample_portfolio(user_id):
    """Sample user portfolio."""
    return UserPortfolio(
        user_id=user_id,
        protocols=[
            ProtocolExposure(
                protocol_id=uuid4(),
                protocol_name="Aave V3",
                chain="ethereum",
                exposure_usd=50000,
                risk_score=2.1,
                risk_level="LOW",
            ),
        ],
        total_value_usd=50000,
        weighted_risk_score=2.1,
    )


class TestRiskAlerts:
    """Test suite for Risk Alert Service."""

    @pytest.mark.asyncio
    async def test_create_alert(self, alert_service, user_id):
        """Test creating a new risk alert."""
        alert = await alert_service.create_alert(
            user_id=user_id,
            alert_type="risk_increase",
            severity="HIGH",
            message="Risk score increased significantly",
            protocol_id=uuid4(),
            old_risk_score=2.0,
            new_risk_score=7.5,
        )
        
        assert alert.user_id == user_id
        assert alert.alert_type == "risk_increase"
        assert alert.severity == "HIGH"
        assert alert.is_read is False

    @pytest.mark.asyncio
    async def test_get_user_alerts(self, alert_service, user_id):
        """Test retrieving user alerts."""
        # Create multiple alerts
        for i in range(3):
            await alert_service.create_alert(
                user_id, "test", "MEDIUM", f"Alert {i}"
            )
        
        alerts = await alert_service.get_user_alerts(user_id)
        assert len(alerts) == 3

    @pytest.mark.asyncio
    async def test_filter_alerts_by_severity(self, alert_service, user_id):
        """Test filtering alerts by severity."""
        # Create alerts with different severities
        await alert_service.create_alert(user_id, "test", "CRITICAL", "Critical")
        await alert_service.create_alert(user_id, "test", "LOW", "Low")
        
        critical_alerts = await alert_service.get_user_alerts(
            user_id, severity="CRITICAL"
        )
        assert len(critical_alerts) == 1
        assert critical_alerts[0].severity == "CRITICAL"

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, alert_service, user_id):
        """Test acknowledging an alert."""
        alert = await alert_service.create_alert(
            user_id, "test", "MEDIUM", "Test alert"
        )
        
        await alert_service.acknowledge_alert(user_id, alert.id)
        
        # Alert should be marked as read
        alerts = await alert_service.get_user_alerts(user_id)
        assert alerts[0].is_read is True

    @pytest.mark.asyncio
    async def test_subscribe_to_alerts(self, alert_service, user_id):
        """Test subscribing to alert types."""
        protocol_id = uuid4()
        
        subscription = await alert_service.subscribe_to_alerts(
            user_id=user_id,
            alert_types=["risk_increase", "anomaly_detected"],
            protocol_id=protocol_id,
            email_enabled=True,
            push_enabled=False,
        )
        
        assert subscription.user_id == user_id
        assert "risk_increase" in subscription.alert_types
        assert subscription.email_enabled is True

    @pytest.mark.asyncio
    async def test_unsubscribe_from_alerts(self, alert_service, user_id):
        """Test unsubscribing from alerts."""
        protocol_id = uuid4()
        
        # Subscribe first
        subscription = await alert_service.subscribe_to_alerts(
            user_id, ["risk_increase"], protocol_id
        )
        
        # Then unsubscribe
        await alert_service.unsubscribe_from_alerts(user_id, subscription.id)
        
        # Subscription should be removed
        subscriptions = await alert_service.get_user_subscriptions(user_id)
        assert len(subscriptions) == 0

    @pytest.mark.asyncio
    async def test_get_unread_alert_count(self, alert_service, user_id):
        """Test getting unread alert count."""
        # Create multiple alerts
        for i in range(5):
            await alert_service.create_alert(user_id, "test", "MEDIUM", f"Alert {i}")
        
        # Acknowledge some
        alerts = await alert_service.get_user_alerts(user_id)
        await alert_service.acknowledge_alert(user_id, alerts[0].id)
        await alert_service.acknowledge_alert(user_id, alerts[1].id)
        
        unread_count = await alert_service.get_unread_count(user_id)
        assert unread_count == 3

    @pytest.mark.asyncio
    async def test_alert_priority_sorting(self, alert_service, user_id):
        """Test that alerts are sorted by severity and timestamp."""
        # Create alerts in different order
        await alert_service.create_alert(user_id, "test", "LOW", "Low")
        await alert_service.create_alert(user_id, "test", "CRITICAL", "Critical")
        await alert_service.create_alert(user_id, "test", "MEDIUM", "Medium")
        
        alerts = await alert_service.get_user_alerts(user_id)
        
        # Should be sorted: CRITICAL, MEDIUM, LOW
        assert alerts[0].severity == "CRITICAL"
        assert alerts[1].severity == "MEDIUM"
        assert alerts[2].severity == "LOW"
