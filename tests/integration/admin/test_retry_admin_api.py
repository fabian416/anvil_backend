"""
Integration tests for Admin Retry API.

Tests admin endpoints for retry system management.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from app.application.admin.retry.get_service_list import GetServiceList
from app.application.admin.retry.get_service_status import GetServiceStatus
from app.application.admin.retry.disable_service import DisableService
from app.application.admin.retry.enable_service import EnableService
from app.application.admin.retry.get_circuit_status import GetCircuitStatus
from app.application.admin.retry.reset_circuit_breaker import ResetCircuitBreaker
from app.application.admin.retry.get_service_metrics import GetServiceMetrics


class TestAdminRetryAPI:
    """Test suite for admin retry API."""
    
    @pytest.fixture
    def mock_circuit_breaker(self):
        """Mock circuit breaker manager."""
        cb = MagicMock()
        cb.get_status.return_value = {
            "service_name": "defillama_mcp",
            "state": "CLOSED",
            "failure_count": 0,
            "success_count": 10,
            "opened_at": None,
            "config": {
                "failure_threshold": 5,
                "success_threshold": 2,
                "timeout_seconds": 60,
            },
        }
        cb.reset = MagicMock()
        return cb
    
    @pytest.fixture
    def mock_service_registry(self):
        """Mock service registry."""
        sr = MagicMock()
        sr.get_service_status.return_value = {
            "enabled": True,
            "reason": None,
            "expires_at": None,
        }
        sr.disable_service = AsyncMock()
        sr.enable_service = AsyncMock()
        return sr
    
    @pytest.fixture
    def mock_repository(self):
        """Mock telemetry repository."""
        repo = AsyncMock()
        repo.get_aggregated_metrics.return_value = [
            {
                "date": "2025-12-01",
                "total_requests": 100,
                "successful_requests": 98,
                "failed_requests": 2,
                "retry_attempts": 5,
                "avg_latency_ms": 250.0,
                "circuit_breaker_opens": 0,
                "success_rate": 0.98,
            }
        ]
        return repo
    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_service_list(self, mock_circuit_breaker, mock_service_registry):
        """Test getting list of all services."""
        interactor = GetServiceList(mock_circuit_breaker, mock_service_registry)
        
        result = await interactor.execute()
        
        assert len(result) == 6  # 6 known services
        assert result[0]["service_name"] == "defillama_mcp"
        assert result[0]["enabled"] is True
        assert result[0]["circuit_state"] == "CLOSED"

        # Optional LLM semantic validation (environment-gated)
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_service_status(self, mock_circuit_breaker, mock_service_registry):
        """Test getting status for specific service."""
        interactor = GetServiceStatus(mock_circuit_breaker, mock_service_registry)
        
        result = await interactor.execute("defillama_mcp")
        
        assert result["service_name"] == "defillama_mcp"
        assert result["enabled"] is True
        assert result["circuit_state"] == "CLOSED"

        # Optional LLM semantic validation (environment-gated)
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_disable_service(self, mock_service_registry):
        """Test disabling a service."""
        interactor = DisableService(mock_service_registry)
        
        await interactor.execute(
            service_name="defillama_mcp",
            reason="Maintenance",
            duration_minutes=60,
        )
        
        mock_service_registry.disable_service.assert_called_once()
        call_args = mock_service_registry.disable_service.call_args
        assert call_args.kwargs["service_name"] == "defillama_mcp"
        assert call_args.kwargs["reason"] == "Maintenance"
        assert call_args.kwargs["duration_minutes"] == 60

        # Optional LLM semantic validation (environment-gated)
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_enable_service(self, mock_service_registry):
        """Test enabling a service."""
        interactor = EnableService(mock_service_registry)
        
        await interactor.execute(
            service_name="defillama_mcp",
            reason="Maintenance complete",
        )
        
        mock_service_registry.enable_service.assert_called_once()
        call_args = mock_service_registry.enable_service.call_args
        assert call_args.kwargs["service_name"] == "defillama_mcp"
        assert call_args.kwargs["reason"] == "Maintenance complete"

        # Optional LLM semantic validation (environment-gated)
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_circuit_status(self, mock_circuit_breaker):
        """Test getting circuit breaker status for all services."""
        interactor = GetCircuitStatus(mock_circuit_breaker)
        
        result = await interactor.execute()
        
        assert len(result) == 6
        assert result[0]["state"] == "CLOSED"

        # Optional LLM semantic validation (environment-gated)
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_reset_circuit_breaker(self, mock_circuit_breaker):
        """Test resetting a circuit breaker."""
        interactor = ResetCircuitBreaker(mock_circuit_breaker)
        
        await interactor.execute(
            service_name="defillama_mcp",
            reason="Manual reset",
        )
        
        mock_circuit_breaker.reset.assert_called_once_with("defillama_mcp")

        # Optional LLM semantic validation (environment-gated)
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_get_service_metrics(self, mock_repository):
        """Test getting service metrics."""
        interactor = GetServiceMetrics(mock_repository)
        
        result = await interactor.execute("defillama_mcp", days=7)
        
        assert result["service_name"] == "defillama_mcp"
        assert result["days"] == 7
        assert len(result["metrics"]) == 1
        assert result["metrics"][0]["total_requests"] == 100
        assert result["summary"]["total_requests"] == 100
        assert result["summary"]["avg_success_rate"] == 0.98

        # Optional LLM semantic validation (environment-gated)
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_service_metrics_empty_data(self, mock_repository):
        """Test service metrics with no data."""
        mock_repository.get_aggregated_metrics.return_value = []
        interactor = GetServiceMetrics(mock_repository)
        
        result = await interactor.execute("defillama_mcp", days=7)
        
        assert result["service_name"] == "defillama_mcp"
        assert len(result["metrics"]) == 0
        assert result["summary"]["total_requests"] == 0

        # Optional LLM semantic validation (environment-gated)