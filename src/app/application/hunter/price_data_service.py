"""Historical price data service.

Collects and preprocesses cryptocurrency price data for LSTM model training.
Based on Hunter AI Bot's data collection module.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np


@dataclass
class PriceDataConfig:
    """Configuration for price data collection."""

    # Data sources
    primary_source: str = "coingecko"  # coingecko, binance, coinbase
    fallback_sources: List[str] = None

    # Time intervals
    default_interval: str = "1h"  # 1m, 5m, 15m, 1h, 4h, 1d
    default_lookback_days: int = 90  # Historical data to fetch

    # Feature engineering
    include_volume: bool = True
    include_market_cap: bool = True
    include_technical_indicators: bool = True

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_minutes: int = 60

    def __post_init__(self):
        """Initialize default fallback sources."""
        if self.fallback_sources is None:
            self.fallback_sources = ["binance", "coinbase"]


@dataclass
class PricePoint:
    """Single price data point."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    market_cap: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "market_cap": self.market_cap,
        }


class PriceDataService:
    """Service for collecting and preprocessing historical price data.

    Provides:
    - Historical OHLCV data collection
    - Data normalization and scaling
    - Feature engineering
    - Train/test split
    """

    def __init__(self, config: PriceDataConfig = None):
        """Initialize price data service.

        Args:
            config: Price data configuration
        """
        self.config = config or PriceDataConfig()

    async def fetch_historical_prices(
        self,
        token_symbol: str,
        days: int = None,
        interval: str = None,
    ) -> List[PricePoint]:
        """Fetch historical price data for a token.

        Args:
            token_symbol: Token symbol (e.g., "ETH")
            days: Days of historical data (default from config)
            interval: Time interval (default from config)

        Returns:
            List of PricePoint objects

        Example:
            >>> service = PriceDataService()
            >>> prices = await service.fetch_historical_prices("ETH", days=30)
            >>> print(f"Fetched {len(prices)} price points")
        """
        days = days or self.config.default_lookback_days
        interval = interval or self.config.default_interval

        # In production, this would call CoinGecko/Binance/Coinbase API
        # For now, generate simulated data
        prices = self._generate_simulated_data(token_symbol, days, interval)

        return prices

    def _generate_simulated_data(
        self, token_symbol: str, days: int, interval: str
    ) -> List[PricePoint]:
        """Generate simulated price data for testing.

        Args:
            token_symbol: Token symbol
            days: Days of data
            interval: Time interval

        Returns:
            List of simulated price points
        """
        # Determine number of data points based on interval
        intervals_per_day = {
            "1m": 1440,
            "5m": 288,
            "15m": 96,
            "1h": 24,
            "4h": 6,
            "1d": 1,
        }

        points_per_day = intervals_per_day.get(interval, 24)
        total_points = days * points_per_day

        # Generate base price trend (with randomness)
        np.random.seed(42)  # For reproducibility in tests
        base_price = 2000.0  # Starting price for ETH
        trend = np.random.randn(total_points).cumsum() * 10
        prices_close = base_price + trend

        # Generate OHLC data
        price_points = []
        current_time = datetime.utcnow() - timedelta(days=days)
        interval_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
        }
        delta = timedelta(minutes=interval_minutes.get(interval, 60))

        for i in range(total_points):
            close = max(prices_close[i], 100.0)  # Prevent negative prices
            high = close * (1 + np.random.uniform(0, 0.02))
            low = close * (1 - np.random.uniform(0, 0.02))
            open_price = (high + low) / 2 + np.random.uniform(-10, 10)

            volume = np.random.uniform(1000000, 10000000)
            market_cap = close * 120000000  # Approx ETH supply

            price_point = PricePoint(
                timestamp=current_time,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                market_cap=market_cap if self.config.include_market_cap else None,
            )

            price_points.append(price_point)
            current_time += delta

        return price_points

    def preprocess_for_lstm(
        self,
        prices: List[PricePoint],
        sequence_length: int = 60,
        target_column: str = "close",
    ) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Preprocess price data for LSTM model.

        Args:
            prices: List of price points
            sequence_length: Number of time steps for LSTM input
            target_column: Column to predict (default: "close")

        Returns:
            Tuple of (X_sequences, y_targets, scaler_params)

        Example:
            >>> service = PriceDataService()
            >>> prices = await service.fetch_historical_prices("ETH")
            >>> X, y, scaler = service.preprocess_for_lstm(prices)
            >>> print(f"X shape: {X.shape}, y shape: {y.shape}")
        """
        # Convert to numpy array
        data = np.array([[p.open, p.high, p.low, p.close, p.volume] for p in prices])

        # Normalize data (min-max scaling)
        scaler_params = {
            "min": data.min(axis=0),
            "max": data.max(axis=0),
        }

        data_normalized = (data - scaler_params["min"]) / (
            scaler_params["max"] - scaler_params["min"] + 1e-8
        )

        # Create sequences
        X_sequences = []
        y_targets = []

        target_idx = {"open": 0, "high": 1, "low": 2, "close": 3, "volume": 4}[
            target_column
        ]

        for i in range(len(data_normalized) - sequence_length):
            X_sequences.append(data_normalized[i : i + sequence_length])
            y_targets.append(data_normalized[i + sequence_length, target_idx])

        X = np.array(X_sequences)
        y = np.array(y_targets)

        return X, y, scaler_params

    def denormalize_prediction(
        self,
        normalized_value: float,
        scaler_params: Dict,
        target_column: str = "close",
    ) -> float:
        """Denormalize a predicted value back to original scale.

        Args:
            normalized_value: Normalized prediction (0-1)
            scaler_params: Scaler parameters from preprocess_for_lstm
            target_column: Column that was predicted

        Returns:
            Denormalized prediction value
        """
        target_idx = {"open": 0, "high": 1, "low": 2, "close": 3, "volume": 4}[
            target_column
        ]

        min_val = scaler_params["min"][target_idx]
        max_val = scaler_params["max"][target_idx]

        return normalized_value * (max_val - min_val) + min_val

    def calculate_technical_indicators(
        self, prices: List[PricePoint]
    ) -> Dict[str, List[float]]:
        """Calculate technical indicators from price data.

        Args:
            prices: List of price points

        Returns:
            Dictionary of indicator name to values

        Indicators calculated:
        - SMA (Simple Moving Average) 7, 25, 99
        - EMA (Exponential Moving Average) 12, 26
        - RSI (Relative Strength Index)
        - MACD (Moving Average Convergence Divergence)
        """
        closes = np.array([p.close for p in prices])

        indicators = {}

        # Simple Moving Averages
        for period in [7, 25, 99]:
            sma = self._calculate_sma(closes, period)
            indicators[f"sma_{period}"] = sma.tolist()

        # Exponential Moving Averages
        for period in [12, 26]:
            ema = self._calculate_ema(closes, period)
            indicators[f"ema_{period}"] = ema.tolist()

        # RSI
        rsi = self._calculate_rsi(closes, period=14)
        indicators["rsi"] = rsi.tolist()

        # MACD
        macd, signal = self._calculate_macd(closes)
        indicators["macd"] = macd.tolist()
        indicators["macd_signal"] = signal.tolist()

        return indicators

    def _calculate_sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average."""
        sma = np.convolve(data, np.ones(period) / period, mode="valid")
        # Pad with NaN for initial period
        return np.concatenate([np.full(period - 1, np.nan), sma])

    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        ema = np.zeros_like(data)
        ema[0] = data[0]
        multiplier = 2 / (period + 1)

        for i in range(1, len(data)):
            ema[i] = (data[i] - ema[i - 1]) * multiplier + ema[i - 1]

        return ema

    def _calculate_rsi(self, data: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index."""
        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gains = np.convolve(gains, np.ones(period) / period, mode="valid")
        avg_losses = np.convolve(losses, np.ones(period) / period, mode="valid")

        rs = avg_gains / (avg_losses + 1e-8)
        rsi = 100 - (100 / (1 + rs))

        # Pad with NaN
        return np.concatenate([np.full(period, np.nan), rsi])

    def _calculate_macd(
        self, data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate MACD and Signal line."""
        ema_fast = self._calculate_ema(data, fast)
        ema_slow = self._calculate_ema(data, slow)

        macd = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd, signal)

        return macd, signal_line

    async def get_latest_price(self, token_symbol: str) -> PricePoint:
        """Get the latest price for a token.

        Args:
            token_symbol: Token symbol

        Returns:
            Latest PricePoint
        """
        prices = await self.fetch_historical_prices(token_symbol, days=1)
        return prices[-1] if prices else None
