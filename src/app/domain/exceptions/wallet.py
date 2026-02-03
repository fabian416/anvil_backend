"""
Wallet-specific domain exceptions with standardized error codes.

This module provides all exceptions related to:
- Wallet connections and addresses
- Transactions and balances
- Blockchain networks and chains
"""

from typing import Any
from uuid import UUID

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


class WalletNotFoundError(ApplicationError):
    """Raised when a wallet is not found."""

    def __init__(
        self,
        wallet_id: str | UUID | None = None,
        address: str | None = None,
    ) -> None:
        details = {}
        if wallet_id:
            details["wallet_id"] = str(wallet_id)
        if address:
            details["address"] = address
        super().__init__(ErrorCode.WALLET_NOT_FOUND, details=details)


class WalletNotConnectedError(ApplicationError):
    """Raised when wallet connection is required but not established."""

    def __init__(
        self,
        user_id: str | UUID | None = None,
    ) -> None:
        details = {}
        if user_id:
            details["user_id"] = str(user_id)
        super().__init__(ErrorCode.WALLET_NOT_CONNECTED, details=details)


class InvalidWalletAddressError(ApplicationError):
    """Raised when a wallet address is invalid."""

    def __init__(
        self,
        address: str | None = None,
        chain: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if address:
            details["address"] = address
        if chain:
            details["chain"] = chain
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.WALLET_INVALID_ADDRESS, details=details, field="address"
        )


class InsufficientBalanceError(ApplicationError):
    """Raised when wallet has insufficient balance for an operation."""

    def __init__(
        self,
        required: str | float | None = None,
        available: str | float | None = None,
        token: str | None = None,
        chain: str | None = None,
    ) -> None:
        details = {}
        if required is not None:
            details["required"] = str(required)
        if available is not None:
            details["available"] = str(available)
        if token:
            details["token"] = token
        if chain:
            details["chain"] = chain
        super().__init__(ErrorCode.WALLET_INSUFFICIENT_BALANCE, details=details)


class TransactionFailedError(ApplicationError):
    """Raised when a blockchain transaction fails."""

    def __init__(
        self,
        tx_hash: str | None = None,
        reason: str | None = None,
        error_code: str | None = None,
        chain: str | None = None,
    ) -> None:
        details = {}
        if tx_hash:
            details["tx_hash"] = tx_hash
        if reason:
            details["reason"] = reason
        if error_code:
            details["error_code"] = error_code
        if chain:
            details["chain"] = chain
        super().__init__(ErrorCode.WALLET_TRANSACTION_FAILED, details=details)


class InvalidChainError(ApplicationError):
    """Raised when an unsupported blockchain network is specified."""

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
        super().__init__(ErrorCode.WALLET_INVALID_CHAIN, details=details, field="chain")


class InvalidAmountError(ApplicationError):
    """Raised when an invalid amount is specified."""

    def __init__(
        self,
        amount: str | float | None = None,
        min_amount: str | float | None = None,
        max_amount: str | float | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if amount is not None:
            details["amount"] = str(amount)
        if min_amount is not None:
            details["min_amount"] = str(min_amount)
        if max_amount is not None:
            details["max_amount"] = str(max_amount)
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.WALLET_INVALID_AMOUNT, details=details, field="amount"
        )


class WalletRateLimitError(ApplicationError):
    """Raised when wallet operation rate limit is exceeded."""

    def __init__(
        self,
        retry_after_seconds: int | None = None,
        operation: str | None = None,
    ) -> None:
        details = {}
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        if operation:
            details["operation"] = operation
        super().__init__(ErrorCode.WALLET_RATE_LIMIT, details=details)


class NetworkCongestedError(ApplicationError):
    """Raised when the blockchain network is congested."""

    def __init__(
        self,
        chain: str | None = None,
        estimated_wait_seconds: int | None = None,
        gas_price: str | None = None,
    ) -> None:
        details = {}
        if chain:
            details["chain"] = chain
        if estimated_wait_seconds is not None:
            details["estimated_wait_seconds"] = estimated_wait_seconds
        if gas_price:
            details["gas_price"] = gas_price
        super().__init__(ErrorCode.WALLET_NETWORK_CONGESTED, details=details)


class InvalidSignatureError(ApplicationError):
    """Raised when a signature is invalid."""

    def __init__(
        self,
        signature_type: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if signature_type:
            details["signature_type"] = signature_type
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.WALLET_SIGNATURE_INVALID, details=details, field="signature"
        )


# Additional wallet-specific exceptions


class WalletConnectionTimeoutError(ApplicationError):
    """Raised when wallet connection times out."""

    def __init__(
        self,
        timeout_seconds: int | None = None,
        wallet_type: str | None = None,
    ) -> None:
        details = {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if wallet_type:
            details["wallet_type"] = wallet_type
        super().__init__(
            ErrorCode.WALLET_NOT_CONNECTED,
            details=details,
            override_message="Wallet connection timed out",
        )


class WalletDisconnectedError(ApplicationError):
    """Raised when wallet unexpectedly disconnects."""

    def __init__(
        self,
        address: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if address:
            details["address"] = address
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.WALLET_NOT_CONNECTED,
            details=details,
            override_message="Wallet has been disconnected",
        )


class TokenNotSupportedError(ApplicationError):
    """Raised when a token is not supported."""

    def __init__(
        self,
        token: str | None = None,
        chain: str | None = None,
        supported_tokens: list[str] | None = None,
    ) -> None:
        details = {}
        if token:
            details["token"] = token
        if chain:
            details["chain"] = chain
        if supported_tokens:
            details["supported_tokens"] = supported_tokens
        super().__init__(
            ErrorCode.WALLET_INVALID_CHAIN,
            details=details,
            override_message="Token is not supported on this chain",
        )


class GasEstimationFailedError(ApplicationError):
    """Raised when gas estimation fails."""

    def __init__(
        self,
        chain: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if chain:
            details["chain"] = chain
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.WALLET_TRANSACTION_FAILED,
            details=details,
            override_message="Failed to estimate gas for transaction",
        )


class TransactionPendingError(ApplicationError):
    """Raised when a transaction is still pending."""

    def __init__(
        self,
        tx_hash: str | None = None,
        pending_seconds: int | None = None,
    ) -> None:
        details = {}
        if tx_hash:
            details["tx_hash"] = tx_hash
        if pending_seconds is not None:
            details["pending_seconds"] = pending_seconds
        super().__init__(
            ErrorCode.WALLET_TRANSACTION_FAILED,
            details=details,
            override_message="Transaction is still pending confirmation",
        )


class TransactionRevertedError(ApplicationError):
    """Raised when a transaction is reverted."""

    def __init__(
        self,
        tx_hash: str | None = None,
        revert_reason: str | None = None,
    ) -> None:
        details = {}
        if tx_hash:
            details["tx_hash"] = tx_hash
        if revert_reason:
            details["revert_reason"] = revert_reason
        super().__init__(
            ErrorCode.WALLET_TRANSACTION_FAILED,
            details=details,
            override_message="Transaction was reverted",
        )
