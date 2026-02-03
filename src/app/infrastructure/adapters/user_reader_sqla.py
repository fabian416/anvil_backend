import logging

from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.common.ports.user_query_gateway import UserQueryGateway
from app.application.common.query_models.user import UserQueryModel
from app.application.common.query_params.sorting import SortingOrder
from app.application.common.query_params.user import UserListParams
from app.domain.enums.user_role import UserRole
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import ReaderError
from app.infrastructure.persistence_sqla.mappings.user import map_users_table
from app.infrastructure.persistence_sqla.registry import mapping_registry

log = logging.getLogger(__name__)

# Valid sorting fields (column names in the users table)
VALID_SORTING_FIELDS = {
    "id",
    "email",
    "first_name",
    "last_name",
    "role",
    "is_active",
    "is_blocked",
    "is_verified",
    "created_at",
    "updated_at",
    "auth_provider",
    "privy_user_id",
    "primary_wallet_address",
}


class SqlaUserReader(UserQueryGateway):
    def __init__(self, session: MainAsyncSession):
        map_users_table()
        self._session = session

    def _build_search_filter(self, users_table, search: str):
        search_pattern = f"%{search.lower()}%"
        return or_(
            func.lower(users_table.c.email).like(search_pattern),
            func.lower(users_table.c.first_name).like(search_pattern),
            func.lower(users_table.c.last_name).like(search_pattern),
            func.lower(users_table.c.privy_user_id).like(search_pattern),
            func.lower(users_table.c.primary_wallet_address).like(search_pattern),
        )

    async def read_all(
        self,
        user_read_all_params: UserListParams,
    ) -> list[UserQueryModel] | None:
        """
        :raises ReaderError:
        """
        sorting_field = user_read_all_params.sorting.sorting_field

        # Validate sorting field
        if sorting_field not in VALID_SORTING_FIELDS:
            log.error(
                "Invalid sorting field: '%s'. Valid fields: %s",
                sorting_field,
                VALID_SORTING_FIELDS,
            )
            return None

        try:
            users_table = mapping_registry.metadata.tables["users"]
            sorting_column = users_table.c[sorting_field]

            order_by = (
                sorting_column.asc()
                if user_read_all_params.sorting.sorting_order == SortingOrder.ASC
                else sorting_column.desc()
            )

            select_stmt: Select = (
                select(users_table)
                .order_by(order_by)
                .limit(user_read_all_params.pagination.limit)
                .offset(user_read_all_params.pagination.offset)
            )

            if user_read_all_params.search:
                select_stmt = select_stmt.where(
                    self._build_search_filter(users_table, user_read_all_params.search)
                )

            rows = (await self._session.execute(select_stmt)).mappings().all()

            return [
                UserQueryModel(
                    id=row["id"],
                    email=row["email"],
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    role=UserRole(row["role"]),
                    is_active=row["is_active"],
                    is_blocked=row["is_blocked"],
                    is_verified=row["is_verified"],
                    retry_count=row["retry_count"] or 0,
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    last_login=row["last_login"],
                    profile_picture=row["profile_picture"],
                    phone_number=row["phone_number"],
                    language=row["language"] or "en",
                    address=row["address"],
                    postal_code=row["postal_code"],
                    country_id=row["country_id"],
                    city_id=row["city_id"],
                    subscription=row["subscription"],
                    # Privy authentication fields
                    privy_user_id=row["privy_user_id"],
                    primary_wallet_address=row["primary_wallet_address"],
                    auth_provider=row["auth_provider"] or "email",
                )
                for row in rows
            ]

        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error

    async def count_all(self, search: str | None = None) -> int:
        """
        Count all users in the system.

        :raises ReaderError:
        """
        try:
            users_table = mapping_registry.metadata.tables["users"]
            stmt = select(func.count()).select_from(users_table)
            if search:
                stmt = stmt.where(self._build_search_filter(users_table, search))
            result = await self._session.execute(stmt)
            return result.scalar_one()
        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error
