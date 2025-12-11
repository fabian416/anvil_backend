"""
Portfolio-related request/response schemas.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# ============================================================
# Portfolio Holdings Schemas
# ============================================================


class TokenHoldingResponse(BaseModel):
    """Token holding in portfolio."""

    token_address: Optional[str] = Field(
        None, description="Token contract address (null for native)"
    )
    symbol: str = Field(..., description="Token symbol (e.g., ETH, USDC)")
    name: str = Field(..., description="Token name")
    decimals: int = Field(..., description="Token decimals")
    amount: float = Field(..., description="Token balance")
    usd_value: Optional[float] = Field(None, description="USD value of holding")
    usd_price: Optional[float] = Field(None, description="Price per token in USD")
    percentage: float = Field(0.0, description="Percentage of total portfolio")


class PortfolioResponse(BaseModel):
    """Portfolio data response for a wallet."""

    wallet_address: str = Field(..., description="Wallet address")
    chain: str = Field(..., description="Blockchain network")
    total_usd: float = Field(..., description="Total portfolio value in USD")
    native_balance: float = Field(..., description="Native token balance")
    native_usd_value: Optional[float] = Field(
        None, description="Native token USD value"
    )
    native_symbol: str = Field(
        ..., description="Native token symbol (ETH, MATIC, etc.)"
    )
    tokens: List[TokenHoldingResponse] = Field(
        default_factory=list, description="Token holdings"
    )
    captured_at: str = Field(..., description="ISO timestamp of data capture")
    has_value: bool = Field(..., description="Whether portfolio has USD value")


class PortfolioHistoryPoint(BaseModel):
    """Single point in portfolio history."""

    captured_at: str
    total_usd: float


class PortfolioHistoryResponse(BaseModel):
    """Portfolio value history for charts."""

    wallet_address: str
    points: List[PortfolioHistoryPoint]
    start_date: str
    end_date: str


# ============================================================
# Risk Analysis Schemas (existing)
# ============================================================


# Response schemas
class ProtocolRiskDetail(BaseModel):
    """Risk details for a protocol in portfolio."""

    protocol_id: str
    protocol_name: str
    exposure_usd: float
    exposure_percentage: float
    risk_score: float
    risk_level: str
    risk_trend: str
    contributing_factors: List[str]
    value_at_risk_usd: float


class DependencyRisk(BaseModel):
    """Risk from protocol dependencies."""

    dependency_protocol_id: str
    dependency_protocol_name: str
    dependent_protocols: List[str]
    impact_if_failure: str
    total_exposure_usd: float
    risk_score: float


class PortfolioRiskResponse(BaseModel):
    """Comprehensive portfolio risk analysis response."""

    user_id: str
    overall_risk_score: float
    risk_distribution: Dict[str, float]
    protocols_at_risk: List[ProtocolRiskDetail]
    dependency_risks: List[DependencyRisk]
    systemic_risk_score: float
    concentration_risk: float
    chain_risk_distribution: Dict[str, float]
    recommendations: List[str]
    total_value_at_risk_usd: float
    last_updated: str


# Request schemas
class CascadeSimulationRequest(BaseModel):
    """Request to simulate cascade failure."""

    origin_protocol_id: str = Field(..., description="Protocol ID that fails")


class CascadeImpact(BaseModel):
    """Impact of cascade failure."""

    origin_protocol_id: str
    origin_protocol_name: str
    directly_affected: List[str]
    indirectly_affected: List[str]
    total_exposure_at_risk_usd: float
    cascade_probability: float
    time_to_impact: str


class CascadeSimulationResponse(BaseModel):
    """Response for cascade simulation."""

    user_id: str
    cascade_impacts: List[CascadeImpact]
    worst_case_loss_usd: float
    worst_case_loss_percentage: float
    protocols_to_exit: List[str]
    protocols_to_reduce: List[str]
    safe_protocols: List[str]
