"""
Get provider status interactor.
"""
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from app.application.distillation.request_distillator import RequestDistillator


@dataclass
class ProviderStatus:
    """Provider status data."""
    provider: str
    healthy: bool
    latency_ms: Optional[float]
    error_rate: Optional[float]
    last_check: Optional[datetime]


class GetProviderStatus:
    """
    Get provider status interactor.
    
    Checks health of distillation providers.
    """
    
    def __init__(self, distillator: RequestDistillator):
        """Initialize interactor."""
        self._distillator = distillator
    
    async def execute(self) -> List[ProviderStatus]:
        """
        Get provider status.
        
        Returns:
            List of provider statuses
        """
        # Check health of both providers
        health = await self._distillator.check_health()
        
        # Extract provider statuses
        statuses = []
        
        if "primary_healthy" in health:
            statuses.append(
                ProviderStatus(
                    provider=self._distillator._primary_provider.provider_name,
                    healthy=health["primary_healthy"],
                    latency_ms=health.get("primary_latency_ms"),
                    error_rate=None,  # TODO: Calculate from recent telemetry
                    last_check=datetime.utcnow(),
                )
            )
        
        if "fallback_healthy" in health:
            statuses.append(
                ProviderStatus(
                    provider=self._distillator._fallback_provider.provider_name,
                    healthy=health["fallback_healthy"],
                    latency_ms=health.get("fallback_latency_ms"),
                    error_rate=None,  # TODO: Calculate from recent telemetry
                    last_check=datetime.utcnow(),
                )
            )
        
        return statuses
