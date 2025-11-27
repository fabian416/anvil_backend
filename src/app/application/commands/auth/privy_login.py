"""
Privy Login interactor - handles authentication via Privy tokens.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.application.common.ports.flusher import Flusher
from app.application.common.ports.session_recorder import SessionRecorder
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.ports.transaction_manager import TransactionManager
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.exceptions.user import EmailAlreadyExistsError
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
from app.infrastructure.exceptions.gateway import DataMapperError

log = logging.getLogger(__name__)


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
        flusher: Flusher,
        session_recorder: SessionRecorder,
    ):
        self._user_gateway = user_gateway
        self._auth_session_service = auth_session_service
        self._transaction_manager = transaction_manager
        self._flusher = flusher
        self._session_recorder = session_recorder

    async def execute(self, request: PrivyLoginRequest) -> PrivyLoginResponse:
        """
        Execute Privy login flow.
        
        1. Check if user exists by privy_user_id
        2. If not, check by email (if provided)
        3. If still not found, create new user
        4. Flush and commit user data to ensure FK constraint is satisfied
        5. Generate JWT tokens via session service
        6. Record the session for tracking
        
        All operations are wrapped in proper transaction handling with rollback on errors.
        """
        try:
            user: Optional[User] = None
            is_new_user = False
            
            # Try to find existing user by privy_user_id (with full format)
            user = await self._find_user_by_privy_id(request.privy_user_id)
            
            # If not found, try without the "did:privy:" prefix (legacy format)
            if not user and request.privy_user_id.startswith("did:privy:"):
                clean_privy_id = request.privy_user_id.replace("did:privy:", "")
                user = await self._find_user_by_privy_id(clean_privy_id)
                # If found with legacy format, update to new format
                if user:
                    user.privy_user_id = PrivyUserId(request.privy_user_id)
                    if request.wallet_address:
                        user.primary_wallet_address = WalletAddress(request.wallet_address)
                    await self._user_gateway.update(user)
            
            # If not found and email provided, try to find by email
            if not user and request.email:
                user = await self._user_gateway.read_by_email(Email(request.email))
                
                # If found by email, update with Privy info
                if user:
                    await self._update_user_privy_info(user, request)
            
            # If still not found, try by generated email (wallet users without email)
            if not user and not request.email:
                # Generate the email that would be created for this privy_user_id
                clean_id = request.privy_user_id.replace(":", "_").replace("did_privy_", "")
                generated_email = f"{clean_id}@wallet.anvil.io"
                user = await self._user_gateway.read_by_email(Email(generated_email))
                if user:
                    # Update privy_user_id to the new format
                    user.privy_user_id = PrivyUserId(request.privy_user_id)
                    if request.wallet_address:
                        user.primary_wallet_address = WalletAddress(request.wallet_address)
                    await self._user_gateway.update(user)
            
            # If still not found, create new user
            if not user:
                user = await self._create_privy_user(request)
                is_new_user = True
            
            # CRITICAL: Flush and commit user data BEFORE creating auth session
            # The auth_sessions table has a FK to users.id, so user must exist first
            try:
                await self._flusher.flush()
            except EmailAlreadyExistsError:
                raise
            await self._transaction_manager.commit()
            
            # Now create session and get tokens (user exists in DB)
            auth_session, access_token = await self._auth_session_service.create_session(user.id_)
            
            # Record the session (like LogInHandler and SignUpHandler do)
            now = datetime.utcnow()
            await self._session_recorder.add(
                user_id=user.id_.value,
                access_token=access_token,
                refresh_token=auth_session.refresh_token or "",
                token_type="bearer",
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                created_at=now,
                expires_at=auth_session.expiration,
                last_activity=now,
                is_active=True,
            )
            
            # Final commit for the session record
            await self._transaction_manager.commit()
            
            log.info(
                "Privy login: done. Email: '%s', is_new_user: %s",
                user.email.value,
                is_new_user,
            )
            
            return PrivyLoginResponse(
                access_token=access_token,
                refresh_token=auth_session.refresh_token or "",
                user_id=user.id_.value,
                email=user.email.value,
                is_new_user=is_new_user,
            )
        except EmailAlreadyExistsError:
            # Rollback and re-raise for proper error handling upstream
            await self._transaction_manager.rollback()
            raise
        except DataMapperError:
            # Rollback and re-raise database errors
            await self._transaction_manager.rollback()
            raise
        except Exception as error:
            # Rollback on any unexpected error to clean up session state
            log.error("Unexpected error in Privy login: %s", error)
            await self._transaction_manager.rollback()
            raise

    async def _find_user_by_privy_id(self, privy_user_id: str) -> Optional[User]:
        """Find user by Privy user ID."""
        return await self._user_gateway.read_by_privy_user_id(
            PrivyUserId(privy_user_id)
        )

    async def _update_user_privy_info(self, user: User, request: PrivyLoginRequest) -> None:
        """
        Update existing user with Privy information.
        
        Note: Does not commit - the caller is responsible for committing the transaction.
        """
        user.privy_user_id = PrivyUserId(request.privy_user_id)
        if request.wallet_address:
            user.primary_wallet_address = WalletAddress(request.wallet_address)
        user.auth_provider = AuthProvider(request.auth_provider)
        await self._user_gateway.update(user)
        # No commit here - transaction is managed by the caller

    async def _create_privy_user(self, request: PrivyLoginRequest) -> User:
        """
        Create a new user from Privy authentication.
        
        Note: Does not commit - the caller is responsible for committing the transaction.
        """
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
        # No commit here - transaction is managed by the caller
        return user

