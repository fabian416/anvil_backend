"""
Get Service List Interactor.

Retrieves comprehensive status for all services in the retry system.
"""

from typing import List, Dict, Any

from app.domain.services.retry import CircuitBreakerManager, ServiceRegistry


class GetServiceList:
    """Interactor to get list of all services with status."""

    # Known services in the system
    KNOWN_SERVICES = [
        "defillama_mcp",
        "oneinch_mcp",
        "thegraph_mcp",
        "coingecko_mcp",
        "aave_mcp",
        "portfolio_mcp",
    ]

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

    async def execute(self) -> List[Dict[str, Any]]:
        """
        Execute interactor.

        Returns:
            List of service status dictionaries
        """
        services = []

        for service_name in self.KNOWN_SERVICES:
            # Get circuit breaker status
            circuit_status = self.circuit_breaker.get_status(service_name)

            # Get service override status
            service_status = self.service_registry.get_service_status(service_name)

            services.append({
                "service_name": service_name,
                "enabled": service_status.get("enabled", True),
                "circuit_state": circuit_status["state"],
                "failure_count": circuit_status["failure_count"],
                "success_count": circuit_status["success_count"],
                "last_error": None,  # Could be extended
                "last_error_at": None,
                "override_reason": service_status.get("reason"),
                "override_expires_at": service_status.get("expires_at"),
            })

        return services
