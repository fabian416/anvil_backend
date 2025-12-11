"""
Axelar Gateway Port.

Defines the domain interface for Axelar cross-chain bridging operations.
"""

from decimal import Decimal
from typing import Protocol

from app.domain.entities.bridge.axelar_transfer import AxelarTransfer
from app.domain.value_objects.bridge.bridge_route import BridgeRoute
from app.domain.value_objects.bridge.transfer_estimate import TransferEstimate


class AxelarGateway(Protocol):
    """
    Port interface for Axelar operations.

    This protocol defines the contract for cross-chain
    bridging and transfer tracking.
    """

    async def get_routes(
        self,
        source_chain: str,
        destination_chain: str,
        token: str = "USDC",
    ) -> list[BridgeRoute]:
        """
        Get available bridge routes.

        Args:
            source_chain: Source blockchain
            destination_chain: Destination blockchain
            token: Token to bridge

        Returns:
            List of BridgeRoute value objects
        """
        ...

    async def estimate_transfer(
        self,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str,
        express: bool = False,
    ) -> TransferEstimate:
        """
        Estimate transfer costs.

        Args:
            source_chain: Source blockchain
            destination_chain: Destination blockchain
            token: Token to bridge
            amount: Amount to transfer
            express: Use express service for faster transfer

        Returns:
            TransferEstimate value object
        """
        ...

    async def track_transfer(
        self,
        tx_hash: str,
    ) -> AxelarTransfer | None:
        """
        Track transfer status.

        Args:
            tx_hash: Source chain transaction hash

        Returns:
            AxelarTransfer entity or None if not found
        """
        ...

    async def get_chains(self) -> list[dict]:
        """
        Get supported chains.

        Returns:
            List of chain information
        """
        ...

    async def get_tokens(
        self,
        chain: str,
    ) -> list[dict]:
        """
        Get supported tokens for a chain.

        Args:
            chain: Chain identifier

        Returns:
            List of token information
        """
        ...
