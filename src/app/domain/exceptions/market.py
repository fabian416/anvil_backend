"""
Market-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Protocols and DeFi platforms
- Tokens and assets
- Market data and pricing
"""

from typing import Any
from uuid import UUID

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class ProtocolNotFoundError(ApplicationError):
    """Raised when a protocol is not found."""

    def __init__(
        self,
        protocol_id: str | None = None,
        protocol_name: str | None = None,
        chain: str | None = None,
    ) -> None:
        details = {}
        if protocol_id:
            details["protocol_id"] = protocol_id
        if protocol_name:
            details["protocol_name"] = protocol_name
        if chain:
            details["chain"] = chain
        super().__init__(ErrorCode.MKT_PROTOCOL_NOT_FOUND, details=details)


class TokenNotFoundError(ApplicationError):
    """Raised when a token is not found."""

    def __init__(
        self,
        token_address: str | None = None,
        token_symbol: str | None = None,
        chain: str | None = None,
    ) -> None:
        details = {}
        if token_address:
            details["token_address"] = token_address
        if token_symbol:
            details["token_symbol"] = token_symbol
        if chain:
            details["chain"] = chain
        super().__init__(ErrorCode.MKT_TOKEN_NOT_FOUND, details=details)


class MarketDataUnavailableError(ApplicationError):
    """Raised when market data is temporarily unavailable."""

    def __init__(
        self,
        data_type: str | None = None,
        source: str | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        details = {}
        if data_type:
            details["data_type"] = data_type
        if source:
            details["source"] = source
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        super().__init__(ErrorCode.MKT_DATA_UNAVAILABLE, details=details)


class InvalidSymbolError(ApplicationError):
    """Raised when an invalid token symbol is provided."""

    def __init__(
        self,
        symbol: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if symbol:
            details["symbol"] = symbol
        if reason:
            details["reason"] = reason
        super().__init__(ErrorCode.MKT_INVALID_SYMBOL, details=details, field="symbol")


class InvalidMarketChainError(ApplicationError):
    """Raised when an unsupported blockchain is specified for market data."""

    def __init__(
        self,
        chain: str | None = None,
        supported_chains: list[str] | None = None,
    ) -> None:
        details = {}
        if chain:
            details["chain"] = chain
        if supported_chains:
            details["supported_chains"] = supported_chains
        super().__init__(ErrorCode.MKT_INVALID_CHAIN, details=details, field="chain")


class MarketRateLimitError(ApplicationError):
    """Raised when market data rate limit is exceeded."""

    def __init__(
        self,
        retry_after_seconds: int | None = None,
        source: str | None = None,
    ) -> None:
        details = {}
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        if source:
            details["source"] = source
        super().__init__(ErrorCode.MKT_RATE_LIMIT, details=details)


# Additional market-specific exceptions


class PriceDataStaleError(ApplicationError):
    """Raised when price data is stale/outdated."""

    def __init__(
        self,
        token: str | None = None,
        last_updated: str | None = None,
        max_age_seconds: int | None = None,
    ) -> None:
        details = {}
        if token:
            details["token"] = token
        if last_updated:
            details["last_updated"] = last_updated
        if max_age_seconds is not None:
            details["max_age_seconds"] = max_age_seconds
        super().__init__(
            ErrorCode.MKT_DATA_UNAVAILABLE,
            details=details,
            override_message="Price data is outdated",
        )


class LiquidityInsufficientError(ApplicationError):
    """Raised when liquidity is insufficient for operation."""

    def __init__(
        self,
        token: str | None = None,
        required_liquidity: str | None = None,
        available_liquidity: str | None = None,
        pool: str | None = None,
    ) -> None:
        details = {}
        if token:
            details["token"] = token
        if required_liquidity:
            details["required_liquidity"] = required_liquidity
        if available_liquidity:
            details["available_liquidity"] = available_liquidity
        if pool:
            details["pool"] = pool
        super().__init__(
            ErrorCode.MKT_DATA_UNAVAILABLE,
            details=details,
            override_message="Insufficient liquidity for this operation",
        )


class SlippageExceededError(ApplicationError):
    """Raised when slippage exceeds tolerance."""

    def __init__(
        self,
        expected_price: str | None = None,
        actual_price: str | None = None,
        slippage_tolerance: float | None = None,
        actual_slippage: float | None = None,
    ) -> None:
        details = {}
        if expected_price:
            details["expected_price"] = expected_price
        if actual_price:
            details["actual_price"] = actual_price
        if slippage_tolerance is not None:
            details["slippage_tolerance"] = slippage_tolerance
        if actual_slippage is not None:
            details["actual_slippage"] = actual_slippage
        super().__init__(
            ErrorCode.MKT_DATA_UNAVAILABLE,
            details=details,
            override_message="Price slippage exceeds tolerance",
        )


class PoolNotFoundError(ApplicationError):
    """Raised when a liquidity pool is not found."""

    def __init__(
        self,
        pool_address: str | None = None,
        token_pair: str | None = None,
        protocol: str | None = None,
    ) -> None:
        details = {}
        if pool_address:
            details["pool_address"] = pool_address
        if token_pair:
            details["token_pair"] = token_pair
        if protocol:
            details["protocol"] = protocol
        super().__init__(
            ErrorCode.MKT_PROTOCOL_NOT_FOUND,
            details=details,
            override_message="Liquidity pool not found",
        )


class OracleDataError(ApplicationError):
    """Raised when oracle data is unavailable or invalid."""

    def __init__(
        self,
        oracle: str | None = None,
        feed: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if oracle:
            details["oracle"] = oracle
        if feed:
            details["feed"] = feed
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.MKT_DATA_UNAVAILABLE,
            details=details,
            override_message="Oracle price feed unavailable",
        )


class TradingPairNotSupportedError(ApplicationError):
    """Raised when a trading pair is not supported."""

    def __init__(
        self,
        base_token: str | None = None,
        quote_token: str | None = None,
        exchange: str | None = None,
    ) -> None:
        details = {}
        if base_token:
            details["base_token"] = base_token
        if quote_token:
            details["quote_token"] = quote_token
        if exchange:
            details["exchange"] = exchange
        super().__init__(
            ErrorCode.MKT_INVALID_SYMBOL,
            details=details,
            override_message="Trading pair not supported",
        )


class ChainDataSyncError(ApplicationError):
    """Raised when chain data is out of sync."""

    def __init__(
        self,
        chain: str | None = None,
        blocks_behind: int | None = None,
    ) -> None:
        details = {}
        if chain:
            details["chain"] = chain
        if blocks_behind is not None:
            details["blocks_behind"] = blocks_behind
        super().__init__(
            ErrorCode.MKT_DATA_UNAVAILABLE,
            details=details,
            override_message="Blockchain data is syncing",
        )
