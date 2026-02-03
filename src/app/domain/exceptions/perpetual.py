"""
Perpetual Futures Domain Exceptions.

Domain-specific exceptions for perpetual trading operations.
"""

from app.domain.exceptions.base import DomainError


class PerpetualError(DomainError):
    """
    Base exception for perpetual futures operations.

    All perpetual-specific exceptions should inherit from this class.
    """

    error_code: str = "PERPETUAL_ERROR"


class SymbolNotFoundError(PerpetualError):
    """
    Exception raised when a trading symbol doesn't exist.

    This typically occurs when:
    - The symbol is invalid
    - The market is delisted
    """

    error_code: str = "PERPETUAL_SYMBOL_NOT_FOUND"

    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Perpetual symbol not found: {symbol}")


class InvalidAddressError(PerpetualError):
    """
    Exception raised when wallet address format is invalid.

    This typically occurs when:
    - Address is not a valid hex string
    - Address length is incorrect
    """

    error_code: str = "PERPETUAL_INVALID_ADDRESS"

    def __init__(self, address: str, message: str | None = None):
        self.address = address
        super().__init__(message or f"Invalid wallet address: {address}")


class HyperliquidAPIError(PerpetualError):
    """
    Exception raised when Hyperliquid API is unavailable or returns error.

    This typically occurs when:
    - API is down
    - Rate limits exceeded
    - Network issues
    """

    error_code: str = "HYPERLIQUID_API_ERROR"

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(
            f"Hyperliquid API error: {message}"
            + (f" (status: {status_code})" if status_code else "")
        )


class InsufficientMarginError(PerpetualError):
    """
    Exception raised when margin is insufficient for operation.
    """

    error_code: str = "PERPETUAL_INSUFFICIENT_MARGIN"

    def __init__(self, required: str, available: str):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient margin: required {required}, available {available}"
        )
