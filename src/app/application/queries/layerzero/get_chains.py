"""
GetChains Query.

Application query for retrieving supported LayerZero chains.
"""

from dataclasses import dataclass, field

from app.domain.ports.layerzero_gateway import LayerZeroGateway
from app.domain.value_objects.cross_chain.lz_chain import LZChain


@dataclass
class ChainsResponse:
    """Response for chains query."""

    chains: list[LZChain]
    evm_chains: list[LZChain] = field(default_factory=list)
    non_evm_chains: list[LZChain] = field(default_factory=list)


class GetChains:
    """
    Query to get supported LayerZero chains.

    Groups chains by ecosystem (EVM vs non-EVM).
    """

    def __init__(self, gateway: LayerZeroGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self) -> ChainsResponse:
        """Execute query to get chains."""
        chains = await self._gateway.get_chains()

        # Sort by name
        chains.sort(key=lambda c: c.name)

        # Group by ecosystem
        evm_chains = [c for c in chains if c.is_evm]
        non_evm_chains = [c for c in chains if not c.is_evm]

        return ChainsResponse(
            chains=chains,
            evm_chains=evm_chains,
            non_evm_chains=non_evm_chains,
        )
