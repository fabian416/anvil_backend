from typing import Protocol
from uuid import UUID

class AgentTaskQueue(Protocol):
    async def enqueue_message_processing(self, conversation_id: UUID, message_id: UUID) -> None:
        ...
