"""
LayerZero Domain Exceptions.

Domain-specific exceptions for cross-chain message tracking.
"""

from app.domain.exceptions.base import DomainError


class LayerZeroError(DomainError):
    """
    Base exception for LayerZero operations.

    All LayerZero-specific exceptions should inherit from this class.
    """

    error_code: str = "LAYERZERO_ERROR"


class MessageNotFoundError(LayerZeroError):
    """
    Exception raised when a message is not found.

    This typically occurs when:
    - The transaction hash is invalid
    - The message hasn't been indexed yet
    """

    error_code: str = "LZ_MESSAGE_NOT_FOUND"

    def __init__(self, tx_hash: str):
        self.tx_hash = tx_hash
        super().__init__(f"Message not found: {tx_hash}")


class InvalidTxHashError(LayerZeroError):
    """
    Exception raised when transaction hash format is invalid.

    This typically occurs when:
    - Hash is not a valid hex string
    - Hash length is incorrect
    """

    error_code: str = "LZ_INVALID_TX_HASH"

    def __init__(self, tx_hash: str):
        self.tx_hash = tx_hash
        super().__init__(f"Invalid transaction hash: {tx_hash}")


class UnsupportedChainError(LayerZeroError):
    """
    Exception raised when a chain is not supported.

    This typically occurs when:
    - Chain is not integrated with LayerZero
    - Chain endpoint doesn't exist
    """

    error_code: str = "LZ_UNSUPPORTED_CHAIN"

    def __init__(self, chain: str):
        self.chain = chain
        super().__init__(f"Unsupported chain: {chain}")


class LayerZeroAPIError(LayerZeroError):
    """
    Exception raised when LayerZero API is unavailable.

    This typically occurs when:
    - API is down
    - Rate limits exceeded
    - Network issues
    """

    error_code: str = "LZ_API_ERROR"

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(
            f"LayerZero API error: {message}"
            + (f" (status: {status_code})" if status_code else "")
        )
