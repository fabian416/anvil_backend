"""
Wallet Ports Module.

Provides abstract interfaces for wallet providers and wallet persistence.
These ports allow switching between different embedded wallet providers
(e.g., Privy, Dynamic, Turnkey) without changing the application logic.
"""

from app.domain.ports.wallet.embedded_wallet_provider import (
    EmbeddedWalletProviderPort,
    WalletInfo,
    UserInfo,
    TokenVerificationResult,
    WalletListResult,
    WalletProviderError,
    WalletNotFoundError,
    AuthenticationError,
    TokenVerificationError,
    RateLimitError,
)
from app.domain.ports.wallet.wallet_repository import WalletRepository

__all__ = [
    # Embedded Wallet Provider
    "EmbeddedWalletProviderPort",
    "WalletInfo",
    "UserInfo",
    "TokenVerificationResult",
    "WalletListResult",
    "WalletProviderError",
    "WalletNotFoundError",
    "AuthenticationError",
    "TokenVerificationError",
    "RateLimitError",
    # Wallet Repository
    "WalletRepository",
]
