"""
Chat router for conversation and message endpoints.
"""

from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status, Security
from fastapi.exceptions import HTTPException

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.common.services.current_user import CurrentUserService
from app.presentation.http.schemas.chat import (
    CreateConversationRequest,
    ConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
    ConversationListResponse,
    MessageListResponse,
)
from app.application.chat.commands.create_conversation import CreateConversation
from app.application.chat.commands.send_message import SendMessage
from app.application.chat.queries.get_conversation import GetConversation
from app.application.chat.queries.list_conversations import ListConversations
from app.application.chat.queries.get_messages import GetMessages


def create_chat_router() -> APIRouter:
    router = APIRouter(
        prefix="/chat",
        tags=["chat"],
    )
    
    @router.post(
        "/conversations",
        status_code=status.HTTP_201_CREATED,
        response_model=ConversationResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def create_conversation(
        request: CreateConversationRequest,
        current_user: FromDishka[CurrentUserService],
        interactor: FromDishka[CreateConversation],
    ) -> ConversationResponse:
        """
        Create a new conversation.
        
        Requires authentication.
        """
        user = await current_user.get_current_user()
        conversation = await interactor.execute(
            user_id=user.id,
            title=request.title,
        )
        
        return ConversationResponse.model_validate(conversation)
    
    @router.get(
        "/conversations",
        status_code=status.HTTP_200_OK,
        response_model=ConversationListResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def list_conversations(
        current_user: FromDishka[CurrentUserService],
        limit: int = 20,
        offset: int = 0,
        interactor: FromDishka[ListConversations] = None,
    ) -> ConversationListResponse:
        """
        List conversations for the authenticated user.
        
        Supports pagination via limit and offset.
        """
        user = await current_user.get_current_user()
        conversations = await interactor.execute(
            user_id=user.id,
            limit=limit,
            offset=offset,
        )
        
        return ConversationListResponse(
            conversations=[
                ConversationResponse.model_validate(c) for c in conversations
            ],
            total=len(conversations),
        )
    
    @router.get(
        "/conversations/{conversation_id}",
        status_code=status.HTTP_200_OK,
        response_model=ConversationResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_conversation(
        conversation_id: UUID,
        current_user: FromDishka[CurrentUserService],
        interactor: FromDishka[GetConversation],
    ) -> ConversationResponse:
        """
        Get a specific conversation.
        
        Returns 404 if not found or not owned by user.
        """
        user = await current_user.get_current_user()
        conversation = await interactor.execute(
            user_id=user.id,
            conversation_id=conversation_id,
        )
        
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        return ConversationResponse.model_validate(conversation)
    
    @router.post(
        "/conversations/{conversation_id}/messages",
        status_code=status.HTTP_201_CREATED,
        response_model=SendMessageResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def send_message(
        conversation_id: UUID,
        request: SendMessageRequest,
        current_user: FromDishka[CurrentUserService],
        interactor: FromDishka[SendMessage],
    ) -> SendMessageResponse:
        """
        Send a message in a conversation.
        
        Returns both the user message and the agent response.
        """
        user = await current_user.get_current_user()
        user_message, agent_message = await interactor.execute(
            user_id=user.id,
            conversation_id=conversation_id,
            content=request.content,
        )
        
        return SendMessageResponse(
            user_message=user_message,
            agent_message=agent_message,
        )
    
    @router.get(
        "/conversations/{conversation_id}/messages",
        status_code=status.HTTP_200_OK,
        response_model=MessageListResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_messages(
        conversation_id: UUID,
        current_user: FromDishka[CurrentUserService],
        limit: int = 50,
        interactor: FromDishka[GetMessages] = None,
    ) -> MessageListResponse:
        """
        Get messages for a conversation.
        
        Messages are returned in chronological order (oldest first).
        """
        user = await current_user.get_current_user()
        messages = await interactor.execute(
            user_id=user.id,
            conversation_id=conversation_id,
            limit=limit,
        )
        
        return MessageListResponse(
            messages=messages,
            total=len(messages),
        )
    
    return router
