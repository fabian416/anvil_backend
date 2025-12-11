"""
LayerZero Gateway Adapter.

Implements the LayerZeroGateway port using the LayerZeroClient
with smart caching based on message status.
"""

import logging
import re
from datetime import datetime
from decimal import Decimal

from app.domain.entities.cross_chain.lz_message import LZMessage
from app.domain.entities.cross_chain.oft_transfer import OFTTransfer
from app.domain.exceptions.layerzero import (
    InvalidTxHashError,
    LayerZeroAPIError,
)
from app.domain.ports.layerzero_gateway import LayerZeroGateway
from app.domain.value_objects.cross_chain.lz_chain import LZChain
from app.domain.value_objects.cross_chain.message_fee import MessageFee
from app.domain.value_objects.cross_chain.message_status import MessageStatus
from app.infrastructure.adapters.external.layerzero_client import (
    CrossChainMessage,
    LayerZeroChain as ClientChain,
    LayerZeroClient,
    MessageFeeEstimate as ClientFee,
    OFTTransfer as ClientOFT,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache

logger = logging.getLogger(__name__)

# Transaction hash pattern
TX_HASH_PATTERN = re.compile(r"^0x[a-fA-F0-9]{64}$")


class LayerZeroAdapter(LayerZeroGateway):
    """
    LayerZero implementation of LayerZeroGateway.

    Uses variable TTL caching:
    - DELIVERED messages: 24h (permanent)
    - INFLIGHT messages: 10s (fast refresh)
    - Chains: 1h (static data)
    """

    DEFAULT_CHAIN_CACHE_TTL = 3600  # 1 hour
    DEFAULT_MESSAGE_CACHE_TTL = 10  # 10 seconds
    DEFAULT_DELIVERED_CACHE_TTL = 86400  # 24 hours
    DEFAULT_FEE_CACHE_TTL = 30  # 30 seconds
    DEFAULT_HISTORY_CACHE_TTL = 60  # 1 minute

    def __init__(
        self,
        client: LayerZeroClient,
        cache: ExternalAPICache,
        chain_cache_ttl: int = DEFAULT_CHAIN_CACHE_TTL,
        message_cache_ttl: int = DEFAULT_MESSAGE_CACHE_TTL,
        delivered_cache_ttl: int = DEFAULT_DELIVERED_CACHE_TTL,
        fee_cache_ttl: int = DEFAULT_FEE_CACHE_TTL,
        history_cache_ttl: int = DEFAULT_HISTORY_CACHE_TTL,
    ):
        """Initialize LayerZeroAdapter."""
        self._client = client
        self._cache = cache
        self._chain_cache_ttl = chain_cache_ttl
        self._message_cache_ttl = message_cache_ttl
        self._delivered_cache_ttl = delivered_cache_ttl
        self._fee_cache_ttl = fee_cache_ttl
        self._history_cache_ttl = history_cache_ttl

    async def track_message(
        self,
        tx_hash: str,
    ) -> LZMessage | None:
        """Track message with smart caching."""
        if not TX_HASH_PATTERN.match(tx_hash):
            raise InvalidTxHashError(tx_hash)

        cache_key_params = {"tx_hash": tx_hash.lower()}

        # Check cache first
        cached = await self._cache.get("layerzero", "message", **cache_key_params)
        if cached:
            msg = LZMessage.from_dict(cached)
            # Return cached DELIVERED messages immediately
            if msg.status == MessageStatus.DELIVERED:
                return msg

        try:
            raw = await self._client.get_message_status(tx_hash)
            if not raw:
                return None

            message = self._transform_message(raw)

            # Cache with variable TTL based on status
            ttl = (
                self._delivered_cache_ttl
                if message.status == MessageStatus.DELIVERED
                else self._message_cache_ttl
            )

            await self._cache.set(
                "layerzero",
                "message",
                message.to_dict(),
                ttl=ttl,
                **cache_key_params,
            )

            return message

        except Exception as e:
            logger.error(f"Error tracking message {tx_hash}: {e}")
            raise LayerZeroAPIError(str(e)) from e

    async def get_message_history(
        self,
        address: str,
        limit: int = 50,
    ) -> list[LZMessage]:
        """Get message history for an address."""
        cache_key_params = {"address": address.lower(), "limit": limit}

        cached = await self._cache.get("layerzero", "history", **cache_key_params)
        if cached:
            return [LZMessage.from_dict(m) for m in cached]

        try:
            raw_messages = await self._client.get_messages_by_address(address, limit)
            messages = [self._transform_message(m) for m in raw_messages]

            await self._cache.set(
                "layerzero",
                "history",
                [m.to_dict() for m in messages],
                ttl=self._history_cache_ttl,
                **cache_key_params,
            )

            return messages

        except Exception as e:
            logger.error(f"Error getting history for {address}: {e}")
            raise LayerZeroAPIError(str(e)) from e

    async def get_chains(self) -> list[LZChain]:
        """Get supported chains with caching."""
        cached = await self._cache.get("layerzero", "chains")
        if cached:
            return [LZChain.from_dict(c) for c in cached]

        try:
            raw_chains = await self._client.get_supported_chains()
            chains = [self._transform_chain(c) for c in raw_chains]

            await self._cache.set(
                "layerzero",
                "chains",
                [c.to_dict() for c in chains],
                ttl=self._chain_cache_ttl,
            )

            return chains

        except Exception as e:
            logger.error(f"Error getting chains: {e}")
            raise LayerZeroAPIError(str(e)) from e

    async def estimate_fees(
        self,
        source_chain: str,
        destination_chain: str,
        payload_size: int = 100,
    ) -> MessageFee:
        """Estimate message fees with caching."""
        cache_key_params = {
            "src": source_chain.lower(),
            "dst": destination_chain.lower(),
            "size": payload_size,
        }

        cached = await self._cache.get("layerzero", "fees", **cache_key_params)
        if cached:
            return MessageFee.from_dict(cached)

        try:
            raw_fee = await self._client.estimate_fees(
                source_chain, destination_chain, payload_size
            )
            fee = self._transform_fee(raw_fee)

            await self._cache.set(
                "layerzero",
                "fees",
                fee.to_dict(),
                ttl=self._fee_cache_ttl,
                **cache_key_params,
            )

            return fee

        except Exception as e:
            logger.error(f"Error estimating fees: {e}")
            raise LayerZeroAPIError(str(e)) from e

    async def get_oft_transfers(
        self,
        address: str,
        limit: int = 50,
    ) -> list[OFTTransfer]:
        """Get OFT transfers for an address."""
        cache_key_params = {"address": address.lower(), "limit": limit}

        cached = await self._cache.get("layerzero", "oft_transfers", **cache_key_params)
        if cached:
            return [OFTTransfer.from_dict(t) for t in cached]

        try:
            raw_transfers = await self._client.get_oft_transfers(address, limit)
            transfers = [self._transform_oft(t) for t in raw_transfers]

            await self._cache.set(
                "layerzero",
                "oft_transfers",
                [t.to_dict() for t in transfers],
                ttl=self._history_cache_ttl,
                **cache_key_params,
            )

            return transfers

        except Exception as e:
            logger.error(f"Error getting OFT transfers for {address}: {e}")
            raise LayerZeroAPIError(str(e)) from e

    # =========================================================================
    # Transformation Methods
    # =========================================================================

    def _transform_message(self, raw: CrossChainMessage) -> LZMessage:
        """Transform client message to domain entity."""
        return LZMessage(
            src_tx_hash=raw.src_tx_hash,
            src_chain_id=raw.src_chain_id,
            dst_chain_id=raw.dst_chain_id,
            status=MessageStatus(raw.status.value),
            src_address=raw.src_ua_address,
            dst_address=raw.dst_ua_address,
            dst_tx_hash=raw.dst_tx_hash,
            message_type=raw.message_type.value,
            created_at=raw.src_block_timestamp,
            completed_at=raw.dst_block_timestamp,
            nonce=raw.nonce,
        )

    def _transform_chain(self, raw: ClientChain) -> LZChain:
        """Transform client chain to domain value object."""
        return LZChain(
            endpoint_id=raw.chain_id,
            name=raw.name,
            network=raw.network,
            native_chain_id=raw.native_chain_id,
            is_evm=True,  # All current chains are EVM
        )

    def _transform_fee(self, raw: ClientFee) -> MessageFee:
        """Transform client fee to domain value object."""
        zro_fee = None
        if raw.zro_fee:
            zro_fee = Decimal(str(raw.zro_fee))

        return MessageFee(
            source_chain_id=raw.source_chain_id,
            destination_chain_id=raw.destination_chain_id,
            native_fee=Decimal(str(raw.native_fee)),
            native_fee_usd=Decimal(str(raw.native_fee_usd)),
            zro_fee=zro_fee,
        )

    def _transform_oft(self, raw: ClientOFT) -> OFTTransfer:
        """Transform client OFT to domain entity."""
        return OFTTransfer(
            tx_hash=raw.tx_hash,
            src_chain_id=raw.src_chain_id,
            dst_chain_id=raw.dst_chain_id,
            token_address=raw.token_address,
            token_symbol=raw.token_symbol,
            amount=Decimal(str(raw.amount)),
            from_address=raw.from_address,
            to_address=raw.to_address,
            status=MessageStatus(raw.status.value),
            timestamp=raw.timestamp,
        )
