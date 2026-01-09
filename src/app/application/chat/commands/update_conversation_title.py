"""
Update conversation title command (user chat system).
"""

from uuid import UUID

from app.application.common.ports.transaction_manager import TransactionManager
from app.domain.chat.ports.conversation_repository import ConversationRepository


class UpdateConversationTitle:
    """
    Update a conversation title for an authenticated user.

    Note: This interactor operates on the legacy user chat conversation store
    (used by /api/v1/user/chat/conversations). It is intentionally separate from
    the Chat System V2 (/api/v1/conversations) which uses a different user model.
    """

    def __init__(
        self,
        repository: ConversationRepository,
        transaction_manager: TransactionManager,
    ):
        self._repository = repository
        self._tx = transaction_manager

    async def execute(
        self,
        *,
        user_id: int,
        conversation_id: UUID,
        title: str,
    ):
        """
        Update the conversation title.

        Args:
            user_id: Authenticated user ID (int)
            conversation_id: Conversation UUID
            title: New title

        Returns:
            Updated Conversation entity or None if not found.

        Raises:
            ValueError: If conversation doesn't belong to user.
        """
        conversation = await self._repository.get_conversation(conversation_id)
        if conversation is None:
            return None

        if conversation.user_id != user_id:
            raise ValueError("Conversation does not belong to user")

        # Update title and persist
        conversation.update_title(title)
        await self._repository.update_conversation(conversation)
        await self._tx.commit()

        return conversation


