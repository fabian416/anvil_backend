import logging
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import ColumnElement, Result, Row, Select, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.common.ports.user_query_gateway import UserQueryGateway
from app.application.common.query_models.user import UserQueryModel
from app.application.common.query_params.sorting import SortingOrder
from app.application.common.query_params.user import UserListParams
from app.domain.enums.user_role import UserRole
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import ReaderError
from app.domain.entities.user import User

log = logging.getLogger(__name__)


class SqlaUserReader(UserQueryGateway):
    def __init__(self, session: MainAsyncSession):
        self._session = session

    async def read_all(
        self,
        user_read_all_params: UserListParams,
    ) -> list[UserQueryModel] | None:
        """
        :raises ReaderError:
        """
        # Get the sorting field attribute from User entity
        sorting_field_attr = getattr(User, user_read_all_params.sorting.sorting_field, None)
        if sorting_field_attr is None:
            log.error(
                "Invalid sorting field: '%s'.",
                user_read_all_params.sorting.sorting_field,
            )
            return None

        order_by = (
            sorting_field_attr.asc()
            if user_read_all_params.sorting.sorting_order == SortingOrder.ASC
            else sorting_field_attr.desc()
        )

        select_stmt: Select[tuple[User]] = (
            select(User)
            .order_by(order_by)
            .limit(user_read_all_params.pagination.limit)
            .offset(user_read_all_params.pagination.offset)
        )

        try:
            result: Result[tuple[User]] = await self._session.execute(select_stmt)
            users: Sequence[Row[tuple[User]]] = result.all()

            return [
                UserQueryModel(
                    id=user[0].id.value,
                    email=user[0].email.value,
                    first_name=user[0].first_name.value,
                    last_name=user[0].last_name.value,
                    role=user[0].role,
                    is_active=user[0].is_active.value,
                    is_blocked=user[0].is_blocked.value,
                    is_verified=user[0].is_verified.value,
                    retry_count=user[0].retry_count.value,
                    created_at=user[0].created_at.value,
                    updated_at=user[0].updated_at.value,
                    last_login=user[0].last_login.value if user[0].last_login else None,
                    profile_picture=user[0].profile_picture.value if user[0].profile_picture else None,
                    phone_number=user[0].phone_number.value if user[0].phone_number else None,
                    language=user[0].language.value,
                    address=user[0].address.value if user[0].address else None,
                    postal_code=user[0].postal_code.value if user[0].postal_code else None,
                    country_id=user[0].country_id.value if user[0].country_id else None,
                    city_id=user[0].city_id.value if user[0].city_id else None,
                    subscription=user[0].subscription.value if user[0].subscription else None,
                )
                for user in users
            ]

        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error
