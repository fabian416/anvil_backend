"""
MoonPay Token Repository Port.

Defines the interface for storing and retrieving MoonPay authentication tokens.
"""

from datetime import datetime, UTC
from typing import Protocol
from uuid import UUID


class MoonPayTokenData:
    """Data class for MoonPay token information."""

    def __init__(
        self,
        id: UUID,
        user_id: int,
        moonpay_token: str,
        moonpay_csrf_token: str,
        created_at: datetime,
        updated_at: datetime,
        expires_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.moonpay_token = moonpay_token
        self.moonpay_csrf_token = moonpay_csrf_token
        self.created_at = created_at
        self.updated_at = updated_at
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """Check if the token has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at


class MoonPayTokenRepository(Protocol):
    """
    Repository interface for MoonPay authentication tokens.

    These tokens are received from MoonPay after a user completes KYC
    via the swapsCustomerSetup widget flow, and are required to execute
    swaps via the MoonPay API.
    """

    async def get_by_user_id(self, user_id: int) -> MoonPayTokenData | None:
        """
        Get MoonPay tokens for a user.

        Args:
            user_id: The user's INTEGER ID (matches users.id)

        Returns:
            MoonPayTokenData if tokens exist, None otherwise
        """
        ...

    async def upsert(
        self,
        user_id: int,
        moonpay_token: str,
        moonpay_csrf_token: str,
        expires_at: datetime | None = None,
    ) -> None:
        """
        Insert or update MoonPay tokens for a user.

        If tokens already exist for the user, they will be updated.
        Otherwise, new tokens will be inserted.

        Args:
            user_id: The user's INTEGER ID (matches users.id)
            moonpay_token: The Bearer token for MoonPay API calls
            moonpay_csrf_token: The CSRF token from MoonPay
            expires_at: Optional expiration time for the tokens
        """
        ...

    async def delete_by_user_id(self, user_id: int) -> None:
        """
        Delete MoonPay tokens for a user.

        Args:
            user_id: The user's INTEGER ID (matches users.id)
        """
        ...

    async def has_valid_tokens(self, user_id: int) -> bool:
        """
        Check if a user has valid (non-expired) MoonPay tokens.

        Args:
            user_id: The user's INTEGER ID (matches users.id)

        Returns:
            True if the user has valid tokens, False otherwise
        """
        ...
