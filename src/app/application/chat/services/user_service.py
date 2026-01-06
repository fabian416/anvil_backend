"""
User Service.

Handles user identification and management for both guest and authenticated users.
"""

import logging
from typing import Protocol
from uuid import UUID

from app.domain.chat.entities.chat_user import ChatUser, UserType

logger = logging.getLogger(__name__)


class PrivyClientProtocol(Protocol):
    """Protocol for Privy client verification."""
    
    async def verify_token(self, access_token: str) -> "TokenVerificationResult":
        """Verify a Privy access token."""
        ...


class TokenVerificationResult:
    """Result of token verification."""
    
    is_valid: bool
    user_id: str | None
    email: str | None
    error_message: str | None


class ChatUserRepositoryProtocol(Protocol):
    """Protocol for chat user repository."""
    
    async def get_by_id(self, user_id: UUID) -> ChatUser | None:
        """Get user by ID."""
        ...
    
    async def get_by_privy_id(self, privy_id: str) -> ChatUser | None:
        """Get user by Privy ID."""
        ...
    
    async def get_by_identifier(self, user_type: str, identifier: str) -> ChatUser | None:
        """Get user by type and identifier."""
        ...
    
    async def save(self, user: ChatUser) -> ChatUser:
        """Save user to database."""
        ...
    
    async def update(self, user: ChatUser) -> ChatUser:
        """Update existing user."""
        ...


class UserService:
    """
    Service for user identification and management.
    
    Handles both guest and authenticated users with Privy token priority.
    """
    
    def __init__(
        self,
        user_repository: ChatUserRepositoryProtocol,
        privy_client: PrivyClientProtocol | None = None,
    ):
        self._user_repo = user_repository
        self._privy_client = privy_client
    
    async def get_or_create_user(
        self,
        ip_address: str,
        privy_token: str | None = None,
        language: str = "en",
    ) -> ChatUser:
        """
        Identify user by Privy token or IP address.
        
        Privy token has priority over IP identification.
        
        Args:
            ip_address: Client IP address (fallback for guests)
            privy_token: Optional Privy access token
            language: Preferred language
            
        Returns:
            ChatUser entity (new or existing)
        """
        # 1. If Privy token provided, validate and get/create authenticated user
        if privy_token and self._privy_client:
            privy_data = await self.verify_privy_token(privy_token)
            if privy_data:
                user = await self._user_repo.get_by_privy_id(privy_data["user_id"])
                if user:
                    # Update last active
                    user.update_last_active()
                    if language != user.preferred_language:
                        user.preferred_language = language
                    await self._user_repo.update(user)
                    return user
                
                # Create new authenticated user
                user = ChatUser.create_authenticated(
                    privy_id=privy_data["user_id"],
                    email=privy_data.get("email"),
                    language=language,
                )
                return await self._user_repo.save(user)
        
        # 2. Fallback to guest identification by IP
        user = await self._user_repo.get_by_identifier("guest", ip_address)
        if user:
            user.update_last_active()
            if language != user.preferred_language:
                user.preferred_language = language
            await self._user_repo.update(user)
            return user
        
        # 3. Create new guest user
        user = ChatUser.create_guest(ip_address=ip_address, language=language)
        return await self._user_repo.save(user)
    
    async def verify_privy_token(self, token: str) -> dict | None:
        """
        Validate token with Privy API.
        
        Args:
            token: Privy access token
            
        Returns:
            Dict with user_id and email if valid, None otherwise
        """
        if not self._privy_client:
            logger.warning("Privy client not configured")
            return None
        
        try:
            result = await self._privy_client.verify_token(token)
            if result.is_valid and result.user_id:
                return {
                    "user_id": result.user_id,
                    "email": getattr(result, "email", None),
                }
            return None
        except Exception as e:
            logger.warning(f"Privy token verification failed: {e}")
            return None
    
    async def get_user_by_id(self, user_id: UUID) -> ChatUser | None:
        """Get user by ID."""
        return await self._user_repo.get_by_id(user_id)
    
    async def upgrade_to_authenticated(
        self,
        guest_user: ChatUser,
        privy_id: str,
        email: str | None = None,
    ) -> ChatUser:
        """
        Upgrade a guest user to authenticated status.
        
        Args:
            guest_user: Existing guest user
            privy_id: Privy user ID
            email: Optional email
            
        Returns:
            Updated user
        """
        if not guest_user.is_guest:
            return guest_user
        
        guest_user.user_type = UserType.AUTHENTICATED
        guest_user.privy_id = privy_id
        guest_user.email = email
        guest_user.identifier = privy_id  # Update identifier
        
        return await self._user_repo.update(guest_user)
    
    async def block_user(self, user_id: UUID) -> bool:
        """Block a user."""
        user = await self._user_repo.get_by_id(user_id)
        if user:
            user.block()
            await self._user_repo.update(user)
            return True
        return False
    
    async def unblock_user(self, user_id: UUID) -> bool:
        """Unblock a user."""
        user = await self._user_repo.get_by_id(user_id)
        if user:
            user.unblock()
            await self._user_repo.update(user)
            return True
        return False

