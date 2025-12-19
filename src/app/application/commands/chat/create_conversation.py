from uuid import UUID, uuid4
from app.domain.chat.entities.conversation import Conversation
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.ports.ai.llm_conversation_repository import LLMConversationRepository
from app.application.common.ports.transaction_manager import TransactionManager

class CreateConversation:
    def __init__(
        self, 
        repo: LLMConversationRepository,
        tx: TransactionManager
    ):
        self.repo = repo
        self.tx = tx

    async def execute(self, user_id: int) -> Conversation:
        # Mismatch: Conversation entity uses UUID user_id in some versions, int in others. 
        # Based on mappings, user_id is Int.
        
        conversation_id = ConversationId(uuid4())
        # Factory method on entity would be better, but direct init for MVP
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            title=None,
            created_at=None, # Auto-set
            updated_at=None
        )
        
        # Transactional save
        # async with self.tx:
        #     await self.repo.add(conversation)
        
        return conversation
