"""
Integration tests for EnterpriseRetryEngine.

Tests retry logic, circuit breaker integration, telemetry tracking,
and service registry integration.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.domain.services.retry.retry_engine import (
    EnterpriseRetryEngine,
    AllRetriesExhaustedError,
    CircuitBreakerOpenError,
    ServiceDisabledError,
)
from app.domain.value_objects.retry_config import RetryConfig


class TestEnterpriseRetryEngine:
    """Test EnterpriseRetryEngine."""
    
    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self):
        """Test successful execution without retry."""
        # Arrange
        config = RetryConfig.for_testing()
        engine = EnterpriseRetryEngine(config=config)
        
        mock_func = AsyncMock(return_value="success")
        
        # Act
        result = await engine.execute_with_retry(
            service_name="test_service",
            func=mock_func,
        )
        
        # Assert
        assert result == "success"
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_failure_then_success(self):
        """Test retry logic when first attempt fails."""
        # Arrange
        config = RetryConfig.for_testing()
        engine = EnterpriseRetryEngine(config=config)
        
        mock_func = AsyncMock(
            side_effect=[
                Exception("Temporary failure"),
                "success",
            ]
        )
        
        # Act
        result = await engine.execute_with_retry(
            service_name="test_service",
            func=mock_func,
        )
        
        # Assert
        assert result == "success"
        assert mock_func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self):
        """Test all retries exhausted scenario."""
        # Arrange
        config = RetryConfig.for_testing()
        engine = EnterpriseRetryEngine(config=config)
        
        mock_func = AsyncMock(side_effect=Exception("Persistent failure"))
        
        # Act & Assert
        with pytest.raises(AllRetriesExhaustedError) as exc_info:
            await engine.execute_with_retry(
                service_name="test_service",
                func=mock_func,
            )
        
        assert "All 2 retries failed" in str(exc_info.value)
        assert mock_func.call_count == 2  # max_retries for testing config
    
    @pytest.mark.asyncio
    async def test_non_retryable_error_no_retry(self):
        """Test that non-retryable errors don't retry."""
        # Arrange
        config = RetryConfig.for_testing()
        engine = EnterpriseRetryEngine(config=config)
        
        mock_func = AsyncMock(side_effect=Exception("401 authentication failed"))
        
        # Act & Assert
        with pytest.raises(AllRetriesExhaustedError):
            await engine.execute_with_retry(
                service_name="test_service",
                func=mock_func,
            )
        
        # Should only try once (no retry for auth errors)
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test circuit breaker integration blocks requests."""
        # Arrange
        config = RetryConfig.for_testing()
        
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.is_open.return_value = True
        
        engine = EnterpriseRetryEngine(
            config=config,
            circuit_breaker=mock_circuit_breaker,
        )
        
        mock_func = AsyncMock(return_value="success")
        
        # Act & Assert
        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await engine.execute_with_retry(
                service_name="test_service",
                func=mock_func,
            )
        
        assert "Circuit breaker open" in str(exc_info.value)
        mock_circuit_breaker.is_open.assert_called_once_with("test_service")
        mock_func.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_success_recorded(self):
        """Test circuit breaker records success."""
        # Arrange
        config = RetryConfig.for_testing()
        
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.is_open.return_value = False
        
        engine = EnterpriseRetryEngine(
            config=config,
            circuit_breaker=mock_circuit_breaker,
        )
        
        mock_func = AsyncMock(return_value="success")
        
        # Act
        result = await engine.execute_with_retry(
            service_name="test_service",
            func=mock_func,
        )
        
        # Assert
        assert result == "success"
        mock_circuit_breaker.record_success.assert_called_once_with("test_service")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_recorded(self):
        """Test circuit breaker records failure."""
        # Arrange
        config = RetryConfig.for_testing()
        
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.is_open.return_value = False
        
        engine = EnterpriseRetryEngine(
            config=config,
            circuit_breaker=mock_circuit_breaker,
        )
        
        mock_func = AsyncMock(side_effect=Exception("Failure"))
        
        # Act & Assert
        with pytest.raises(AllRetriesExhaustedError):
            await engine.execute_with_retry(
                service_name="test_service",
                func=mock_func,
            )
        
        # Should record failure for each attempt
        assert mock_circuit_breaker.record_failure.call_count == 2
    
    @pytest.mark.asyncio
    async def test_service_registry_disabled_service(self):
        """Test service registry blocks disabled services."""
        # Arrange
        config = RetryConfig.for_testing()
        
        mock_service_registry = MagicMock()
        mock_service_registry.is_enabled.return_value = False
        
        engine = EnterpriseRetryEngine(
            config=config,
            service_registry=mock_service_registry,
        )
        
        mock_func = AsyncMock(return_value="success")
        
        # Act & Assert
        with pytest.raises(ServiceDisabledError) as exc_info:
            await engine.execute_with_retry(
                service_name="test_service",
                func=mock_func,
            )
        
        assert "manually disabled" in str(exc_info.value)
        mock_service_registry.is_enabled.assert_called_once_with("test_service")
        mock_func.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_telemetry_records_success(self):
        """Test telemetry records successful execution."""
        # Arrange
        config = RetryConfig.for_testing()
        
        mock_telemetry = AsyncMock()
        
        engine = EnterpriseRetryEngine(
            config=config,
            telemetry=mock_telemetry,
        )
        
        mock_func = AsyncMock(return_value="success")
        
        # Act
        await engine.execute_with_retry(
            service_name="test_service",
            func=mock_func,
            context={"user_id": "123"},
        )
        
        # Assert
        mock_telemetry.record_attempt_start.assert_called_once()
        mock_telemetry.record_success.assert_called_once()
        
        # Check telemetry call arguments
        success_call = mock_telemetry.record_success.call_args
        assert success_call[0][0] == "test_service"  # service_name
        assert success_call[0][1] == 0  # attempt
        assert success_call[0][2] > 0  # latency_ms
        assert success_call[0][3] == {"user_id": "123"}  # context
    
    @pytest.mark.asyncio
    async def test_telemetry_records_failure(self):
        """Test telemetry records failures."""
        # Arrange
        config = RetryConfig.for_testing()
        
        mock_telemetry = AsyncMock()
        
        engine = EnterpriseRetryEngine(
            config=config,
            telemetry=mock_telemetry,
        )
        
        mock_func = AsyncMock(side_effect=Exception("Service unavailable"))
        
        # Act & Assert
        with pytest.raises(AllRetriesExhaustedError):
            await engine.execute_with_retry(
                service_name="test_service",
                func=mock_func,
            )
        
        # Should record attempt start and failure for each attempt
        assert mock_telemetry.record_attempt_start.call_count == 2
        assert mock_telemetry.record_failure.call_count == 2
        
        # Check failure call arguments
        failure_call = mock_telemetry.record_failure.call_args
        assert failure_call[0][0] == "test_service"  # service_name
        assert failure_call[0][2] == "internal_error"  # error_type
        assert "Service unavailable" in failure_call[0][3]  # error_message
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_applied(self):
        """Test exponential backoff is applied between retries."""
        # Arrange
        config = RetryConfig.for_testing()
        engine = EnterpriseRetryEngine(config=config)
        
        call_times = []
        
        async def failing_func():
            call_times.append(asyncio.get_event_loop().time())
            raise Exception("Temporary failure")
        
        # Act
        with pytest.raises(AllRetriesExhaustedError):
            await engine.execute_with_retry(
                service_name="test_service",
                func=failing_func,
            )
        
        # Assert - check that there was a delay between calls
        assert len(call_times) == 2
        delay = call_times[1] - call_times[0]
        assert delay >= 0.1  # At least initial backoff (100ms for testing)
    
    @pytest.mark.asyncio
    async def test_error_classification(self):
        """Test error type classification."""
        # Arrange
        engine = EnterpriseRetryEngine(config=RetryConfig.for_testing())
        
        # Act & Assert
        assert engine.classify_error(Exception("Rate limit exceeded")) == "rate_limit"
        assert engine.classify_error(Exception("429 Too Many Requests")) == "rate_limit"
        assert engine.classify_error(Exception("Request timeout")) == "timeout"
        assert engine.classify_error(Exception("503 Service Unavailable")) == "service_unavailable"
        assert engine.classify_error(Exception("Model overloaded")) == "model_overloaded"
        assert engine.classify_error(Exception("401 Unauthorized")) == "authentication_error"
        assert engine.classify_error(Exception("400 Bad Request")) == "invalid_request"
        assert engine.classify_error(Exception("Content policy violation")) == "content_policy"
        assert engine.classify_error(Exception("Unknown error")) == "internal_error"
    
    @pytest.mark.asyncio
    async def test_full_integration_success_after_failures(self):
        """Test full integration with all components."""
        # Arrange
        config = RetryConfig.for_testing()
        
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.is_open.return_value = False
        
        mock_telemetry = AsyncMock()
        
        mock_service_registry = MagicMock()
        mock_service_registry.is_enabled.return_value = True
        
        engine = EnterpriseRetryEngine(
            config=config,
            circuit_breaker=mock_circuit_breaker,
            telemetry=mock_telemetry,
            service_registry=mock_service_registry,
        )
        
        # Fail twice, then succeed
        mock_func = AsyncMock(
            side_effect=[
                Exception("Temporary failure 1"),
                Exception("Temporary failure 2"),
                "success",
            ]
        )
        
        # Act
        result = await engine.execute_with_retry(
            service_name="test_service",
            func=mock_func,
            context={"user_id": "123"},
        )
        
        # Assert
        assert result == "success"
        
        # Check all components were called correctly
        mock_service_registry.is_enabled.assert_called_once()
        mock_circuit_breaker.is_open.assert_called_once()
        assert mock_circuit_breaker.record_failure.call_count == 2
        mock_circuit_breaker.record_success.assert_called_once()
        assert mock_telemetry.record_attempt_start.call_count == 3
        assert mock_telemetry.record_failure.call_count == 2
        mock_telemetry.record_success.assert_called_once()
