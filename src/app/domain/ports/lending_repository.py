"""
Domain port (interface) for lending repository.

Defines the contract for lending position persistence following hexagonal architecture.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.lending import (
    LendingPosition,
    SupplyPosition,
    BorrowPosition,
    LendingTransaction,
)


class ILendingRepository(ABC):
    """
    Port for lending position persistence.

    This interface defines operations for persisting and retrieving lending data.
    Concrete implementations (adapters) handle database-specific logic.
    """

    @abstractmethod
    async def save_position(self, position: LendingPosition) -> None:
        """
        Save or update a lending position.

        Args:
            position: LendingPosition entity to persist

        Raises:
            RepositoryError: If save operation fails
        """
        ...

    @abstractmethod
    async def save_supply(self, supply: SupplyPosition) -> None:
        """
        Save a supply position.

        Args:
            supply: SupplyPosition entity to persist

        Raises:
            RepositoryError: If save operation fails
        """
        ...

    @abstractmethod
    async def save_borrow(self, borrow: BorrowPosition) -> None:
        """
        Save a borrow position.

        Args:
            borrow: BorrowPosition entity to persist

        Raises:
            RepositoryError: If save operation fails
        """
        ...

    @abstractmethod
    async def save_transaction(self, transaction: LendingTransaction) -> None:
        """
        Save a lending transaction.

        Args:
            transaction: LendingTransaction entity to persist

        Raises:
            RepositoryError: If save operation fails
        """
        ...

    @abstractmethod
    async def get_user_positions(
        self, user_id: UUID, protocol: Optional[str] = None
    ) -> List[LendingPosition]:
        """
        Get all lending positions for a user.

        Args:
            user_id: User UUID
            protocol: Optional protocol filter ('aave' or 'morpho')

        Returns:
            List of LendingPosition entities

        Raises:
            RepositoryError: If query fails
        """
        ...

    @abstractmethod
    async def get_position_by_id(
        self, position_id: UUID
    ) -> Optional[LendingPosition]:
        """
        Get a lending position by ID.

        Args:
            position_id: Position UUID

        Returns:
            LendingPosition if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        ...

    @abstractmethod
    async def get_user_transactions(
        self,
        user_id: UUID,
        protocol: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[LendingTransaction]:
        """
        Get transaction history for a user.

        Args:
            user_id: User UUID
            protocol: Optional protocol filter
            action_type: Optional action type filter
            limit: Maximum number of transactions to return

        Returns:
            List of LendingTransaction entities

        Raises:
            RepositoryError: If query fails
        """
        ...

    @abstractmethod
    async def update_transaction_status(
        self,
        transaction_hash: str,
        status: str,
        confirmed_at: Optional[str] = None,
    ) -> None:
        """
        Update transaction status after on-chain confirmation.

        Args:
            transaction_hash: Transaction hash
            status: New status ('confirmed' or 'failed')
            confirmed_at: ISO timestamp of confirmation

        Raises:
            RepositoryError: If update fails
        """
        ...
