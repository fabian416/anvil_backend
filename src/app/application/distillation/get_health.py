"""
Get distillation health interactor.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.application.distillation.request_distillator import RequestDistillator
from app.application.distillation.get_provider_status import ProviderStatus


@dataclass
class DistillationHealth:
    """Overall distillation health data."""
    healthy: bool
    primary_provider: ProviderStatus
    fallback_provider: ProviderStatus
    telemetry_enabled: bool


class GetDistillationHealth:
    """
    Get distillation health interactor.
    
    Checks overall health of distillation system.
    """
    
    def __init__(self, distillator: RequestDistillator):
        """Initialize interactor."""
        self._distillator = distillator
    
    async def execute(self) -> DistillationHealth:
        """
        Get distillation health.
        
        Returns:
            Overall system health
        """
        # Check health
        health = await self._distillator.check_health()
        
        # Get provider statuses
        primary_healthy = health.get("primary_healthy", False)
        fallback_healthy = health.get("fallback_healthy", False)
        
        primary_status = ProviderStatus(
            provider=self._distillator._primary_provider.provider_name,
            healthy=primary_healthy,
            latency_ms=health.get("primary_latency_ms"),
            error_rate=None,
            last_check=datetime.utcnow(),
        )
        
        fallback_status = ProviderStatus(
            provider=self._distillator._fallback_provider.provider_name,
            healthy=fallback_healthy,
            latency_ms=health.get("fallback_latency_ms"),
            error_rate=None,
            last_check=datetime.utcnow(),
        )
        
        # System is healthy if at least one provider is healthy
        overall_healthy = primary_healthy or fallback_healthy
        
        # Check if telemetry is enabled
        telemetry_enabled = (
            self._distillator._telemetry_collector is not None
            and self._distillator._settings.telemetry.enabled
        )
        
        return DistillationHealth(
            healthy=overall_healthy,
            primary_provider=primary_status,
            fallback_provider=fallback_status,
            telemetry_enabled=telemetry_enabled,
        )
