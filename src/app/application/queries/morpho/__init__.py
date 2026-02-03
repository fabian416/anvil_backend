"""Morpho Protocol application queries."""

from app.application.queries.morpho.compare_yields import (
    CompareYields,
    CompareYieldsRequest,
)
from app.application.queries.morpho.get_markets import GetMarkets, GetMarketsRequest
from app.application.queries.morpho.get_user_positions import (
    GetUserPositions,
    GetUserPositionsRequest,
)
from app.application.queries.morpho.get_vault_apy import GetVaultAPY, GetVaultAPYRequest
from app.application.queries.morpho.get_vault_details import (
    GetVaultDetails,
    GetVaultDetailsRequest,
)
from app.application.queries.morpho.get_vaults import GetVaults, GetVaultsRequest

__all__ = [
    "GetVaults",
    "GetVaultsRequest",
    "GetVaultDetails",
    "GetVaultDetailsRequest",
    "GetVaultAPY",
    "GetVaultAPYRequest",
    "GetMarkets",
    "GetMarketsRequest",
    "GetUserPositions",
    "GetUserPositionsRequest",
    "CompareYields",
    "CompareYieldsRequest",
]
