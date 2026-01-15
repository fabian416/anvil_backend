"""SQLAlchemy repository for distillation static responses."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ports.distillation_repository import StaticResponseRepository
from app.domain.value_objects.distillation import Intent, StaticResponse
from app.infrastructure.persistence_sqla.mappings.distillation import (
    distillation_static_responses,
)


class DistillationStaticRepositorySqla(StaticResponseRepository):
    """SQLAlchemy implementation of static response repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_response(
        self,
        intent: Intent,
        variant: str = "default",
    ) -> Optional[StaticResponse]:
        """Get static response for intent and variant."""
        query = select(distillation_static_responses).where(
            distillation_static_responses.c.intent == intent.value,
            distillation_static_responses.c.variant == variant,
            distillation_static_responses.c.is_active == True,
        )
        
        result = await self.session.execute(query)
        row = result.first()
        
        if not row:
            # Try default variant if specific variant not found
            if variant != "default":
                return await self.get_response(intent, "default")
            return None
        
        return StaticResponse(
            id=row.id,
            intent=Intent(row.intent),
            variant=row.variant,
            response_template=row.response_template,
            template_variables=row.template_variables or [],
            data_source=row.data_source,
            conditions=row.conditions or {},
            is_active=row.is_active,
            priority=row.priority,
        )
    
    async def list_responses(
        self,
        intent: Optional[Intent] = None,
        is_active: Optional[bool] = None,
    ) -> List[StaticResponse]:
        """List static responses with optional filters."""
        query = select(distillation_static_responses)
        
        if intent:
            query = query.where(distillation_static_responses.c.intent == intent.value)
        
        if is_active is not None:
            query = query.where(distillation_static_responses.c.is_active == is_active)
        
        query = query.order_by(
            distillation_static_responses.c.intent,
            distillation_static_responses.c.priority.desc(),
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [
            StaticResponse(
                id=row.id,
                intent=Intent(row.intent),
                variant=row.variant,
                response_template=row.response_template,
                template_variables=row.template_variables or [],
                data_source=row.data_source,
                conditions=row.conditions or {},
                is_active=row.is_active,
                priority=row.priority,
            )
            for row in rows
        ]
    
    async def update_response(
        self,
        response_id: UUID,
        response_template: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> None:
        """Update static response."""
        from datetime import datetime, UTC
        
        values = {}
        if response_template is not None:
            values["response_template"] = response_template
        if is_active is not None:
            values["is_active"] = is_active
        
        if not values:
            return
        
        values["updated_at"] = datetime.now(UTC)
        
        query = (
            update(distillation_static_responses)
            .where(distillation_static_responses.c.id == response_id)
            .values(**values)
        )
        
        await self.session.execute(query)
        await self.session.commit()
