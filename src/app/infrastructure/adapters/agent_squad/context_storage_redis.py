"""
Context Storage Redis adapter - Redis-based conversation storage.
"""

import json
from typing import Any
from datetime import datetime

from app.domain.value_objects.conversation_id import ConversationId
from app.domain.services.agent_squad.context_manager import ConversationMessage
from app.domain.ports.agent_squad.context_storage_gateway import ContextStorageGateway


class ContextStorageRedis:
    """
    Context Storage Redis adapter.
    
    Implements: ContextStorageGateway
    
    Stores conversation history and metadata in Redis.
    
    Redis Keys:
    - conversation:{id}:messages - List of messages (JSON)
    - conversation:{id}:metadata - Conversation metadata (JSON)
    - conversation:{id}:count - Message count (integer)
    """
    
    def __init__(self, redis_client: Any):
        """
        Initialize Redis storage.
        
        Args:
            redis_client: Redis client instance (e.g., redis.asyncio.Redis)
        """
        self._redis = redis_client
        self._ttl = 86400  # 24 hours
    
    async def add_message(
        self,
        conversation_id: ConversationId,
        message: ConversationMessage,
    ) -> None:
        """Add message to conversation history."""
        key = f"conversation:{conversation_id.value}:messages"
        
        # Serialize message
        message_json = json.dumps(message.to_dict())
        
        # Add to list (append)
        await self._redis.rpush(key, message_json)
        
        # Set TTL
        await self._redis.expire(key, self._ttl)
        
        # Increment count
        count_key = f"conversation:{conversation_id.value}:count"
        await self._redis.incr(count_key)
        await self._redis.expire(count_key, self._ttl)
    
    async def get_messages(
        self,
        conversation_id: ConversationId,
        limit: int,
    ) -> list[ConversationMessage]:
        """Get recent messages."""
        key = f"conversation:{conversation_id.value}:messages"
        
        # Get last N messages
        messages_json = await self._redis.lrange(key, -limit, -1)
        
        # Deserialize
        messages = []
        for msg_json in messages_json:
            msg_dict = json.loads(msg_json)
            message = self._deserialize_message(msg_dict)
            messages.append(message)
        
        return messages
    
    async def get_metadata(
        self,
        conversation_id: ConversationId,
    ) -> dict:
        """Get conversation metadata."""
        key = f"conversation:{conversation_id.value}:metadata"
        
        metadata_json = await self._redis.get(key)
        if metadata_json:
            return json.loads(metadata_json)
        
        return {"user": {}, "session": {}}
    
    async def update_metadata(
        self,
        conversation_id: ConversationId,
        user_metadata: dict | None,
        session_metadata: dict | None,
    ) -> None:
        """Update conversation metadata."""
        # Get existing metadata
        metadata = await self.get_metadata(conversation_id)
        
        # Update
        if user_metadata:
            metadata["user"].update(user_metadata)
        if session_metadata:
            metadata["session"].update(session_metadata)
        
        # Save
        key = f"conversation:{conversation_id.value}:metadata"
        await self._redis.set(key, json.dumps(metadata), ex=self._ttl)
    
    async def clear_messages(
        self,
        conversation_id: ConversationId,
    ) -> None:
        """Clear conversation history."""
        key = f"conversation:{conversation_id.value}:messages"
        count_key = f"conversation:{conversation_id.value}:count"
        
        await self._redis.delete(key)
        await self._redis.delete(count_key)
    
    async def get_message_count(
        self,
        conversation_id: ConversationId,
    ) -> int:
        """Get message count."""
        count_key = f"conversation:{conversation_id.value}:count"
        count = await self._redis.get(count_key)
        return int(count) if count else 0
    
    async def remove_oldest_messages(
        self,
        conversation_id: ConversationId,
        count: int,
    ) -> None:
        """Remove oldest messages."""
        key = f"conversation:{conversation_id.value}:messages"
        
        # Remove from left (oldest)
        for _ in range(count):
            await self._redis.lpop(key)
    
    def _deserialize_message(self, data: dict) -> ConversationMessage:
        """Deserialize message from dict."""
        from app.domain.value_objects.message_id import MessageId
        from app.domain.enums.agent_type import AgentType
        
        agent_type = None
        if data.get("agent_type"):
            try:
                agent_type = AgentType[data["agent_type"].upper()]
            except KeyError:
                pass
        
        return ConversationMessage(
            message_id=MessageId(data["message_id"]),
            role=data["role"],
            content=data["content"],
            agent_type=agent_type,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )
