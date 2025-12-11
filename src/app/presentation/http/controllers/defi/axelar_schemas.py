"""
Axelar Pydantic Schemas.

Request and response models for Axelar API endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities.bridge.axelar_transfer import AxelarTransfer
from app.domain.value_objects.bridge.bridge_route import BridgeRoute
from app.domain.value_objects.bridge.transfer_estimate import TransferEstimate


# =============================================================================
# Response Models
# =============================================================================


class BridgeRouteResponse(BaseModel):
    """Bridge route response model."""

    source_chain: str
    destination_chain: str
    token: str
    estimated_time_seconds: int
    estimated_time_minutes: int
    fee_usd: str
    fee_native: str
    security_score: int
    is_express: bool = False

    @classmethod
    def from_domain(cls, route: BridgeRoute) -> "BridgeRouteResponse":
        """Create from domain value object."""
        return cls(
            source_chain=route.source_chain,
            destination_chain=route.destination_chain,
            token=route.token,
            estimated_time_seconds=route.estimated_time_seconds,
            estimated_time_minutes=route.estimated_time_minutes,
            fee_usd=str(route.fee_usd),
            fee_native=str(route.fee_native),
            security_score=route.security_score,
            is_express=route.is_express,
        )


class RoutesResponse(BaseModel):
    """Routes list response model."""

    routes: list[BridgeRouteResponse]
    count: int


class TransferEstimateResponseModel(BaseModel):
    """Transfer estimate response model."""

    source_chain: str
    destination_chain: str
    token: str
    amount: str
    fee_usd: str
    gas_estimate_usd: str
    total_cost_usd: str
    estimated_time_seconds: int
    estimated_time_minutes: int
    is_express: bool = False

    @classmethod
    def from_domain(cls, estimate: TransferEstimate) -> "TransferEstimateResponseModel":
        """Create from domain value object."""
        return cls(
            source_chain=estimate.source_chain,
            destination_chain=estimate.destination_chain,
            token=estimate.token,
            amount=str(estimate.amount),
            fee_usd=str(estimate.fee_usd),
            gas_estimate_usd=str(estimate.gas_estimate_usd),
            total_cost_usd=str(estimate.total_cost_usd),
            estimated_time_seconds=estimate.estimated_time_seconds,
            estimated_time_minutes=estimate.estimated_time_minutes,
            is_express=estimate.is_express,
        )


class TransferEstimateResponse(BaseModel):
    """Transfer estimate with express option response model."""

    standard: TransferEstimateResponseModel
    express: TransferEstimateResponseModel | None = None
    recommendation: str | None = Field(
        default=None, description="STANDARD or EXPRESS recommendation"
    )


class TransferResponse(BaseModel):
    """Transfer response model."""

    tx_hash: str
    source_chain: str
    destination_chain: str
    token: str
    amount: str
    status: str
    source_tx_hash: str | None = None
    destination_tx_hash: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    is_express: bool = False

    @classmethod
    def from_domain(cls, transfer: AxelarTransfer) -> "TransferResponse":
        """Create from domain entity."""
        return cls(
            tx_hash=transfer.tx_hash,
            source_chain=transfer.source_chain,
            destination_chain=transfer.destination_chain,
            token=transfer.token,
            amount=str(transfer.amount),
            status=transfer.status.value,
            source_tx_hash=transfer.source_tx_hash,
            destination_tx_hash=transfer.destination_tx_hash,
            created_at=transfer.created_at,
            completed_at=transfer.completed_at,
            error_message=transfer.error_message,
            is_express=transfer.is_express,
        )


class TransferTrackingResponse(BaseModel):
    """Transfer tracking response model."""

    transfer: TransferResponse
    progress_pct: int = Field(description="Progress percentage (0-100)")
    next_step: str = Field(description="Human-readable next step")
    estimated_completion: datetime | None = None


class ChainResponse(BaseModel):
    """Chain response model."""

    id: str
    name: str
    chain_id: int


class ChainsResponse(BaseModel):
    """Chains list response model."""

    chains: list[ChainResponse]
    count: int


class TokenResponse(BaseModel):
    """Token response model."""

    symbol: str
    name: str
    decimals: int
    is_axl_wrapped: bool = False


class TokensResponse(BaseModel):
    """Tokens list response model."""

    tokens: list[TokenResponse]
    chain: str
    count: int
