"""
Axelar Domain Exceptions.

Domain-specific exceptions for cross-chain bridging operations.
"""

from app.domain.exceptions.base import DomainError


class AxelarError(DomainError):
    """
    Base exception for Axelar operations.

    All Axelar-specific exceptions should inherit from this class.
    """

    error_code: str = "AXELAR_ERROR"


class TransferNotFoundError(AxelarError):
    """
    Exception raised when a transfer is not found.

    This typically occurs when:
    - The transaction hash is invalid
    - The transfer hasn't been indexed yet
    """

    error_code: str = "AXELAR_TRANSFER_NOT_FOUND"

    def __init__(self, tx_hash: str):
        self.tx_hash = tx_hash
        super().__init__(f"Transfer not found: {tx_hash}")


class UnsupportedChainError(AxelarError):
    """
    Exception raised when a chain is not supported.

    This typically occurs when:
    - Chain is not integrated with Axelar
    - Chain is deprecated
    """

    error_code: str = "AXELAR_UNSUPPORTED_CHAIN"

    def __init__(self, chain: str):
        self.chain = chain
        super().__init__(f"Unsupported chain: {chain}")


class UnsupportedTokenError(AxelarError):
    """
    Exception raised when a token is not supported.

    This typically occurs when:
    - Token is not available on the chain pair
    - Token is not bridgeable
    """

    error_code: str = "AXELAR_UNSUPPORTED_TOKEN"

    def __init__(self, token: str, chain: str | None = None):
        self.token = token
        self.chain = chain
        msg = f"Unsupported token: {token}"
        if chain:
            msg += f" on {chain}"
        super().__init__(msg)


class AxelarAPIError(AxelarError):
    """
    Exception raised when Axelar API is unavailable.

    This typically occurs when:
    - API is down
    - Rate limits exceeded
    - Network issues
    """

    error_code: str = "AXELAR_API_ERROR"

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(
            f"Axelar API error: {message}"
            + (f" (status: {status_code})" if status_code else "")
        )


class InvalidTxHashError(AxelarError):
    """
    Exception raised when transaction hash format is invalid.
    """

    error_code: str = "AXELAR_INVALID_TX_HASH"

    def __init__(self, tx_hash: str):
        self.tx_hash = tx_hash
        super().__init__(f"Invalid transaction hash: {tx_hash}")
