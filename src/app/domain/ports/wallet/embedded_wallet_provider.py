"""
Embedded Wallet Provider Port.

Defines the abstract interface for embedded wallet providers.
This abstraction allows switching between providers like Privy, Dynamic,
Turnkey, or any other wallet-as-a-service provider without changing
the application logic.

To add a new provider:
1. Create an adapter in infrastructure/wallet_providers/<provider_name>/
2. Implement all methods from EmbeddedWalletProviderPort
3. Register the adapter in the dependency injection container

Current implementations:
- Privy: infrastructure/privy/client.py
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol, Optional, runtime_checkable


# ============================================================
# Data Transfer Objects (DTOs)
# ============================================================


class ChainType(str, Enum):
    """Supported blockchain types."""

    ETHEREUM = "ethereum"
    SOLANA = "solana"
    BITCOIN = "bitcoin"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    OTHER = "other"


class WalletType(str, Enum):
    """Types of wallet ownership."""

    EMBEDDED = "embedded"  # Provider-managed wallet (e.g., Privy embedded)
    EXTERNAL = "external"  # User-owned wallet (e.g., MetaMask, Phantom)
    SERVER_CONTROLLED = "server_controlled"  # Backend-controlled wallet
    IMPORTED = "imported"  # Wallet imported via private key


@dataclass
class WalletInfo:
    """
    Wallet information returned from the provider.

    This is a provider-agnostic representation of a wallet.
    Each provider adapter should map their specific response to this DTO.
    """

    wallet_id: str
    """Unique identifier from the provider (e.g., Privy wallet ID)."""

    address: str
    """Blockchain address (e.g., 0x... for Ethereum)."""

    chain_type: ChainType
    """Blockchain type (ethereum, solana, etc.)."""

    wallet_type: WalletType
    """Type of wallet (embedded, external, server_controlled)."""

    created_at: Optional[datetime] = None
    """When the wallet was created."""

    owner_id: Optional[str] = None
    """Provider user ID that owns this wallet."""

    is_recoverable: bool = True
    """Whether the wallet can be recovered by the user."""

    metadata: dict = field(default_factory=dict)
    """Additional provider-specific data."""


@dataclass
class UserInfo:
    """
    User information from the wallet provider.

    Contains the user profile and linked accounts/wallets.
    """

    user_id: str
    """Unique identifier from the provider (e.g., did:privy:xxx)."""

    email: Optional[str] = None
    """User's email if linked."""

    phone: Optional[str] = None
    """User's phone if linked."""

    created_at: Optional[datetime] = None
    """When the user was created in the provider."""

    linked_wallets: list[WalletInfo] = field(default_factory=list)
    """All wallets linked to this user."""

    linked_accounts: list[str] = field(default_factory=list)
    """Linked social accounts (e.g., google, apple, twitter)."""

    metadata: dict = field(default_factory=dict)
    """Additional provider-specific data."""


@dataclass
class TokenVerificationResult:
    """
    Result of verifying an access token from the provider.

    This is used to validate that a token from the frontend is legitimate.
    """

    is_valid: bool
    """Whether the token is valid."""

    user_id: Optional[str] = None
    """The user ID if the token is valid."""

    app_id: Optional[str] = None
    """The app ID the token was issued for."""

    issued_at: Optional[datetime] = None
    """When the token was issued."""

    expires_at: Optional[datetime] = None
    """When the token expires."""

    error_message: Optional[str] = None
    """Error message if validation failed."""


@dataclass
class WalletListResult:
    """
    Paginated list of wallets.

    Used for listing all wallets in the application.
    """

    wallets: list[WalletInfo]
    """List of wallets in this page."""

    next_cursor: Optional[str] = None
    """Cursor for the next page, None if no more pages."""

    total_count: Optional[int] = None
    """Total count if available from the provider."""


# ============================================================
# Exceptions
# ============================================================


class WalletProviderError(Exception):
    """Base exception for wallet provider errors."""

    def __init__(self, message: str, provider: str = "unknown"):
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class WalletNotFoundError(WalletProviderError):
    """Wallet not found in the provider."""

    pass


class AuthenticationError(WalletProviderError):
    """Authentication with the provider failed (invalid credentials)."""

    pass


class TokenVerificationError(WalletProviderError):
    """Token verification failed."""

    pass


class RateLimitError(WalletProviderError):
    """Provider rate limit exceeded."""

    def __init__(self, message: str, provider: str = "unknown", retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(message, provider)


class UserNotFoundError(WalletProviderError):
    """User not found in the provider."""

    pass


# ============================================================
# Port Interface (Abstract)
# ============================================================


@runtime_checkable
class EmbeddedWalletProviderPort(Protocol):
    """
    Abstract interface for embedded wallet providers.

    All wallet provider adapters (Privy, Dynamic, Turnkey, etc.)
    must implement this interface.

    To switch providers:
    1. Implement this interface for the new provider
    2. Change the dependency injection binding

    Example usage:
        # In your service
        class WalletService:
            def __init__(self, provider: EmbeddedWalletProviderPort):
                self._provider = provider

            async def get_user_wallets(self, user_id: str) -> list[WalletInfo]:
                user = await self._provider.get_user(user_id)
                return user.linked_wallets
    """

    @property
    def provider_name(self) -> str:
        """
        Get the provider name (e.g., 'privy', 'dynamic', 'turnkey').

        This is useful for logging and debugging.
        """
        ...

    # --------------------------------------------------------
    # Token Verification
    # --------------------------------------------------------

    async def verify_token(self, access_token: str) -> TokenVerificationResult:
        """
        Verify an access token from the frontend.

        This should be called during login to ensure the token
        sent by the frontend is legitimate.

        Args:
            access_token: The JWT token from the frontend.

        Returns:
            TokenVerificationResult with validation status and user info.

        Raises:
            AuthenticationError: If provider credentials are invalid.
            WalletProviderError: For other API errors.
        """
        ...

    # --------------------------------------------------------
    # User Operations
    # --------------------------------------------------------

    async def get_user(self, user_id: str) -> UserInfo:
        """
        Get user information by their provider user ID.

        Args:
            user_id: The provider's user ID (e.g., did:privy:xxx).

        Returns:
            UserInfo with user profile and linked wallets.

        Raises:
            UserNotFoundError: If user doesn't exist.
            AuthenticationError: If provider credentials are invalid.
            WalletProviderError: For other API errors.
        """
        ...

    async def get_user_by_email(self, email: str) -> Optional[UserInfo]:
        """
        Get user information by email.

        Args:
            email: User's email address.

        Returns:
            UserInfo if found, None otherwise.

        Raises:
            AuthenticationError: If provider credentials are invalid.
            WalletProviderError: For other API errors.
        """
        ...

    async def get_user_by_wallet_address(self, address: str) -> Optional[UserInfo]:
        """
        Get user information by wallet address.

        Args:
            address: Blockchain wallet address.

        Returns:
            UserInfo if found, None otherwise.

        Raises:
            AuthenticationError: If provider credentials are invalid.
            WalletProviderError: For other API errors.
        """
        ...

    # --------------------------------------------------------
    # Wallet Operations
    # --------------------------------------------------------

    async def get_wallet(self, wallet_id: str) -> WalletInfo:
        """
        Get wallet information by wallet ID.

        Args:
            wallet_id: The provider's wallet ID.

        Returns:
            WalletInfo with wallet details.

        Raises:
            WalletNotFoundError: If wallet doesn't exist.
            AuthenticationError: If provider credentials are invalid.
            WalletProviderError: For other API errors.
        """
        ...

    async def get_wallet_by_address(self, address: str, chain_type: ChainType = ChainType.ETHEREUM) -> Optional[WalletInfo]:
        """
        Get wallet information by blockchain address.

        Args:
            address: Blockchain wallet address.
            chain_type: The blockchain type to search in.

        Returns:
            WalletInfo if found, None otherwise.

        Raises:
            AuthenticationError: If provider credentials are invalid.
            WalletProviderError: For other API errors.
        """
        ...

    async def list_wallets(
        self,
        cursor: Optional[str] = None,
        limit: int = 100,
        chain_type: Optional[ChainType] = None,
    ) -> WalletListResult:
        """
        List all wallets for the application (paginated).

        This returns all wallets managed by the application,
        not just for a specific user.

        Args:
            cursor: Pagination cursor from previous request.
            limit: Maximum wallets per page (default: 100).
            chain_type: Filter by blockchain type.

        Returns:
            WalletListResult with paginated wallets.

        Raises:
            AuthenticationError: If provider credentials are invalid.
            WalletProviderError: For other API errors.
        """
        ...

    async def list_user_wallets(self, user_id: str) -> list[WalletInfo]:
        """
        List all wallets for a specific user.

        Args:
            user_id: The provider's user ID.

        Returns:
            List of WalletInfo for the user.

        Raises:
            UserNotFoundError: If user doesn't exist.
            AuthenticationError: If provider credentials are invalid.
            WalletProviderError: For other API errors.
        """
        ...

    # --------------------------------------------------------
    # Wallet Creation (Optional - not all providers support this from backend)
    # --------------------------------------------------------

    async def create_wallet_for_user(
        self,
        user_id: str,
        chain_type: ChainType = ChainType.ETHEREUM,
    ) -> WalletInfo:
        """
        Create a new embedded wallet for a user.

        Note: Not all providers support backend wallet creation.
        Check provider documentation.

        Args:
            user_id: The provider's user ID.
            chain_type: Blockchain type for the new wallet.

        Returns:
            WalletInfo for the newly created wallet.

        Raises:
            UserNotFoundError: If user doesn't exist.
            AuthenticationError: If provider credentials are invalid.
            WalletProviderError: For other API errors.
        """
        ...

    # --------------------------------------------------------
    # Health Check
    # --------------------------------------------------------

    async def health_check(self) -> dict:
        """
        Check provider API health.

        Returns:
            Dict with:
            - status: 'healthy', 'degraded', or 'down'
            - latency_ms: Response time in milliseconds
            - message: Optional status message
        """
        ...

    # --------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------

    async def close(self) -> None:
        """
        Close any open connections.

        Should be called when the application shuts down.
        """
        ...
