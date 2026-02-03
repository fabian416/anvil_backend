"""
Lending infrastructure adapters.

Provides implementations of lending domain ports:
- LendingRepositoryAdapterSqla: SQLAlchemy repository for health checks, alerts, preferences
- PositionProviderAdapter: MCP-based position fetching from Aave and Morpho
"""

from app.infrastructure.adapters.lending.lending_repository_adapter_sqla import (
    LendingRepositoryAdapterSqla,
)
from app.infrastructure.adapters.lending.position_provider_adapter import (
    PositionProviderAdapter,
)

__all__ = [
    "LendingRepositoryAdapterSqla",
    "PositionProviderAdapter",
]
