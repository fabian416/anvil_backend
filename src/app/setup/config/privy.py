"""
Privy Configuration Settings

Includes wallet source mode configuration for offline-capable behavior:
- privy: Prefer Privy API, use DB as cache/analytics store
- hybrid: Use Privy when available, but always persist & read from DB
- local: Do not call Privy at all; rely entirely on DB (offline/air-gapped mode)
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class WalletSourceMode(str, Enum):
    """
    Wallet data source mode configuration.

    Controls how the backend fetches and stores wallet data:
    - PRIVY: Primary source is Privy API; DB used for caching/analytics
    - HYBRID: Use Privy when available, always persist to DB; tolerate outages
    - LOCAL: No Privy calls; DB-only mode for offline/air-gapped environments
    """

    PRIVY = "privy"
    HYBRID = "hybrid"
    LOCAL = "local"


class PrivySettings(BaseModel):
    """Privy API configuration for wallet operations."""

    model_config = ConfigDict(populate_by_name=True)

    app_id: str = Field(..., alias="APP_ID", description="Privy App ID")
    client_id: str = Field(
        default="", alias="CLIENT_ID", description="Privy Client ID (for frontend SDK)"
    )
    app_secret: str = Field(
        default="", alias="APP_SECRET", description="Privy App Secret"
    )
    api_base_url: str = Field(
        default="https://api.privy.io",
        alias="API_BASE_URL",
        description="Privy API base URL",
    )

    # Wallet source mode configuration
    wallets_source_mode: WalletSourceMode = Field(
        default=WalletSourceMode.HYBRID,
        alias="WALLETS_SOURCE_MODE",
        description=(
            "Controls wallet data sourcing behavior: "
            "'privy' = prefer Privy API, DB as cache; "
            "'hybrid' = use Privy when available, always persist to DB; "
            "'local' = DB-only mode for offline environments"
        ),
    )

    @property
    def basic_auth_credentials(self) -> str:
        """Returns base64-encoded Basic Auth credentials."""
        import base64

        credentials = f"{self.app_id}:{self.app_secret}"
        return base64.b64encode(credentials.encode()).decode()

    @property
    def is_offline_mode(self) -> bool:
        """Check if operating in local/offline mode."""
        return self.wallets_source_mode == WalletSourceMode.LOCAL

    @property
    def should_call_privy(self) -> bool:
        """Check if Privy API calls should be made."""
        return self.wallets_source_mode in (
            WalletSourceMode.PRIVY,
            WalletSourceMode.HYBRID,
        )

    @property
    def should_persist_to_db(self) -> bool:
        """Check if wallet data should always be persisted to DB."""
        return self.wallets_source_mode in (
            WalletSourceMode.HYBRID,
            WalletSourceMode.LOCAL,
        )
