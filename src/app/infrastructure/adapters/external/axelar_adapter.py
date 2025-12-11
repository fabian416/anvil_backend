"""
Axelar Gateway Adapter.

Implements the AxelarGateway port using the AxelarClient
with caching and express transfer support.
"""

import logging
import re
from datetime import datetime
from decimal import Decimal

from app.domain.entities.bridge.axelar_transfer import AxelarTransfer
from app.domain.exceptions.axelar import AxelarAPIError
from app.domain.ports.axelar_gateway import AxelarGateway
from app.domain.value_objects.bridge.bridge_route import BridgeRoute
from app.domain.value_objects.bridge.transfer_estimate import TransferEstimate
from app.domain.value_objects.bridge.transfer_status import TransferStatus
from app.infrastructure.adapters.external.axelar_client import (
    AxelarClient,
    BridgeRoute as ClientRoute,
    CrossChainTransfer as ClientTransfer,
    TransferEstimate as ClientEstimate,
    TransferStatus as ClientStatus,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache

logger = logging.getLogger(__name__)

# Transaction hash pattern
TX_HASH_PATTERN = re.compile(r"^0x[a-fA-F0-9]{64}$")


class AxelarAdapter(AxelarGateway):
    """
    Axelar implementation of AxelarGateway.

    Uses caching for static data:
    - Routes: 5 minutes
    - Chains: 1 hour
    - Active transfers: 15 seconds
    - Completed transfers: 24 hours
    """

    DEFAULT_ROUTE_CACHE_TTL = 300  # 5 minutes
    DEFAULT_CHAIN_CACHE_TTL = 3600  # 1 hour
    DEFAULT_TRANSFER_CACHE_TTL = 15  # 15 seconds
    DEFAULT_COMPLETED_CACHE_TTL = 86400  # 24 hours

    # Express service parameters
    EXPRESS_FEE_MULTIPLIER = Decimal("2.0")  # 2x fee
    EXPRESS_TIME_DIVISOR = 3  # 3x faster

    def __init__(
        self,
        client: AxelarClient,
        cache: ExternalAPICache,
        route_cache_ttl: int = DEFAULT_ROUTE_CACHE_TTL,
        chain_cache_ttl: int = DEFAULT_CHAIN_CACHE_TTL,
        transfer_cache_ttl: int = DEFAULT_TRANSFER_CACHE_TTL,
        completed_cache_ttl: int = DEFAULT_COMPLETED_CACHE_TTL,
        express_fee_multiplier: Decimal = EXPRESS_FEE_MULTIPLIER,
        express_time_divisor: int = EXPRESS_TIME_DIVISOR,
    ):
        """Initialize AxelarAdapter."""
        self._client = client
        self._cache = cache
        self._route_cache_ttl = route_cache_ttl
        self._chain_cache_ttl = chain_cache_ttl
        self._transfer_cache_ttl = transfer_cache_ttl
        self._completed_cache_ttl = completed_cache_ttl
        self._express_fee_multiplier = express_fee_multiplier
        self._express_time_divisor = express_time_divisor

    async def get_routes(
        self,
        source_chain: str,
        destination_chain: str,
        token: str = "USDC",
    ) -> list[BridgeRoute]:
        """Get available bridge routes with caching."""
        cache_key_params = {
            "src": source_chain.lower(),
            "dst": destination_chain.lower(),
            "token": token.upper(),
        }

        cached = await self._cache.get("axelar", "routes", **cache_key_params)
        if cached:
            return [BridgeRoute.from_dict(r) for r in cached]

        try:
            raw_routes = await self._client.get_bridge_routes(
                source_chain, destination_chain, token
            )
            routes = [self._transform_route(r) for r in raw_routes]

            # Add express route option
            if routes:
                express_route = self._create_express_route(routes[0])
                routes.append(express_route)

            await self._cache.set(
                "axelar",
                "routes",
                [r.to_dict() for r in routes],
                ttl=self._route_cache_ttl,
                **cache_key_params,
            )

            return routes

        except Exception as e:
            logger.error(f"Error getting routes: {e}")
            raise AxelarAPIError(str(e)) from e

    async def estimate_transfer(
        self,
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str,
        express: bool = False,
    ) -> TransferEstimate:
        """Estimate transfer costs."""
        try:
            raw_estimate = await self._client.estimate_transfer(
                source_chain, destination_chain, token, amount
            )
            estimate = self._transform_estimate(raw_estimate)

            # Apply express premium if requested
            if express:
                estimate = self._apply_express_premium(estimate)

            return estimate

        except Exception as e:
            logger.error(f"Error estimating transfer: {e}")
            raise AxelarAPIError(str(e)) from e

    async def track_transfer(
        self,
        tx_hash: str,
    ) -> AxelarTransfer | None:
        """Track transfer status with smart caching."""
        cache_key_params = {"tx_hash": tx_hash.lower()}

        # Check cache
        cached = await self._cache.get("axelar", "transfer", **cache_key_params)
        if cached:
            transfer = AxelarTransfer.from_dict(cached)
            # Return cached completed transfers immediately
            if transfer.status == TransferStatus.EXECUTED:
                return transfer

        try:
            raw = await self._client.get_transfer_status(tx_hash)
            if not raw:
                return None

            transfer = self._transform_transfer(raw)

            # Cache with variable TTL based on status
            ttl = (
                self._completed_cache_ttl
                if transfer.status == TransferStatus.EXECUTED
                else self._transfer_cache_ttl
            )

            await self._cache.set(
                "axelar",
                "transfer",
                transfer.to_dict(),
                ttl=ttl,
                **cache_key_params,
            )

            return transfer

        except Exception as e:
            logger.error(f"Error tracking transfer {tx_hash}: {e}")
            raise AxelarAPIError(str(e)) from e

    async def get_chains(self) -> list[dict]:
        """Get supported chains with caching."""
        cached = await self._cache.get("axelar", "chains")
        if cached:
            return cached

        try:
            chains = await self._client.get_supported_chains()

            await self._cache.set(
                "axelar",
                "chains",
                chains,
                ttl=self._chain_cache_ttl,
            )

            return chains

        except Exception as e:
            logger.error(f"Error getting chains: {e}")
            raise AxelarAPIError(str(e)) from e

    async def get_tokens(
        self,
        chain: str,
    ) -> list[dict]:
        """Get supported tokens for a chain."""
        cache_key_params = {"chain": chain.lower()}

        cached = await self._cache.get("axelar", "tokens", **cache_key_params)
        if cached:
            return cached

        try:
            tokens = await self._client.get_supported_tokens(chain)

            await self._cache.set(
                "axelar",
                "tokens",
                tokens,
                ttl=self._chain_cache_ttl,
                **cache_key_params,
            )

            return tokens

        except Exception as e:
            logger.error(f"Error getting tokens for {chain}: {e}")
            raise AxelarAPIError(str(e)) from e

    # =========================================================================
    # Express Service
    # =========================================================================

    def _apply_express_premium(
        self, estimate: TransferEstimate
    ) -> TransferEstimate:
        """Apply express service premium."""
        return TransferEstimate(
            source_chain=estimate.source_chain,
            destination_chain=estimate.destination_chain,
            token=estimate.token,
            amount=estimate.amount,
            fee_usd=estimate.fee_usd * self._express_fee_multiplier,
            gas_estimate_usd=estimate.gas_estimate_usd,
            total_cost_usd=(
                estimate.fee_usd * self._express_fee_multiplier
                + estimate.gas_estimate_usd
            ),
            estimated_time_seconds=estimate.estimated_time_seconds // self._express_time_divisor,
            is_express=True,
        )

    def _create_express_route(self, standard_route: BridgeRoute) -> BridgeRoute:
        """Create express route from standard route."""
        return BridgeRoute(
            source_chain=standard_route.source_chain,
            destination_chain=standard_route.destination_chain,
            token=standard_route.token,
            estimated_time_seconds=standard_route.estimated_time_seconds // self._express_time_divisor,
            fee_usd=standard_route.fee_usd * self._express_fee_multiplier,
            fee_native=standard_route.fee_native * self._express_fee_multiplier,
            security_score=standard_route.security_score,
            is_express=True,
        )

    # =========================================================================
    # Transformation Methods
    # =========================================================================

    def _transform_route(self, raw: ClientRoute) -> BridgeRoute:
        """Transform client route to domain value object."""
        return BridgeRoute(
            source_chain=raw.source_chain,
            destination_chain=raw.destination_chain,
            token=raw.token,
            estimated_time_seconds=raw.estimated_time_seconds,
            fee_usd=Decimal(str(raw.fee_usd)),
            fee_native=Decimal(str(raw.fee_native)),
            security_score=raw.security_score,
            is_express=False,
        )

    def _transform_estimate(self, raw: ClientEstimate) -> TransferEstimate:
        """Transform client estimate to domain value object."""
        return TransferEstimate(
            source_chain=raw.source_chain,
            destination_chain=raw.destination_chain,
            token=raw.token,
            amount=Decimal(str(raw.amount)),
            fee_usd=Decimal(str(raw.fee_usd)),
            gas_estimate_usd=Decimal(str(raw.gas_estimate_usd)),
            total_cost_usd=Decimal(str(raw.total_cost_usd)),
            estimated_time_seconds=raw.estimated_time_seconds,
            is_express=False,
        )

    def _transform_transfer(self, raw: ClientTransfer) -> AxelarTransfer:
        """Transform client transfer to domain entity."""
        status_map = {
            ClientStatus.PENDING: TransferStatus.PENDING,
            ClientStatus.CONFIRMED: TransferStatus.CONFIRMED,
            ClientStatus.EXECUTING: TransferStatus.EXECUTING,
            ClientStatus.EXECUTED: TransferStatus.EXECUTED,
            ClientStatus.FAILED: TransferStatus.FAILED,
        }

        return AxelarTransfer(
            tx_hash=raw.tx_hash,
            source_chain=raw.source_chain,
            destination_chain=raw.destination_chain,
            token=raw.token,
            amount=Decimal(str(raw.amount)),
            status=status_map.get(raw.status, TransferStatus.PENDING),
            source_tx_hash=raw.source_tx_hash,
            destination_tx_hash=raw.destination_tx_hash,
            created_at=raw.created_at,
            completed_at=raw.completed_at,
            error_message=raw.error_message,
            is_express=False,  # Would need to determine from transfer data
        )
