"""
Enterprise Retry Engine with Circuit Breaker and Telemetry.

Provides intelligent retry logic with exponential backoff, circuit breaker
integration, telemetry tracking, and manual service override support.
"""

import logging
import asyncio
import time
from typing import Callable, Any, Optional, Dict
from datetime import datetime

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

from app.domain.value_objects.retry_config import RetryConfig

logger = logging.getLogger(__name__)


class AllRetriesExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class ServiceDisabledError(Exception):
    """Raised when service is manually disabled."""
    pass


class EnterpriseRetryEngine:
    """
    Enterprise retry engine with circuit breaker and telemetry.
    
    Features:
    - Exponential backoff with jitter
    - Circuit breaker integration
    - Comprehensive telemetry
    - Manual service override
    - Service health tracking
    
    Usage:
        engine = EnterpriseRetryEngine(
            config=RetryConfig(),
            circuit_breaker=circuit_breaker,
            telemetry=telemetry_collector,
            service_registry=service_registry,
        )
        
        result = await engine.execute_with_retry(
            service_name="defillama_mcp",
            func=make_api_call,
            context={"user_id": user_id},
        )
    """
    
    def __init__(
        self,
        config: RetryConfig,
        circuit_breaker: Optional[Any] = None,
        telemetry: Optional[Any] = None,
        service_registry: Optional[Any] = None,
    ):
        """
        Initialize retry engine.
        
        Args:
            config: Retry configuration
            circuit_breaker: Circuit breaker manager (optional)
            telemetry: Telemetry collector (optional)
            service_registry: Service registry for manual override (optional)
        """
        self.config = config
        self.circuit_breaker = circuit_breaker
        self.telemetry = telemetry
        self.service_registry = service_registry
    
    def calculate_backoff(self, attempt: int) -> float:
        """
        Calculate backoff delay for attempt.
        
        Args:
            attempt: Attempt number (0-indexed)
        
        Returns:
            Delay in seconds
        """
        delay_ms = self.config.calculate_delay(attempt)
        return delay_ms / 1000.0
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if error should trigger retry.
        
        Args:
            error: Exception raised
            attempt: Current attempt number
        
        Returns:
            True if should retry
        """
        # Check max retries
        if attempt >= self.config.max_retries:
            return False
        
        # Check error type
        error_type = self.classify_error(error)
        
        # Non-retryable errors
        non_retryable = [
            "authentication_error",
            "invalid_request",
            "content_policy",
        ]
        
        if error_type in non_retryable:
            logger.info(f"Non-retryable error: {error_type}")
            return False
        
        # Retryable errors
        retryable = [
            "rate_limit",
            "timeout",
            "service_unavailable",
            "model_overloaded",
            "internal_error",
        ]
        
        if error_type in retryable:
            logger.info(f"Retryable error: {error_type}")
            return True
        
        # Default: retry for safety
        logger.warning(f"Unknown error type, will retry: {type(error).__name__}")
        return True
    
    def classify_error(self, error: Exception) -> str:
        """
        Classify error type for tracking.
        
        Args:
            error: Exception
        
        Returns:
            Error type string
        """
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "429" in error_str:
            return "rate_limit"
        elif "timeout" in error_str:
            return "timeout"
        elif "503" in error_str or "unavailable" in error_str:
            return "service_unavailable"
        elif "overloaded" in error_str:
            return "model_overloaded"
        elif "authentication" in error_str or "401" in error_str or "403" in error_str:
            return "authentication_error"
        elif "invalid" in error_str or "400" in error_str:
            return "invalid_request"
        elif "content" in error_str and "policy" in error_str:
            return "content_policy"
        else:
            return "internal_error"
    
    async def execute_with_retry(
        self,
        service_name: str,
        func: Callable,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute function with retry, circuit breaker, and telemetry.
        
        Flow:
        1. Check manual override (service disabled?)
        2. Check circuit breaker (too many failures?)
        3. Execute with retry
        4. Record telemetry
        5. Update circuit breaker state
        
        Args:
            service_name: Name of service (e.g., "defillama_mcp")
            func: Async function to execute
            context: Additional context for telemetry
        
        Returns:
            Function result
        
        Raises:
            ServiceDisabledError: If service is manually disabled
            CircuitBreakerOpenError: If circuit breaker is open
            AllRetriesExhaustedError: If all retries exhausted
        """
        context = context or {}
        
        # 1. Manual override check
        if self.service_registry and not self.service_registry.is_enabled(service_name):
            error_msg = f"Service '{service_name}' is manually disabled"
            logger.warning(error_msg)
            raise ServiceDisabledError(error_msg)
        
        # 2. Circuit breaker check
        if self.circuit_breaker and self.circuit_breaker.is_open(service_name):
            error_msg = f"Circuit breaker open for '{service_name}'"
            logger.warning(error_msg)
            raise CircuitBreakerOpenError(error_msg)
        
        # 3. Execute with retry + telemetry
        start_time = time.time()
        attempt = 0
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Record attempt start
                if self.telemetry:
                    await self.telemetry.record_attempt_start(
                        service_name, attempt, context
                    )
                
                # Execute
                result = await func()
                
                # Record success
                latency_ms = int((time.time() - start_time) * 1000)
                if self.telemetry:
                    await self.telemetry.record_success(
                        service_name, attempt, latency_ms, context
                    )
                
                # Reset circuit breaker on success
                if self.circuit_breaker:
                    self.circuit_breaker.record_success(service_name)
                
                logger.info(
                    f"Success on attempt {attempt + 1} for {service_name} "
                    f"(latency: {latency_ms}ms)"
                )
                
                return result
                
            except Exception as e:
                last_error = e
                error_type = self.classify_error(e)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed for {service_name}: "
                    f"{error_type} - {str(e)}"
                )
                
                # Record failure
                if self.telemetry:
                    await self.telemetry.record_failure(
                        service_name, attempt, error_type, str(e), context
                    )
                
                # Update circuit breaker
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure(service_name)
                
                # Check if should retry
                if not self.should_retry(e, attempt):
                    logger.error(
                        f"Non-retryable error for {service_name}: {error_type}"
                    )
                    break
                
                # Apply backoff if not last attempt
                if attempt < self.config.max_retries - 1:
                    backoff = self.calculate_backoff(attempt)
                    logger.debug(f"Applying backoff: {backoff:.2f}s")
                    await asyncio.sleep(backoff)
        
        # All retries exhausted
        error_message = (
            f"All {attempt + 1} retries failed for {service_name}. "
            f"Last error: {last_error}"
        )
        
        logger.error(error_message)
        raise AllRetriesExhaustedError(error_message)
    
    def create_retry_decorator(
        self,
        service_name: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a tenacity retry decorator for a specific service.
        
        This provides a decorator-based approach for simpler use cases.
        
        Args:
            service_name: Name of service
            context: Additional context
        
        Returns:
            Tenacity retry decorator
        
        Usage:
            @engine.create_retry_decorator("my_service")
            async def my_function():
                return await api_call()
        """
        return retry(
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_exponential(
                multiplier=1,
                min=self.config.initial_backoff_seconds,
                max=self.config.max_backoff_seconds,
            ),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
