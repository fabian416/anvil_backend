"""
Execute action request/response schemas.

Schemas for the execute endpoint that allows users to execute
recommendations from chat (swaps, deposits, withdrawals, etc.).
"""

from datetime import datetime, UTC
from typing import Optional, List, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ActionType(str, Enum):
    """Types of executable actions."""

    SWAP = "swap"
    SWAP_MOONPAY = "swap_moonpay"  # MoonPay crypto-to-crypto swap (via Privy)
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    APPROVE = "approve"
    TRANSFER = "transfer"
    BRIDGE = "bridge"


class ActionStatus(str, Enum):
    """Status of an executed action."""

    PENDING = "pending"
    SIMULATING = "simulating"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    CONFIRMED = "confirmed"
    AWAITING_SIGNING = (
        "awaiting_signing"  # Transaction ready, waiting for Privy signing
    )
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ExecuteActionRequest(BaseModel):
    """Request to execute a recommended action."""

    action_type: ActionType = Field(
        ...,
        description="Type of action to execute: swap, deposit, withdraw, approve, transfer, bridge",
    )

    # Common fields
    chain: str = Field(
        default="base",
        description="Blockchain to execute on: ethereum, base, arbitrum, polygon",
    )

    # Token fields (for swap, transfer, approve)
    from_token: Optional[str] = Field(
        default=None,
        description="Source token symbol or address (for swap/transfer)",
    )
    to_token: Optional[str] = Field(
        default=None,
        description="Destination token symbol (for swap)",
    )
    amount: Optional[str] = Field(
        default=None,
        description="Amount to swap/deposit/withdraw/transfer (human readable)",
    )

    # Protocol fields (for deposit, withdraw)
    protocol: Optional[str] = Field(
        default=None,
        description="Protocol name: morpho, aave, compound",
    )
    vault_address: Optional[str] = Field(
        default=None,
        description="Vault address (for Morpho deposits)",
    )

    # Transfer fields
    recipient: Optional[str] = Field(
        default=None,
        description="Recipient address (for transfer)",
    )

    # Swap fields
    slippage: Optional[float] = Field(
        default=1.0,
        ge=0.1,
        le=50.0,
        description="Slippage tolerance in percent (default: 1%)",
    )
    to_chain: Optional[str] = Field(
        default=None,
        description="Destination chain (for cross-chain swap/bridge)",
    )

    # Confirmation
    confirmed: bool = Field(
        default=False,
        description="User has confirmed the action (required for execution)",
    )

    # Reference to previous message
    reference_message_id: Optional[UUID] = Field(
        default=None,
        description="Reference to the chat message with the recommendation",
    )

    # Language for response
    language: Optional[str] = Field(
        default="en",
        description="Response language code: en, es, fr, zh, pt",
        pattern="^(en|es|fr|zh|pt)$",
    )


class TransactionDetails(BaseModel):
    """Details of a blockchain transaction."""

    hash: Optional[str] = Field(
        default=None, description="Transaction hash (after execution)"
    )
    chain: str = Field(..., description="Blockchain")
    from_address: str = Field(..., description="Sender address")
    to_address: str = Field(..., description="Contract/recipient address")
    value: str = Field(default="0", description="ETH value sent")
    gas_used: Optional[int] = Field(default=None, description="Gas used")
    gas_price: Optional[str] = Field(default=None, description="Gas price in gwei")
    status: ActionStatus = Field(..., description="Transaction status")
    block_number: Optional[int] = Field(default=None, description="Block number")
    timestamp: Optional[datetime] = Field(
        default=None, description="Transaction timestamp"
    )
    explorer_url: Optional[str] = Field(default=None, description="Block explorer URL")

    # Transaction data for Privy signing (when confirmed but not yet signed)
    data: Optional[str] = Field(
        default=None,
        description="Transaction calldata (hex) - for Privy signing in frontend",
    )
    gas_limit: Optional[int] = Field(
        default=None, description="Gas limit for the transaction"
    )
    nonce: Optional[int] = Field(default=None, description="Transaction nonce")


class SimulationResult(BaseModel):
    """Result of transaction simulation."""

    success: bool = Field(..., description="Whether simulation succeeded")
    estimated_gas: int = Field(..., description="Estimated gas units")
    estimated_gas_usd: float = Field(..., description="Estimated gas cost in USD")
    output_amount: Optional[str] = Field(
        default=None, description="Expected output amount"
    )
    price_impact: Optional[float] = Field(
        default=None, description="Price impact percent"
    )
    warnings: List[str] = Field(default_factory=list, description="Simulation warnings")
    errors: List[str] = Field(default_factory=list, description="Simulation errors")


class ExecuteActionResponse(BaseModel):
    """Response from execute action endpoint."""

    action_id: UUID = Field(..., description="Unique action ID")
    action_type: ActionType = Field(..., description="Type of action")
    status: ActionStatus = Field(..., description="Current status")

    # Confirmation required
    requires_confirmation: bool = Field(
        default=True,
        description="Whether user confirmation is required",
    )
    confirmation_message: Optional[str] = Field(
        default=None,
        description="Message to display for user confirmation",
    )

    # Simulation (before confirmation)
    simulation: Optional[SimulationResult] = Field(
        default=None,
        description="Simulation result (before execution)",
    )

    # Transaction (after execution)
    transaction: Optional[TransactionDetails] = Field(
        default=None,
        description="Transaction details (after execution)",
    )

    # Summary
    summary: str = Field(..., description="Human-readable summary")

    # Enrichment data
    enrichment: Optional[dict] = Field(
        default=None,
        description="Additional context-specific data",
    )

    # Timing
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the action expires (for confirmation)",
    )

    model_config = ConfigDict(from_attributes=True)
