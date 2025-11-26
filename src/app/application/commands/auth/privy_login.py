"""
Privy Login interactor - handles authentication via Privy tokens.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.ports.transaction_manager import TransactionManager
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.value_objects.auth_provider import AuthProvider
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.email import Email
from app.domain.value_objects.first_name import FirstName
from app.domain.value_objects.language import Language
from app.domain.value_objects.last_name import LastName
from app.domain.value_objects.privy_user_id import PrivyUserId
from app.domain.value_objects.retry_count import RetryCount
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.user_password_hash import UserPasswordHash
from app.domain.value_objects.user_status import UserActive, UserBlocked, UserVerified
from app.domain.value_objects.wallet_address import WalletAddress
from app.infrastructure.auth.session.service import AuthSessionService


@dataclass
class PrivyLoginRequest:
    """Request data for Privy login."""
    privy_user_id: str
    email: Optional[str] = None
    wallet_address: Optional[str] = None
    auth_provider: str = "privy"  # privy, wallet, google, apple, etc.
    # Optional user info from Privy
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    # For session tracking
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class PrivyLoginResponse:
    """Response from Privy login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int = 0
    email: str = ""
    is_new_user: bool = False


class PrivyLogin:
    """
    Interactor for handling Privy-based authentication.
    
    This handles login/registration for users authenticating via Privy,
    which includes wallet connections, social logins, and email via Privy.
    """

    def __init__(
        self,
        user_gateway: UserCommandGateway,
        auth_session_service: AuthSessionService,
        transaction_manager: TransactionManager,
    ):
        self._user_gateway = user_gateway
        self._auth_session_service = auth_session_service
        self._transaction_manager = transaction_manager

    async def execute(self, request: PrivyLoginRequest) -> PrivyLoginResponse:
        """
        Execute Privy login flow.
        
        1. Check if user exists by privy_user_id
        2. If not, check by email (if provided)
        3. If still not found, create new user
        4. Generate JWT tokens via session service
        """
        user: Optional[User] = None
        is_new_user = False
        
        # Try to find existing user by privy_user_id
        user = await self._find_user_by_privy_id(request.privy_user_id)
        
        # If not found and email provided, try to find by email
        if not user and request.email:
            user = await self._user_gateway.read_by_email(Email(request.email))
            
            # If found by email, update with Privy info
            if user:
                await self._update_user_privy_info(user, request)
        
        # If still not found, create new user
        if not user:
            user = await self._create_privy_user(request)
            is_new_user = True
        
        # Create session and get tokens (same as regular login)
        auth_session, access_token = await self._auth_session_service.create_session(user.id_)
        await self._transaction_manager.commit()
        
        return PrivyLoginResponse(
            access_token=access_token,
            refresh_token=auth_session.refresh_token or "",
            user_id=user.id_.value,
            email=user.email.value,
            is_new_user=is_new_user,
        )

    async def _find_user_by_privy_id(self, privy_user_id: str) -> Optional[User]:
        """Find user by Privy user ID."""
        # This requires a new method in the gateway - for now return None
        # The actual implementation would query by privy_user_id
        return None

    async def _update_user_privy_info(self, user: User, request: PrivyLoginRequest) -> None:
        """Update existing user with Privy information."""
        # Update user with Privy fields
        user.privy_user_id = PrivyUserId(request.privy_user_id)
        if request.wallet_address:
            user.primary_wallet_address = WalletAddress(request.wallet_address)
        user.auth_provider = AuthProvider(request.auth_provider)
        await self._user_gateway.update(user)
        await self._transaction_manager.commit()

    async def _create_privy_user(self, request: PrivyLoginRequest) -> User:
        """Create a new user from Privy authentication."""
        now = datetime.utcnow()
        
        # Generate email if not provided (wallet-only users)
        # Clean privy_user_id for email (remove special chars)
        clean_id = request.privy_user_id.replace(":", "_").replace("did_privy_", "")
        email = request.email or f"{clean_id}@wallet.anvil.io"
        
        # Use provided names or defaults
        first_name = request.first_name or "Anvil"
        last_name = request.last_name or "User"
        
        user = User(
            id_=UserId(0),  # Will be set by database
            email=Email(email),
            first_name=FirstName(first_name),
            last_name=LastName(last_name),
            role=UserRole.USER,
            is_active=UserActive(True),
            is_blocked=UserBlocked(False),
            is_verified=UserVerified(True),  # Privy users are pre-verified
            retry_count=RetryCount(0),
            password=UserPasswordHash(b""),  # No password for Privy users
            created_at=CreatedAt(now),
            updated_at=UpdatedAt(now),
            last_login=None,
            profile_picture=None,
            phone_number=None,
            language=Language("en"),
            address=None,
            postal_code=None,
            country_id=None,
            city_id=None,
            subscription=None,
            privy_user_id=PrivyUserId(request.privy_user_id),
            primary_wallet_address=WalletAddress(request.wallet_address) if request.wallet_address else None,
            auth_provider=AuthProvider(request.auth_provider),
        )
        
        await self._user_gateway.add(user)
        await self._transaction_manager.commit()
        return user

