"""
Wallet Query Gateway Port.

Defines the abstract interface for wallet read operations optimized for queries.
"""

from abc import abstractmethod
from typing import Protocol

from app.application.common.query_models.wallet import WalletQueryModel
from app.application.common.query_params.wallet import WalletListParams


class WalletQueryGateway(Protocol):
    """
    Query gateway for wallet read operations.

    Optimized for admin views with owner information and search capabilities.
    """

    @abstractmethod
    async def read_all(
        self,
        params: WalletListParams,
    ) -> list[WalletQueryModel] | None:
        """
        Retrieve a paginated list of wallets with owner info.

        Returns None if sorting field is invalid.

        :raises ReaderError: If database query fails.
        """
        ...

    @abstractmethod
    async def count_all(self, search: str | None = None) -> int:
        """
        Count all wallets in the system, optionally filtered by search term.

        :raises ReaderError: If database query fails.
        """
        ...
