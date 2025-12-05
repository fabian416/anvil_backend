"""
Get Conversation Context Query.

This interactor retrieves conversation history and builds context for agents.
"""

from uuid import UUID

from app.domain.ports.agent_squad.context_storage_gateway import ContextStorageGateway
from app.domain.services.agent_squad.context_manager import ContextManager
from app.domain.value_objects.conversation_id import ConversationId


class GetConversationContext:
    """
    Query interactor for retrieving conversation context.

    Responsibilities:
    - Retrieve conversation messages from storage
    - Build conversation context with metadata
    - Support pagination for large conversations
    """

    def __init__(
        self,
        context_manager: ContextManager,
        context_storage: ContextStorageGateway,
    ):
        self._context_manager = context_manager
        self._context_storage = context_storage

    async def execute(
        self,
        conversation_id: UUID,
        limit: int = 50,
        include_metadata: bool = True,
    ) -> dict:
        """
        Get conversation context.

        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to retrieve (default: 50)
            include_metadata: Whether to include conversation metadata

        Returns:
            dict with:
                - conversation_id: Conversation identifier
                - messages: List of messages with role, content, timestamp
                - total_messages: Total message count
                - metadata: Conversation metadata (if requested)

        Raises:
            ValueError: If conversation not found
        """
        conv_id = ConversationId(conversation_id)

        # Get messages from context storage
        messages = await self._context_storage.get_messages(
            conversation_id=conv_id,
            limit=limit,
        )

        # Get conversation metadata (if requested)
        metadata = None
        if include_metadata:
            metadata = await self._context_storage.get_metadata(conv_id)

        # Format response
        return {
            "conversation_id": str(conversation_id),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata,
                }
                for msg in messages
            ],
            "total_messages": len(messages),
            "metadata": metadata,
        }
