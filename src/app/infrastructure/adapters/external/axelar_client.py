"""
Axelar Network API Client - Stub implementation.

This is a stub that provides the necessary classes for the AxelarAdapter.
Actual implementation should use Axelar Network APIs.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from datetime import datetime, UTC
import httpx


@dataclass
class BridgeRoute:
    """Bridge route from API."""
    source_chain: str
    dest_chain: str
    asset: str
    estimated_time_seconds: int
    fee_usd: Decimal
    available: bool


@dataclass
class TransferEstimate:
    """Transfer estimate from API."""
    source_chain: str
    dest_chain: str
    asset: str
    amount: Decimal
    fee: Decimal
    fee_usd: Decimal
    estimated_time_seconds: int
    gas_cost: Decimal


@dataclass
class TransferStatus:
    """Transfer status from API."""
    tx_hash: str
    status: str  # "pending", "processing", "completed", "failed"
    source_chain: str
    dest_chain: str
    source_tx_hash: Optional[str]
    dest_tx_hash: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class CrossChainTransfer:
    """Cross-chain transfer data."""
    tx_hash: str
    source_chain: str
    dest_chain: str
    asset: str
    amount: Decimal
    sender: str
    recipient: str
    status: str


class AxelarClient:
    """
    Axelar Network API client.
    
    Provides access to cross-chain bridge routes, transfers, and status tracking.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.axelar.dev",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get_routes(
        self,
        source_chain: Optional[str] = None,
        dest_chain: Optional[str] = None,
    ) -> List[BridgeRoute]:
        """Get available bridge routes."""
        return []
    
    async def estimate_transfer(
        self,
        source_chain: str,
        dest_chain: str,
        asset: str,
        amount: Decimal,
    ) -> TransferEstimate:
        """Estimate transfer cost and time."""
        return TransferEstimate(
            source_chain=source_chain,
            dest_chain=dest_chain,
            asset=asset,
            amount=amount,
            fee=Decimal("0"),
            fee_usd=Decimal("0"),
            estimated_time_seconds=300,
            gas_cost=Decimal("0"),
        )
    
    async def track_transfer(self, tx_hash: str) -> TransferStatus:
        """Track transfer status."""
        return TransferStatus(
            tx_hash=tx_hash,
            status="pending",
            source_chain="ethereum",
            dest_chain="polygon",
            source_tx_hash=tx_hash,
            dest_tx_hash=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    
    async def get_supported_chains(self) -> List[str]:
        """Get list of supported chains."""
        return ["ethereum", "polygon", "avalanche", "arbitrum", "optimism"]
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
