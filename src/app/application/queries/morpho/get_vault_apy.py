"""
GetVaultAPY Query.

Application query for retrieving vault APY with breakdown.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.value_objects.lending.vault_apy import VaultAPY


@dataclass
class GetVaultAPYRequest:
    """Request parameters for GetVaultAPY query."""

    vault_address: str
    chain: str = "ethereum"


@dataclass
class VaultAPYResponse:
    """Response for vault APY query."""

    apy: VaultAPY
    effective_apy: Decimal
    fee_impact: Decimal


class GetVaultAPY:
    """
    Query to get vault APY with detailed breakdown.

    Returns APY components and calculates effective APY after fees.
    """

    def __init__(self, gateway: MorphoGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetVaultAPYRequest) -> VaultAPYResponse:
        """Execute query to get vault APY."""
        apy = await self._gateway.get_vault_apy(
            vault_address=request.vault_address,
            chain=request.chain,
        )

        # Calculate fee impact
        fee_impact = apy.total_apy * apy.fee_percentage

        return VaultAPYResponse(
            apy=apy,
            effective_apy=apy.effective_apy,
            fee_impact=fee_impact,
        )
