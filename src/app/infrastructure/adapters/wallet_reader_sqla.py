"""
SQLAlchemy implementation of WalletQueryGateway.

Handles read operations for wallet listing with owner information and search.
"""

import logging
from typing import Any

from sqlalchemy import Select, Table, func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.common.ports.wallet_query_gateway import WalletQueryGateway
from app.application.common.query_models.wallet import WalletOwnerInfo, WalletQueryModel
from app.application.common.query_params.sorting import SortingOrder
from app.application.common.query_params.wallet import WalletListParams
from app.domain.enums.chain_type import ChainType
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.enums.wallet_status import WalletStatus
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import ReaderError
from app.infrastructure.persistence_sqla.mappings.user import map_users_table
from app.infrastructure.persistence_sqla.mappings.wallet import map_wallet_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry

log = logging.getLogger(__name__)

# Valid sorting fields (column names in the wallets table or aliased columns)
VALID_SORTING_FIELDS = {
    "id",
    "address",
    "privy_wallet_id",
    "provider",
    "default_chain",
    "status",
    "created_at",
    "updated_at",
    "user_email",  # Aliased from users.email
    "user_name",  # Aliased: first_name || ' ' || last_name
}


class SqlaWalletReader(WalletQueryGateway):
    """SQLAlchemy implementation of WalletQueryGateway."""

    def __init__(self, session: MainAsyncSession):
        map_wallet_tables()
        map_users_table()
        self._session = session

    def _get_wallets_table(self) -> Table:
        """Get the wallets table from registry."""
        return mapping_registry.metadata.tables["wallets"]

    def _get_users_table(self) -> Table:
        """Get the users table from registry."""
        return mapping_registry.metadata.tables["users"]

    def _build_search_filter(
        self, search: str, wallets_table: Table, users_table: Table
    ) -> Any:
        """Build search filter for address, email, or user name."""
        search_pattern = f"%{search.lower()}%"
        return or_(
            func.lower(wallets_table.c.address).like(search_pattern),
            func.lower(users_table.c.email).like(search_pattern),
            func.lower(users_table.c.first_name).like(search_pattern),
            func.lower(users_table.c.last_name).like(search_pattern),
            func.lower(wallets_table.c.privy_wallet_id).like(search_pattern),
        )

    async def read_all(
        self,
        params: WalletListParams,
    ) -> list[WalletQueryModel] | None:
        """
        Retrieve a paginated list of wallets with owner info.

        :raises ReaderError: If database query fails.
        """
        sorting_field = params.sorting.sorting_field

        # Validate sorting field
        if sorting_field not in VALID_SORTING_FIELDS:
            log.error(
                "Invalid sorting field: '%s'. Valid fields: %s",
                sorting_field,
                VALID_SORTING_FIELDS,
            )
            return None

        try:
            wallets_table = self._get_wallets_table()
            users_table = self._get_users_table()

            # Determine sorting column
            if sorting_field == "user_email":
                sorting_column = users_table.c.email
            elif sorting_field == "user_name":
                sorting_column = users_table.c.first_name
            else:
                sorting_column = wallets_table.c[sorting_field]

            order_by = (
                sorting_column.asc()
                if params.sorting.sorting_order == SortingOrder.ASC
                else sorting_column.desc()
            )

            # Build query with JOIN to users
            select_stmt: Select[Any] = (
                select(
                    wallets_table.c.id,
                    wallets_table.c.address,
                    wallets_table.c.privy_wallet_id,
                    wallets_table.c.provider,
                    wallets_table.c.default_chain,
                    wallets_table.c.status,
                    wallets_table.c.created_at,
                    wallets_table.c.updated_at,
                    wallets_table.c.policy_ids,
                    wallets_table.c.owner_type,
                    wallets_table.c.owner_id,
                    wallets_table.c.exported_at,
                    wallets_table.c.imported_at,
                    wallets_table.c.last_privy_sync_at,
                    # User columns
                    users_table.c.id.label("user_id"),
                    users_table.c.email.label("user_email"),
                    users_table.c.first_name.label("user_first_name"),
                    users_table.c.last_name.label("user_last_name"),
                )
                .select_from(
                    wallets_table.join(
                        users_table,
                        wallets_table.c.user_id == users_table.c.id,
                    )
                )
                .order_by(order_by)
                .limit(params.pagination.limit)
                .offset(params.pagination.offset)
            )

            # Apply search filter if provided
            if params.search:
                select_stmt = select_stmt.where(
                    self._build_search_filter(params.search, wallets_table, users_table)
                )

            rows = (await self._session.execute(select_stmt)).mappings().all()

            return [self._row_to_wallet_query_model(dict(row)) for row in rows]

        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error

    def _row_to_wallet_query_model(self, row: dict[str, Any]) -> WalletQueryModel:
        """Convert a database row to a WalletQueryModel."""
        # Parse provider
        provider_val = row.get("provider")
        try:
            provider = (
                WalletProvider(provider_val) if provider_val else WalletProvider.PRIVY
            )
        except ValueError:
            provider = WalletProvider.PRIVY

        # Parse chain type
        chain_val = row.get("default_chain")
        try:
            default_chain = ChainType(chain_val) if chain_val else ChainType.ETHEREUM
        except ValueError:
            default_chain = ChainType.ETHEREUM

        # Parse status
        status_val = row.get("status", WalletStatus.ACTIVE.value)
        try:
            status = WalletStatus(status_val)
        except ValueError:
            status = WalletStatus.ACTIVE

        # Parse policy_ids (JSON array)
        policy_ids_raw = row.get("policy_ids")
        policy_ids: list[str] = (
            policy_ids_raw if isinstance(policy_ids_raw, list) else []
        )

        return WalletQueryModel(
            id=row["id"],
            address=row["address"],
            privy_wallet_id=row.get("privy_wallet_id"),
            provider=provider,
            default_chain=default_chain,
            status=status,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            owner=WalletOwnerInfo(
                user_id=row["user_id"],
                email=row["user_email"],
                first_name=row["user_first_name"],
                last_name=row["user_last_name"],
            ),
            policy_ids=policy_ids,
            owner_type=row.get("owner_type"),
            owner_id=row.get("owner_id"),
            exported_at=row.get("exported_at"),
            imported_at=row.get("imported_at"),
            last_privy_sync_at=row.get("last_privy_sync_at"),
        )

    async def count_all(self, search: str | None = None) -> int:
        """
        Count all wallets in the system, optionally filtered by search term.

        :raises ReaderError: If database query fails.
        """
        try:
            wallets_table = self._get_wallets_table()
            users_table = self._get_users_table()

            stmt = (
                select(func.count())
                .select_from(
                    wallets_table.join(
                        users_table,
                        wallets_table.c.user_id == users_table.c.id,
                    )
                )
            )

            # Apply search filter if provided
            if search:
                stmt = stmt.where(
                    self._build_search_filter(search, wallets_table, users_table)
                )

            result = await self._session.execute(stmt)
            return result.scalar_one()

        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error
