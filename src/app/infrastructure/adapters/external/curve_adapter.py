"""
Curve Finance Gateway Adapter.

Implements the CurveGateway port using the existing CurveClient
with caching support via ExternalAPICache.
"""

import logging
from decimal import Decimal

from app.domain.entities.curve.gauge import Gauge
from app.domain.entities.curve.pool import Pool
from app.domain.exceptions.curve import (
    CurveAPIError,
    PoolNotFoundError,
)
from app.domain.ports.curve_gateway import CurveGateway
from app.domain.value_objects.curve.pool_apy import PoolAPY
from app.domain.value_objects.curve.swap_quote import SwapQuote
from app.domain.value_objects.curve.tvl_data import TVLData
from app.infrastructure.adapters.external.curve_client import (
    CurveClient,
    CurvePool,
    GaugeData,
    PoolAPY as ClientPoolAPY,
    SwapQuote as ClientSwapQuote,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache

logger = logging.getLogger(__name__)


class CurveAdapter(CurveGateway):
    """
    Curve Finance implementation of CurveGateway.

    This adapter bridges the domain port to the infrastructure client,
    handling:
    - Data transformation from client models to domain entities
    - Caching with configurable TTLs
    - Error mapping from API errors to domain exceptions
    """

    # Cache TTL defaults (in seconds)
    DEFAULT_POOL_CACHE_TTL = 300  # 5 minutes
    DEFAULT_APY_CACHE_TTL = 60  # 1 minute
    DEFAULT_GAUGE_CACHE_TTL = 600  # 10 minutes
    DEFAULT_TVL_CACHE_TTL = 300  # 5 minutes

    def __init__(
        self,
        client: CurveClient,
        cache: ExternalAPICache,
        pool_cache_ttl: int = DEFAULT_POOL_CACHE_TTL,
        apy_cache_ttl: int = DEFAULT_APY_CACHE_TTL,
        gauge_cache_ttl: int = DEFAULT_GAUGE_CACHE_TTL,
        tvl_cache_ttl: int = DEFAULT_TVL_CACHE_TTL,
    ):
        """
        Initialize CurveAdapter.

        Args:
            client: CurveClient for API communication
            cache: ExternalAPICache for caching responses
            pool_cache_ttl: Cache TTL for pool data (default: 5 min)
            apy_cache_ttl: Cache TTL for APY data (default: 1 min)
            gauge_cache_ttl: Cache TTL for gauge data (default: 10 min)
            tvl_cache_ttl: Cache TTL for TVL data (default: 5 min)
        """
        self._client = client
        self._cache = cache
        self._pool_cache_ttl = pool_cache_ttl
        self._apy_cache_ttl = apy_cache_ttl
        self._gauge_cache_ttl = gauge_cache_ttl
        self._tvl_cache_ttl = tvl_cache_ttl

    async def get_pools(self, chain: str = "ethereum") -> list[Pool]:
        """Get all pools with caching."""
        cache_key_params = {"chain": chain}

        # Try cache first
        cached = await self._cache.get("curve", "pools", **cache_key_params)
        if cached:
            logger.debug(f"Cache hit for Curve pools on {chain}")
            return [Pool.from_dict(p) for p in cached]

        # Fetch from API
        try:
            # Create a new client for the specific chain if needed
            if self._client._chain != chain:
                temp_client = CurveClient(chain=chain)
                try:
                    raw_pools = await temp_client.get_pools()
                finally:
                    await temp_client.close()
            else:
                raw_pools = await self._client.get_pools()

            # Transform to domain entities
            pools = [self._transform_pool(p, chain) for p in raw_pools]

            # Cache the result
            await self._cache.set(
                "curve",
                "pools",
                [p.to_dict() for p in pools],
                ttl=self._pool_cache_ttl,
                **cache_key_params,
            )

            logger.debug(f"Fetched {len(pools)} Curve pools on {chain}")
            return pools

        except Exception as e:
            logger.error(f"Error fetching Curve pools: {e}")
            raise CurveAPIError(str(e)) from e

    async def get_pool_by_address(
        self,
        pool_address: str,
        chain: str = "ethereum",
    ) -> Pool:
        """Get a specific pool by address."""
        pools = await self.get_pools(chain=chain)

        for pool in pools:
            if pool.id.lower() == pool_address.lower():
                return pool

        raise PoolNotFoundError(pool_address, chain)

    async def get_pool_apy(
        self,
        pool_address: str,
        chain: str = "ethereum",
    ) -> PoolAPY:
        """Get APY breakdown for a pool with caching."""
        cache_key_params = {"pool_address": pool_address, "chain": chain}

        # Try cache first
        cached = await self._cache.get("curve", "apy", **cache_key_params)
        if cached:
            logger.debug(f"Cache hit for Curve APY: {pool_address}")
            return PoolAPY.from_dict(cached)

        # Fetch from API
        try:
            # Create a new client for the specific chain if needed
            if self._client._chain != chain:
                temp_client = CurveClient(chain=chain)
                try:
                    raw_apy = await temp_client.get_pool_apy(pool_address)
                finally:
                    await temp_client.close()
            else:
                raw_apy = await self._client.get_pool_apy(pool_address)

            # Transform to domain value object
            apy = self._transform_apy(raw_apy)

            # Cache the result
            await self._cache.set(
                "curve",
                "apy",
                apy.to_dict(),
                ttl=self._apy_cache_ttl,
                **cache_key_params,
            )

            logger.debug(f"Fetched Curve APY for {pool_address}")
            return apy

        except ValueError as e:
            # Pool not found in APY data
            raise PoolNotFoundError(pool_address, chain) from e
        except Exception as e:
            logger.error(f"Error fetching Curve APY: {e}")
            raise CurveAPIError(str(e)) from e

    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        chain: str = "ethereum",
    ) -> SwapQuote:
        """Get swap quote (not cached - real-time data)."""
        try:
            # Create a new client for the specific chain if needed
            if self._client._chain != chain:
                temp_client = CurveClient(chain=chain)
                try:
                    raw_quote = await temp_client.get_swap_quote(
                        from_token, to_token, amount
                    )
                finally:
                    await temp_client.close()
            else:
                raw_quote = await self._client.get_swap_quote(
                    from_token, to_token, amount
                )

            # Transform to domain value object
            quote = self._transform_quote(raw_quote)

            logger.debug(
                f"Got Curve quote: {from_token} -> {to_token}, "
                f"impact: {quote.price_impact}%"
            )
            return quote

        except Exception as e:
            logger.error(f"Error fetching Curve swap quote: {e}")
            raise CurveAPIError(str(e)) from e

    async def get_gauges(self, chain: str = "ethereum") -> list[Gauge]:
        """Get all gauges with caching."""
        cache_key_params = {"chain": chain}

        # Try cache first
        cached = await self._cache.get("curve", "gauges", **cache_key_params)
        if cached:
            logger.debug(f"Cache hit for Curve gauges on {chain}")
            return [Gauge.from_dict(g) for g in cached]

        # Fetch from API
        try:
            # Create a new client for the specific chain if needed
            if self._client._chain != chain:
                temp_client = CurveClient(chain=chain)
                try:
                    raw_gauges = await temp_client.get_gauges()
                finally:
                    await temp_client.close()
            else:
                raw_gauges = await self._client.get_gauges()

            # Transform to domain entities
            gauges = [self._transform_gauge(g) for g in raw_gauges]

            # Cache the result
            await self._cache.set(
                "curve",
                "gauges",
                [g.to_dict() for g in gauges],
                ttl=self._gauge_cache_ttl,
                **cache_key_params,
            )

            logger.debug(f"Fetched {len(gauges)} Curve gauges on {chain}")
            return gauges

        except Exception as e:
            logger.error(f"Error fetching Curve gauges: {e}")
            raise CurveAPIError(str(e)) from e

    async def get_tvl(self, chain: str = "ethereum") -> TVLData:
        """Get TVL data with caching."""
        cache_key_params = {"chain": chain}

        # Try cache first
        cached = await self._cache.get("curve", "tvl", **cache_key_params)
        if cached:
            logger.debug(f"Cache hit for Curve TVL on {chain}")
            return TVLData.from_dict(cached)

        # Fetch from API
        try:
            # Create a new client for the specific chain if needed
            if self._client._chain != chain:
                temp_client = CurveClient(chain=chain)
                try:
                    raw_tvl = await temp_client.get_tvl()
                    raw_pools = await temp_client.get_pools()
                finally:
                    await temp_client.close()
            else:
                raw_tvl = await self._client.get_tvl()
                raw_pools = await self._client.get_pools()

            # Transform to domain value object
            tvl = TVLData(
                chain=chain,
                total_tvl=Decimal(str(raw_tvl.get("total", 0))),
                pool_count=len(raw_pools),
            )

            # Cache the result
            await self._cache.set(
                "curve",
                "tvl",
                tvl.to_dict(),
                ttl=self._tvl_cache_ttl,
                **cache_key_params,
            )

            logger.debug(f"Fetched Curve TVL for {chain}: ${tvl.total_tvl}")
            return tvl

        except Exception as e:
            logger.error(f"Error fetching Curve TVL: {e}")
            raise CurveAPIError(str(e)) from e

    # =========================================================================
    # Transformation Methods
    # =========================================================================

    def _transform_pool(self, raw: CurvePool, chain: str) -> Pool:
        """Transform CurveClient pool to domain entity."""
        return Pool(
            id=raw.id,
            name=raw.name,
            symbol=raw.symbol,
            chain=chain,
            coins=raw.coins,
            coin_names=raw.coin_names,
            tvl_usd=Decimal(str(raw.tvl_usd)),
            apy=Decimal(str(raw.apy)),
            volume_24h_usd=Decimal(str(raw.volume_24h_usd)),
            fee_percentage=Decimal(str(raw.fee_percentage)),
            is_factory=False,
        )

    def _transform_apy(self, raw: ClientPoolAPY) -> PoolAPY:
        """Transform CurveClient APY to domain value object."""
        return PoolAPY(
            pool_address=raw.pool_address,
            base_apy=Decimal(str(raw.base_apy)),
            crv_apy=Decimal(str(raw.crv_apy or 0)),
            reward_apy=Decimal(str(raw.reward_apy)),
            total_apy=Decimal(str(raw.total_apy)),
            boost_min=Decimal("1.0"),
            boost_max=Decimal(str(raw.boost)) if raw.boost > 1 else Decimal("2.5"),
        )

    def _transform_quote(self, raw: ClientSwapQuote) -> SwapQuote:
        """Transform CurveClient quote to domain value object."""
        return SwapQuote(
            from_token=raw.from_token,
            to_token=raw.to_token,
            amount_in=Decimal(str(raw.amount_in)),
            amount_out=Decimal(str(raw.amount_out)),
            price_impact=Decimal(str(raw.price_impact)),
            fee_amount=Decimal(str(raw.fee_amount)),
            exchange_rate=Decimal(str(raw.exchange_rate)),
            pool_address="",  # Not provided by client
            warnings=(),
        )

    def _transform_gauge(self, raw: GaugeData) -> Gauge:
        """Transform CurveClient gauge to domain entity."""
        return Gauge(
            address=raw.address,
            pool_address=raw.pool_address,
            crv_emissions_per_day=Decimal(str(raw.crv_emissions_per_day)),
            relative_weight=Decimal(str(raw.relative_weight)),
            total_staked=Decimal(str(raw.total_staked)),
            apy=Decimal(str(raw.apy)),
        )
