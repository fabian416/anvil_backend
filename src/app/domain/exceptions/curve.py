"""
Curve Finance Domain Exceptions.

Domain-specific exceptions for Curve operations following the
existing exception patterns in the codebase.
"""

from app.domain.exceptions.base import DomainError


class CurveError(DomainError):
    """
    Base exception for Curve Finance operations.

    All Curve-specific exceptions should inherit from this class
    to allow for targeted exception handling.
    """

    error_code: str = "CURVE_ERROR"


class PoolNotFoundError(CurveError):
    """
    Exception raised when a pool address doesn't exist.

    This typically occurs when:
    - The pool address is invalid
    - The pool doesn't exist on the specified chain
    - The pool has been deprecated
    """

    error_code: str = "CURVE_POOL_NOT_FOUND"

    def __init__(self, pool_address: str, chain: str = "ethereum"):
        self.pool_address = pool_address
        self.chain = chain
        super().__init__(f"Curve pool not found: {pool_address} on {chain}")


class InvalidTokenError(CurveError):
    """
    Exception raised when a token is not supported on Curve.

    This typically occurs when:
    - The token address is invalid
    - The token is not part of any Curve pool
    - No route exists between the tokens
    """

    error_code: str = "CURVE_INVALID_TOKEN"

    def __init__(self, token_address: str, message: str | None = None):
        self.token_address = token_address
        super().__init__(message or f"Token not supported on Curve: {token_address}")


class CurveAPIError(CurveError):
    """
    Exception raised when the Curve API is unavailable or returns an error.

    This typically occurs when:
    - The Curve API is down
    - Rate limits are exceeded
    - Network connectivity issues
    """

    error_code: str = "CURVE_API_ERROR"

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(
            f"Curve API error: {message}"
            + (f" (status: {status_code})" if status_code else "")
        )


class NoRouteFoundError(CurveError):
    """
    Exception raised when no swap route exists between tokens.

    This typically occurs when:
    - The tokens are not in any common pool
    - The amount is too large for available liquidity
    """

    error_code: str = "CURVE_NO_ROUTE"

    def __init__(self, from_token: str, to_token: str):
        self.from_token = from_token
        self.to_token = to_token
        super().__init__(f"No Curve route found from {from_token} to {to_token}")


class InsufficientLiquidityError(CurveError):
    """
    Exception raised when there's insufficient liquidity for a swap.

    This typically occurs when:
    - The swap amount exceeds pool liquidity
    - Price impact would be too high
    """

    error_code: str = "CURVE_INSUFFICIENT_LIQUIDITY"

    def __init__(self, pool_id: str, required: str, available: str):
        self.pool_id = pool_id
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient liquidity in pool {pool_id}: required {required}, available {available}"
        )
