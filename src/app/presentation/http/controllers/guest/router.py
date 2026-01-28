"""
Guest Chat Router.

Public endpoints for unauthenticated guest users.
Provides demo chat functionality with limited features.
"""

from datetime import datetime, timedelta, UTC

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Request, status
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.agent_squad.supervisor_coordinator import SupervisorCoordinator

from app.application.guest.commands.send_guest_message import (
    RATE_LIMIT_MESSAGES_PER_HOUR,
    SendGuestMessage,
)
from app.domain.guest.ports.guest_repository import GuestRepository
from app.presentation.http.schemas.guest import (
    GuestChatRequest,
    GuestChatResponse,
    GuestDeleteChatResponse,
    GuestHistoryMessage,
    GuestHistoryResponse,
    GuestInfo,
    GuestRegistrationRequired,
    GuestRoutingData,
    GuestStatusResponse,
)

def _get_client_ip(http_request: Request) -> str:
    """
    Resolve client IP address.

    Prefer X-Forwarded-For (first IP) to support local/testing behind proxies.
    Fallback to the direct client host.
    """
    xff = http_request.headers.get("x-forwarded-for")
    if xff:
        # X-Forwarded-For can be a comma-separated list. The first one is the original client.
        first = xff.split(",")[0].strip()
        if first:
            return first
    return http_request.client.host if http_request.client else "unknown"


def create_guest_router() -> APIRouter:
    """Create the guest chat router."""

    router = APIRouter(
        prefix="/guest",
        tags=["Guest Chat"],
    )

    @router.post(
        "/chat",
        response_model=GuestChatResponse,
        status_code=status.HTTP_200_OK,
        summary="Send Guest Message",
        description="""
        Send a chat message as a guest user.
        
        **Demo Mode Features:**
        - Protocol search and discovery
        - Risk assessment information
        - Lending/money market rates (view only)
        - Swap quotes (view only)
        - General DeFi questions
        
        **Restricted Actions (require registration):**
        - View portfolio, balance, activity
        - Execute swaps, deposits, withdrawals
        - Get wallet receive address
        
        **Rate Limits:**
        - 5000 messages per hour (testing)
        - 10000 messages per day (testing)
        - Max 500 characters per message
        
        **Languages:** en (English), es (Spanish), pt (Portuguese), zh (Mandarin)
        """,
    )
    @inject
    async def send_guest_message(
        request_body: GuestChatRequest,
        http_request: Request,
        command: FromDishka[SendGuestMessage],
    ) -> GuestChatResponse:
        """
        Send a guest message with Agent Squad Supervisor as primary handler.
        
        SupervisorCoordinator is injected if available from AgentSquadDomainProvider.
        """
        """
        Send a guest chat message.

        Automatically creates guest user and conversation based on IP.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Extract client info
            ip_address = _get_client_ip(http_request)
            user_agent = http_request.headers.get("user-agent")
            referer = http_request.headers.get("referer")

            result = await command.execute(
                ip_address=ip_address,
                content=request_body.content,
                language=request_body.language,
                user_agent=user_agent,
                referer=referer,
            )
        except Exception as e:
            logger.error(
                f"Error processing guest message: {e}",
                exc_info=True,
                extra={
                    "ip_address": _get_client_ip(http_request),
                    "content_length": len(request_body.content) if request_body.content else 0,
                    "language": request_body.language,
                }
            )
            # Re-raise to let FastAPI's error handler deal with it
            raise

        # Build response
        routing = GuestRoutingData(
            intent=result.routing.get("intent", "GENERAL_CONVERSATION"),
            confidence=result.routing.get("confidence", 0.5),
            handler=result.routing.get("handler", "demo_handler"),
            language=result.routing.get("language", "en"),
            is_demo_mode=True,
        )

        registration_required = None
        if result.registration_required:
            registration_required = GuestRegistrationRequired(
                required=True,
                reason=result.registration_required.get("reason", "execute_action"),
                message=result.registration_required.get("message", {}),
                cta=result.registration_required.get("cta", {}),
                # signup_url removed - URLs not shown in guest chat
            )

        guest_info = None
        if result.guest_info:
            guest_info = GuestInfo(
                messages_remaining=result.guest_info.get("messages_remaining", RATE_LIMIT_MESSAGES_PER_HOUR),
                session_active=result.guest_info.get("session_active", True),
            )

        return GuestChatResponse(
            conversation_id=result.conversation_id,
            message_id=result.message_id,
            user_message=result.user_message,
            agent_message=result.agent_message,
            routing=routing,
            enrichment=result.enrichment,
            registration_required=registration_required,
            guest_info=guest_info,
            rate_limited=result.rate_limited,
        )

    @router.get(
        "/chat/history",
        response_model=GuestHistoryResponse,
        status_code=status.HTTP_200_OK,
        summary="Get Guest Chat History",
        description="Get chat history for the current guest user (by IP).",
    )
    @inject
    async def get_guest_history(
        http_request: Request,
        repository: FromDishka[GuestRepository],
        limit: int = 50,
    ) -> GuestHistoryResponse:
        """Get guest chat history for current IP."""
        ip_address = _get_client_ip(http_request)

        # Get guest user
        guest = await repository.get_guest_by_ip(ip_address)
        if not guest:
            return GuestHistoryResponse()

        # Get active conversation
        conversation = await repository.get_active_conversation(guest.id)
        if not conversation:
            return GuestHistoryResponse(
                is_active=False,
                language=guest.language,
            )

        # Get messages
        messages = await repository.get_messages(conversation.id, limit=limit)

        return GuestHistoryResponse(
            conversation_id=conversation.id,
            messages=[
                GuestHistoryMessage(
                    id=msg.id,
                    role=msg.role.value,
                    content=msg.content,
                    intent=msg.intent,
                    is_restricted_action=msg.is_restricted_action,
                    created_at=msg.created_at,
                )
                for msg in messages
            ],
            total_messages=len(messages),
            is_active=conversation.is_active,
            language=conversation.language,
        )

    @router.get(
        "/chat/status",
        response_model=GuestStatusResponse,
        status_code=status.HTTP_200_OK,
        summary="Get Guest Status",
        description="Check guest session status and rate limits.",
    )
    @inject
    async def get_guest_status(
        http_request: Request,
        repository: FromDishka[GuestRepository],
    ) -> GuestStatusResponse:
        """Get guest status for current IP."""
        ip_address = _get_client_ip(http_request)

        # Get guest user
        guest = await repository.get_guest_by_ip(ip_address)
        if not guest:
            return GuestStatusResponse()

        # Get active conversation
        conversation = await repository.get_active_conversation(guest.id)

        # Get message count this hour
        hour_ago = datetime.now(UTC) - timedelta(hours=1)
        messages_this_hour = await repository.get_message_count_since(
            guest.id, hour_ago
        )
        messages_remaining = max(0, RATE_LIMIT_MESSAGES_PER_HOUR - messages_this_hour)

        return GuestStatusResponse(
            has_active_session=conversation is not None and conversation.is_active,
            conversation_id=conversation.id if conversation else None,
            messages_remaining=messages_remaining,
            messages_this_hour=messages_this_hour,
            is_blocked=guest.is_blocked,
            language=guest.language,
        )

    @router.delete(
        "/chat",
        response_model=GuestDeleteChatResponse,
        status_code=status.HTTP_200_OK,
        summary="Delete Guest Chat",
        description="""
        Delete the current guest chat session and all its messages.
        
        This will:
        - Archive the current conversation
        - Delete all messages in the conversation
        - Allow the guest to start a fresh chat
        
        The guest user record is preserved (for rate limiting tracking).
        """,
    )
    @inject
    async def delete_guest_chat(
        http_request: Request,
        repository: FromDishka[GuestRepository],
    ) -> GuestDeleteChatResponse:
        """Delete guest chat for current IP."""
        ip_address = _get_client_ip(http_request)

        # Get guest user
        guest = await repository.get_guest_by_ip(ip_address)
        if not guest:
            return GuestDeleteChatResponse(
                success=False,
                message="No guest session found",
            )

        # Delete the active conversation and its messages
        deleted = await repository.delete_conversation_for_guest(guest.id)

        if deleted:
            return GuestDeleteChatResponse(
                success=True,
                message="Chat deleted successfully",
            )
        else:
            return GuestDeleteChatResponse(
                success=False,
                message="No active chat to delete",
            )

    return router
