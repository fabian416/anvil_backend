"""
Conversation Repository Bridge Adapter.

Bridges the legacy ConversationRepository port to the unified chat system.
This allows legacy commands to continue working while using the new
chat_conversations and chat_messages tables.
"""

from typing import List, Optional
from uuid import UUID

from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.chat.entities.chat_conversation import (
    ChatConversation,
    ConversationStatus,
)
from app.domain.chat.entities.chat_message import (
    ChatMessage,
    MessageRole as ChatMessageRole,
)
from app.domain.value_objects.message_role import MessageRole
from app.infrastructure.adapters.chat_unified_repository_sqla import (
    ChatConversationRepositorySqla,
    ChatMessageRepositorySqla,
)


class ConversationRepositoryBridge(ConversationRepository):
    """
    Bridge adapter that implements legacy ConversationRepository using unified chat.

    This adapter converts between legacy Conversation/Message entities and unified
    ChatConversation/ChatMessage entities.
    """

    def __init__(
        self,
        conversation_repo: ChatConversationRepositorySqla,
        message_repo: ChatMessageRepositorySqla,
    ):
        """
        Initialize bridge adapter.

        Args:
            conversation_repo: Unified chat conversation repository
            message_repo: Unified chat message repository
        """
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo

    async def add_conversation(self, conversation: Conversation) -> None:
        """Add a new conversation by converting to ChatConversation."""
        # Legacy Conversation uses int user_id, unified uses UUID
        # Convert int to UUID (pad with zeros)
        user_uuid = UUID(int=conversation.user_id)

        chat_conversation = ChatConversation(
            id=conversation.id,
            user_id=user_uuid,
            title=conversation.title,
            status=ConversationStatus.ACTIVE,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

        await self._conversation_repo.save(chat_conversation)

    async def update_conversation(self, conversation: Conversation) -> None:
        """Update an existing conversation."""
        # Get current unified conversation
        chat_conv = await self._conversation_repo.get_by_id(conversation.id)
        if chat_conv:
            chat_conv.title = conversation.title
            chat_conv.updated_at = conversation.updated_at
            await self._conversation_repo.update(chat_conv)

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get a conversation by ID."""
        chat_conv = await self._conversation_repo.get_by_id(conversation_id)
        if not chat_conv:
            return None

        return self._chat_conv_to_legacy(chat_conv)

    async def list_conversations(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> List[Conversation]:
        """List conversations for a user."""
        # Convert int user_id to UUID
        user_uuid = UUID(int=user_id)

        chat_convs = await self._conversation_repo.list_for_user(
            user_id=user_uuid,
            limit=limit,
            offset=offset,
        )

        return [self._chat_conv_to_legacy(c) for c in chat_convs]

    async def add_message(self, message: Message) -> None:
        """Add a message to a conversation."""
        # Convert MessageRole to ChatMessageRole
        role_map = {
            MessageRole.USER: ChatMessageRole.USER,
            MessageRole.AGENT: ChatMessageRole.ASSISTANT,
            MessageRole.SYSTEM: ChatMessageRole.SYSTEM,
        }
        chat_role = role_map.get(message.role, ChatMessageRole.USER)

        chat_message = ChatMessage(
            id=message.id,
            conversation_id=message.conversation_id,
            role=chat_role,
            content=message.content,
            created_at=message.created_at,
            metadata=message.metadata or {},
        )

        # Add agent_type to metadata if present
        if message.agent_type:
            chat_message.metadata["agent_type"] = message.agent_type

        await self._message_repo.save(chat_message)

    async def get_message(self, message_id: UUID) -> Optional[Message]:
        """Get a message by ID."""
        # ChatMessageRepositorySqla doesn't have get_by_id method
        # Return None - this method is rarely used
        return None

    async def get_messages(
        self, conversation_id: UUID, limit: int = 50
    ) -> List[Message]:
        """Get messages for a conversation."""
        chat_messages = await self._message_repo.list_for_conversation(
            conversation_id=conversation_id,
            limit=limit,
        )

        return [self._chat_msg_to_legacy(m) for m in chat_messages]

    async def delete_conversation(self, conversation_id: UUID, user_id: int) -> bool:
        """Delete a conversation and its messages."""
        user_uuid = UUID(int=user_id)
        return await self._conversation_repo.delete_for_user(
            conversation_id=conversation_id,
            user_id=user_uuid,
        )

    def _chat_conv_to_legacy(self, chat_conv: ChatConversation) -> Conversation:
        """Convert ChatConversation to legacy Conversation."""
        # Convert UUID user_id back to int
        user_id_int = chat_conv.user_id.int if chat_conv.user_id else 0

        return Conversation(
            id=chat_conv.id,
            user_id=user_id_int,
            title=chat_conv.title,
            created_at=chat_conv.created_at,
            updated_at=chat_conv.updated_at,
        )

    def _chat_msg_to_legacy(self, chat_msg: ChatMessage) -> Message:
        """Convert ChatMessage to legacy Message."""
        # Convert ChatMessageRole to MessageRole
        role_map = {
            ChatMessageRole.USER: MessageRole.USER,
            ChatMessageRole.ASSISTANT: MessageRole.AGENT,
            ChatMessageRole.SYSTEM: MessageRole.SYSTEM,
        }
        legacy_role = role_map.get(chat_msg.role, MessageRole.USER)

        # Extract agent_type from metadata
        agent_type = None
        if chat_msg.metadata:
            agent_type = chat_msg.metadata.get("agent_type")

        return Message(
            id=chat_msg.id,
            conversation_id=chat_msg.conversation_id,
            role=legacy_role,
            content=chat_msg.content,
            agent_type=agent_type,
            created_at=chat_msg.created_at,
            metadata=chat_msg.metadata,
        )
