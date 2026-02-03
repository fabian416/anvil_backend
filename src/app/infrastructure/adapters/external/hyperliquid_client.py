"""
Hyperliquid API Client.

Provides access to Hyperliquid exchange:
- Perpetual futures trading
- Spot trading (swaps)
- Order book data
- Funding rates
- Liquidation data
- Position information
- Order placement (trading)

API Docs: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
Rate Limit: 1200 requests/minute
"""

import hmac
import hashlib
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class OrderBook:
    """Order book data."""

    symbol: str
    bids: list[tuple[float, float]]  # (price, size)
    asks: list[tuple[float, float]]  # (price, size)
    timestamp: int


@dataclass
class FundingRate:
    """Funding rate data."""

    symbol: str
    funding_rate: float  # 8-hour funding rate
    next_funding_time: int  # Unix timestamp
    timestamp: int


@dataclass
class Liquidation:
    """Liquidation event data."""

    symbol: str
    side: str  # "buy" or "sell"
    size: float
    price: float
    timestamp: int


@dataclass
class Position:
    """User position data."""

    symbol: str
    side: str  # "long" or "short"
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    leverage: float
    liquidation_price: float


@dataclass
class Order:
    """Order data."""

    order_id: str
    symbol: str
    side: str  # "buy" or "sell"
    size: float
    price: float | None  # None for market orders
    status: str  # "open", "filled", "cancelled"
    filled_size: float
    timestamp: int


@dataclass
class SpotMeta:
    """Spot market metadata."""

    name: str  # e.g., "ETH/USDC"
    base_token: str  # e.g., "ETH"
    quote_token: str  # e.g., "USDC"
    index: int  # Spot market index
    min_size: float
    price_decimals: int
    size_decimals: int


@dataclass
class SpotQuote:
    """Spot swap quote from Hyperliquid."""

    from_token: str
    to_token: str
    from_amount: float
    to_amount: float
    price: float  # Effective price (to_amount / from_amount)
    mid_price: float  # Mid market price
    spread_bps: float  # Spread in basis points
    timestamp: int


class HyperliquidClient:
    """
    Hyperliquid API client for perpetual futures and spot trading.

    Features:
    - Market data (order book, funding rates, liquidations)
    - Spot trading (swaps) with real-time quotes
    - Position management
    - Order placement and management
    - Account information
    """

    BASE_URL = "https://api.hyperliquid.xyz"

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        testnet: bool = False,
    ):
        """
        Initialize Hyperliquid client.

        Args:
            api_key: API key for authenticated requests (optional for public data)
            api_secret: API secret for signing requests (required for trading)
            testnet: Use testnet API (default: False)
        """
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = (
            "https://api.hyperliquid-testnet.xyz" if testnet else self.BASE_URL
        )
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            headers={
                "Content-Type": "application/json",
            },
        )

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    def _sign_request(self, data: dict) -> str:
        """
        Sign request data for authenticated endpoints.

        Args:
            data: Request payload

        Returns:
            Signature string
        """
        if not self._api_secret:
            raise ValueError("API secret required for authenticated requests")

        message = str(data).encode()
        signature = hmac.new(
            self._api_secret.encode(), message, hashlib.sha256
        ).hexdigest()
        return signature

    async def get_order_book(self, symbol: str, depth: int = 20) -> OrderBook:
        """
        Get order book for a symbol.

        Args:
            symbol: Trading pair (e.g., "ETH-PERP")
            depth: Order book depth (default: 20)

        Returns:
            OrderBook with bids and asks

        Example:
            >>> order_book = await client.get_order_book("ETH-PERP")
            >>> print(f"Best bid: ${order_book.bids[0][0]}")
            >>> print(f"Best ask: ${order_book.asks[0][0]}")
        """
        response = await self._client.post(
            "/info",
            json={
                "type": "l2Book",
                "coin": symbol,
                "nSigFigs": 5,
            },
        )
        response.raise_for_status()
        data = response.json()

        # Parse order book
        levels = data.get("levels", [])
        bids = (
            [(float(level["px"]), float(level["sz"])) for level in levels[0]]
            if levels
            else []
        )
        asks = (
            [(float(level["px"]), float(level["sz"])) for level in levels[1]]
            if len(levels) > 1
            else []
        )

        return OrderBook(
            symbol=symbol,
            bids=bids[:depth],
            asks=asks[:depth],
            timestamp=int(time.time() * 1000),
        )

    async def get_funding_rate(self, symbol: str) -> FundingRate:
        """
        Get current funding rate for a symbol.

        Args:
            symbol: Trading pair (e.g., "ETH-PERP")

        Returns:
            FundingRate with current rate and next funding time

        Example:
            >>> funding = await client.get_funding_rate("ETH-PERP")
            >>> print(f"8h funding rate: {funding.funding_rate * 100:.4f}%")
        """
        response = await self._client.post(
            "/info",
            json={
                "type": "metaAndAssetCtxs",
            },
        )
        response.raise_for_status()
        data = response.json()

        # Find symbol data
        for asset in data[1]:
            if asset.get("coin") == symbol:
                funding_rate = float(asset.get("funding", 0))
                next_funding = int(asset.get("nextFunding", time.time() * 1000))

                return FundingRate(
                    symbol=symbol,
                    funding_rate=funding_rate,
                    next_funding_time=next_funding,
                    timestamp=int(time.time() * 1000),
                )

        raise ValueError(f"Symbol {symbol} not found")

    async def get_liquidations(
        self,
        symbol: str | None = None,
        hours: int = 24,
    ) -> list[Liquidation]:
        """
        Get recent liquidations.

        Args:
            symbol: Filter by symbol (optional, None = all symbols)
            hours: Look back period in hours (default: 24)

        Returns:
            List of liquidations

        Example:
            >>> liquidations = await client.get_liquidations("ETH-PERP", hours=1)
            >>> total_liq_volume = sum(liq.size * liq.price for liq in liquidations)
            >>> print(f"1h liquidation volume: ${total_liq_volume:,.2f}")
        """
        response = await self._client.post(
            "/info",
            json={
                "type": "clearinghouseState",
                "user": "0x0000000000000000000000000000000000000000",  # Public data
            },
        )
        response.raise_for_status()
        data = response.json()

        # Parse liquidations
        liquidations = []
        cutoff_time = int((time.time() - hours * 3600) * 1000)

        for liq_data in data.get("assetPositions", []):
            if symbol and liq_data.get("coin") != symbol:
                continue

            timestamp = int(liq_data.get("time", 0))
            if timestamp < cutoff_time:
                continue

            liquidations.append(
                Liquidation(
                    symbol=liq_data.get("coin", ""),
                    side=liq_data.get("side", ""),
                    size=float(liq_data.get("szi", 0)),
                    price=float(liq_data.get("px", 0)),
                    timestamp=timestamp,
                )
            )

        return liquidations

    async def get_user_positions(self, address: str) -> list[Position]:
        """
        Get user's current positions.

        Args:
            address: User's Ethereum address

        Returns:
            List of open positions

        Requires:
            API key for authentication

        Example:
            >>> positions = await client.get_user_positions("0x...")
            >>> for pos in positions:
            >>>     print(f"{pos.symbol}: {pos.size} @ ${pos.entry_price}")
        """
        response = await self._client.post(
            "/info",
            json={
                "type": "clearinghouseState",
                "user": address,
            },
        )
        response.raise_for_status()
        data = response.json()

        # Parse positions
        positions = []
        for pos_data in data.get("assetPositions", []):
            size = float(pos_data.get("position", {}).get("szi", 0))
            if size == 0:
                continue  # Skip closed positions

            positions.append(
                Position(
                    symbol=pos_data.get("position", {}).get("coin", ""),
                    side="long" if size > 0 else "short",
                    size=abs(size),
                    entry_price=float(pos_data.get("position", {}).get("entryPx", 0)),
                    mark_price=float(
                        pos_data.get("position", {}).get("positionValue", 0)
                    )
                    / abs(size)
                    if size != 0
                    else 0,
                    unrealized_pnl=float(
                        pos_data.get("position", {}).get("unrealizedPnl", 0)
                    ),
                    leverage=float(
                        pos_data.get("position", {}).get("leverage", {}).get("value", 1)
                    ),
                    liquidation_price=float(
                        pos_data.get("position", {}).get("liquidationPx", 0)
                    ),
                )
            )

        return positions

    async def place_order(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float | None = None,
        reduce_only: bool = False,
    ) -> Order:
        """
        Place a new order.

        Args:
            symbol: Trading pair (e.g., "ETH-PERP")
            side: "buy" or "sell"
            size: Order size (contracts)
            price: Limit price (None for market order)
            reduce_only: Only reduce existing position (default: False)

        Returns:
            Order with order ID and status

        Requires:
            API key and secret for authentication

        Example:
            >>> # Place limit order
            >>> order = await client.place_order("ETH-PERP", "buy", 1.0, 3000.0)
            >>> print(f"Order ID: {order.order_id}")
            >>>
            >>> # Place market order
            >>> order = await client.place_order("ETH-PERP", "buy", 1.0)
        """
        if not self._api_key or not self._api_secret:
            raise ValueError("API key and secret required for trading")

        # Build order request
        order_data = {
            "coin": symbol,
            "is_buy": side.lower() == "buy",
            "sz": size,
            "limit_px": price if price else 0,
            "order_type": {"limit": price is not None, "market": price is None},
            "reduce_only": reduce_only,
        }

        # Sign request
        signature = self._sign_request(order_data)

        response = await self._client.post(
            "/exchange",
            json={
                "type": "order",
                "orders": [order_data],
            },
            headers={
                "X-API-KEY": self._api_key,
                "X-SIGNATURE": signature,
            },
        )
        response.raise_for_status()
        data = response.json()

        # Parse response
        order_response = (
            data.get("response", {}).get("data", {}).get("statuses", [{}])[0]
        )

        return Order(
            order_id=order_response.get("resting", {}).get("oid", ""),
            symbol=symbol,
            side=side,
            size=size,
            price=price,
            status="open",
            filled_size=0.0,
            timestamp=int(time.time() * 1000),
        )

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order ID to cancel
            symbol: Trading pair

        Returns:
            True if cancelled successfully

        Requires:
            API key and secret for authentication
        """
        if not self._api_key or not self._api_secret:
            raise ValueError("API key and secret required for trading")

        cancel_data = {
            "coin": symbol,
            "oid": order_id,
        }

        signature = self._sign_request(cancel_data)

        response = await self._client.post(
            "/exchange",
            json={
                "type": "cancel",
                "cancels": [cancel_data],
            },
            headers={
                "X-API-KEY": self._api_key,
                "X-SIGNATURE": signature,
            },
        )
        response.raise_for_status()

        return True

    # ========================================
    # BALANCE METHODS (Perps + Spot)
    # ========================================

    async def get_perps_balance(self, address: str) -> dict[str, float]:
        """
        Get user's Perps (perpetuals) account balance on Hyperliquid.

        This is where funds land after bridging from Arbitrum/Base.
        User must transfer from Perps → Spot to do spot swaps.

        Args:
            address: User's Ethereum address (0x...)

        Returns:
            Dictionary of token symbol → balance
            Example: {"USDC": 100.5, "USDT": 50.0}

        Example:
            >>> balances = await client.get_perps_balance("0x123...")
            >>> print(f"USDC on Perps: {balances.get('USDC', 0)}")
        """
        try:
            response = await self._client.post(
                "/info",
                json={
                    "type": "clearinghouseState",
                    "user": address,
                },
            )
            response.raise_for_status()
            data = response.json()

            balances: dict[str, float] = {}

            # Parse margin summary for USDC balance
            margin_summary = data.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))

            # The main balance in perps is typically USDC
            if account_value > 0:
                balances["USDC"] = account_value

            # Also check withdrawable balance
            withdrawable = data.get("withdrawable", "0")
            if float(withdrawable) > 0:
                # Use withdrawable as the actual available USDC
                balances["USDC"] = float(withdrawable)

            return balances

        except Exception as e:
            # Return empty balances on error (user may not have Hyperliquid account)
            return {}

    async def get_spot_balance(self, address: str) -> dict[str, float]:
        """
        Get user's Spot account balance on Hyperliquid.

        This is where funds must be to execute spot swaps (meme tokens).
        User must transfer from Perps → Spot before swapping.

        Args:
            address: User's Ethereum address (0x...)

        Returns:
            Dictionary of token symbol → balance
            Example: {"USDC": 50.0, "PURR": 10000.0}

        Example:
            >>> balances = await client.get_spot_balance("0x123...")
            >>> print(f"USDC on Spot: {balances.get('USDC', 0)}")
            >>> print(f"PURR on Spot: {balances.get('PURR', 0)}")
        """
        try:
            response = await self._client.post(
                "/info",
                json={
                    "type": "spotClearinghouseState",
                    "user": address,
                },
            )
            response.raise_for_status()
            data = response.json()

            balances: dict[str, float] = {}

            # Parse spot balances
            for balance_data in data.get("balances", []):
                coin = balance_data.get("coin", "")
                # "hold" is locked, "total" is total including hold
                total = float(balance_data.get("total", 0))

                if total > 0 and coin:
                    balances[coin] = total

            return balances

        except Exception as e:
            # Return empty balances on error (user may not have Hyperliquid account)
            return {}

    async def get_all_balances(self, address: str) -> dict[str, dict[str, float]]:
        """
        Get user's complete Hyperliquid balances (both Perps and Spot).

        Args:
            address: User's Ethereum address (0x...)

        Returns:
            Dictionary with "perps" and "spot" sub-dictionaries
            Example: {
                "perps": {"USDC": 100.0},
                "spot": {"USDC": 50.0, "PURR": 10000.0}
            }

        Example:
            >>> all_balances = await client.get_all_balances("0x123...")
            >>> perps_usdc = all_balances["perps"].get("USDC", 0)
            >>> spot_usdc = all_balances["spot"].get("USDC", 0)
            >>> total_usdc = perps_usdc + spot_usdc
        """
        perps_balance = await self.get_perps_balance(address)
        spot_balance = await self.get_spot_balance(address)

        return {
            "perps": perps_balance,
            "spot": spot_balance,
        }

    # ========================================
    # SPOT TRADING METHODS
    # ========================================

    async def get_spot_meta(self) -> list[SpotMeta]:
        """
        Get metadata for all spot markets.

        Returns:
            List of SpotMeta with market information

        Example:
            >>> markets = await client.get_spot_meta()
            >>> for m in markets:
            ...     print(f"{m.name}: {m.base_token}/{m.quote_token}")
        """
        response = await self._client.post("/info", json={"type": "spotMeta"})
        response.raise_for_status()
        data = response.json()

        markets = []
        tokens = data.get("tokens", [])
        universe = data.get("universe", [])

        for i, market in enumerate(universe):
            # Get token names from indices
            base_idx = market.get("tokens", [0, 0])[0]
            quote_idx = market.get("tokens", [0, 0])[1]

            base_token = (
                tokens[base_idx].get("name", f"TOKEN{base_idx}")
                if base_idx < len(tokens)
                else f"TOKEN{base_idx}"
            )
            quote_token = (
                tokens[quote_idx].get("name", f"TOKEN{quote_idx}")
                if quote_idx < len(tokens)
                else f"TOKEN{quote_idx}"
            )

            markets.append(
                SpotMeta(
                    name=market.get("name", f"{base_token}/{quote_token}"),
                    base_token=base_token,
                    quote_token=quote_token,
                    index=i,
                    min_size=float(market.get("minSz", 0.001)),
                    price_decimals=int(market.get("priceSzDecimals", 2)),
                    size_decimals=int(market.get("szDecimals", 4)),
                )
            )

        return markets

    async def get_spot_order_book(self, symbol: str, depth: int = 20) -> OrderBook:
        """
        Get order book for a spot market.

        Args:
            symbol: Spot pair (e.g., "ETH/USDC" or "@1" for index 1)
            depth: Order book depth (default: 20)

        Returns:
            OrderBook with bids and asks

        Example:
            >>> order_book = await client.get_spot_order_book("ETH/USDC")
            >>> print(f"Best bid: ${order_book.bids[0][0]}")
            >>> print(f"Best ask: ${order_book.asks[0][0]}")
        """
        # Convert symbol name to spot format if needed
        coin = symbol if symbol.startswith("@") else symbol

        response = await self._client.post(
            "/info",
            json={
                "type": "l2Book",
                "coin": coin,
            },
        )
        response.raise_for_status()
        data = response.json()

        # Parse order book
        levels = data.get("levels", [])
        bids = (
            [(float(level["px"]), float(level["sz"])) for level in levels[0]]
            if levels
            else []
        )
        asks = (
            [(float(level["px"]), float(level["sz"])) for level in levels[1]]
            if len(levels) > 1
            else []
        )

        return OrderBook(
            symbol=symbol,
            bids=bids[:depth],
            asks=asks[:depth],
            timestamp=int(time.time() * 1000),
        )

    async def get_spot_price(self, base_token: str, quote_token: str = "USDC") -> float:
        """
        Get current spot price for a token pair.

        Args:
            base_token: Base token (e.g., "ETH", "BTC")
            quote_token: Quote token (default: "USDC")

        Returns:
            Current mid-market price

        Example:
            >>> price = await client.get_spot_price("ETH", "USDC")
            >>> print(f"ETH/USDC: ${price:.2f}")
        """
        symbol = f"{base_token}/{quote_token}"
        order_book = await self.get_spot_order_book(symbol)

        if order_book.bids and order_book.asks:
            best_bid = order_book.bids[0][0]
            best_ask = order_book.asks[0][0]
            return (best_bid + best_ask) / 2
        elif order_book.bids:
            return order_book.bids[0][0]
        elif order_book.asks:
            return order_book.asks[0][0]

        raise ValueError(f"No price data for {symbol}")

    async def get_spot_quote(
        self,
        from_token: str,
        to_token: str,
        amount: float,
    ) -> SpotQuote:
        """
        Get a spot swap quote for exchanging tokens.

        Args:
            from_token: Token to sell (e.g., "ETH")
            to_token: Token to buy (e.g., "USDC")
            amount: Amount of from_token to sell

        Returns:
            SpotQuote with expected output and pricing

        Example:
            >>> quote = await client.get_spot_quote("ETH", "USDC", 1.0)
            >>> print(f"1 ETH = {quote.to_amount:.2f} USDC")
            >>> print(f"Effective rate: ${quote.price:.2f}")
        """
        # Determine if we're selling base or quote
        # Try both orderings: from/to and to/from
        symbol = f"{from_token}/{to_token}"
        reverse_symbol = f"{to_token}/{from_token}"

        try:
            order_book = await self.get_spot_order_book(symbol)
            is_sell = True  # Selling from_token (base) for to_token (quote)
        except Exception:
            try:
                order_book = await self.get_spot_order_book(reverse_symbol)
                is_sell = False  # Buying from_token with to_token
            except Exception:
                raise ValueError(f"No spot market found for {from_token}/{to_token}")

        if is_sell:
            # Selling base token - use bids (others buying from us)
            if not order_book.bids:
                raise ValueError(f"No bid liquidity for {symbol}")

            # Calculate output by walking through order book
            remaining = amount
            total_output = 0.0

            for price, size in order_book.bids:
                if remaining <= 0:
                    break
                fill_size = min(remaining, size)
                total_output += fill_size * price
                remaining -= fill_size

            if remaining > 0:
                # Not enough liquidity - estimate rest at worst price
                total_output += (
                    remaining * order_book.bids[-1][0] if order_book.bids else 0
                )

            effective_price = total_output / amount if amount > 0 else 0
            mid_price = (
                (order_book.bids[0][0] + order_book.asks[0][0]) / 2
                if order_book.asks
                else order_book.bids[0][0]
            )
            spread_bps = (
                ((order_book.asks[0][0] - order_book.bids[0][0]) / mid_price * 10000)
                if order_book.asks
                else 0
            )

            return SpotQuote(
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount=total_output,
                price=effective_price,
                mid_price=mid_price,
                spread_bps=spread_bps,
                timestamp=int(time.time() * 1000),
            )
        else:
            # Buying base token - use asks (others selling to us)
            if not order_book.asks:
                raise ValueError(f"No ask liquidity for {reverse_symbol}")

            # We have 'amount' of from_token (which is the quote in reverse_symbol)
            # We want to buy to_token (which is the base in reverse_symbol)
            remaining_quote = amount
            total_base = 0.0

            for price, size in order_book.asks:
                if remaining_quote <= 0:
                    break
                # cost = size * price (quote needed to buy 'size' base)
                cost = size * price
                if cost <= remaining_quote:
                    total_base += size
                    remaining_quote -= cost
                else:
                    # Partial fill
                    fill_size = remaining_quote / price
                    total_base += fill_size
                    remaining_quote = 0

            effective_price = (
                amount / total_base if total_base > 0 else 0
            )  # Price in from_token per to_token
            mid_price = (
                (order_book.bids[0][0] + order_book.asks[0][0]) / 2
                if order_book.bids
                else order_book.asks[0][0]
            )
            spread_bps = (
                ((order_book.asks[0][0] - order_book.bids[0][0]) / mid_price * 10000)
                if order_book.bids
                else 0
            )

            return SpotQuote(
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount=total_base,
                price=effective_price,
                mid_price=mid_price,
                spread_bps=spread_bps,
                timestamp=int(time.time() * 1000),
            )
