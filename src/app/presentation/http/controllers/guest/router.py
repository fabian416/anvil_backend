"""
Guest Chat Router.

Public endpoints for unauthenticated guest users.
Provides demo chat functionality with limited features.
"""

from datetime import datetime, timedelta

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Request, status

from app.application.guest.commands.send_guest_message import SendGuestMessage
from app.domain.guest.ports.guest_repository import GuestRepository
from app.presentation.http.schemas.guest import (
    GuestChatRequest,
    GuestChatResponse,
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
        - 20 messages per hour
        - 50 messages per day
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
        Send a guest chat message.

        Automatically creates guest user and conversation based on IP.
        """
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
                signup_url=result.registration_required.get("signup_url", "/signup"),
            )

        guest_info = None
        if result.guest_info:
            guest_info = GuestInfo(
                messages_remaining=result.guest_info.get("messages_remaining", 20),
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
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        messages_this_hour = await repository.get_message_count_since(
            guest.id, hour_ago
        )
        messages_remaining = max(0, 20 - messages_this_hour)

        return GuestStatusResponse(
            has_active_session=conversation is not None and conversation.is_active,
            conversation_id=conversation.id if conversation else None,
            messages_remaining=messages_remaining,
            messages_this_hour=messages_this_hour,
            is_blocked=guest.is_blocked,
            language=guest.language,
        )

    return router
