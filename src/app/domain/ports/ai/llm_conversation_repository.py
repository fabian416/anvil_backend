from typing import Protocol
from uuid import UUID

from app.domain.entities.ai.llm_conversation import LLMConversation, LLMConversationId
from app.domain.entities.ai.conversation_feedback import ConversationFeedback


class LLMConversationRepository(Protocol):
    async def save(self, conversation: LLMConversation) -> None: ...

    async def get_by_id(self, id: LLMConversationId) -> LLMConversation | None: ...

    async def save_feedback(self, feedback: ConversationFeedback) -> None: ...
