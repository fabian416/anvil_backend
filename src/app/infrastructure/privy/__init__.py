"""
Privy Infrastructure Module.

Provides adapters for Privy wallet and user operations.
Implements EmbeddedWalletProviderPort for easy provider switching.

To switch to another provider (e.g., Dynamic, Turnkey):
1. Create a new module in infrastructure/wallet_providers/<provider>/
2. Implement EmbeddedWalletProviderPort interface
3. Update dependency injection in setup/providers.py

Usage:
    from app.infrastructure.privy import PrivyClient
    from app.setup.config.privy import PrivySettings

    settings = PrivySettings(APP_ID="xxx", APP_SECRET="yyy")
    client = PrivyClient(settings)

    # Verify token
    result = await client.verify_token(access_token)

    # Get user's wallets
    wallets = await client.list_user_wallets(user_id)

    await client.close()
"""

from app.infrastructure.privy.client import (
    PrivyClient,
    WalletExportResponse,
    PrivyClientError,
    PrivyAuthenticationError,
    PrivyWalletNotFoundError,
    PrivyUserNotFoundError,
    PrivyRateLimitError,
)
from app.infrastructure.privy.hpke import HPKEDecryptor, HPKEKeyPair

__all__ = [
    # Main client
    "PrivyClient",
    # HPKE utilities
    "HPKEDecryptor",
    "HPKEKeyPair",
    # DTOs
    "WalletExportResponse",
    # Exceptions
    "PrivyClientError",
    "PrivyAuthenticationError",
    "PrivyWalletNotFoundError",
    "PrivyUserNotFoundError",
    "PrivyRateLimitError",
]
