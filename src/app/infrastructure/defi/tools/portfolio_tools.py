"""
Portfolio tools for PortfolioAgent.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.infrastructure.defi.providers.wallet_provider import WalletProvider
from app.infrastructure.defi.providers.defillama import DeFiLlamaClient
from app.infrastructure.defi.providers.coingecko import CoinGeckoClient

logger = logging.getLogger(__name__)


async def get_wallet_balance_tool(
    address: str,
    wallet_provider: WalletProvider,
    coingecko_client: CoinGeckoClient,
    network: str = "ethereum",
) -> str:
    """
    Get wallet balances for an address.

    Args:
        address: Wallet address (0x...)
        network: Network name (ethereum, polygon, arbitrum, optimism)
        wallet_provider: Wallet provider client
        coingecko_client: CoinGecko client for prices

    Returns:
        Formatted wallet balance information
    """
    try:
        # Get portfolio balances
        portfolio = await wallet_provider.get_portfolio_balances(
            address=address,
            network=network,
        )

        # Format native balance
        native = portfolio["native"]
        native_symbol = native["token"]
        native_balance = Decimal(native["balance"])

        # Get ETH price for valuation
        eth_price_data = await coingecko_client.get_price("ethereum")
        eth_price = Decimal(str(eth_price_data["price"]))
        native_value_usd = native_balance * eth_price

        # Build response
        lines = [
            f"Wallet Balance: {address[:10]}...{address[-8:]}",
            f"Network: {network.capitalize()}",
            f"",
            f"**Native Balance:**",
            f"• {native_symbol}: {native['formatted']} (${native_value_usd:,.2f})",
        ]

        # Token balances
        tokens = portfolio["tokens"]
        if tokens:
            lines.append(f"")
            lines.append(f"**Token Balances:**")

            total_value = native_value_usd

            for token in tokens:
                symbol = token["symbol"]
                balance = Decimal(token["balance"])

                # Get token price
                try:
                    coin_id = coingecko_client.resolve_token_symbol(symbol)
                    if coin_id:
                        price_data = await coingecko_client.get_price(coin_id)
                        price = Decimal(str(price_data["price"]))
                        value = balance * price
                        total_value += value

                        lines.append(
                            f"• {symbol}: {token['formatted']} (${value:,.2f})"
                        )
                    else:
                        lines.append(f"• {symbol}: {token['formatted']}")

                except Exception as e:
                    logger.warning(f"Failed to get price for {symbol}: {e}")
                    lines.append(f"• {symbol}: {token['formatted']}")

            lines.append(f"")
            lines.append(f"**Total Portfolio Value:** ${total_value:,.2f}")
        else:
            lines.append(f"")
            lines.append(f"No token balances found.")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}")
        return f"Error: {str(e)}"


async def get_protocol_info_tool(
    protocol: str,
    defillama_client: DeFiLlamaClient,
) -> str:
    """
    Get DeFi protocol information.

    Args:
        protocol: Protocol name or slug (e.g., "aave", "uniswap")
        defillama_client: DeFiLlama client

    Returns:
        Protocol information string
    """
    try:
        # Search for protocol first
        matches = await defillama_client.search_protocol(protocol)

        if not matches:
            return (
                f"Protocol '{protocol}' not found. Try searching for similar protocols."
            )

        # Get detailed info for best match
        best_match = matches[0]
        protocol_slug = best_match.get("slug", protocol.lower())

        tvl_data = await defillama_client.get_protocol_tvl(protocol_slug)

        tvl_usd = tvl_data["current_tvl_usd"]

        return (
            f"Protocol: {tvl_data['protocol']}\n"
            f"\n"
            f"**Overview:**\n"
            f"• Category: {tvl_data['category']}\n"
            f"• Total Value Locked: ${tvl_usd:,.0f}\n"
            f"• Chains: {', '.join(tvl_data['chains'][:5])}\n"
            f"• Website: {tvl_data['url']}\n"
            f"\n"
            f"**Description:**\n"
            f"{tvl_data['description'][:200]}...\n"
        )

    except Exception as e:
        logger.error(f"Error getting protocol info: {e}")
        return f"Error: {str(e)}"


async def get_top_protocols_tool(
    defillama_client: DeFiLlamaClient,
    limit: int = 10,
) -> str:
    """
    Get top DeFi protocols by TVL.

    Args:
        limit: Number of protocols to return
        defillama_client: DeFiLlama client

    Returns:
        Top protocols list
    """
    try:
        protocols = await defillama_client.get_top_protocols(limit=limit)

        lines = [
            f"Top {limit} DeFi Protocols by TVL:\n",
        ]

        for i, protocol in enumerate(protocols, 1):
            name = protocol.get("name", "Unknown")
            tvl = protocol.get("tvl", 0)
            category = protocol.get("category", "Unknown")

            lines.append(f"{i}. **{name}** ({category}): ${tvl:,.0f}")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error getting top protocols: {e}")
        return f"Error: {str(e)}"


async def get_token_price_tool(
    token: str,
    coingecko_client: CoinGeckoClient,
) -> str:
    """
    Get current token price and 24h change.

    Args:
        token: Token symbol (BTC, ETH, etc.)
        coingecko_client: CoinGecko client

    Returns:
        Price information string
    """
    try:
        # Resolve symbol to coin ID
        coin_id = coingecko_client.resolve_token_symbol(token)

        if not coin_id:
            # Try searching
            results = await coingecko_client.search_coins(token)
            if not results:
                return f"Token '{token}' not found. Try a different symbol."

            coin_id = results[0]["id"]

        # Get price data
        price_data = await coingecko_client.get_price(coin_id)

        price = price_data["price"]
        change_24h = price_data["change_24h"]

        # Format change with color indicator
        change_indicator = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
        change_sign = "+" if change_24h > 0 else ""

        return (
            f"Token Price: {token.upper()}\n"
            f"\n"
            f"• Current Price: ${price:,.2f}\n"
            f"• 24h Change: {change_indicator} {change_sign}{change_24h:.2f}%\n"
        )

    except Exception as e:
        logger.error(f"Error getting token price: {e}")
        return f"Error: {str(e)}"


async def get_market_overview_tool(
    coingecko_client: CoinGeckoClient,
) -> str:
    """
    Get crypto market overview.

    Args:
        coingecko_client: CoinGecko client

    Returns:
        Market overview string
    """
    try:
        # Get prices for major cryptocurrencies
        major_coins = ["bitcoin", "ethereum", "binancecoin", "ripple", "cardano"]

        prices = await coingecko_client.get_multiple_prices(major_coins)

        lines = [
            "Crypto Market Overview:\n",
        ]

        coin_names = {
            "bitcoin": "Bitcoin (BTC)",
            "ethereum": "Ethereum (ETH)",
            "binancecoin": "BNB",
            "ripple": "XRP",
            "cardano": "Cardano (ADA)",
        }

        for coin_id, data in prices.items():
            name = coin_names.get(coin_id, coin_id.capitalize())
            price = data["price"]
            change = data["change_24h"]

            change_indicator = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            change_sign = "+" if change > 0 else ""

            lines.append(
                f"• {name}: ${price:,.2f} ({change_indicator} {change_sign}{change:.2f}%)"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        return f"Error: {str(e)}"


async def get_yield_opportunities_tool(
    defillama_client: DeFiLlamaClient,
    protocol: Optional[str] = None,
    chain: Optional[str] = None,
) -> str:
    """
    Get top yield farming opportunities.

    Args:
        protocol: Filter by protocol (optional)
        chain: Filter by chain (optional)
        defillama_client: DeFiLlama client

    Returns:
        Yield opportunities list
    """
    try:
        pools = await defillama_client.get_protocol_yields(
            protocol=protocol,
            chain=chain,
        )

        if not pools:
            return "No yield opportunities found for the given criteria."

        lines = [
            "Top Yield Opportunities:\n",
        ]

        for i, pool in enumerate(pools[:10], 1):
            project = pool.get("project", "Unknown")
            symbol = pool.get("symbol", "")
            apy = pool.get("apy", 0)
            tvl = pool.get("tvlUsd", 0)
            chain_name = pool.get("chain", "Unknown")

            lines.append(
                f"{i}. **{project}** - {symbol} ({chain_name})\n"
                f"   APY: {apy:.2f}% | TVL: ${tvl:,.0f}"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error getting yield opportunities: {e}")
        return f"Error: {str(e)}"
