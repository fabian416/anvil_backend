"""
MoonPay Configuration Settings.

Supports both on-ramp (fiat → crypto) and swap (crypto → crypto) operations.

Environment Variables:
- MOONPAY_API_KEY: Publishable API key (pk_test_... or pk_live_...)
- MOONPAY_SECRET_KEY: Secret key for signing (optional, for webhooks)
- MOONPAY_ENVIRONMENT: "sandbox" or "production"
"""

from pydantic import BaseModel, ConfigDict, Field


class MoonPaySettings(BaseModel):
    """MoonPay API configuration for on-ramp and swap operations."""

    model_config = ConfigDict(populate_by_name=True)

    api_key: str = Field(
        default="",
        alias="MOONPAY_API_KEY",
        description="MoonPay publishable API key (pk_test_... or pk_live_...)",
    )
    secret_key: str = Field(
        default="",
        alias="MOONPAY_SECRET_KEY",
        description="MoonPay secret key for signing webhooks",
    )
    environment: str = Field(
        default="sandbox",
        alias="MOONPAY_ENVIRONMENT",
        description="Environment: 'sandbox' for testing, 'production' for live",
    )

    @property
    def is_configured(self) -> bool:
        """Check if MoonPay is properly configured."""
        return bool(self.api_key)

    @property
    def is_sandbox(self) -> bool:
        """Check if running in sandbox mode."""
        return self.environment == "sandbox"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

