"""Repository ports for distillation system."""
from abc import abstractmethod
from datetime import datetime
from typing import List, Optional, Protocol
from uuid import UUID

from app.domain.value_objects.distillation import (
    CachedResponse,
    DistillationConfig,
    DistillationTelemetry,
    Intent,
    StaticResponse,
    TelemetryMetrics,
)


class DistillationConfigRepository(Protocol):
    """Port for distillation configuration storage."""
    
    @abstractmethod
    async def get_config(self) -> DistillationConfig:
        """Get current distillation configuration."""
        ...
    
    @abstractmethod
    async def update_config(
        self,
        config_key: str,
        config_value: dict,
        modified_by: Optional[UUID] = None,
    ) -> None:
        """Update specific configuration."""
        ...


class StaticResponseRepository(Protocol):
    """Port for static response storage."""
    
    @abstractmethod
    async def get_response(
        self,
        intent: Intent,
        variant: str = "default",
    ) -> Optional[StaticResponse]:
        """Get static response for intent and variant."""
        ...
    
    @abstractmethod
    async def list_responses(
        self,
        intent: Optional[Intent] = None,
        is_active: bool = True,
    ) -> List[StaticResponse]:
        """List static responses with optional filtering."""
        ...
    
    @abstractmethod
    async def create_response(self, response: StaticResponse) -> StaticResponse:
        """Create new static response."""
        ...
    
    @abstractmethod
    async def update_response(
        self,
        response_id: UUID,
        **updates,
    ) -> StaticResponse:
        """Update existing static response."""
        ...
    
    @abstractmethod
    async def delete_response(self, response_id: UUID) -> None:
        """Delete static response."""
        ...


class CacheRepository(Protocol):
    """Port for distillation cache storage."""
    
    @abstractmethod
    async def get_exact(self, cache_key: str) -> Optional[CachedResponse]:
        """Get exact cache match by key."""
        ...
    
    @abstractmethod
    async def get_semantic(
        self,
        query_embedding: List[float],
        threshold: float = 0.95,
    ) -> Optional[CachedResponse]:
        """Get semantic cache match by embedding similarity."""
        ...
    
    @abstractmethod
    async def set_exact(
        self,
        cache_key: str,
        normalized_query: str,
        intent: Intent,
        response_content: str,
        ttl_seconds: int,
        **metadata,
    ) -> None:
        """Set exact cache entry."""
        ...
    
    @abstractmethod
    async def set_semantic(
        self,
        query_embedding: List[float],
        original_query: str,
        intent: Intent,
        response_content: str,
        ttl_seconds: int,
        **metadata,
    ) -> None:
        """Set semantic cache entry."""
        ...
    
    @abstractmethod
    async def invalidate(
        self,
        cache_type: str,  # "exact", "semantic", "all"
        filters: Optional[dict] = None,
    ) -> int:
        """Invalidate cache entries. Returns count of invalidated entries."""
        ...
    
    @abstractmethod
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        ...


class DistillationTelemetryRepository(Protocol):
    """Port for distillation telemetry storage."""
    
    @abstractmethod
    async def log_request(self, telemetry: DistillationTelemetry) -> None:
        """Log distillation request."""
        ...
    
    @abstractmethod
    async def get_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> TelemetryMetrics:
        """Get aggregated metrics for time period."""
        ...
    
    @abstractmethod
    async def get_hourly_metrics(
        self,
        hours: int = 24,
    ) -> List[TelemetryMetrics]:
        """Get pre-aggregated hourly metrics."""
        ...
    
    @abstractmethod
    async def get_intent_distribution(
        self,
        hours: int = 24,
    ) -> dict:
        """Get intent distribution for time period."""
        ...
