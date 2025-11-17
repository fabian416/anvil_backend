import logging
from collections.abc import Mapping
from typing import Any, cast

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.application.common.ports.flusher import Flusher
from app.domain.exceptions.user import EmailAlreadyExistsError
from app.infrastructure.adapters.constants import (
    DB_CONSTRAINT_VIOLATION,
    DB_FLUSH_DONE,
    DB_FLUSH_FAILED,
    DB_QUERY_FAILED,
)
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError

log = logging.getLogger(__name__)


class SqlaMainFlusher(Flusher):
    def __init__(self, session: MainAsyncSession):
        self._session = session

    async def flush(self) -> None:
        """
        :raises DataMapperError:
        :raises EmailAlreadyExistsError:
        """
        try:
            await self._session.flush()
            log.debug("%s Main session.", DB_FLUSH_DONE)

        except IntegrityError as error:
            # Check for email uniqueness constraint violation
            if "uq_users_email" in str(error) or "email" in str(error).lower():
                params: Mapping[str, Any] = cast(Mapping[str, Any], error.params)
                email = str(params.get("email", "unknown"))
                raise EmailAlreadyExistsError(email) from error

            raise DataMapperError(DB_CONSTRAINT_VIOLATION) from error

        except SQLAlchemyError as error:
            raise DataMapperError(f"{DB_QUERY_FAILED} {DB_FLUSH_FAILED}") from error
