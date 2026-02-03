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
    UserLendingPreferences,
    LendingHealthCheck,
    LeverageLoopExecution,
    LendingAlert,
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
    async def get_position_by_id(self, position_id: UUID) -> Optional[LendingPosition]:
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

    # =========================================================================
    # USER PREFERENCES
    # =========================================================================

    @abstractmethod
    async def save_user_preferences(self, preferences: UserLendingPreferences) -> None:
        """
        Save or update user lending preferences.

        Args:
            preferences: UserLendingPreferences entity to persist

        Raises:
            RepositoryError: If save operation fails
        """
        ...

    @abstractmethod
    async def get_user_preferences(
        self, user_id: UUID
    ) -> Optional[UserLendingPreferences]:
        """
        Get user lending preferences.

        Args:
            user_id: User UUID

        Returns:
            UserLendingPreferences if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        ...

    # =========================================================================
    # HEALTH CHECKS
    # =========================================================================

    @abstractmethod
    async def save_health_check(self, check: LendingHealthCheck) -> None:
        """
        Save a health factor check snapshot.

        Args:
            check: LendingHealthCheck entity to persist

        Raises:
            RepositoryError: If save operation fails
        """
        ...

    @abstractmethod
    async def get_recent_health_checks(
        self, user_id: UUID, protocol: Optional[str] = None, limit: int = 10
    ) -> List[LendingHealthCheck]:
        """
        Get recent health checks for a user.

        Args:
            user_id: User UUID
            protocol: Optional protocol filter ('aave' or 'morpho')
            limit: Maximum number of checks to return (default: 10)

        Returns:
            List of LendingHealthCheck entities, ordered by checked_at DESC

        Raises:
            RepositoryError: If query fails
        """
        ...

    # =========================================================================
    # LEVERAGE LOOP EXECUTIONS
    # =========================================================================

    @abstractmethod
    async def save_loop_execution(self, execution: LeverageLoopExecution) -> None:
        """
        Save a leverage loop execution.

        Args:
            execution: LeverageLoopExecution entity to persist

        Raises:
            RepositoryError: If save operation fails
        """
        ...

    @abstractmethod
    async def get_loop_execution(
        self, loop_id: UUID
    ) -> Optional[LeverageLoopExecution]:
        """
        Get a leverage loop execution by ID.

        Args:
            loop_id: Loop execution UUID

        Returns:
            LeverageLoopExecution if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        ...

    @abstractmethod
    async def update_loop_execution(self, execution: LeverageLoopExecution) -> None:
        """
        Update a leverage loop execution (progress, status, results).

        Args:
            execution: LeverageLoopExecution entity with updated data

        Raises:
            RepositoryError: If update fails
        """
        ...

    @abstractmethod
    async def get_user_loop_executions(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[LeverageLoopExecution]:
        """
        Get leverage loop executions for a user.

        Args:
            user_id: User UUID
            status: Optional status filter
            limit: Maximum number of executions to return

        Returns:
            List of LeverageLoopExecution entities, ordered by created_at DESC

        Raises:
            RepositoryError: If query fails
        """
        ...

    # =========================================================================
    # ALERTS
    # =========================================================================

    @abstractmethod
    async def create_alert(self, alert: LendingAlert) -> None:
        """
        Create a lending alert.

        Args:
            alert: LendingAlert entity to persist

        Raises:
            RepositoryError: If save operation fails
        """
        ...

    @abstractmethod
    async def get_unread_alerts(
        self, user_id: UUID, severity: Optional[str] = None
    ) -> List[LendingAlert]:
        """
        Get unread alerts for a user.

        Args:
            user_id: User UUID
            severity: Optional severity filter ('info', 'warning', 'critical')

        Returns:
            List of unread LendingAlert entities, ordered by created_at DESC

        Raises:
            RepositoryError: If query fails
        """
        ...

    @abstractmethod
    async def mark_alert_as_read(self, alert_id: UUID) -> None:
        """
        Mark an alert as read.

        Args:
            alert_id: Alert UUID

        Raises:
            RepositoryError: If update fails
        """
        ...

    @abstractmethod
    async def get_user_alerts(
        self,
        user_id: UUID,
        include_read: bool = False,
        limit: int = 50,
    ) -> List[LendingAlert]:
        """
        Get alerts for a user.

        Args:
            user_id: User UUID
            include_read: Include read alerts (default: False)
            limit: Maximum number of alerts to return

        Returns:
            List of LendingAlert entities, ordered by created_at DESC

        Raises:
            RepositoryError: If query fails
        """
        ...
