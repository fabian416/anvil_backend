"""
Value object for Authentication Provider.
"""

from dataclasses import dataclass
from enum import Enum

from app.domain.value_objects.base import ValueObject


class AuthProviderType(str, Enum):
    """Supported authentication providers."""
    EMAIL = "email"
    PRIVY = "privy"
    GOOGLE = "google"
    APPLE = "apple"
    TWITTER = "twitter"
    DISCORD = "discord"
    WALLET = "wallet"


@dataclass(frozen=True, slots=True)
class AuthProvider(ValueObject[str]):
    """
    Represents the authentication provider used by the user.
    """
    value: str

    def __post_init__(self) -> None:
        # Validate that the provider is one of the supported types
        valid_providers = [p.value for p in AuthProviderType]
        if self.value and self.value not in valid_providers:
            raise ValueError(f"Invalid auth provider. Must be one of: {valid_providers}")

    @property
    def provider_type(self) -> AuthProviderType | None:
        """Get the provider type enum."""
        if not self.value:
            return None
        return AuthProviderType(self.value)

