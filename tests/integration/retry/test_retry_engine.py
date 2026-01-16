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
    @pytest.mark.llm_validation
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_successful_execution_no_retry",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_retry_on_failure_then_success",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_all_retries_exhausted",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_non_retryable_error_no_retry",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_circuit_breaker_integration",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_circuit_breaker_success_recorded",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_circuit_breaker_failure_recorded",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_service_registry_disabled_service",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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
        assert success_call[0][2] >= 0  # latency_ms (may be 0 for fast mocks)
        assert success_call[0][3] == {"user_id": "123"}  # context

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_telemetry_records_success",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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
        assert failure_call[0][2] == "service_unavailable"  # error_type (classified from message)
        assert "Service unavailable" in failure_call[0][3]  # error_message

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_telemetry_records_failure",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_exponential_backoff_applied",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_error_classification",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_full_integration_success_after_failures(self):
        """Test full integration with all components."""
        # Arrange
        config = RetryConfig(max_retries=3, initial_backoff_seconds=0.01, max_backoff_seconds=0.1)
        
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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_full_integration_success_after_failures",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        mock_telemetry.record_success.assert_called_once()