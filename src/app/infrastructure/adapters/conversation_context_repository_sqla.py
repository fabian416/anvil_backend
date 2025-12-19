"""
SQLAlchemy implementation of ConversationContextRepository.
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.entities.conversation_context import ConversationContext
from app.domain.chat.ports.conversation_context_repository import ConversationContextRepository
from app.infrastructure.persistence_sqla.mappings.conversation_context import (
    conversation_context_table,
)

logger = logging.getLogger(__name__)


class ConversationContextRepositorySqla(ConversationContextRepository):
    """
    SQLAlchemy-based conversation context repository.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            session: Database session
        """
        self._session = session
    
    async def get_by_conversation_id(
        self,
        conversation_id: UUID,
    ) -> Optional[ConversationContext]:
        """Get context by conversation ID."""
        stmt = select(conversation_context_table).where(
            conversation_context_table.c.conversation_id == conversation_id
        )
        
        result = await self._session.execute(stmt)
        row = result.first()
        
        if not row:
            return None
        
        return self._row_to_entity(row)
    
    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> Optional[ConversationContext]:
        """Get most recent context for a user."""
        stmt = (
            select(conversation_context_table)
            .where(conversation_context_table.c.user_id == user_id)
            .order_by(conversation_context_table.c.updated_at.desc())
            .limit(1)
        )
        
        result = await self._session.execute(stmt)
        row = result.first()
        
        if not row:
            return None
        
        return self._row_to_entity(row)
    
    async def save(self, context: ConversationContext) -> None:
        """Save or update conversation context."""
        # Check if exists
        existing = await self.get_by_conversation_id(context.conversation_id)
        
        context.updated_at = datetime.utcnow()
        
        if existing:
            # Update
            stmt = (
                update(conversation_context_table)
                .where(conversation_context_table.c.id == context.id)
                .values(**context.to_dict())
            )
            await self._session.execute(stmt)
        else:
            # Insert
            stmt = conversation_context_table.insert().values(**context.to_dict())
            await self._session.execute(stmt)
        
        await self._session.commit()
        
        logger.info(f"Saved conversation context: {context.id}")
    
    async def delete(self, context_id: UUID) -> None:
        """Delete conversation context."""
        stmt = delete(conversation_context_table).where(
            conversation_context_table.c.id == context_id
        )
        
        await self._session.execute(stmt)
        await self._session.commit()
        
        logger.info(f"Deleted conversation context: {context_id}")
    
    def _row_to_entity(self, row) -> ConversationContext:
        """Convert database row to ConversationContext entity."""
        return ConversationContext(
            id=row.id,
            conversation_id=row.conversation_id,
            user_id=row.user_id,
            current_topic=row.current_topic,
            recent_intents=row.recent_intents or [],
            mentioned_tokens=row.mentioned_tokens or [],
            mentioned_protocols=row.mentioned_protocols or [],
            active_positions=row.active_positions or [],
            preferred_slippage=row.preferred_slippage,
            preferred_leverage=row.preferred_leverage,
            risk_tolerance=row.risk_tolerance,
            preferred_chains=row.preferred_chains or [],
            frequent_operations=row.frequent_operations or {},
            typical_trade_sizes=row.typical_trade_sizes or {},
            interaction_count=row.interaction_count,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
