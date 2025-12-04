"""
Get Service Status Interactor.

Retrieves detailed status for a specific service.
"""
from typing import Dict, Any

from app.domain.services.retry import CircuitBreakerManager, ServiceRegistry


class GetServiceStatus:
    """Interactor to get detailed status for a service."""
    
    def __init__(
        self,
        circuit_breaker: CircuitBreakerManager,
        service_registry: ServiceRegistry,
    ):
        """
        Initialize interactor.
        
        Args:
            circuit_breaker: Circuit breaker manager
            service_registry: Service registry
        """
        self.circuit_breaker = circuit_breaker
        self.service_registry = service_registry
    
    async def execute(self, service_name: str) -> Dict[str, Any]:
        """
        Execute interactor.
        
        Args:
            service_name: Name of the service
        
        Returns:
            Service status dictionary
        """
        # Get circuit breaker status
        circuit_status = self.circuit_breaker.get_status(service_name)
        
        # Get service override status
        service_status = self.service_registry.get_service_status(service_name)
        
        return {
            "service_name": service_name,
            "enabled": service_status.get("enabled", True),
            "circuit_state": circuit_status["state"],
            "failure_count": circuit_status["failure_count"],
            "success_count": circuit_status["success_count"],
            "last_error": None,
            "last_error_at": None,
            "override_reason": service_status.get("reason"),
            "override_expires_at": service_status.get("expires_at"),
        }
