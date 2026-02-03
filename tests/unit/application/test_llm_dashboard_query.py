"""
Unit tests for LLM dashboard query service.

Tests dashboard data aggregation for admin.
"""

import pytest
from datetime import datetime
from uuid import uuid4


@pytest.mark.unit
class TestDashboardDataModel:
    """Tests for DashboardData dataclass."""

    def test_dashboard_data_exists(self):
        """Test DashboardData dataclass exists."""
        from app.application.llm.queries.get_dashboard_data import DashboardData

        assert DashboardData is not None

    def test_dashboard_data_structure(self):
        """Test DashboardData has correct structure."""
        from app.application.llm.queries.get_dashboard_data import DashboardData

        data = DashboardData(
            system_health={"status": "healthy"},
            providers=[],
            top_models=[],
            metrics_summary={},
            cost_summary={},
            recent_requests=[],
            active_alerts=[],
        )

        assert data.system_health == {"status": "healthy"}
        assert data.providers == []
        assert data.top_models == []
        assert data.metrics_summary == {}
        assert data.cost_summary == {}
        assert data.recent_requests == []
        assert data.active_alerts == []


@pytest.mark.unit
class TestGetDashboardDataQuery:
    """Tests for GetDashboardData query service."""

    def test_get_dashboard_data_exists(self):
        """Test GetDashboardData query exists."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        assert GetDashboardData is not None

    def test_get_dashboard_data_instantiation(self):
        """Test query can be instantiated."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        query = GetDashboardData()

        assert query is not None

    @pytest.mark.asyncio
    async def test_execute_returns_dashboard_data(self):
        """Test execute returns DashboardData."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        assert result is not None
        assert hasattr(result, "system_health")
        assert hasattr(result, "providers")
        assert hasattr(result, "top_models")
        assert hasattr(result, "metrics_summary")
        assert hasattr(result, "cost_summary")
        assert hasattr(result, "recent_requests")
        assert hasattr(result, "active_alerts")

    @pytest.mark.asyncio
    async def test_execute_with_24h_period(self):
        """Test execute with 24h period."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute(period="24h")

        # Assert
        assert result is not None
        assert result.metrics_summary.get("period") == "24h"

    @pytest.mark.asyncio
    async def test_execute_with_user_filter(self):
        """Test execute with user_id filter."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()
        user_id = uuid4()

        # Act
        result = await query.execute(period="7d", user_id=user_id)

        # Assert
        assert result is not None

    @pytest.mark.asyncio
    async def test_system_health_structure(self):
        """Test system_health has expected structure."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        health = result.system_health
        assert "status" in health
        assert "uptime_percentage" in health
        assert "total_providers" in health
        assert "healthy_providers" in health
        assert "total_models" in health
        assert "available_models" in health
        assert "circuit_breakers_open" in health
        assert "last_updated" in health

    @pytest.mark.asyncio
    async def test_providers_structure(self):
        """Test providers have expected structure."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        assert len(result.providers) > 0
        provider = result.providers[0]
        assert "id" in provider
        assert "name" in provider
        assert "display_name" in provider
        assert "status" in provider
        assert "priority" in provider
        assert "request_count_24h" in provider
        assert "success_rate" in provider
        assert "avg_latency_ms" in provider
        assert "cost_24h_usd" in provider

    @pytest.mark.asyncio
    async def test_top_models_structure(self):
        """Test top_models have expected structure."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        assert len(result.top_models) > 0
        model = result.top_models[0]
        assert "rank" in model
        assert "model_name" in model
        assert "provider" in model
        assert "ranking_score" in model
        assert "success_rate" in model
        assert "avg_latency_ms" in model
        assert "requests_24h" in model

    @pytest.mark.asyncio
    async def test_metrics_summary_structure(self):
        """Test metrics_summary has expected structure."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        metrics = result.metrics_summary
        assert "period" in metrics
        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "success_rate" in metrics
        assert "avg_latency_ms" in metrics
        assert "p50_latency_ms" in metrics
        assert "p95_latency_ms" in metrics
        assert "p99_latency_ms" in metrics
        assert "retry_rate" in metrics
        assert "cache_hit_rate" in metrics
        assert "total_tokens" in metrics

    @pytest.mark.asyncio
    async def test_cost_summary_structure(self):
        """Test cost_summary has expected structure."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        cost = result.cost_summary
        assert "period" in cost
        assert "total_cost_usd" in cost
        assert "daily_average_usd" in cost
        assert "projected_monthly_usd" in cost
        assert "budget_monthly_usd" in cost
        assert "budget_used_percentage" in cost
        assert "cost_by_provider" in cost
        assert "trend" in cost

    @pytest.mark.asyncio
    async def test_recent_requests_structure(self):
        """Test recent_requests have expected structure."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        assert len(result.recent_requests) > 0
        request = result.recent_requests[0]
        assert "request_id" in request
        assert "timestamp" in request
        assert "agent_type" in request
        assert "provider" in request
        assert "model" in request
        assert "status" in request
        assert "latency_ms" in request
        assert "cost_usd" in request

    @pytest.mark.asyncio
    async def test_active_alerts_structure(self):
        """Test active_alerts have expected structure."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        if len(result.active_alerts) > 0:
            alert = result.active_alerts[0]
            assert "id" in alert
            assert "type" in alert
            assert "severity" in alert
            assert "message" in alert
            assert "timestamp" in alert

    @pytest.mark.asyncio
    async def test_different_periods(self):
        """Test execute with different time periods."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act & Assert
        for period in ["1h", "24h", "7d", "30d"]:
            result = await query.execute(period=period)
            assert result is not None
            assert result.metrics_summary.get("period") == period


@pytest.mark.unit
class TestDashboardDataValidation:
    """Tests for dashboard data validation."""

    @pytest.mark.asyncio
    async def test_provider_priority_ordering(self):
        """Test providers are ordered by priority."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        priorities = [p["priority"] for p in result.providers]
        assert priorities == sorted(priorities), (
            "Providers should be ordered by priority"
        )

    @pytest.mark.asyncio
    async def test_top_models_ranking(self):
        """Test top models are ranked correctly."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        ranks = [m["rank"] for m in result.top_models]
        assert ranks == list(range(1, len(ranks) + 1)), (
            "Models should have sequential ranks starting at 1"
        )

    @pytest.mark.asyncio
    async def test_success_rates_valid_range(self):
        """Test success rates are between 0 and 1."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        for provider in result.providers:
            success_rate = provider["success_rate"]
            assert 0 <= success_rate <= 1, (
                f"Success rate {success_rate} out of valid range"
            )

    @pytest.mark.asyncio
    async def test_cost_calculations_valid(self):
        """Test cost calculations are valid."""
        from app.application.llm.queries.get_dashboard_data import GetDashboardData

        # Arrange
        query = GetDashboardData()

        # Act
        result = await query.execute()

        # Assert
        cost = result.cost_summary
        assert cost["total_cost_usd"] >= 0
        assert cost["daily_average_usd"] >= 0
        assert cost["projected_monthly_usd"] >= 0
        assert 0 <= cost["budget_used_percentage"] <= 100
