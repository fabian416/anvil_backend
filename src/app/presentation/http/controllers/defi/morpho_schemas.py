"""
Morpho Pydantic Schemas.

Request and response models for Morpho API endpoints.
"""

from pydantic import BaseModel, Field

from app.domain.entities.lending.morpho_market import MorphoMarket
from app.domain.entities.lending.morpho_position import MorphoPosition
from app.domain.entities.lending.morpho_vault import MorphoVault
from app.domain.value_objects.lending.market_allocation import MarketAllocation
from app.domain.value_objects.lending.vault_apy import VaultAPY


# =============================================================================
# Response Models
# =============================================================================


class MarketAllocationResponse(BaseModel):
    """Market allocation response model."""

    market_id: str
    collateral_asset: str
    loan_asset: str
    allocation_percentage: str
    lltv: str
    supply_apy: str

    @classmethod
    def from_domain(cls, alloc: MarketAllocation) -> "MarketAllocationResponse":
        """Create from domain value object."""
        return cls(
            market_id=alloc.market_id,
            collateral_asset=alloc.collateral_asset,
            loan_asset=alloc.loan_asset,
            allocation_percentage=str(alloc.allocation_percentage),
            lltv=str(alloc.lltv),
            supply_apy=str(alloc.supply_apy),
        )


class VaultResponse(BaseModel):
    """Vault response model."""

    address: str
    name: str
    symbol: str
    asset: str
    total_assets: str
    total_shares: str
    apy: str
    net_apy: str = Field(description="APY after fees")
    fee_percentage: str
    risk_tier: str
    curator_address: str | None = None
    market_allocations: list[MarketAllocationResponse] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, vault: MorphoVault) -> "VaultResponse":
        """Create from domain entity."""
        return cls(
            address=vault.address,
            name=vault.name,
            symbol=vault.symbol,
            asset=vault.asset,
            total_assets=str(vault.total_assets),
            total_shares=str(vault.total_shares),
            apy=str(vault.apy),
            net_apy=str(vault.net_apy),
            fee_percentage=str(vault.fee_percentage),
            risk_tier=vault.risk_tier.value,
            curator_address=vault.curator_address,
            market_allocations=[
                MarketAllocationResponse.from_domain(a)
                for a in vault.market_allocations
            ],
        )


class VaultOpportunityResponse(BaseModel):
    """Vault opportunity response model."""

    vault_address: str
    vault_name: str
    asset: str
    apy: str
    risk_tier: str


class VaultsResponse(BaseModel):
    """Vaults list response model."""

    vaults: list[VaultResponse]
    top_opportunities: list[VaultOpportunityResponse]
    total_count: int


class VaultAPYResponse(BaseModel):
    """Vault APY response model."""

    vault_address: str
    base_apy: str
    supply_apy: str
    reward_apy: str
    total_apy: str
    effective_apy: str = Field(description="APY after fees")
    fee_percentage: str
    fee_impact: str = Field(description="APY lost to fees")
    apy_7d_avg: str
    apy_30d_avg: str

    @classmethod
    def from_domain(cls, apy: VaultAPY, fee_impact: str = "0") -> "VaultAPYResponse":
        """Create from domain value object."""
        return cls(
            vault_address=apy.vault_address,
            base_apy=str(apy.base_apy),
            supply_apy=str(apy.supply_apy),
            reward_apy=str(apy.reward_apy),
            total_apy=str(apy.total_apy),
            effective_apy=str(apy.effective_apy),
            fee_percentage=str(apy.fee_percentage),
            fee_impact=fee_impact,
            apy_7d_avg=str(apy.apy_7d_avg),
            apy_30d_avg=str(apy.apy_30d_avg),
        )


class MarketResponse(BaseModel):
    """Market response model."""

    market_id: str
    collateral_asset: str
    loan_asset: str
    lltv: str
    total_supply: str
    total_borrow: str
    utilization: str
    supply_apy: str
    borrow_apy: str

    @classmethod
    def from_domain(cls, market: MorphoMarket) -> "MarketResponse":
        """Create from domain entity."""
        return cls(
            market_id=market.market_id,
            collateral_asset=market.collateral_asset,
            loan_asset=market.loan_asset,
            lltv=str(market.lltv),
            total_supply=str(market.total_supply),
            total_borrow=str(market.total_borrow),
            utilization=str(market.utilization),
            supply_apy=str(market.supply_apy),
            borrow_apy=str(market.borrow_apy),
        )


class MarketsResponse(BaseModel):
    """Markets list response model."""

    markets: list[MarketResponse]
    count: int


class PositionResponse(BaseModel):
    """Position response model."""

    vault_address: str
    vault_name: str
    asset_symbol: str
    shares: str
    assets: str
    deposited_assets: str
    earnings: str
    earnings_pct: str
    apy: str

    @classmethod
    def from_domain(cls, position: MorphoPosition) -> "PositionResponse":
        """Create from domain entity."""
        return cls(
            vault_address=position.vault_address,
            vault_name=position.vault_name,
            asset_symbol=position.asset_symbol,
            shares=str(position.shares),
            assets=str(position.assets),
            deposited_assets=str(position.deposited_assets),
            earnings=str(position.earnings),
            earnings_pct=str(position.earnings_pct),
            apy=str(position.apy),
        )


class PositionsSummaryResponse(BaseModel):
    """Positions summary response model."""

    total_positions: int
    total_deposited: str
    total_current_value: str
    total_earnings: str
    average_apy: str


class UserPositionsResponse(BaseModel):
    """User positions response model."""

    positions: list[PositionResponse]
    summary: PositionsSummaryResponse


class YieldComparisonResponse(BaseModel):
    """Yield comparison response model."""

    protocol: str
    vault_name: str
    apy: str
    risk_tier: str
    apy_advantage: str


class YieldComparisonListResponse(BaseModel):
    """Yield comparison list response model."""

    asset: str
    comparisons: list[YieldComparisonResponse]
    best_option: YieldComparisonResponse | None = None
