"""
0x Protocol API Client.

Provides access to 0x swap aggregator for decentralized trading:
- Swap quotes across multiple DEXes
- Best price routing with gas optimization
- Permit2 integration for gasless approvals
- Multi-chain support (Ethereum, Base, Polygon, etc.)

This client is used for Privy + 0x swap execution flow.
The frontend uses Privy SDK to sign and execute the swap transaction.

API Docs: https://0x.org/docs/api
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx

from app.setup.config.settings import AppSettings

logger = logging.getLogger(__name__)


@dataclass
class OxSwapQuote:
    """Swap quote from 0x Protocol."""

    # Quote identification
    quote_id: str | None
    expires_at: str | None

    # Token amounts
    sell_token: str
    buy_token: str
    sell_amount: str  # In wei
    buy_amount: str  # In wei
    price: str  # Exchange rate

    # Gas estimates
    estimated_gas: str | None
    gas_price: str | None

    # Transaction data (for execution)
    to: str | None  # Contract address
    data: str | None  # Transaction calldata
    value: str | None  # ETH value to send


class OxProtocolClient:
    """
    0x Protocol API client for decentralized swap quotes.

    Features:
    - Multi-DEX swap quotes with best pricing
    - Permit2 integration for gasless token approvals
    - Support for major chains (Ethereum, Base, Polygon, etc.)
    - Gas-optimized routing

    The frontend uses Privy SDK to execute the swap transaction
    with the quote data from this client.

    Usage:
        >>> client = OxProtocolClient(settings)
        >>> quote = await client.get_swap_quote(
        ...     chain="base",
        ...     from_token="ETH",
        ...     to_token="USDC",
        ...     amount="1.0",
        ...     from_address="0x..."
        ... )
        >>> print(f"Expected output: {quote.buy_amount}")
    """

    # 0x API endpoints per chain
    API_ENDPOINTS = {
        "ethereum": "https://api.0x.org",
        "base": "https://base.api.0x.org",
        "polygon": "https://polygon.api.0x.org",
        "arbitrum": "https://arbitrum.api.0x.org",
        "optimism": "https://optimism.api.0x.org",
        "bsc": "https://bsc.api.0x.org",
        "avalanche": "https://avalanche.api.0x.org",
    }

    # Native token addresses (for ETH, MATIC, etc.)
    NATIVE_TOKEN_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

    # Common token addresses per chain
    TOKEN_ADDRESSES = {
        "base": {
            "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            "WETH": "0x4200000000000000000000000000000000000006",
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "USDT": "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",
            "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        },
        "ethereum": {
            "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        },
        "polygon": {
            "MATIC": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
            "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
        },
    }

    # Token decimals (default 18 for most ERC20)
    TOKEN_DECIMALS = {
        "USDC": 6,
        "USDT": 6,
        "WBTC": 8,
        "ETH": 18,
        "WETH": 18,
        "DAI": 18,
        "MATIC": 18,
        "WMATIC": 18,
    }

    def __init__(self, settings: AppSettings):
        """
        Initialize 0x Protocol client.

        Args:
            settings: Application settings with 0x API configuration
        """
        self._settings = settings
        self._api_key = settings.ox_protocol.api_key if settings.ox_protocol.is_configured else ""

        # Create HTTP client (will be configured per chain)
        self._client: httpx.AsyncClient | None = None

    def _get_client(self, chain: str) -> httpx.AsyncClient:
        """Get or create HTTP client for specific chain."""
        base_url = self.API_ENDPOINTS.get(chain.lower(), self.API_ENDPOINTS["base"])

        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["0x-api-key"] = self._api_key

        return httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
            headers=headers,
        )

    def _get_token_address(self, chain: str, token: str) -> str:
        """
        Get token contract address for a given chain.

        Args:
            chain: Chain name (base, ethereum, polygon, etc.)
            token: Token symbol (ETH, USDC, etc.)

        Returns:
            Token contract address
        """
        chain_tokens = self.TOKEN_ADDRESSES.get(chain.lower(), {})
        return chain_tokens.get(token.upper(), self.NATIVE_TOKEN_ADDRESS)

    def _to_wei(self, amount: str, token: str) -> str:
        """
        Convert token amount to wei (smallest unit).

        Args:
            amount: Human-readable amount (e.g., "1.5")
            token: Token symbol (for decimals lookup)

        Returns:
            Amount in wei as string
        """
        decimals = self.TOKEN_DECIMALS.get(token.upper(), 18)
        amount_decimal = Decimal(amount)
        wei_amount = int(amount_decimal * Decimal(10**decimals))
        return str(wei_amount)

    def _from_wei(self, amount: str, token: str) -> str:
        """
        Convert wei amount to human-readable format.

        Args:
            amount: Amount in wei
            token: Token symbol (for decimals lookup)

        Returns:
            Human-readable amount as string
        """
        decimals = self.TOKEN_DECIMALS.get(token.upper(), 18)
        amount_int = int(amount)
        human_amount = Decimal(amount_int) / Decimal(10**decimals)
        return str(human_amount)

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()

    async def get_swap_quote(
        self,
        chain: str,
        from_token: str,
        to_token: str,
        amount: str,
        from_address: str,
        slippage: float = 1.0,
    ) -> OxSwapQuote:
        """
        Get swap quote from 0x Protocol.

        Args:
            chain: Chain name (base, ethereum, polygon, etc.)
            from_token: Source token symbol (ETH, USDC, etc.)
            to_token: Destination token symbol
            amount: Amount to swap (human-readable, e.g., "1.5")
            from_address: User's wallet address
            slippage: Slippage tolerance in percent (default: 1.0)

        Returns:
            OxSwapQuote with expected output and transaction data

        Example:
            >>> quote = await client.get_swap_quote(
            ...     chain="base",
            ...     from_token="ETH",
            ...     to_token="USDC",
            ...     amount="1.0",
            ...     from_address="0x123..."
            ... )
            >>> print(f"Expected output: {quote.buy_amount} {to_token}")
        """
        try:
            # Get token addresses
            sell_token_address = self._get_token_address(chain, from_token)
            buy_token_address = self._get_token_address(chain, to_token)

            # Convert amount to wei
            sell_amount_wei = self._to_wei(amount, from_token)

            # Get chain-specific client
            client = self._get_client(chain)

            # Call 0x swap/permit2/quote API
            # https://0x.org/docs/api#tag/Swap/operation/swap::permit2::getQuote
            params = {
                "sellToken": sell_token_address,
                "buyToken": buy_token_address,
                "sellAmount": sell_amount_wei,
                "taker": from_address,
                "slippageBps": int(slippage * 100),  # Convert to basis points (1% = 100)
            }

            logger.info(
                f"[0X_CLIENT] Requesting quote: {amount} {from_token} → {to_token} on {chain}"
            )

            response = await client.get("/swap/permit2/quote", params=params)
            response.raise_for_status()
            data = response.json()

            # Parse quote response
            quote = OxSwapQuote(
                quote_id=data.get("quote", {}).get("id"),
                expires_at=data.get("quote", {}).get("expiresAt"),
                sell_token=from_token,
                buy_token=to_token,
                sell_amount=data.get("sellAmount", sell_amount_wei),
                buy_amount=data.get("buyAmount", "0"),
                price=data.get("price", "0"),
                estimated_gas=data.get("gas"),
                gas_price=data.get("gasPrice"),
                to=data.get("transaction", {}).get("to"),
                data=data.get("transaction", {}).get("data"),
                value=data.get("transaction", {}).get("value"),
            )

            logger.info(
                f"[0X_CLIENT] ✅ Quote received: {amount} {from_token} → "
                f"{self._from_wei(quote.buy_amount, to_token)} {to_token} "
                f"(rate: {quote.price})"
            )

            await client.aclose()
            return quote

        except httpx.HTTPStatusError as e:
            logger.error(f"[0X_CLIENT] ❌ HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"[0X_CLIENT] ❌ Error getting quote: {e}", exc_info=True)
            raise

    async def get_price(
        self,
        chain: str,
        from_token: str,
        to_token: str,
        amount: str = "1.0",
    ) -> str:
        """
        Get simple price quote without transaction data.

        Args:
            chain: Chain name
            from_token: Source token symbol
            to_token: Destination token symbol
            amount: Amount to price (default: "1.0")

        Returns:
            Exchange rate as string

        Example:
            >>> rate = await client.get_price("base", "ETH", "USDC")
            >>> print(f"1 ETH = {rate} USDC")
        """
        try:
            # Get token addresses
            sell_token_address = self._get_token_address(chain, from_token)
            buy_token_address = self._get_token_address(chain, to_token)

            # Convert amount to wei
            sell_amount_wei = self._to_wei(amount, from_token)

            # Get chain-specific client
            client = self._get_client(chain)

            # Call 0x price API
            params = {
                "sellToken": sell_token_address,
                "buyToken": buy_token_address,
                "sellAmount": sell_amount_wei,
            }

            response = await client.get("/swap/permit2/price", params=params)
            response.raise_for_status()
            data = response.json()

            price = data.get("price", "0")

            await client.aclose()
            return price

        except Exception as e:
            logger.error(f"[0X_CLIENT] Error getting price: {e}", exc_info=True)
            # Return fallback price
            return "0"
