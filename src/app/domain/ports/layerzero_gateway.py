"""
LayerZero Gateway Port.

Defines the domain interface for LayerZero cross-chain operations.
"""

from decimal import Decimal
from typing import Protocol

from app.domain.entities.cross_chain.lz_message import LZMessage
from app.domain.entities.cross_chain.oft_transfer import OFTTransfer
from app.domain.value_objects.cross_chain.lz_chain import LZChain
from app.domain.value_objects.cross_chain.message_fee import MessageFee


class LayerZeroGateway(Protocol):
    """
    Port interface for LayerZero operations.

    This protocol defines the contract for tracking
    cross-chain messages and OFT transfers.
    """

    async def track_message(
        self,
        tx_hash: str,
    ) -> LZMessage | None:
        """
        Track message by source transaction hash.

        Args:
            tx_hash: Source chain transaction hash

        Returns:
            LZMessage entity or None if not found
        """
        ...

    async def get_message_history(
        self,
        address: str,
        limit: int = 50,
    ) -> list[LZMessage]:
        """
        Get message history for an address.

        Args:
            address: Wallet or contract address
            limit: Maximum messages to return

        Returns:
            List of LZMessage entities
        """
        ...

    async def get_chains(self) -> list[LZChain]:
        """
        Get supported LayerZero chains.

        Returns:
            List of LZChain value objects
        """
        ...

    async def estimate_fees(
        self,
        source_chain: str,
        destination_chain: str,
        payload_size: int = 100,
    ) -> MessageFee:
        """
        Estimate message fees.

        Args:
            source_chain: Source chain name
            destination_chain: Destination chain name
            payload_size: Approximate payload size in bytes

        Returns:
            MessageFee value object
        """
        ...

    async def get_oft_transfers(
        self,
        address: str,
        limit: int = 50,
    ) -> list[OFTTransfer]:
        """
        Get OFT transfers for an address.

        Args:
            address: Wallet address
            limit: Maximum transfers to return

        Returns:
            List of OFTTransfer entities
        """
        ...
