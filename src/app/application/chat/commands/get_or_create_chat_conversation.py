"""Get or Create Chat Conversation Command.

Handles getting the active conversation or creating a new one for authenticated users.
"""

import logging
from uuid import UUID, uuid4

from app.domain.chat.entities import ChatConversation
from app.domain.ports.chat_repository import ChatConversationRepository

logger = logging.getLogger(__name__)


class GetOrCreateChatConversationCommand:
    """Command to get or create active chat conversation."""

    def __init__(self, chat_conversation_repository: ChatConversationRepository):
        """Initialize command.

        Args:
            chat_conversation_repository: Repository for conversation persistence
        """
        self._repo = chat_conversation_repository

    async def execute(self, chat_user_id: UUID, language: str = "en") -> ChatConversation:
        """Get existing active conversation or create new one.

        Args:
            chat_user_id: Chat user UUID
            language: Conversation language (en, es, pt, zh)

        Returns:
            ChatConversation entity (existing or newly created)
        """
        # Validate language
        if language not in ("en", "es", "pt", "zh"):
            logger.warning(f"Invalid language '{language}', defaulting to 'en'")
            language = "en"

        # Try to get existing active conversation
        existing = await self._repo.get_active_conversation(chat_user_id, language)
        if existing:
            logger.debug(
                f"Found existing active conversation for chat_user_id={chat_user_id}, "
                f"conversation_id={existing.id_}"
            )
            return existing

        # Create new conversation
        logger.info(f"Creating new conversation for chat_user_id={chat_user_id}")

        conversation = ChatConversation(
            id_=uuid4(),
            chat_user_id=chat_user_id,
            language=language,
        )

        return await self._repo.create(conversation)
