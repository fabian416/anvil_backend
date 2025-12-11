"""
GetTokens Query.

Application query for retrieving supported tokens on a chain.
"""

from dataclasses import dataclass

from app.domain.ports.axelar_gateway import AxelarGateway


@dataclass
class TokenInfo:
    """Token information."""

    symbol: str
    name: str
    decimals: int
    is_axl_wrapped: bool = False


@dataclass
class GetTokensRequest:
    """Request parameters for GetTokens query."""

    chain: str


@dataclass
class TokensResponse:
    """Response for tokens query."""

    tokens: list[TokenInfo]
    chain: str
    count: int = 0


class GetTokens:
    """
    Query to get supported tokens for a chain.
    """

    def __init__(self, gateway: AxelarGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetTokensRequest) -> TokensResponse:
        """Execute query to get tokens."""
        raw_tokens = await self._gateway.get_tokens(request.chain)

        tokens = [
            TokenInfo(
                symbol=t.get("symbol", ""),
                name=t.get("name", ""),
                decimals=t.get("decimals", 18),
                is_axl_wrapped=t.get("symbol", "").startswith("axl"),
            )
            for t in raw_tokens
        ]

        # Sort by symbol
        tokens.sort(key=lambda t: t.symbol)

        return TokensResponse(
            tokens=tokens,
            chain=request.chain,
            count=len(tokens),
        )
