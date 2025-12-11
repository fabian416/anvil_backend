"""
NFT Domain Exceptions.

Domain-specific exceptions for NFT marketplace operations.
"""

from app.domain.exceptions.base import DomainError


class NFTError(DomainError):
    """
    Base exception for NFT operations.

    All NFT-specific exceptions should inherit from this class.
    """

    error_code: str = "NFT_ERROR"


class CollectionNotFoundError(NFTError):
    """
    Exception raised when a collection is not found.

    This typically occurs when:
    - Collection slug is invalid
    - Collection has been delisted
    """

    error_code: str = "NFT_COLLECTION_NOT_FOUND"

    def __init__(self, collection_slug: str):
        self.collection_slug = collection_slug
        super().__init__(f"Collection not found: {collection_slug}")


class NFTNotFoundError(NFTError):
    """
    Exception raised when an NFT is not found.

    This typically occurs when:
    - Contract address or token ID is invalid
    - NFT has been burned
    """

    error_code: str = "NFT_NOT_FOUND"

    def __init__(self, contract: str, token_id: str):
        self.contract = contract
        self.token_id = token_id
        super().__init__(f"NFT not found: {contract}/{token_id}")


class InvalidAddressError(NFTError):
    """
    Exception raised when wallet address is invalid.

    This typically occurs when:
    - Address format is incorrect
    - Address is not a valid hex string
    """

    error_code: str = "NFT_INVALID_ADDRESS"

    def __init__(self, address: str):
        self.address = address
        super().__init__(f"Invalid address: {address}")


class OpenSeaAPIError(NFTError):
    """
    Exception raised when OpenSea API is unavailable.

    This typically occurs when:
    - API is down
    - Rate limits exceeded
    - API key is invalid
    """

    error_code: str = "NFT_OPENSEA_API_ERROR"

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(
            f"OpenSea API error: {message}"
            + (f" (status: {status_code})" if status_code else "")
        )


class RateLimitError(NFTError):
    """
    Exception raised when rate limit is exceeded.

    This typically occurs when:
    - Too many requests in short time
    - API quota exceeded
    """

    error_code: str = "NFT_RATE_LIMIT"

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f" - retry after {retry_after}s"
        super().__init__(msg)
