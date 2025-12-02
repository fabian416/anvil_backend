"""SQLAlchemy repository for distillation telemetry."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ports.distillation_repository import DistillationTelemetryRepository
from app.domain.value_objects.distillation import DistillationTelemetry
from app.infrastructure.persistence_sqla.mappings.distillation import (
    distillation_requests,
)


class DistillationTelemetryRepositorySqla(DistillationTelemetryRepository):
    """SQLAlchemy implementation of telemetry repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_request(self, telemetry: DistillationTelemetry) -> None:
        """Log distillation request."""
        query = insert(distillation_requests).values(
            request_id=telemetry.request_id,
            user_id=telemetry.user_id,
            original_query=telemetry.original_query,
            normalized_query=telemetry.normalized_query,
            intent=telemetry.intent.value,
            intent_confidence=telemetry.intent_confidence,
            complexity=telemetry.complexity.value,
            entities=telemetry.entities.__dict__ if hasattr(telemetry.entities, "__dict__") else telemetry.entities,
            route_type=telemetry.route_type.value,
            routing_reason=telemetry.routing_reason,
            suggested_model_tier=telemetry.suggested_model_tier,
            suggested_agent=telemetry.suggested_agent,
            cache_key=telemetry.cache_key,
            cache_hit=telemetry.cache_hit,
            cache_level=telemetry.cache_level.value,
            classification_latency_ms=telemetry.classification_latency_ms,
            total_latency_ms=telemetry.total_latency_ms,
            was_processed=telemetry.was_processed,
            llm_request_id=telemetry.llm_request_id,
            created_at=telemetry.created_at,
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def update_llm_info(
        self,
        request_id: str,
        llm_request_id: Optional[UUID] = None,
        llm_response_latency_ms: Optional[int] = None,
        llm_cost_usd: Optional[float] = None,
    ) -> None:
        """Update LLM processing info for a request."""
        from sqlalchemy import update
        from decimal import Decimal
        
        values = {}
        if llm_request_id:
            values["llm_request_id"] = llm_request_id
        if llm_response_latency_ms:
            values["llm_response_latency_ms"] = llm_response_latency_ms
            values["total_latency_ms"] = distillation_requests.c.classification_latency_ms + llm_response_latency_ms
        if llm_cost_usd is not None:
            values["llm_cost_usd"] = Decimal(str(llm_cost_usd))
        
        if not values:
            return
        
        query = (
            update(distillation_requests)
            .where(distillation_requests.c.request_id == request_id)
            .values(**values)
        )
        
        await self.session.execute(query)
        await self.session.commit()
