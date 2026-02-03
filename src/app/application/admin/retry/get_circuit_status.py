"""
Get Circuit Status Interactor.

Retrieves circuit breaker status for all services.
"""

from typing import List, Dict, Any

from app.domain.services.retry import CircuitBreakerManager


class GetCircuitStatus:
    """Interactor to get circuit breaker status for all services."""

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
    ):
        """
        Initialize interactor.

        Args:
            circuit_breaker: Circuit breaker manager
        """
        self.circuit_breaker = circuit_breaker

    async def execute(self) -> List[Dict[str, Any]]:
        """
        Execute interactor.

        Returns:
            List of circuit breaker status dictionaries
        """
        statuses = []

        for service_name in self.KNOWN_SERVICES:
            status = self.circuit_breaker.get_status(service_name)
            statuses.append(status)

        return statuses
