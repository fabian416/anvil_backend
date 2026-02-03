"""
Hyperliquid perpetual futures API client.
"""

import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


class HyperliquidClient:
    """
    Client for Hyperliquid perpetual futures exchange.

    Provides position opening/closing and market data.
    """

    BASE_URL = "https://api.hyperliquid.xyz"

    def __init__(self, testnet: bool = True):
        """
        Initialize Hyperliquid client.

        Args:
            testnet: Use testnet API (True) or mainnet (False)
        """
        self.testnet = testnet
        self.base_url = (
            "https://api.hyperliquid-testnet.xyz"
            if testnet
            else "https://api.hyperliquid.xyz"
        )
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )

    async def get_market_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current market price for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., "BTC", "ETH")

        Returns:
            Price data including bid, ask, last
        """
        try:
            response = await self._client.post(
                "/info", json={"type": "l2Book", "coin": symbol}
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Hyperliquid price for {symbol}: {data}")

            return data

        except httpx.HTTPError as e:
            logger.error(f"Hyperliquid price error: {e}")
            raise

    async def get_user_state(self, user_address: str) -> Dict[str, Any]:
        """
        Get user's current positions and balances.

        Args:
            user_address: User's wallet address

        Returns:
            User state including positions and balances
        """
        try:
            response = await self._client.post(
                "/info", json={"type": "clearinghouseState", "user": user_address}
            )
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Hyperliquid user state error: {e}")
            raise

    async def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Get current funding rate for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            Funding rate data
        """
        try:
            response = await self._client.post(
                "/info", json={"type": "metaAndAssetCtxs"}
            )
            response.raise_for_status()

            data = response.json()

            # Find the specific coin's funding rate
            for asset in data:
                if asset.get("name") == symbol:
                    return {
                        "symbol": symbol,
                        "funding_rate": asset.get("funding", "0"),
                        "mark_price": asset.get("markPx", "0"),
                    }

            return {"symbol": symbol, "funding_rate": "0"}

        except httpx.HTTPError as e:
            logger.error(f"Hyperliquid funding rate error: {e}")
            raise

    async def calculate_liquidation_price(
        self,
        entry_price: Decimal,
        leverage: int,
        is_long: bool,
        maintenance_margin: Decimal = Decimal("0.03"),  # 3%
    ) -> Decimal:
        """
        Calculate liquidation price for a position.

        Args:
            entry_price: Position entry price
            leverage: Leverage multiplier
            is_long: True for long, False for short
            maintenance_margin: Maintenance margin requirement (default 3%)

        Returns:
            Liquidation price
        """
        # Formula:
        # Long: liquidation = entry * (1 - 1/leverage + maintenance_margin)
        # Short: liquidation = entry * (1 + 1/leverage - maintenance_margin)

        leverage_factor = Decimal("1") / Decimal(leverage)

        if is_long:
            liq_price = entry_price * (
                Decimal("1") - leverage_factor + maintenance_margin
            )
        else:
            liq_price = entry_price * (
                Decimal("1") + leverage_factor - maintenance_margin
            )

        return liq_price

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


class HyperliquidError(Exception):
    """Hyperliquid API error."""

    pass
