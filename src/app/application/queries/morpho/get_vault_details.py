"""
GetVaultDetails Query.

Application query for retrieving detailed vault information.
"""

from dataclasses import dataclass

from app.domain.entities.lending.morpho_vault import MorphoVault
from app.domain.ports.morpho_gateway import MorphoGateway


@dataclass
class GetVaultDetailsRequest:
    """Request parameters for GetVaultDetails query."""

    vault_address: str
    chain: str = "ethereum"


class GetVaultDetails:
    """
    Query to get detailed vault information.

    Returns vault with full market allocations and current APY.
    """

    def __init__(self, gateway: MorphoGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetVaultDetailsRequest) -> MorphoVault:
        """Execute query to get vault details."""
        # Get vault details (raises VaultNotFoundError if not found)
        vault = await self._gateway.get_vault_details(
            vault_address=request.vault_address,
            chain=request.chain,
        )

        # Enrich with APY
        try:
            apy = await self._gateway.get_vault_apy(
                request.vault_address, request.chain
            )
            vault.apy = apy.total_apy
        except Exception:
            pass  # Keep default APY

        return vault
