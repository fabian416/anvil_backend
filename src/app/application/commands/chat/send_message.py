from uuid import UUID, uuid4
from app.domain.chat.entities.message import Message
from app.domain.value_objects.message_role import MessageRole
from app.domain.value_objects.message_id import MessageId
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.ports.ai.llm_conversation_repository import LLMConversationRepository
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.ports.agent_task_queue import AgentTaskQueue

from app.domain.value_objects.message_content import MessageContent


class SendMessage:
    def __init__(
        self,
        repo: LLMConversationRepository,
        tx: TransactionManager,
        task_queue: AgentTaskQueue,
    ):
        self.repo = repo
        self.tx = tx
        self.task_queue = task_queue

    async def execute(self, conversation_id: UUID, content: str) -> Message:
        message_id = uuid4()
        message = Message(
            id=message_id,
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            agent_type=None,
            created_at=None,
        )

        # Save Message
        # async with self.tx:
        #     await self.repo.add_message(message)

        # Trigger Async Processing
        await self.task_queue.enqueue_message_processing(conversation_id, message_id)

        return message
