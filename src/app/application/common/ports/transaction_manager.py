from abc import abstractmethod
from typing import Protocol


class TransactionManager(Protocol):
    """
    UoW-compatible interface for committing a business transaction.
    Supports both commit and rollback operations for proper transaction management.
    The implementation may be an ORM session, such as SQLAlchemy's.
    """

    @abstractmethod
    async def commit(self) -> None:
        """
        Commit the successful outcome of a business transaction.

        :raises DataMapperError:
        """

    @abstractmethod
    async def rollback(self) -> None:
        """
        Rollback the transaction in case of failure.
        This cleans up the session state after an error occurs.
        
        This is a best-effort operation that should not raise exceptions.
        If rollback fails, the error is logged but not propagated to avoid
        masking the original error that triggered the rollback.
        """
