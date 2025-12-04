"""
Get Service Metrics Interactor.

Retrieves aggregated metrics for a service over time.
"""
from typing import Dict, Any

from app.infrastructure.persistence_sqla.repositories.retry_telemetry_repository import (
    RetryTelemetryRepository,
)


class GetServiceMetrics:
    """Interactor to get service metrics."""
    
    def __init__(
        self,
        repository: RetryTelemetryRepository,
    ):
        """
        Initialize interactor.
        
        Args:
            repository: Retry telemetry repository
        """
        self.repository = repository
    
    async def execute(
        self,
        service_name: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Execute interactor.
        
        Args:
            service_name: Name of the service
            days: Number of days to retrieve
        
        Returns:
            Metrics dictionary with summary
        """
        metrics = await self.repository.get_aggregated_metrics(
            service_name=service_name,
            days=days,
        )
        
        # Calculate summary statistics
        if metrics:
            total_requests = sum(m["total_requests"] for m in metrics)
            total_successful = sum(m["successful_requests"] for m in metrics)
            avg_success_rate = (
                total_successful / total_requests
                if total_requests > 0
                else 0
            )
            avg_latency = (
                sum(m["avg_latency_ms"] for m in metrics) / len(metrics)
                if metrics
                else 0
            )
            total_circuit_opens = sum(m["circuit_breaker_opens"] for m in metrics)
        else:
            total_requests = 0
            avg_success_rate = 0
            avg_latency = 0
            total_circuit_opens = 0
        
        return {
            "service_name": service_name,
            "days": days,
            "metrics": metrics,
            "summary": {
                "total_requests": total_requests,
                "avg_success_rate": avg_success_rate,
                "avg_latency_ms": avg_latency,
                "total_circuit_opens": total_circuit_opens,
            },
        }
