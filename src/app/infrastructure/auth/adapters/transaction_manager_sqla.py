import logging

from sqlalchemy.exc import SQLAlchemyError, InvalidRequestError

from app.infrastructure.adapters.constants import (
    DB_COMMIT_DONE,
    DB_COMMIT_FAILED,
    DB_QUERY_FAILED,
    DB_ROLLBACK_DONE,
    DB_ROLLBACK_FAILED,
)
from app.infrastructure.auth.adapters.types import AuthAsyncSession
from app.infrastructure.auth.session.ports.transaction_manager import (
    AuthSessionTransactionManager,
)
from app.infrastructure.exceptions.gateway import DataMapperError

log = logging.getLogger(__name__)


class SqlaAuthSessionTransactionManager(AuthSessionTransactionManager):
    def __init__(self, session: AuthAsyncSession):
        self._session = session

    async def commit(self) -> None:
        """
        :raises DataMapperError:
        """
        try:
            await self._session.commit()
            log.debug("%s. Auth session.", DB_COMMIT_DONE)

        except SQLAlchemyError as error:
            # Auto-rollback on commit failure to clean up session state
            await self.rollback()
            raise DataMapperError(f"{DB_QUERY_FAILED} {DB_COMMIT_FAILED}") from error

    async def rollback(self) -> None:
        """
        Rollback the transaction to clean up session state.

        This is a best-effort operation - if it fails, we log the error but don't
        raise an exception to avoid masking the original error that triggered the rollback.

        Common cases where rollback might fail:
        - Session is provisioning a new connection (no transaction to rollback)
        - Session is already closed or invalidated
        - Concurrent operations on the session
        """
        try:
            # Check if the session is in a state where rollback is possible
            if self._session.is_active:
                await self._session.rollback()
                log.debug("%s. Auth session.", DB_ROLLBACK_DONE)
            else:
                log.debug("Rollback skipped - no active transaction. Auth session.")

        except InvalidRequestError as error:
            # Session is in an invalid state (e.g., provisioning connection)
            # This is expected in some edge cases - just log and continue
            log.warning(
                "Rollback skipped - session in invalid state. Auth session. Error: %s",
                error,
            )
        except SQLAlchemyError as error:
            # Other database errors during rollback - log but don't raise
            log.error("%s. Auth session. Error: %s", DB_ROLLBACK_FAILED, error)
