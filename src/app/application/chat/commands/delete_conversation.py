"""
Delete conversation command.
"""

from uuid import UUID

from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.application.common.ports.transaction_manager import TransactionManager


class DeleteConversation:
    """
    Delete a conversation for a user.

    This permanently removes the conversation and all its messages.
    """

    def __init__(
        self,
        repository: ConversationRepository,
        transaction_manager: TransactionManager,
    ):
        """
        Initialize interactor.

        Args:
            repository: Conversation repository
            transaction_manager: Transaction manager for committing changes
        """
        self._repository = repository
        self._tx = transaction_manager

    async def execute(
        self,
        user_id: int,
        conversation_id: UUID,
    ) -> bool:
        """
        Execute the command.

        Args:
            user_id: User identifier (for authorization)
            conversation_id: Conversation to delete

        Returns:
            True if deleted, False if not found or not authorized
        """
        # Delete conversation (repository handles authorization check)
        deleted = await self._repository.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if deleted:
            # Commit transaction to persist changes
            await self._tx.commit()

        return deleted
