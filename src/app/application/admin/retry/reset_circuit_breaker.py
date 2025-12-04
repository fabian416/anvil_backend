"""
Reset Circuit Breaker Interactor.

Manually resets a circuit breaker to CLOSED state.
"""
from app.domain.services.retry import CircuitBreakerManager


class ResetCircuitBreaker:
    """Interactor to reset a circuit breaker manually."""
    
    def __init__(
        self,
        circuit_breaker: CircuitBreakerManager,
    ):
        """
        Initialize interactor.
        
        Args:
            circuit_breaker: Circuit breaker manager
        """
        self.circuit_breaker = circuit_breaker
    
    async def execute(
        self,
        service_name: str,
        reason: str,
    ) -> None:
        """
        Execute interactor.
        
        Args:
            service_name: Name of the service
            reason: Reason for resetting
        """
        self.circuit_breaker.reset(service_name)
