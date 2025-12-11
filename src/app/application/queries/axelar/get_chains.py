"""
GetChains Query.

Application query for retrieving supported Axelar chains.
"""

from dataclasses import dataclass, field

from app.domain.ports.axelar_gateway import AxelarGateway


@dataclass
class ChainInfo:
    """Chain information."""

    id: str
    name: str
    chain_id: int


@dataclass
class ChainsResponse:
    """Response for chains query."""

    chains: list[ChainInfo]
    count: int = 0


class GetChains:
    """
    Query to get supported Axelar chains.
    """

    def __init__(self, gateway: AxelarGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self) -> ChainsResponse:
        """Execute query to get chains."""
        raw_chains = await self._gateway.get_chains()

        chains = [
            ChainInfo(
                id=c.get("id", ""),
                name=c.get("name", ""),
                chain_id=c.get("chain_id", 0),
            )
            for c in raw_chains
        ]

        # Sort by name
        chains.sort(key=lambda c: c.name)

        return ChainsResponse(
            chains=chains,
            count=len(chains),
        )
