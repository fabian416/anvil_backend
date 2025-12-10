"""
Transaction Confirmation Worker Configuration.

Settings for the background worker that monitors and confirms
pending blockchain transactions.
"""

from pydantic import BaseModel, ConfigDict, Field


class TransactionConfirmationSettings(BaseModel):
    """Configuration for Transaction Confirmation Worker."""

    model_config = ConfigDict(populate_by_name=True)

    # Network mode
    use_testnet: bool = Field(
        default=True,
        alias="USE_TESTNET",
        description="Use testnet RPC endpoints (Sepolia, Base Sepolia). "
        "Set to False for mainnet in production.",
    )

    # Batch processing
    interval_seconds: int = Field(
        default=30,
        alias="INTERVAL_SECONDS",
        description="Seconds between processing batches in loop mode.",
    )

    batch_limit: int = Field(
        default=50,
        alias="BATCH_LIMIT",
        description="Maximum number of transactions to process per batch.",
    )

    older_than_seconds: int = Field(
        default=10,
        alias="OLDER_THAN_SECONDS",
        description="Only process transactions older than this.",
    )

    # HTTP settings
    http_timeout: int = Field(
        default=30,
        alias="HTTP_TIMEOUT",
        description="Timeout for RPC HTTP requests in seconds.",
    )

    # Worker mode
    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="Enable or disable the confirmation worker.",
    )
