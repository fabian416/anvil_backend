"""
Privy Login endpoint controller.
"""

from typing import Optional

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Request, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, Field

from app.application.commands.auth.privy_login import (
    PrivyLogin,
    PrivyLoginRequest,
    PrivyLoginResponse,
)
from app.domain.exceptions.base import DomainFieldError
from app.domain.exceptions.user import EmailAlreadyExistsError
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class PrivyLoginRequestSchema(BaseModel):
    """Request schema for Privy login."""
    privy_user_id: str = Field(..., description="The Privy user ID (did:privy:xxxxx)")
    email: Optional[str] = Field(None, description="User email if available")
    wallet_address: Optional[str] = Field(None, description="Primary wallet address")
    auth_provider: str = Field("privy", description="Auth provider: privy, wallet, google, apple, etc.")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")

    class Config:
        json_schema_extra = {
            "example": {
                "privy_user_id": "did:privy:abc123xyz",
                "email": "user@example.com",
                "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
                "auth_provider": "wallet",
                "first_name": "John",
                "last_name": "Doe"
            }
        }


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
                            "is_new_user": False
                        }
                    }
                }
            },
            400: {"description": "Invalid request data (privy_user_id, email, or wallet_address)"},
            401: {"description": "Authentication failed"},
            409: {"description": "Email already exists with different auth provider"},
            500: {"description": "Internal server error"},
            503: {"description": "Service temporarily unavailable"},
        }
    )
    @inject
    async def privy_login(
        request_body: PrivyLoginRequestSchema,
        http_request: Request,
        interactor: FromDishka[PrivyLogin],
    ) -> PrivyLoginResponseSchema:
        """
        Authenticate user via Privy.
        
        This is the main entry point for Privy-based authentication.
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
        return PrivyLoginResponseSchema.from_response(response)

    return router
