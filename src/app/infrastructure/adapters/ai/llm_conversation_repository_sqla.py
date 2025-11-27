from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ports.ai.llm_conversation_repository import LLMConversationRepository
from app.domain.entities.ai.llm_conversation import LLMConversation, LLMConversationId
from app.domain.entities.ai.conversation_feedback import ConversationFeedback
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.infrastructure.adapters.types import MainAsyncSession

class LLMConversationRepositorySqla(LLMConversationRepository):
    def __init__(self, session: MainAsyncSession):
        self._session = session

    async def save(self, conversation: LLMConversation) -> None:
        # In a real implementation, this would map entity fields to the mapped table model
        # For now, we assume the mapping logic or direct ORM usage
        self._session.add(conversation)
        await self._session.flush()

    async def get_by_id(self, id: LLMConversationId) -> LLMConversation | None:
        LLMConversationsTable = mapping_registry.metadata.tables["llm_conversations"] # type: ignore
        stmt = select(LLMConversationsTable).where(LLMConversationsTable.c.id == id.value)
        # Note: This requires a proper data mapper from Row to Entity, similar to user_data_mapper_sqla.py
        # Simplified for this step
        return await self._session.scalar(stmt)

    async def save_feedback(self, feedback: ConversationFeedback) -> None:
        self._session.add(feedback)
        await self._session.flush()
