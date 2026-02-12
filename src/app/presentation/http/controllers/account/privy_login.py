"""
Privy Login endpoint controller.

On successful login/register we:
- Upsert user_sync_schedule so the user is eligible for recent-user incremental sync
  (Celery task runs every 1 min with 1→3→6→12 min backoff).
- Enqueue recent_user_sync.sync_user so tx history sync runs immediately in Celery.
"""

from typing import Optional

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from app.application.commands.auth.privy_login import (
    PrivyLogin,
    PrivyLoginRequest,
    PrivyLoginResponse,
)
from app.domain.exceptions.base import DomainFieldError
from app.domain.exceptions.user import EmailAlreadyExistsError
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class PrivyLoginRequestSchema(BaseModel):
    """Request schema for Privy login."""

    privy_user_id: str = Field(..., description="The Privy user ID (did:privy:xxxxx)")
    email: Optional[str] = Field(None, description="User email if available")
    wallet_address: Optional[str] = Field(None, description="Primary wallet address")
    auth_provider: str = Field(
        "privy", description="Auth provider: privy, wallet, google, apple, etc."
    )
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "privy_user_id": "did:privy:abc123xyz",
                "email": "user@example.com",
                "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
                "auth_provider": "wallet",
                "first_name": "John",
                "last_name": "Doe",
            }
        }
    )


class PrivyLoginResponseSchema(BaseModel):
    """Response schema for Privy login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    is_new_user: bool

    @classmethod
    def from_response(cls, response: PrivyLoginResponse) -> "PrivyLoginResponseSchema":
        return cls(
            access_token=response.access_token,
            refresh_token=response.refresh_token,
            token_type=response.token_type,
            user_id=response.user_id,
            email=response.email,
            is_new_user=response.is_new_user,
        )


_EARN_RECOVERY_COOLDOWN_SECONDS = 300  # 5 minutes


async def _trigger_earn_recovery(*, user_id: str, wallet_address: str) -> None:
    """
    Dispatch earn position recovery for Aave/Compound on login.

    Uses a Redis key with 5-minute TTL to prevent repeated recovery
    when the user refreshes the page quickly.
    """
    import os
    import logging

    from redis.asyncio import Redis as AsyncRedis

    logger = logging.getLogger("privy_login.earn_recovery")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client: AsyncRedis | None = None
    try:
        redis_client = AsyncRedis.from_url(
            redis_url, decode_responses=True, socket_timeout=2
        )
        cooldown_key = f"earn_recovery_cooldown:{user_id}"

        # Check cooldown — if key exists, skip recovery
        if await redis_client.exists(cooldown_key):
            logger.debug(
                "Earn recovery cooldown active for user %s, skipping",
                user_id,
            )
            return

        # Set cooldown key with TTL
        await redis_client.setex(
            cooldown_key,
            _EARN_RECOVERY_COOLDOWN_SECONDS,
            "1",
        )

        # Dispatch Celery task
        from app.infrastructure.celery.tasks import recover_earn_positions

        recover_earn_positions.delay(
            user_id=user_id,
            wallet_address=wallet_address,
        )
        logger.info(
            "Earn recovery dispatched for user %s wallet %s",
            user_id,
            wallet_address[:10] + "...",
        )
    finally:
        if redis_client:
            await redis_client.aclose()


def create_privy_login_router() -> APIRouter:
    """Create the Privy login router."""
    router = ErrorAwareRouter(tags=["Account"])

    @router.post(
        "/privy-login",
        response_model=PrivyLoginResponseSchema,
        status_code=status.HTTP_200_OK,
        summary="Privy Authentication",
        description="""
        Authenticate a user via Privy.
        
        This endpoint handles authentication for users coming from Privy,
        which includes:
        - Wallet connections (MetaMask, WalletConnect, etc.)
        - Social logins (Google, Apple, Twitter, Discord)
        - Email via Privy
        
        If the user doesn't exist, a new account is created automatically.
        
        **Frontend Integration:**
        1. User authenticates with Privy on frontend
        2. Frontend receives Privy user data
        3. Frontend calls this endpoint with Privy user info
        4. Backend returns JWT tokens for API authentication
        """,
        error_map={
            DomainFieldError: status.HTTP_400_BAD_REQUEST,
            EmailAlreadyExistsError: status.HTTP_409_CONFLICT,
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
            ValueError: status.HTTP_400_BAD_REQUEST,
            Exception: rule(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_info,
        responses={
            200: {
                "description": "Successfully authenticated",
                "content": {
                    "application/json": {
                        "example": {
                            "access_token": "eyJhbGciOiJIUzI1NiIs...",
                            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                            "token_type": "bearer",
                            "user_id": 123,
                            "email": "user@example.com",
                            "is_new_user": False,
                        }
                    }
                },
            },
            400: {
                "description": "Invalid request data (privy_user_id, email, or wallet_address)"
            },
            401: {"description": "Authentication failed"},
            409: {"description": "Email already exists with different auth provider"},
            500: {"description": "Internal server error"},
            503: {"description": "Service temporarily unavailable"},
        },
    )
    @inject
    async def privy_login(
        request_body: PrivyLoginRequestSchema,
        http_request: Request,
        interactor: FromDishka[PrivyLogin],
        session: FromDishka[MainAsyncSession] = None,
    ) -> PrivyLoginResponseSchema:
        """
        Authenticate user via Privy.

        This is the main entry point for Privy-based authentication.
        On success we upsert user_sync_schedule so the user is eligible for
        recent-user incremental sync (tx history backfill).
        """
        # Extract client info for session tracking
        ip_address = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")

        login_request = PrivyLoginRequest(
            privy_user_id=request_body.privy_user_id,
            email=request_body.email,
            wallet_address=request_body.wallet_address,
            auth_provider=request_body.auth_provider,
            first_name=request_body.first_name,
            last_name=request_body.last_name,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        response = await interactor.execute(login_request)

        # Make user eligible for recent-user incremental sync (1→3→6→12 min backoff)
        if session and response.user_id:
            try:
                from datetime import datetime, UTC, timedelta
                from sqlalchemy import insert
                from app.infrastructure.persistence_sqla.registry import mapping_registry
                from app.infrastructure.persistence_sqla.mappings.user_sync_schedule_mapping import (
                    map_user_sync_schedule_table,
                )
                map_user_sync_schedule_table()
                schedule_table = mapping_registry.metadata.tables.get("user_sync_schedule")
                if schedule_table:
                    now_utc = datetime.now(UTC)
                    # First sync in 1 minute so Celery picks them up soon
                    next_sync = now_utc + timedelta(minutes=1)
                    stmt = insert(schedule_table).values(
                        user_id=response.user_id,
                        next_sync_at=next_sync,
                        interval_index=0,
                        last_synced_at=None,
                        created_at=now_utc,
                        updated_at=now_utc,
                    ).on_conflict_do_update(
                        index_elements=["user_id"],
                        set_={
                            "next_sync_at": next_sync,
                            "interval_index": 0,
                            "updated_at": now_utc,
                        },
                    )
                    await session.execute(stmt)
            except Exception:
                pass  # Non-critical: sync will still seed from auth_sessions

        # Trigger sync now in Celery so tx history updates without waiting for beat
        if response.user_id:
            try:
                from app.infrastructure.celery.tasks.recent_user_sync_tasks import (
                    sync_single_user,
                )
                sync_single_user.delay(response.user_id)
            except Exception:
                pass  # Non-critical: login succeeds; incremental will run later

        # Trigger earn position recovery (Aave/Compound) with 5-min cooldown
        if response.user_id and request_body.wallet_address:
            try:
                await _trigger_earn_recovery(
                    user_id=str(response.user_id),
                    wallet_address=request_body.wallet_address,
                )
            except Exception:
                pass  # Non-critical: recovery will run via scheduled task

        return PrivyLoginResponseSchema.from_response(response)

    return router
