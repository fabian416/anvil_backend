"""
Get distillation metrics interactor.
"""
from datetime import datetime, timedelta, UTC
from typing import List, Optional
from dataclasses import dataclass

from app.domain.ports.distillation_telemetry_repository import DistillationTelemetryRepository


@dataclass
class DistillationMetric:
    """Distillation metric data."""
    date: datetime
    provider: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_latency_ms: float
    p95_latency_ms: Optional[float]
    avg_confidence: float
    total_tokens: int
    total_cost_usd: float
    fallback_used_count: int


class GetDistillationMetrics:
    """
    Get distillation metrics interactor.
    
    Retrieves aggregated metrics from telemetry data.
    """
    
    def __init__(self, repository: DistillationTelemetryRepository):
        """Initialize interactor."""
        self._repository = repository
    
    async def execute(
        self,
        days: int = 7,
        provider: Optional[str] = None,
    ) -> List[DistillationMetric]:
        """
        Get distillation metrics.
        
        Args:
            days: Number of days to retrieve (1-90)
            provider: Filter by provider name (optional)
        
        Returns:
            List of daily metrics
        """
        # Calculate date range
        end_date = datetime.now(UTC).date()
        start_date = end_date - timedelta(days=days)
        
        # Get metrics from repository
        metrics = await self._repository.get_daily_metrics(
            start_date=start_date,
            end_date=end_date,
            provider=provider,
        )
        
        # Convert to response format
        return [
            DistillationMetric(
                date=m.date,
                provider=m.provider,
                total_requests=m.total_requests,
                successful_requests=m.successful_requests,
                failed_requests=m.total_requests - m.successful_requests,
                success_rate=m.successful_requests / m.total_requests if m.total_requests > 0 else 0.0,
                avg_latency_ms=m.avg_latency_ms,
                p95_latency_ms=None,  # TODO: Calculate from raw data if needed
                avg_confidence=m.avg_confidence,
                total_tokens=m.total_tokens,
                total_cost_usd=m.total_cost_usd,
                fallback_used_count=m.fallback_used_count,
            )
            for m in metrics
        ]
