"""
Morpho Protocol Domain Exceptions.

Domain-specific exceptions for Morpho lending operations.
"""

from app.domain.exceptions.base import DomainError


class MorphoError(DomainError):
    """
    Base exception for Morpho operations.

    All Morpho-specific exceptions should inherit from this class.
    """

    error_code: str = "MORPHO_ERROR"


class VaultNotFoundError(MorphoError):
    """
    Exception raised when a vault doesn't exist.

    This typically occurs when:
    - The vault address is invalid
    - The vault has been deprecated
    """

    error_code: str = "MORPHO_VAULT_NOT_FOUND"

    def __init__(self, vault_address: str, chain: str = "ethereum"):
        self.vault_address = vault_address
        self.chain = chain
        super().__init__(f"Vault not found: {vault_address} on {chain}")


class InvalidVaultAddressError(MorphoError):
    """
    Exception raised when vault address format is invalid.

    This typically occurs when:
    - Address is not a valid hex string
    - Address length is incorrect
    """

    error_code: str = "MORPHO_INVALID_ADDRESS"

    def __init__(self, address: str, message: str | None = None):
        self.address = address
        super().__init__(message or f"Invalid vault address: {address}")


class MorphoAPIError(MorphoError):
    """
    Exception raised when Morpho API is unavailable or returns error.

    This typically occurs when:
    - Subgraph is down
    - API rate limits exceeded
    - Network issues
    """

    error_code: str = "MORPHO_API_ERROR"

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(
            f"Morpho API error: {message}"
            + (f" (status: {status_code})" if status_code else "")
        )


class SubgraphError(MorphoError):
    """
    Exception raised when GraphQL subgraph query fails.

    This typically occurs when:
    - Invalid query structure
    - Subgraph indexing issues
    """

    error_code: str = "MORPHO_SUBGRAPH_ERROR"

    def __init__(self, message: str, query: str | None = None):
        self.query = query
        super().__init__(f"Subgraph error: {message}")


class InvalidAddressError(MorphoError):
    """
    Exception raised when wallet address format is invalid.
    """

    error_code: str = "MORPHO_INVALID_ADDRESS"

    def __init__(self, address: str, message: str | None = None):
        self.address = address
        super().__init__(message or f"Invalid address format: {address}")
