"""
LayerZero Pydantic Schemas.

Request and response models for LayerZero API endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities.cross_chain.lz_message import LZMessage
from app.domain.entities.cross_chain.oft_transfer import OFTTransfer
from app.domain.value_objects.cross_chain.lz_chain import LZChain
from app.domain.value_objects.cross_chain.message_fee import MessageFee


# =============================================================================
# Response Models
# =============================================================================


class LZMessageResponse(BaseModel):
    """Message response model."""

    src_tx_hash: str
    src_chain_id: int
    dst_chain_id: int
    status: str
    src_address: str
    dst_address: str
    dst_tx_hash: str | None = None
    message_type: str
    created_at: datetime
    completed_at: datetime | None = None
    nonce: int | None = None

    @classmethod
    def from_domain(cls, msg: LZMessage) -> "LZMessageResponse":
        """Create from domain entity."""
        return cls(
            src_tx_hash=msg.src_tx_hash,
            src_chain_id=msg.src_chain_id,
            dst_chain_id=msg.dst_chain_id,
            status=msg.status.value,
            src_address=msg.src_address,
            dst_address=msg.dst_address,
            dst_tx_hash=msg.dst_tx_hash,
            message_type=msg.message_type,
            created_at=msg.created_at,
            completed_at=msg.completed_at,
            nonce=msg.nonce,
        )


class MessageTrackingResponse(BaseModel):
    """Message tracking response model."""

    message: LZMessageResponse
    progress_pct: int = Field(description="Progress percentage (0-100)")
    estimated_completion: datetime | None = Field(
        default=None, description="Estimated completion time"
    )


class MessageHistoryResponse(BaseModel):
    """Message history response model."""

    messages: list[LZMessageResponse]
    total_count: int
    pending_count: int
    delivered_count: int


class LZChainResponse(BaseModel):
    """Chain response model."""

    endpoint_id: int
    name: str
    network: str
    native_chain_id: int
    is_evm: bool = True

    @classmethod
    def from_domain(cls, chain: LZChain) -> "LZChainResponse":
        """Create from domain value object."""
        return cls(
            endpoint_id=chain.endpoint_id,
            name=chain.name,
            network=chain.network,
            native_chain_id=chain.native_chain_id,
            is_evm=chain.is_evm,
        )


class ChainsResponse(BaseModel):
    """Chains list response model."""

    chains: list[LZChainResponse]
    evm_chains: list[LZChainResponse]
    non_evm_chains: list[LZChainResponse]


class FeeEstimateResponse(BaseModel):
    """Fee estimate response model."""

    source_chain_id: int
    destination_chain_id: int
    native_fee: str
    native_fee_usd: str
    zro_fee: str | None = None
    total_fee_usd: str

    @classmethod
    def from_domain(cls, fee: MessageFee) -> "FeeEstimateResponse":
        """Create from domain value object."""
        return cls(
            source_chain_id=fee.source_chain_id,
            destination_chain_id=fee.destination_chain_id,
            native_fee=str(fee.native_fee),
            native_fee_usd=str(fee.native_fee_usd),
            zro_fee=str(fee.zro_fee) if fee.zro_fee else None,
            total_fee_usd=str(fee.total_fee_usd),
        )


class OFTTransferResponse(BaseModel):
    """OFT transfer response model."""

    tx_hash: str
    src_chain_id: int
    dst_chain_id: int
    token_address: str
    token_symbol: str
    amount: str
    from_address: str
    to_address: str
    status: str
    timestamp: datetime

    @classmethod
    def from_domain(cls, transfer: OFTTransfer) -> "OFTTransferResponse":
        """Create from domain entity."""
        return cls(
            tx_hash=transfer.tx_hash,
            src_chain_id=transfer.src_chain_id,
            dst_chain_id=transfer.dst_chain_id,
            token_address=transfer.token_address,
            token_symbol=transfer.token_symbol,
            amount=str(transfer.amount),
            from_address=transfer.from_address,
            to_address=transfer.to_address,
            status=transfer.status.value,
            timestamp=transfer.timestamp,
        )


class OFTTransfersSummaryResponse(BaseModel):
    """OFT transfers summary response model."""

    total_transfers: int
    pending_count: int
    completed_count: int
    total_volume: str


class OFTTransfersResponse(BaseModel):
    """OFT transfers list response model."""

    transfers: list[OFTTransferResponse]
    summary: OFTTransfersSummaryResponse
