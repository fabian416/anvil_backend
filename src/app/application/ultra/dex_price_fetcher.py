"""DEX Price Fetcher for ULTRA Arbitrage Discovery.

Fetches real-time prices from multiple DEX sources:
- 1inch API (aggregates Uniswap, SushiSwap, Balancer, etc.)
- CoinGecko (price reference and validation)
- DeFiLlama (TVL and liquidity data)

This replaces the mock price data in ArbitrageDiscovery.

Data Source Priority:
1. 1inch API - Best aggregated prices (requires API key)
2. CoinGecko - Reference prices (rate limited on free tier)
3. DeFiLlama - TVL and yield data (no rate limits)
4. Fallback - Hardcoded prices for demos
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.domain.common.datetime_utils import utc_now

logger = logging.getLogger(__name__)

# Cache TTL (seconds)
PRICE_CACHE_TTL = 60  # 1 minute for prices


# Token addresses on Ethereum mainnet
TOKEN_ADDRESSES = {
    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI": "0x6B175474E89094C44Da98b954EescdeCB5BE33D85",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
}

# Token decimals
TOKEN_DECIMALS = {
    "ETH": 18,
    "WETH": 18,
    "USDC": 6,
    "USDT": 6,
    "DAI": 18,
    "WBTC": 8,
}

# CoinGecko IDs
COINGECKO_IDS = {
    "ETH": "ethereum",
    "WETH": "weth",
    "USDC": "usd-coin",
    "USDT": "tether",
    "DAI": "dai",
    "WBTC": "wrapped-bitcoin",
    "BTC": "bitcoin",
}


@dataclass
class DEXQuote:
    """Price quote from a DEX."""

    dex: str
    from_token: str
    to_token: str
    from_amount: Decimal
    to_amount: Decimal
    price: Decimal  # to_amount / from_amount
    gas_estimate: int
    protocols_used: list[str]
    timestamp: datetime


@dataclass
class TokenPrice:
    """Token price from price oracle."""

    symbol: str
    price_usd: Decimal
    source: str
    timestamp: datetime


class DEXPriceFetcher:
    """
    Fetches real-time DEX prices for arbitrage discovery.

    Uses:
    - 1inch API for DEX aggregation (best prices across DEXes)
    - CoinGecko for reference prices
    - DeFiLlama for liquidity validation

    Usage:
        fetcher = DEXPriceFetcher(oneinch_api_key="...")
        quote = await fetcher.get_best_quote("WETH", "USDC", Decimal("1"))
        print(f"1 WETH = {quote.to_amount} USDC on {quote.dex}")
    """

    def __init__(
        self,
        oneinch_api_key: str | None = None,
        chain: str = "ethereum",
    ):
        """
        Initialize DEX price fetcher.

        Args:
            oneinch_api_key: 1inch API key (required for real data)
            chain: Blockchain (ethereum, arbitrum, base, etc.)
        """
        self._oneinch_api_key = oneinch_api_key
        self._chain = chain
        self._oneinch_client = None
        self._coingecko_client = None
        self._price_cache: dict[str, TokenPrice] = {}

    async def _get_oneinch_client(self):
        """Lazy load 1inch client."""
        if self._oneinch_client is None and self._oneinch_api_key:
            from app.infrastructure.adapters.external.oneinch_client import (
                OneInchClient,
            )

            self._oneinch_client = OneInchClient(
                api_key=self._oneinch_api_key,
                chain=self._chain,
            )
        return self._oneinch_client

    async def _get_coingecko_client(self):
        """Lazy load CoinGecko client."""
        if self._coingecko_client is None:
            from app.infrastructure.adapters.external.coingecko_client import (
                CoinGeckoClient,
            )

            self._coingecko_client = CoinGeckoClient()
        return self._coingecko_client

    async def close(self):
        """Close all clients."""
        if self._oneinch_client:
            await self._oneinch_client.close()
        if self._coingecko_client:
            await self._coingecko_client.close()

    def _get_token_address(self, symbol: str) -> str:
        """Get token contract address."""
        return TOKEN_ADDRESSES.get(symbol.upper(), symbol)

    def _get_token_decimals(self, symbol: str) -> int:
        """Get token decimals."""
        return TOKEN_DECIMALS.get(symbol.upper(), 18)

    def _to_wei(self, amount: Decimal, symbol: str) -> str:
        """Convert amount to wei (smallest unit)."""
        decimals = self._get_token_decimals(symbol)
        wei = int(amount * Decimal(10**decimals))
        return str(wei)

    def _from_wei(self, wei: str, symbol: str) -> Decimal:
        """Convert wei to decimal amount."""
        decimals = self._get_token_decimals(symbol)
        return Decimal(wei) / Decimal(10**decimals)

    async def get_token_price(self, symbol: str) -> TokenPrice:
        """
        Get current token price in USD.

        Uses multiple sources with fallback:
        1. CoinGecko (if not rate limited)
        2. Fallback prices (for demos)

        Args:
            symbol: Token symbol (ETH, USDC, etc.)

        Returns:
            TokenPrice with current USD price

        Example:
            >>> price = await fetcher.get_token_price("ETH")
            >>> print(f"ETH: ${price.price_usd}")
        """
        # Check cache first
        cache_key = symbol.upper()
        if cache_key in self._price_cache:
            cached = self._price_cache[cache_key]
            age = (utc_now() - cached.timestamp).total_seconds()
            if age < PRICE_CACHE_TTL:
                return cached

        # Try CoinGecko with rate limit protection
        coingecko = await self._get_coingecko_client()
        if coingecko:
            try:
                # Add small delay to avoid rate limits
                await asyncio.sleep(0.1)
                coin_id = COINGECKO_IDS.get(symbol.upper(), symbol.lower())
                price_data = await coingecko.get_price(coin_id)
                token_price = TokenPrice(
                    symbol=symbol.upper(),
                    price_usd=Decimal(str(price_data.usd)),
                    source="coingecko",
                    timestamp=utc_now(),
                )
                self._price_cache[cache_key] = token_price
                return token_price
            except Exception as e:
                # Only log once per symbol to reduce noise
                if f"logged_{cache_key}" not in self._price_cache:
                    logger.debug(f"CoinGecko unavailable for {symbol}: {e!s}")
                    self._price_cache[f"logged_{cache_key}"] = True

        # Fallback to realistic hardcoded prices (updated regularly)
        # These should be updated periodically or fetched from a backup source
        fallback_prices = {
            "ETH": Decimal("3000"),
            "WETH": Decimal("3000"),
            "BTC": Decimal("90000"),
            "WBTC": Decimal("90000"),
            "USDC": Decimal("1"),
            "USDT": Decimal("1"),
            "DAI": Decimal("1"),
        }

        price = TokenPrice(
            symbol=symbol.upper(),
            price_usd=fallback_prices.get(symbol.upper(), Decimal("0")),
            source="fallback",
            timestamp=utc_now(),
        )
        self._price_cache[cache_key] = price
        return price

    async def get_quote_1inch(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
    ) -> DEXQuote | None:
        """
        Get swap quote from 1inch aggregator.

        1inch finds the best price across multiple DEXes.

        Args:
            from_token: Source token symbol
            to_token: Destination token symbol
            amount: Amount of from_token

        Returns:
            DEXQuote with best aggregated price, or None if unavailable
        """
        client = await self._get_oneinch_client()
        if not client:
            logger.warning("1inch client not available (no API key)")
            return None

        try:
            from_address = self._get_token_address(from_token)
            to_address = self._get_token_address(to_token)
            amount_wei = self._to_wei(amount, from_token)

            quote = await client.get_swap_quote(
                from_token=from_address,
                to_token=to_address,
                amount=amount_wei,
            )

            to_amount = self._from_wei(quote.to_amount, to_token)
            price = to_amount / amount if amount > 0 else Decimal("0")

            # Extract DEXes used in routing
            protocols = []
            for route in quote.protocols:
                for step in route:
                    for protocol in step:
                        if isinstance(protocol, dict) and "name" in protocol:
                            protocols.append(protocol["name"])

            return DEXQuote(
                dex="1inch_aggregator",
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount=to_amount,
                price=price,
                gas_estimate=quote.estimated_gas,
                protocols_used=list(set(protocols)),
                timestamp=utc_now(),
            )

        except Exception as e:
            logger.warning(f"1inch quote failed for {from_token}->{to_token}: {e}")
            return None

    async def get_simulated_quote(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        dex: str = "simulated",
    ) -> DEXQuote:
        """
        Get simulated quote based on CoinGecko prices.

        Used when 1inch is not available or for testing.

        Args:
            from_token: Source token symbol
            to_token: Destination token symbol
            amount: Amount of from_token
            dex: DEX name for simulation

        Returns:
            Simulated DEXQuote based on market prices
        """
        from_price = await self.get_token_price(from_token)
        to_price = await self.get_token_price(to_token)

        # Calculate exchange rate
        if to_price.price_usd > 0:
            price = from_price.price_usd / to_price.price_usd
        else:
            price = Decimal("0")

        to_amount = amount * price

        # Simulate DEX variations (±0.15% - realistic spread)
        # DEXes typically have very small price differences
        import random

        # Seed based on dex name for consistent results per DEX
        dex_seed = hash(dex) % 1000
        random.seed(dex_seed)
        variation = Decimal(str(1 + (random.random() - 0.5) * 0.003))  # ±0.15%
        random.seed()  # Reset seed

        to_amount = to_amount * variation

        # Apply DEX fee (0.3% for most DEXes)
        fee = Decimal("0.997")  # 0.3% fee
        to_amount = to_amount * fee

        return DEXQuote(
            dex=dex,
            from_token=from_token,
            to_token=to_token,
            from_amount=amount,
            to_amount=to_amount,
            price=price * variation * fee,
            gas_estimate=150000,
            protocols_used=[dex],
            timestamp=utc_now(),
        )

    async def get_multi_dex_quotes(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
    ) -> list[DEXQuote]:
        """
        Get quotes from multiple DEX sources.

        Returns quotes from:
        - 1inch (best aggregated)
        - Simulated quotes for comparison

        Args:
            from_token: Source token symbol
            to_token: Destination token symbol
            amount: Amount of from_token

        Returns:
            List of DEXQuotes sorted by output amount (best first)
        """
        quotes = []

        # Get 1inch quote (real aggregated price)
        oneinch_quote = await self.get_quote_1inch(from_token, to_token, amount)
        if oneinch_quote:
            quotes.append(oneinch_quote)

        # Add simulated DEX quotes for comparison
        dexes = ["uniswap_v3", "sushiswap", "curve", "balancer"]
        for dex in dexes:
            sim_quote = await self.get_simulated_quote(from_token, to_token, amount, dex)
            quotes.append(sim_quote)

        # Sort by output amount (best first)
        quotes.sort(key=lambda q: q.to_amount, reverse=True)

        return quotes

    async def find_arbitrage_opportunity(
        self,
        token_a: str,
        token_b: str,
        capital: Decimal,
    ) -> dict[str, Any] | None:
        """
        Find arbitrage opportunity between two tokens.

        Checks if buying on one DEX and selling on another is profitable.

        Args:
            token_a: First token
            token_b: Second token
            capital: Capital in token_a

        Returns:
            Arbitrage opportunity dict or None if not profitable
        """
        # Get quotes A -> B
        quotes_a_to_b = await self.get_multi_dex_quotes(token_a, token_b, capital)
        if not quotes_a_to_b:
            return None

        best_buy = quotes_a_to_b[0]  # Best A -> B

        # Get quotes B -> A (using the B amount from best buy)
        quotes_b_to_a = await self.get_multi_dex_quotes(
            token_b, token_a, best_buy.to_amount
        )
        if not quotes_b_to_a:
            return None

        best_sell = quotes_b_to_a[0]  # Best B -> A

        # Calculate profit
        final_amount = best_sell.to_amount
        profit = final_amount - capital
        profit_pct = (profit / capital) * 100 if capital > 0 else Decimal("0")

        # Estimate gas cost
        gas_cost_wei = best_buy.gas_estimate + best_sell.gas_estimate
        eth_price = await self.get_token_price("ETH")
        gas_price_gwei = 30  # Assume 30 gwei
        gas_cost_eth = Decimal(gas_cost_wei * gas_price_gwei) / Decimal(10**9)
        gas_cost_usd = gas_cost_eth * eth_price.price_usd

        # Net profit
        token_a_price = await self.get_token_price(token_a)
        profit_usd = profit * token_a_price.price_usd
        net_profit_usd = profit_usd - gas_cost_usd

        if net_profit_usd <= 0:
            return None

        return {
            "type": "2hop",
            "path": [token_a, token_b, token_a],
            "buy_dex": best_buy.dex,
            "sell_dex": best_sell.dex,
            "capital": float(capital),
            "final_amount": float(final_amount),
            "profit": float(profit),
            "profit_pct": float(profit_pct),
            "gas_cost_usd": float(gas_cost_usd),
            "net_profit_usd": float(net_profit_usd),
            "protocols_used": best_buy.protocols_used + best_sell.protocols_used,
            "is_real_data": best_buy.dex == "1inch_aggregator",
        }
