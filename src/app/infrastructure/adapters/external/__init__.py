"""
External API adapters for Agent Squad.

This package contains clients for external DeFi, enterprise, and blockchain APIs.
"""

from .oneinch_client import OneInchClient
from .defillama_client import DefiLlamaClient
from .coingecko_client import CoinGeckoClient
from .hyperliquid_client import HyperliquidClient

__all__ = [
    "OneInchClient",
    "DefiLlamaClient",
    "CoinGeckoClient",
    "HyperliquidClient",
]
