"""
1inch DEX Aggregator API Client.

Provides access to 1inch swap aggregator:
- Swap quotes across multiple DEXes
- Best price routing
- Token lists
- Swap execution

API Docs: https://docs.1inch.io/docs/aggregation-protocol/api/
Rate Limit: 1 req/sec (free), 10 req/sec (paid)
"""

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class SwapQuote:
    """Swap quote from 1inch."""

    from_token: str
    to_token: str
    from_amount: str
    to_amount: str
    estimated_gas: int
    protocols: list[list[dict]]  # Routing path
    price_impact: float  # Percentage


@dataclass
class SwapTransaction:
    """Swap transaction data."""

    from_token: str
    to_token: str
    to_amount: str
    tx_data: str  # Transaction calldata
    tx_to: str  # Contract address
    tx_value: str  # ETH value
    gas_price: str


@dataclass
class Token:
    """Token information."""

    address: str
    symbol: str
    name: str
    decimals: int
    logo_uri: str | None = None


class OneInchClient:
    """
    1inch API client for DEX aggregation.

    Features:
    - Multi-DEX swap quotes
    - Optimal routing
    - Token information
    - Swap execution
    """

    BASE_URL = "https://api.1inch.dev"

    # Supported chains
    CHAINS = {
        "ethereum": 1,
        "bsc": 56,
        "polygon": 137,
        "optimism": 10,
        "arbitrum": 42161,
        "gnosis": 100,
        "avalanche": 43114,
        "fantom": 250,
        "base": 8453,
    }

    def __init__(self, api_key: str, chain: str = "ethereum"):
        """
        Initialize 1inch client.

        Args:
            api_key: 1inch API key
            chain: Blockchain name (default: "ethereum")
        """
        self._api_key = api_key
        self._chain = chain
        self._chain_id = self.CHAINS.get(chain.lower(), 1)
        self._client = httpx.AsyncClient(
            base_url=f"{self.BASE_URL}/swap/v5.2/{self._chain_id}",
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
        )

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        slippage: float = 1.0,
    ) -> SwapQuote:
        """
        Get swap quote without gas estimation.

        Args:
            from_token: Source token address
            to_token: Destination token address
            amount: Amount in wei
            slippage: Slippage tolerance (percent, default: 1.0)

        Returns:
            SwapQuote with expected output amount

        Example:
            >>> quote = await client.get_swap_quote(
            ...     from_token="0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  # ETH
            ...     to_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            ...     amount="1000000000000000000"  # 1 ETH
            ... )
            >>> print(f"Expected output: {int(quote.to_amount) / 1e6} USDC")
        """
        response = await self._client.get(
            "/quote",
            params={
                "src": from_token,
                "dst": to_token,
                "amount": amount,
                "includeProtocols": "true",
                "includeGas": "true",
            },
        )
        response.raise_for_status()
        data = response.json()

        return SwapQuote(
            from_token=from_token,
            to_token=to_token,
            from_amount=amount,
            to_amount=data["toAmount"],
            estimated_gas=int(data.get("estimatedGas", 0)),
            protocols=data.get("protocols", []),
            price_impact=float(data.get("priceImpact", 0)),
        )

    async def get_swap_data(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        from_address: str,
        slippage: float = 1.0,
        disable_estimate: bool = False,
    ) -> SwapTransaction:
        """
        Get swap transaction data for execution.

        Args:
            from_token: Source token address
            to_token: Destination token address
            amount: Amount in wei
            from_address: User's wallet address
            slippage: Slippage tolerance (percent, default: 1.0)
            disable_estimate: Skip gas estimation (default: False)

        Returns:
            SwapTransaction with transaction data

        Example:
            >>> swap_tx = await client.get_swap_data(
            ...     from_token="0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            ...     to_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            ...     amount="1000000000000000000",
            ...     from_address="0x..."
            ... )
            >>> # Submit tx_data to blockchain
        """
        response = await self._client.get(
            "/swap",
            params={
                "src": from_token,
                "dst": to_token,
                "amount": amount,
                "from": from_address,
                "slippage": slippage,
                "disableEstimate": str(disable_estimate).lower(),
            },
        )
        response.raise_for_status()
        data = response.json()

        tx = data["tx"]
        return SwapTransaction(
            from_token=from_token,
            to_token=to_token,
            to_amount=data["toAmount"],
            tx_data=tx["data"],
            tx_to=tx["to"],
            tx_value=tx["value"],
            gas_price=tx.get("gasPrice", "0"),
        )

    async def get_tokens(self) -> list[Token]:
        """
        Get list of supported tokens.

        Returns:
            List of tokens with metadata

        Example:
            >>> tokens = await client.get_tokens()
            >>> usdc = next(t for t in tokens if t.symbol == "USDC")
            >>> print(f"USDC address: {usdc.address}")
        """
        response = await self._client.get("/tokens")
        response.raise_for_status()
        data = response.json()

        tokens = []
        for address, token_data in data["tokens"].items():
            tokens.append(
                Token(
                    address=address,
                    symbol=token_data["symbol"],
                    name=token_data["name"],
                    decimals=token_data["decimals"],
                    logo_uri=token_data.get("logoURI"),
                )
            )

        return tokens

    async def get_token_price(
        self,
        token_address: str,
        vs_currency: str = "USD",
    ) -> float:
        """
        Get current token price.

        Args:
            token_address: Token contract address
            vs_currency: Quote currency (default: "USD")

        Returns:
            Token price in quote currency

        Example:
            >>> eth_price = await client.get_token_price(
            ...     "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
            ... )
            >>> print(f"ETH price: ${eth_price:.2f}")
        """
        # Use quote API to get price (1 token to USD)
        one_token = "1" + "0" * 18  # 1 token in wei

        usdc_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC on Ethereum

        quote = await self.get_swap_quote(
            from_token=token_address,
            to_token=usdc_address,
            amount=one_token,
        )

        # Convert to USD (USDC has 6 decimals)
        price_usd = int(quote.to_amount) / 1e6
        return price_usd

    async def get_protocols(self) -> list[dict]:
        """
        Get list of supported DEX protocols.

        Returns:
            List of protocol names and IDs
        """
        response = await self._client.get("/liquidity-sources")
        response.raise_for_status()
        data = response.json()

        return data["protocols"]
