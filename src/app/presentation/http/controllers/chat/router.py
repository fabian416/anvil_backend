from typing import List
from uuid import uuid4, UUID
from datetime import datetime
from fastapi import APIRouter

from app.presentation.http.schemas.chat.conversation import ConversationCreate, ConversationRead
from app.presentation.http.schemas.chat.message import MessageCreate, MessageRead
from app.domain.enums.message_role import MessageRole

def create_chat_router() -> APIRouter:
    router = APIRouter(prefix="/chat", tags=["chat"])

    @router.post("/conversations", response_model=ConversationRead)
    async def create_conversation(data: ConversationCreate):
        return ConversationRead(
            id=uuid4(),
            user_id=1,
            title=data.title or "New Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @router.get("/conversations", response_model=List[ConversationRead])
    async def list_conversations():
        return [
            ConversationRead(
                id=uuid4(),
                user_id=1,
                title="DeFi Strategy 1",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

    @router.get("/conversations/{conversation_id}", response_model=ConversationRead)
    async def get_conversation(conversation_id: UUID):
        return ConversationRead(
            id=conversation_id,
            user_id=1,
            title="DeFi Strategy 1",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @router.post("/conversations/{conversation_id}/messages", response_model=MessageRead)
    async def send_message(conversation_id: UUID, data: MessageCreate):
        return MessageRead(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=data.content,
            agent_type=data.agent_type,
            created_at=datetime.now()
        )

    return router
