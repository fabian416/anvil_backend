"""
Aave Pydantic Schemas.

Request and response models for Aave V3 API endpoints.
"""

from pydantic import BaseModel, Field

from app.domain.entities.lending.aave_market import AaveMarket
from app.domain.entities.lending.aave_position import AavePosition
from app.domain.value_objects.lending.health_factor import HealthFactor


# =============================================================================
# Response Models
# =============================================================================


class AaveMarketResponse(BaseModel):
    """Aave market response model."""

    asset_address: str
    symbol: str
    name: str
    chain: str

    # Supply metrics
    supply_apy: str = Field(description="Annual supply APY (decimal, e.g., 0.05 = 5%)")
    total_supplied: str
    total_supplied_usd: str

    # Borrow metrics
    borrow_apy_variable: str = Field(description="Variable borrow APY")
    borrow_apy_stable: str = Field(description="Stable borrow APY")
    total_borrowed: str
    total_borrowed_usd: str

    # Utilization
    utilization_rate: str = Field(description="Utilization percentage")
    liquidity_available: str

    # Collateral parameters
    ltv: str = Field(description="Max loan-to-value ratio")
    liquidation_threshold: str
    liquidation_bonus: str

    # Status
    is_active: bool
    can_use_as_collateral: bool
    can_borrow: bool

    # Price
    price_usd: str

    @classmethod
    def from_domain(cls, market: AaveMarket) -> "AaveMarketResponse":
        """Create from domain entity."""
        return cls(
            asset_address=market.asset_address,
            symbol=market.symbol,
            name=market.name,
            chain=market.chain,
            supply_apy=str(market.supply_apy),
            total_supplied=str(market.total_supplied),
            total_supplied_usd=str(market.total_supplied_usd),
            borrow_apy_variable=str(market.borrow_apy_variable),
            borrow_apy_stable=str(market.borrow_apy_stable),
            total_borrowed=str(market.total_borrowed),
            total_borrowed_usd=str(market.total_borrowed_usd),
            utilization_rate=str(market.utilization_rate),
            liquidity_available=str(market.liquidity_available),
            ltv=str(market.ltv),
            liquidation_threshold=str(market.liquidation_threshold),
            liquidation_bonus=str(market.liquidation_bonus),
            is_active=market.is_active,
            can_use_as_collateral=market.can_use_as_collateral,
            can_borrow=market.can_borrow,
            price_usd=str(market.price_usd),
        )


class AaveMarketsResponse(BaseModel):
    """Aave markets list response model."""

    markets: list[AaveMarketResponse]
    count: int
    chain: str
    total_supplied_usd: str = Field(description="Total TVL supplied")
    total_borrowed_usd: str = Field(description="Total borrowed")


class AaveSupplyPositionResponse(BaseModel):
    """Individual supply position response."""

    asset_address: str
    symbol: str
    balance: str
    balance_usd: str
    apy: str
    is_collateral: bool


class AaveBorrowPositionResponse(BaseModel):
    """Individual borrow position response."""

    asset_address: str
    symbol: str
    balance: str
    balance_usd: str
    apy: str
    borrow_type: str = Field(description="'variable' or 'stable'")


class AavePositionResponse(BaseModel):
    """Aave position response model."""

    user_address: str
    chain: str

    # Aggregated values
    total_collateral_usd: str
    total_debt_usd: str
    available_borrow_usd: str
    net_worth_usd: str

    # Health metrics
    health_factor: str = Field(description="Health factor (∞ if no debt)")
    current_ltv: str
    is_healthy: bool
    is_at_risk: bool = Field(description="True if 1 < HF < 1.5")
    is_liquidatable: bool = Field(description="True if HF < 1")

    # Positions
    supplies: list[AaveSupplyPositionResponse]
    borrows: list[AaveBorrowPositionResponse]

    @classmethod
    def from_domain(cls, position: AavePosition) -> "AavePositionResponse":
        """Create from domain entity."""
        # Handle infinity health factor
        hf_str = str(position.health_factor)
        if "inf" in hf_str.lower():
            hf_str = "∞"

        return cls(
            user_address=position.user_address,
            chain=position.chain,
            total_collateral_usd=str(position.total_collateral_usd),
            total_debt_usd=str(position.total_debt_usd),
            available_borrow_usd=str(position.available_borrow_usd),
            net_worth_usd=str(position.net_worth_usd),
            health_factor=hf_str,
            current_ltv=str(position.current_ltv),
            is_healthy=position.is_healthy,
            is_at_risk=position.is_at_risk,
            is_liquidatable=position.is_liquidatable,
            supplies=[
                AaveSupplyPositionResponse(
                    asset_address=s.asset_address,
                    symbol=s.symbol,
                    balance=str(s.balance),
                    balance_usd=str(s.balance_usd),
                    apy=str(s.apy),
                    is_collateral=s.is_collateral,
                )
                for s in position.supplies
            ],
            borrows=[
                AaveBorrowPositionResponse(
                    asset_address=b.asset_address,
                    symbol=b.symbol,
                    balance=str(b.balance),
                    balance_usd=str(b.balance_usd),
                    apy=str(b.apy),
                    borrow_type=b.borrow_type,
                )
                for b in position.borrows
            ],
        )


class HealthFactorResponse(BaseModel):
    """Health factor response model."""

    value: str = Field(description="Health factor value (∞ if no debt)")
    collateral_usd: str
    debt_usd: str
    risk_level: str = Field(
        description="Risk classification: safe, moderate, high, critical, liquidatable"
    )
    is_liquidatable: bool
    distance_to_liquidation: str = Field(description="Percentage above liquidation threshold")
    max_withdrawable_pct: str = Field(description="Max collateral withdrawal %")
    max_borrowable_pct: str = Field(description="Max additional borrow %")

    @classmethod
    def from_domain(cls, hf: HealthFactor) -> "HealthFactorResponse":
        """Create from domain value object."""
        # Handle infinity
        value_str = str(hf.value)
        if "inf" in value_str.lower():
            value_str = "∞"

        return cls(
            value=value_str,
            collateral_usd=str(hf.collateral_usd),
            debt_usd=str(hf.debt_usd),
            risk_level=hf.risk_level.value,
            is_liquidatable=hf.is_liquidatable,
            distance_to_liquidation=str(hf.distance_to_liquidation),
            max_withdrawable_pct=str(hf.max_withdrawable_pct),
            max_borrowable_pct=str(hf.max_borrowable_pct),
        )


class ProtocolStatsResponse(BaseModel):
    """Protocol statistics response model."""

    chain: str
    total_tvl_usd: str = Field(description="Total value locked")
    total_supplied_usd: str
    total_borrowed_usd: str
    num_markets: int


class AvailableToBorrowResponse(BaseModel):
    """Available to borrow response model."""

    asset: str
    chain: str
    max_borrowable: str = Field(description="Maximum borrowable amount")
    max_borrowable_usd: str
    current_debt: str
    collateral_usd: str
    health_factor_after_max_borrow: str


class CalculateHealthFactorRequest(BaseModel):
    """Calculate health factor request model."""

    collateral_usd: float = Field(..., gt=0, description="Total collateral in USD")
    debt_usd: float = Field(..., ge=0, description="Total debt in USD")
    liquidation_threshold: float = Field(
        default=0.825, gt=0, le=1, description="Liquidation threshold (e.g., 0.825)"
    )
