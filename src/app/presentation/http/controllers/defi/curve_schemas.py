"""
Curve Finance Pydantic Schemas.

Request and response models for Curve API endpoints.
"""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.entities.curve.gauge import Gauge
from app.domain.entities.curve.pool import Pool
from app.domain.value_objects.curve.pool_apy import PoolAPY
from app.domain.value_objects.curve.swap_quote import SwapQuote
from app.domain.value_objects.curve.tvl_data import TVLData


# =============================================================================
# Request Models
# =============================================================================


class SwapQuoteRequestModel(BaseModel):
    """Request model for swap quote."""

    from_token: str = Field(..., description="Source token address")
    to_token: str = Field(..., description="Destination token address")
    amount: str = Field(..., description="Amount to swap in smallest unit (wei)")
    chain: str = Field(default="ethereum", description="Blockchain name")


# =============================================================================
# Response Models
# =============================================================================


class PoolResponse(BaseModel):
    """Pool response model."""

    id: str = Field(..., description="Pool contract address")
    name: str
    symbol: str
    chain: str
    coins: list[str] = Field(default_factory=list, description="Token addresses")
    coin_names: list[str] = Field(default_factory=list, description="Token symbols")
    tvl_usd: str = Field(..., description="Total value locked in USD")
    apy: str = Field(..., description="Total APY percentage")
    volume_24h_usd: str = Field(..., description="24h volume in USD")
    fee_percentage: str = Field(..., description="Pool fee percentage")
    is_factory: bool = Field(default=False, description="Factory-deployed pool")

    @classmethod
    def from_domain(cls, pool: Pool) -> "PoolResponse":
        """Create response from domain entity."""
        return cls(
            id=pool.id,
            name=pool.name,
            symbol=pool.symbol,
            chain=pool.chain,
            coins=pool.coins,
            coin_names=pool.coin_names,
            tvl_usd=str(pool.tvl_usd),
            apy=str(pool.apy),
            volume_24h_usd=str(pool.volume_24h_usd),
            fee_percentage=str(pool.fee_percentage),
            is_factory=pool.is_factory,
        )


class PoolsResponse(BaseModel):
    """Pools list response model."""

    pools: list[PoolResponse]
    count: int
    chain: str

    @classmethod
    def from_domain(cls, pools: list[Pool], chain: str) -> "PoolsResponse":
        """Create response from domain entities."""
        return cls(
            pools=[PoolResponse.from_domain(p) for p in pools],
            count=len(pools),
            chain=chain,
        )


class PoolAPYResponse(BaseModel):
    """Pool APY breakdown response model."""

    pool_address: str
    base_apy: str = Field(..., description="APY from trading fees")
    crv_apy: str = Field(..., description="APY from CRV rewards")
    reward_apy: str = Field(..., description="APY from additional rewards")
    total_apy: str = Field(..., description="Combined total APY")
    boost_min: str = Field(..., description="Minimum boost (1x)")
    boost_max: str = Field(..., description="Maximum boost with veCRV")

    @classmethod
    def from_domain(cls, apy: PoolAPY) -> "PoolAPYResponse":
        """Create response from domain value object."""
        return cls(
            pool_address=apy.pool_address,
            base_apy=str(apy.base_apy),
            crv_apy=str(apy.crv_apy),
            reward_apy=str(apy.reward_apy),
            total_apy=str(apy.total_apy),
            boost_min=str(apy.boost_min),
            boost_max=str(apy.boost_max),
        )


class SwapQuoteResponse(BaseModel):
    """Swap quote response model."""

    from_token: str
    to_token: str
    amount_in: str
    amount_out: str
    price_impact: str = Field(..., description="Price impact percentage")
    fee_amount: str
    exchange_rate: str
    pool_address: str
    warnings: list[str] = Field(default_factory=list, description="Risk warnings")

    @classmethod
    def from_domain(cls, quote: SwapQuote) -> "SwapQuoteResponse":
        """Create response from domain value object."""
        return cls(
            from_token=quote.from_token,
            to_token=quote.to_token,
            amount_in=str(quote.amount_in),
            amount_out=str(quote.amount_out),
            price_impact=str(quote.price_impact),
            fee_amount=str(quote.fee_amount),
            exchange_rate=str(quote.exchange_rate),
            pool_address=quote.pool_address,
            warnings=list(quote.warnings),
        )


class GaugeResponse(BaseModel):
    """Gauge response model."""

    address: str = Field(..., description="Gauge contract address")
    pool_address: str = Field(..., description="Associated pool address")
    crv_emissions_per_day: str = Field(..., description="CRV emissions per day")
    relative_weight: str = Field(..., description="Gauge weight for emissions")
    total_staked: str = Field(..., description="Total staked LP tokens")
    apy: str = Field(..., description="CRV APY")

    @classmethod
    def from_domain(cls, gauge: Gauge) -> "GaugeResponse":
        """Create response from domain entity."""
        return cls(
            address=gauge.address,
            pool_address=gauge.pool_address,
            crv_emissions_per_day=str(gauge.crv_emissions_per_day),
            relative_weight=str(gauge.relative_weight),
            total_staked=str(gauge.total_staked),
            apy=str(gauge.apy),
        )


class GaugesResponse(BaseModel):
    """Gauges list response model."""

    gauges: list[GaugeResponse]
    count: int
    chain: str

    @classmethod
    def from_domain(cls, gauges: list[Gauge], chain: str) -> "GaugesResponse":
        """Create response from domain entities."""
        return cls(
            gauges=[GaugeResponse.from_domain(g) for g in gauges],
            count=len(gauges),
            chain=chain,
        )


class TVLResponse(BaseModel):
    """TVL response model."""

    chain: str
    total_tvl: str = Field(..., description="Total value locked in USD")
    pool_count: int = Field(..., description="Number of pools")

    @classmethod
    def from_domain(cls, tvl: TVLData) -> "TVLResponse":
        """Create response from domain value object."""
        return cls(
            chain=tvl.chain,
            total_tvl=str(tvl.total_tvl),
            pool_count=tvl.pool_count,
        )
