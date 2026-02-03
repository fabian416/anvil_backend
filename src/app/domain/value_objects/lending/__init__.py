"""Lending domain value objects."""

from app.domain.value_objects.lending.health_factor import HealthFactor, RiskLevel
from app.domain.value_objects.lending.health_factor_result import (
    HealthFactorLevel,
    HealthFactorResult,
)
from app.domain.value_objects.lending.market_allocation import MarketAllocation
from app.domain.value_objects.lending.risk_tier import RiskTier
from app.domain.value_objects.lending.vault_apy import VaultAPY

__all__ = [
    "HealthFactor",
    "HealthFactorLevel",
    "HealthFactorResult",
    "RiskLevel",
    "VaultAPY",
    "RiskTier",
    "MarketAllocation",
]
