"""
0x Protocol Configuration Settings.

Configuration for 0x Protocol swap integration.

Environment Variables:
- OX_API_KEY: 0x API key for swap quotes and execution
- OX_ENVIRONMENT: "testnet" or "mainnet"
"""

from pydantic import BaseModel, ConfigDict, Field


class OxProtocolSettings(BaseModel):
    """0x Protocol API configuration for swap operations."""

    model_config = ConfigDict(populate_by_name=True)

    api_key: str = Field(
        default="",
        alias="OX_API_KEY",
        description="0x Protocol API key",
    )
    environment: str = Field(
        default="testnet",
        alias="OX_ENVIRONMENT",
        description="Environment: 'testnet' for testing, 'mainnet' for production",
    )

    @property
    def is_configured(self) -> bool:
        """Check if 0x Protocol is properly configured."""
        return bool(self.api_key)

    @property
    def is_testnet(self) -> bool:
        """Check if running in testnet mode."""
        return self.environment == "testnet"

    @property
    def is_mainnet(self) -> bool:
        """Check if running in mainnet mode."""
        return self.environment == "mainnet"
