"""
Privy Login interactor - handles authentication via Privy tokens.

Also handles automatic wallet synchronization to the wallets table
when a user logs in with a wallet address.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, UTC

from app.application.common.ports.flusher import Flusher
from app.application.common.ports.session_recorder import SessionRecorder
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.exceptions.user import EmailAlreadyExistsError
from app.domain.ports.wallet.wallet_repository import WalletRepository
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
from app.domain.value_objects.ip_address import IpAddress
from app.infrastructure.auth.session.service import AuthSessionService
from app.infrastructure.exceptions.gateway import DataMapperError
from app.setup.config.admin import AdminSettings
from app.application.chat.services.user_context_service import UserContextService
from app.domain.ports.chat_repository import ChatUserRepository

log = logging.getLogger(__name__)


@dataclass
class PrivyLoginRequest:
    """Request data for Privy login."""
    privy_user_id: str
    email: str | None = None
    wallet_address: str | None = None
    auth_provider: str = "privy"  # privy, wallet, google, apple, etc.
    # Optional user info from Privy
    first_name: str | None = None
    last_name: str | None = None
    # For session tracking
    ip_address: str | None = None
    user_agent: str | None = None


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
    
    Users whose email is in ALLOWED_ADMIN_EMAILS will automatically be
    assigned the admin role upon registration or login.
    
    Also automatically syncs wallets to the wallets table for portfolio tracking.
    """

    def __init__(
        self,
        user_gateway: UserCommandGateway,
        auth_session_service: AuthSessionService,
        transaction_manager: TransactionManager,
        flusher: Flusher,
        session_recorder: SessionRecorder,
        admin_settings: AdminSettings,
        wallet_repository: WalletRepository,
        # Context-aware agents dependencies (optional for backwards compat)
        user_context_service: UserContextService | None = None,
        chat_user_repository: ChatUserRepository | None = None,
    ):
        self._user_gateway = user_gateway
        self._auth_session_service = auth_session_service
        self._transaction_manager = transaction_manager
        self._flusher = flusher
        self._session_recorder = session_recorder
        self._admin_settings = admin_settings
        self._wallet_repository = wallet_repository
        # Context-aware agents
        self._user_context_service = user_context_service
        self._chat_user_repository = chat_user_repository

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
            user: User | None = None
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
            else:
                # Existing user login - update last_ip
                if request.ip_address:
                    user.last_ip = IpAddress.from_optional(request.ip_address)
                    await self._user_gateway.update(user)
                
                # Check if existing user should be promoted to admin
                await self._maybe_upgrade_to_admin(user)

            # CRITICAL: Flush and commit user data BEFORE creating auth session
            # The auth_sessions table has a FK to users.id, so user must exist first
            try:
                await self._flusher.flush()
            except EmailAlreadyExistsError:
                raise
            await self._transaction_manager.commit()

            # Sync wallet to wallets table for portfolio tracking
            if request.wallet_address and user.id_.value > 0:
                await self._sync_wallet_to_db(user, request.wallet_address)

            # Ensure user context entry exists for context-aware agents
            # For new users: create with defaults
            # For existing users: verify context exists (may have been created by Celery)
            if self._user_context_service and self._chat_user_repository:
                await self._ensure_user_context(user, request)

            # Now create session and get tokens (user exists in DB)
            auth_session, access_token = await self._auth_session_service.create_session(user.id_)

            # Record the session (like LogInHandler and SignUpHandler do)
            now = datetime.now(UTC)
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

    async def _find_user_by_privy_id(self, privy_user_id: str) -> User | None:
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
        
        # Update last_ip on login (existing user)
        if request.ip_address:
            user.last_ip = IpAddress.from_optional(request.ip_address)
        
        await self._user_gateway.update(user)
        # No commit here - transaction is managed by the caller

    async def _maybe_upgrade_to_admin(self, user: User) -> None:
        """
        Check if existing user should be upgraded to admin based on their email.
        
        If the user's email is in ALLOWED_ADMIN_EMAILS and they're currently
        a regular user, upgrade them to admin.
        """
        if user.role != UserRole.ADMIN and self._admin_settings.is_admin_email(user.email.value):
            log.info(
                "Auto-upgrading user to admin: '%s' (email in ALLOWED_ADMIN_EMAILS)",
                user.email.value,
            )
            user.role = UserRole.ADMIN
            user.updated_at = UpdatedAt(datetime.now(UTC))
            await self._user_gateway.update(user)

    async def _create_privy_user(self, request: PrivyLoginRequest) -> User:
        """
        Create a new user from Privy authentication.
        
        Note: Does not commit - the caller is responsible for committing the transaction.
        
        If the user's email is in ALLOWED_ADMIN_EMAILS, they will be
        automatically assigned the admin role.
        """
        now = datetime.now(UTC)

        # Generate email if not provided (wallet-only users)
        # Clean privy_user_id for email (remove special chars)
        clean_id = request.privy_user_id.replace(":", "_").replace("did_privy_", "")
        email = request.email or f"{clean_id}@wallet.anvil.io"

        # Use provided names or defaults
        first_name = request.first_name or "Anvil"
        last_name = request.last_name or "User"

        # Determine role based on admin email list
        role = UserRole.USER
        if self._admin_settings.is_admin_email(email):
            log.info(
                "Auto-assigning admin role for new Privy user: '%s' (email in ALLOWED_ADMIN_EMAILS)",
                email,
            )
            role = UserRole.ADMIN

        # Set IP tracking fields on registration
        ip = IpAddress.from_optional(request.ip_address)
        
        user = User(
            id_=UserId(0),  # Will be set by database
            email=Email(email),
            first_name=FirstName(first_name),
            last_name=LastName(last_name),
            role=role,
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
            # IP tracking
            registration_ip=ip,
            last_ip=ip,
        )

        await self._user_gateway.add(user)
        # No commit here - transaction is managed by the caller
        return user

    async def _ensure_user_context(self, user: User, request: PrivyLoginRequest) -> None:
        """
        Ensure user context entry exists for context-aware agents.
        
        This is called on every login (both new and existing users) to
        ensure the context entry exists in the user_context_aware table.
        
        For new users: Creates context with default values
        For existing users: Verifies context exists, creates if missing
        
        The context is used by the authenticated supervisor to provide
        personalized responses based on user classification.
        """
        try:
            # Get or create chat user (UUID-based)
            chat_user = await self._chat_user_repository.get_by_user_id(user.id_.value)
            
            if not chat_user:
                # Create chat user entry
                from app.domain.chat.entities import ChatUser
                from uuid import uuid4
                
                chat_user = ChatUser(
                    id_=uuid4(),
                    user_id=user.id_.value,
                    email=user.email.value,
                    subscription_tier="free",
                    total_messages=0,
                    language="en",
                    chat_preferences={},
                    first_seen_at=datetime.now(UTC),
                    last_seen_at=datetime.now(UTC),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                chat_user = await self._chat_user_repository.create(chat_user)
            
            # Check if context already exists
            existing = await self._user_context_service.exists(chat_user.id_)
            if existing:
                log.debug(
                    "User context already exists for user %s (chat_user_id=%s)",
                    user.id_.value,
                    chat_user.id_,
                )
                return
            
            # Create user context with defaults
            await self._user_context_service.create_for_new_user(
                chat_user_id=chat_user.id_,
                legacy_user_id=user.id_.value,
                wallet_address=request.wallet_address,
                wallet_provider=request.auth_provider,
                language="en",
            )
            
            log.info(
                "Created user context for user %s (chat_user_id=%s)",
                user.id_.value,
                chat_user.id_,
            )
            
        except Exception as e:
            # Log but don't fail login if context creation fails
            log.warning(
                "Failed to ensure user context for user %s: %s",
                user.id_.value,
                e,
            )

    async def _sync_wallet_to_db(self, user: User, wallet_address: str) -> None:
        """
        Sync the user's wallet to the wallets table.

        This ensures the wallet exists in the wallets table for portfolio
        tracking and other features that depend on wallet records.
        """
        try:
            # Determine chain type from address format
            # NOTE: ChainType enum only supports: arbitrum, base, hyperliquid
            # Using 'base' as default for EVM addresses (previously was 'ethereum')
            chain_type = "base"  # Default for EVM addresses (0x...)
            if wallet_address.startswith("bc1") or wallet_address.startswith("tb1"):
                chain_type = "bitcoin"
            elif wallet_address.startswith("1") or wallet_address.startswith("3"):
                chain_type = "bitcoin"
            elif wallet_address.startswith("m") or wallet_address.startswith("n") or wallet_address.startswith("2"):
                chain_type = "bitcoin_testnet"

            await self._wallet_repository.upsert(
                user_id=user.id_,
                address=wallet_address,
                provider=WalletProvider.PRIVY,
                privy_wallet_id=None,  # Will be updated when wallet is synced from Privy
                chain_type=chain_type,
            )
            log.info(
                "Synced wallet to DB: user=%s, address=%s, chain=%s",
                user.id_.value,
                wallet_address[:10] + "...",
                chain_type,
            )
        except DataMapperError as e:
            # Log but don't fail login if wallet sync fails
            log.warning(
                "Failed to sync wallet to DB for user %s: %s",
                user.id_.value,
                e,
            )
