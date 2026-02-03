"""
LayerZero Protocol API Client - Stub implementation.

This is a stub that provides the necessary classes for the LayerZeroAdapter.
Actual implementation should use LayerZero Protocol APIs.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from datetime import datetime, UTC
import httpx


@dataclass
class LayerZeroChain:
    """LayerZero supported chain."""

    chain_id: int
    name: str
    endpoint_id: int
    rpc_url: Optional[str] = None


@dataclass
class MessageFeeEstimate:
    """Message fee estimate from API."""

    source_chain_id: int
    dest_chain_id: int
    native_fee: Decimal
    zro_fee: Decimal
    total_fee_usd: Decimal


@dataclass
class CrossChainMessage:
    """Cross-chain message data."""

    tx_hash: str
    source_chain_id: int
    dest_chain_id: int
    nonce: int
    status: str  # "pending", "inflight", "delivered", "failed"
    sender: str
    receiver: str
    payload: Optional[str] = None
    created_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


@dataclass
class OFTTransfer:
    """Omnichain Fungible Token transfer."""

    tx_hash: str
    source_chain_id: int
    dest_chain_id: int
    token_address: str
    amount: Decimal
    sender: str
    recipient: str
    status: str


class LayerZeroClient:
    """
    LayerZero Protocol API client.

    Provides access to cross-chain messaging, fee estimation, and status tracking.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.layerzero.network",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)

    async def get_chains(self) -> List[LayerZeroChain]:
        """Get supported chains."""
        return [
            LayerZeroChain(chain_id=1, name="Ethereum", endpoint_id=101),
            LayerZeroChain(chain_id=137, name="Polygon", endpoint_id=109),
            LayerZeroChain(chain_id=42161, name="Arbitrum", endpoint_id=110),
        ]

    async def estimate_message_fee(
        self,
        source_chain_id: int,
        dest_chain_id: int,
        payload_size: int = 0,
    ) -> MessageFeeEstimate:
        """Estimate message fee."""
        return MessageFeeEstimate(
            source_chain_id=source_chain_id,
            dest_chain_id=dest_chain_id,
            native_fee=Decimal("0.001"),
            zro_fee=Decimal("0"),
            total_fee_usd=Decimal("2.5"),
        )

    async def track_message(self, tx_hash: str) -> CrossChainMessage:
        """Track cross-chain message status."""
        return CrossChainMessage(
            tx_hash=tx_hash,
            source_chain_id=1,
            dest_chain_id=137,
            nonce=1,
            status="pending",
            sender="0x0000000000000000000000000000000000000000",
            receiver="0x0000000000000000000000000000000000000000",
            created_at=datetime.now(UTC),
        )

    async def get_oft_transfer(self, tx_hash: str) -> OFTTransfer:
        """Get OFT transfer details."""
        return OFTTransfer(
            tx_hash=tx_hash,
            source_chain_id=1,
            dest_chain_id=137,
            token_address="0x0000000000000000000000000000000000000000",
            amount=Decimal("100"),
            sender="0x0000000000000000000000000000000000000000",
            recipient="0x0000000000000000000000000000000000000000",
            status="pending",
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
