"""
Create conversation command.
"""

from uuid import UUID
from typing import Optional

from app.domain.chat.entities.conversation import Conversation
from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.application.common.ports.transaction_manager import TransactionManager


class CreateConversation:
    """
    Create a new conversation for a user.

    This is the entry point for starting a new chat session.
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
        title: Optional[str] = None,
    ) -> Conversation:
        """
        Execute the command.

        Args:
            user_id: User identifier
            title: Optional conversation title

        Returns:
            Created conversation entity
        """
        # Create conversation
        conversation = Conversation.create(
            user_id=user_id,
            title=title,
        )

        # Save to repository
        await self._repository.add_conversation(conversation)

        # Commit transaction to persist changes
        await self._tx.commit()

        return conversation
