"""
Aave Protocol Domain Exceptions.

Domain-specific exceptions for Aave V3 lending operations.
"""

from app.domain.exceptions.base import DomainError


class AaveError(DomainError):
    """
    Base exception for Aave operations.

    All Aave-specific exceptions should inherit from this class.
    """

    error_code: str = "AAVE_ERROR"


class MarketNotFoundError(AaveError):
    """
    Exception raised when an Aave market doesn't exist.

    This typically occurs when:
    - The asset is not listed on Aave
    - The market has been deprecated
    """

    error_code: str = "AAVE_MARKET_NOT_FOUND"

    def __init__(self, asset: str, chain: str = "ethereum"):
        self.asset = asset
        self.chain = chain
        super().__init__(f"Aave market not found: {asset} on {chain}")


class PositionNotFoundError(AaveError):
    """
    Exception raised when a user position doesn't exist.

    This typically occurs when:
    - User has no active positions
    - Invalid user address
    """

    error_code: str = "AAVE_POSITION_NOT_FOUND"

    def __init__(self, user_address: str, chain: str = "ethereum"):
        self.user_address = user_address
        self.chain = chain
        super().__init__(f"No Aave position found for {user_address} on {chain}")


class InvalidAddressError(AaveError):
    """
    Exception raised when address format is invalid.

    This typically occurs when:
    - Address is not a valid hex string
    - Address length is incorrect
    """

    error_code: str = "AAVE_INVALID_ADDRESS"

    def __init__(self, address: str, message: str | None = None):
        self.address = address
        super().__init__(message or f"Invalid address format: {address}")


class InsufficientCollateralError(AaveError):
    """
    Exception raised when collateral is insufficient for operation.

    This typically occurs when:
    - User tries to borrow more than allowed
    - User tries to withdraw collateral below safe threshold
    """

    error_code: str = "AAVE_INSUFFICIENT_COLLATERAL"

    def __init__(
        self,
        user_address: str,
        required: str,
        available: str,
    ):
        self.user_address = user_address
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient collateral: required {required}, available {available}"
        )


class HealthFactorTooLowError(AaveError):
    """
    Exception raised when health factor is below safe threshold.

    This typically occurs when:
    - Position is at risk of liquidation
    - User tries operation that would lower HF too much
    """

    error_code: str = "AAVE_HEALTH_FACTOR_TOO_LOW"

    def __init__(
        self,
        health_factor: str,
        threshold: str = "1.0",
    ):
        self.health_factor = health_factor
        self.threshold = threshold
        super().__init__(
            f"Health factor {health_factor} is below safe threshold {threshold}"
        )


class AssetNotCollateralError(AaveError):
    """
    Exception raised when asset cannot be used as collateral.

    This typically occurs when:
    - Asset has collateral disabled on Aave
    - Asset's LTV is 0
    """

    error_code: str = "AAVE_ASSET_NOT_COLLATERAL"

    def __init__(self, asset: str):
        self.asset = asset
        super().__init__(f"Asset {asset} cannot be used as collateral on Aave")


class BorrowCapReachedError(AaveError):
    """
    Exception raised when borrow cap is reached.

    This typically occurs when:
    - Protocol-level borrow cap for asset is reached
    - Market is at capacity
    """

    error_code: str = "AAVE_BORROW_CAP_REACHED"

    def __init__(self, asset: str, cap: str):
        self.asset = asset
        self.cap = cap
        super().__init__(f"Borrow cap reached for {asset}: {cap}")


class SupplyCapReachedError(AaveError):
    """
    Exception raised when supply cap is reached.

    This typically occurs when:
    - Protocol-level supply cap for asset is reached
    - Market is at capacity
    """

    error_code: str = "AAVE_SUPPLY_CAP_REACHED"

    def __init__(self, asset: str, cap: str):
        self.asset = asset
        self.cap = cap
        super().__init__(f"Supply cap reached for {asset}: {cap}")


class AaveAPIError(AaveError):
    """
    Exception raised when Aave API is unavailable or returns error.

    This typically occurs when:
    - Subgraph is down
    - API rate limits exceeded
    - Network issues
    """

    error_code: str = "AAVE_API_ERROR"

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(
            f"Aave API error: {message}"
            + (f" (status: {status_code})" if status_code else "")
        )


class SubgraphError(AaveError):
    """
    Exception raised when GraphQL subgraph query fails.

    This typically occurs when:
    - Invalid query structure
    - Subgraph indexing issues
    """

    error_code: str = "AAVE_SUBGRAPH_ERROR"

    def __init__(self, message: str, query: str | None = None):
        self.query = query
        super().__init__(f"Subgraph error: {message}")


class UnsupportedChainError(AaveError):
    """
    Exception raised when chain is not supported.

    This typically occurs when:
    - Aave V3 is not deployed on the chain
    - Invalid chain identifier
    """

    error_code: str = "AAVE_UNSUPPORTED_CHAIN"

    def __init__(self, chain: str):
        self.chain = chain
        super().__init__(f"Chain not supported by Aave V3: {chain}")


class RateLimitError(AaveError):
    """
    Exception raised when API rate limit is exceeded.

    This typically occurs when:
    - Too many requests to The Graph
    - API quota exceeded
    """

    error_code: str = "AAVE_RATE_LIMIT"

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(message)
