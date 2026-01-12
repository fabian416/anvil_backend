"""Create Chat Message Command.

Handles creating new messages in authenticated user conversations.
"""

import logging
from typing import Optional
from uuid import UUID, uuid4

from app.domain.chat.entities import ChatMessage
from app.domain.ports.chat_repository import (
    ChatMessageRepository,
    ChatConversationRepository,
)

logger = logging.getLogger(__name__)


class CreateChatMessageCommand:
    """Command to create chat message."""

    def __init__(
        self,
        chat_message_repository: ChatMessageRepository,
        chat_conversation_repository: ChatConversationRepository,
    ):
        """Initialize command.

        Args:
            chat_message_repository: Repository for message persistence
            chat_conversation_repository: Repository for conversation updates
        """
        self._message_repo = chat_message_repository
        self._conversation_repo = chat_conversation_repository

    async def execute(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        intent: Optional[str] = None,
        enrichment: Optional[dict] = None,
        language: str = "en",
    ) -> ChatMessage:
        """Create a new message in the conversation.

        Args:
            conversation_id: Conversation UUID
            role: Message role (user, assistant)
            content: Message content
            intent: Detected intent (optional)
            enrichment: Hunter AI enrichment data (optional)
            language: Message language

        Returns:
            Created ChatMessage entity
        """
        # Validate role
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid message role: {role}. Must be 'user' or 'assistant'")

        # Validate language
        if language not in ("en", "es", "pt", "zh"):
            logger.warning(f"Invalid language '{language}', defaulting to 'en'")
            language = "en"

        # Create message
        message = ChatMessage(
            id_=uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            intent=intent,
            language=language,
            metadata=enrichment or {},
        )

        # Save message
        created_message = await self._message_repo.create(message)

        # Increment conversation message count
        await self._conversation_repo.increment_message_count(conversation_id)

        logger.debug(
            f"Created message: conversation_id={conversation_id}, "
            f"role={role}, intent={intent}"
        )

        return created_message
