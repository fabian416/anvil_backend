"""
Privy Configuration Settings
"""

from pydantic import BaseModel, Field, ConfigDict


class PrivySettings(BaseModel):
    """Privy API configuration for wallet operations."""

    model_config = ConfigDict(populate_by_name=True)

    app_id: str = Field(..., alias="APP_ID", description="Privy App ID")
    app_secret: str = Field(default="", alias="APP_SECRET", description="Privy App Secret")
    api_base_url: str = Field(
        default="https://api.privy.io",
        alias="API_BASE_URL",
        description="Privy API base URL",
    )

    @property
    def basic_auth_credentials(self) -> str:
        """Returns base64-encoded Basic Auth credentials."""
        import base64

        credentials = f"{self.app_id}:{self.app_secret}"
        return base64.b64encode(credentials.encode()).decode()

