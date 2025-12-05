"""
Hyperliquid API Client.

Provides access to Hyperliquid perpetual futures exchange:
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


class HyperliquidClient:
    """
    Hyperliquid API client for perpetual futures trading.
    
    Features:
    - Market data (order book, funding rates, liquidations)
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
            self._api_secret.encode(),
            message,
            hashlib.sha256
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
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Parse order book
        levels = data.get("levels", [])
        bids = [(float(level["px"]), float(level["sz"])) for level in levels[0]] if levels else []
        asks = [(float(level["px"]), float(level["sz"])) for level in levels[1]] if len(levels) > 1 else []
        
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
            }
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
            }
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
            }
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
                    mark_price=float(pos_data.get("position", {}).get("positionValue", 0)) / abs(size) if size != 0 else 0,
                    unrealized_pnl=float(pos_data.get("position", {}).get("unrealizedPnl", 0)),
                    leverage=float(pos_data.get("position", {}).get("leverage", {}).get("value", 1)),
                    liquidation_price=float(pos_data.get("position", {}).get("liquidationPx", 0)),
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
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Parse response
        order_response = data.get("response", {}).get("data", {}).get("statuses", [{}])[0]
        
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
            }
        )
        response.raise_for_status()
        
        return True
