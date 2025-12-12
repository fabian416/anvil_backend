"""
SQLAlchemy implementation of TransactionRepository.

Handles CRUD operations for transactions stored locally in the database.
Transactions represent on-chain operations initiated by users via Privy.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, func, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.domain.entities.transaction import Transaction, TransactionId
from app.domain.entities.wallet import WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
from app.domain.ports.transaction.transaction_repository import TransactionRepository
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.user_id import UserId
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.transaction import (
    map_transaction_table,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaTransactionRepository(TransactionRepository):
    """SQLAlchemy implementation of TransactionRepository."""

    def __init__(self, session: MainAsyncSession):
        map_transaction_table()
        self._session = session

    def _get_table(self):
        """Get the transactions table from registry."""
        return mapping_registry.metadata.tables["transactions"]

    def _row_to_transaction(self, row: dict[str, Any]) -> Transaction:
        """Convert a database row to a Transaction entity."""
        # Parse chain type
        chain_val = row.get("chain")
        try:
            if isinstance(chain_val, ChainType):
                chain = chain_val
            elif isinstance(chain_val, str):
                chain = ChainType(chain_val)
            else:
                chain = ChainType.ETHEREUM
        except ValueError:
            chain = ChainType.ETHEREUM

        # Parse transaction type
        type_val = row.get("type")
        try:
            if isinstance(type_val, TransactionType):
                tx_type = type_val
            elif isinstance(type_val, int):
                tx_type = TransactionType(type_val)
            else:
                tx_type = TransactionType.SEND
        except ValueError:
            tx_type = TransactionType.SEND

        # Parse status
        status_val = row.get("status")
        try:
            if isinstance(status_val, TransactionStatus):
                status = status_val
            elif isinstance(status_val, int):
                status = TransactionStatus(status_val)
            else:
                status = TransactionStatus.PENDING
        except ValueError:
            status = TransactionStatus.PENDING

        # Parse timestamps
        created_at_val = row.get("created_at")
        if created_at_val:
            created_at = CreatedAt(created_at_val)
        else:
            created_at = CreatedAt(datetime.now(UTC))

        # Parse decimal values
        def parse_decimal(val: Any) -> Decimal | None:
            if val is None:
                return None
            if isinstance(val, Decimal):
                return val
            return Decimal(str(val))

        # Parse optional int values
        def parse_optional_int(val: Any) -> int | None:
            if val is None:
                return None
            return int(val)

        return Transaction(
            id_=TransactionId(row["id"]),
            user_id=UserId(row["user_id"]),
            wallet_id=WalletId(row["wallet_id"]),
            to_address=row.get("to_address"),
            type=tx_type,
            chain=chain,
            asset_in=row.get("asset_in"),
            amount_in=parse_decimal(row.get("amount_in")),
            asset_out=row.get("asset_out"),
            amount_out=parse_decimal(row.get("amount_out")),
            fee=parse_decimal(row.get("fee")),
            fee_usd=parse_decimal(row.get("fee_usd")),
            tx_hash=row.get("tx_hash"),
            status=status,
            dex_aggregator=row.get("dex_aggregator"),
            dex_route=row.get("dex_route"),
            slippage=parse_decimal(row.get("slippage")),
            error_message=row.get("error_message"),
            block_number=row.get("block_number"),
            confirmed_at=row.get("confirmed_at"),
            created_at=created_at,
            gas_used=parse_optional_int(row.get("gas_used")),
            gas_price=parse_optional_int(row.get("gas_price")),
            tx_metadata=row.get("tx_metadata"),
        )

    def _transaction_to_dict(self, transaction: Transaction) -> dict[str, Any]:
        """Convert a Transaction entity to a dictionary for database insert."""
        return {
            "user_id": transaction.user_id.value,
            "wallet_id": transaction.wallet_id.value,
            "to_address": transaction.to_address,
            "type": transaction.type.value,
            "chain": transaction.chain.value,
            "asset_in": transaction.asset_in,
            "amount_in": transaction.amount_in,
            "asset_out": transaction.asset_out,
            "amount_out": transaction.amount_out,
            "fee": transaction.fee,
            "fee_usd": transaction.fee_usd,
            "tx_hash": transaction.tx_hash,
            "status": transaction.status.value,
            "dex_aggregator": transaction.dex_aggregator,
            "dex_route": transaction.dex_route,
            "slippage": transaction.slippage,
            "error_message": transaction.error_message,
            "block_number": transaction.block_number,
            "confirmed_at": transaction.confirmed_at,
            "gas_used": transaction.gas_used,
            "gas_price": transaction.gas_price,
            "tx_metadata": transaction.tx_metadata,
        }

    async def get_by_id(self, transaction_id: TransactionId) -> Transaction | None:
        """Get transaction by ID."""
        try:
            table = self._get_table()
            stmt: Select = select(table).where(table.c.id == transaction_id.value)
            row = (await self._session.execute(stmt)).mappings().first()
            return self._row_to_transaction(dict(row)) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_by_tx_hash(self, tx_hash: str) -> Transaction | None:
        """Get transaction by blockchain hash (returns first match)."""
        try:
            table = self._get_table()
            stmt: Select = select(table).where(table.c.tx_hash == tx_hash.lower())
            row = (await self._session.execute(stmt)).mappings().first()
            return self._row_to_transaction(dict(row)) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_by_user_and_tx_hash(
        self,
        user_id: UserId,
        tx_hash: str,
    ) -> Transaction | None:
        """Get transaction by user ID and blockchain hash combination."""
        try:
            table = self._get_table()
            stmt: Select = select(table).where(
                and_(
                    table.c.user_id == user_id.value,
                    table.c.tx_hash == tx_hash.lower(),
                )
            )
            row = (await self._session.execute(stmt)).mappings().first()
            return self._row_to_transaction(dict(row)) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_by_user_id(
        self,
        user_id: UserId,
        *,
        limit: int = 50,
        offset: int = 0,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[Transaction]:
        """Get transactions for a specific user with optional filters."""
        try:
            table = self._get_table()
            conditions = [table.c.user_id == user_id.value]

            if chain is not None:
                conditions.append(table.c.chain == chain.value)
            if status is not None:
                conditions.append(table.c.status == status.value)
            if tx_type is not None:
                conditions.append(table.c.type == tx_type.value)

            stmt: Select = (
                select(table)
                .where(and_(*conditions))
                .order_by(table.c.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            rows = (await self._session.execute(stmt)).mappings().all()
            return [self._row_to_transaction(dict(row)) for row in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_by_wallet_id(
        self,
        wallet_id: WalletId,
        *,
        limit: int = 50,
        offset: int = 0,
        status: TransactionStatus | None = None,
    ) -> list[Transaction]:
        """Get transactions for a specific wallet."""
        try:
            table = self._get_table()
            conditions = [table.c.wallet_id == wallet_id.value]

            if status is not None:
                conditions.append(table.c.status == status.value)

            stmt: Select = (
                select(table)
                .where(and_(*conditions))
                .order_by(table.c.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            rows = (await self._session.execute(stmt)).mappings().all()
            return [self._row_to_transaction(dict(row)) for row in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_pending_transactions(
        self,
        *,
        limit: int = 100,
        older_than_seconds: int | None = None,
    ) -> list[Transaction]:
        """Get pending transactions that need confirmation."""
        try:
            table = self._get_table()
            conditions = [
                table.c.status == TransactionStatus.PENDING.value,
                table.c.tx_hash.isnot(None),
            ]

            if older_than_seconds is not None:
                cutoff = datetime.now(UTC) - timedelta(seconds=older_than_seconds)
                conditions.append(table.c.created_at < cutoff)

            stmt: Select = (
                select(table)
                .where(and_(*conditions))
                .order_by(table.c.created_at.asc())
                .limit(limit)
            )
            rows = (await self._session.execute(stmt)).mappings().all()
            return [self._row_to_transaction(dict(row)) for row in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def count_by_user_id(
        self,
        user_id: UserId,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int:
        """Count transactions for a user with optional filters."""
        try:
            table = self._get_table()
            conditions = [table.c.user_id == user_id.value]

            if chain is not None:
                conditions.append(table.c.chain == chain.value)
            if status is not None:
                conditions.append(table.c.status == status.value)
            if tx_type is not None:
                conditions.append(table.c.type == tx_type.value)

            stmt = select(func.count()).select_from(table).where(and_(*conditions))
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def save(self, transaction: Transaction) -> Transaction:
        """Save a new transaction to the database."""
        try:
            table = self._get_table()
            data = self._transaction_to_dict(transaction)

            stmt = table.insert().values(**data).returning(table.c.id)
            result = await self._session.execute(stmt)
            new_id = result.scalar_one()
            await self._session.commit()

            # Return the saved transaction with the new ID
            return Transaction(
                id_=TransactionId(new_id),
                user_id=transaction.user_id,
                wallet_id=transaction.wallet_id,
                to_address=transaction.to_address,
                type=transaction.type,
                chain=transaction.chain,
                asset_in=transaction.asset_in,
                amount_in=transaction.amount_in,
                asset_out=transaction.asset_out,
                amount_out=transaction.amount_out,
                fee=transaction.fee,
                fee_usd=transaction.fee_usd,
                tx_hash=transaction.tx_hash,
                status=transaction.status,
                dex_aggregator=transaction.dex_aggregator,
                dex_route=transaction.dex_route,
                slippage=transaction.slippage,
                error_message=transaction.error_message,
                block_number=transaction.block_number,
                confirmed_at=transaction.confirmed_at,
                created_at=transaction.created_at,
                gas_used=transaction.gas_used,
                gas_price=transaction.gas_price,
                tx_metadata=transaction.tx_metadata,
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update(self, transaction: Transaction) -> Transaction:
        """Update an existing transaction."""
        try:
            table = self._get_table()
            data = self._transaction_to_dict(transaction)

            stmt = (
                update(table).where(table.c.id == transaction.id_.value).values(**data)
            )
            await self._session.execute(stmt)
            await self._session.flush()
            return transaction
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update_status(
        self,
        transaction_id: TransactionId,
        status: TransactionStatus,
        *,
        block_number: int | None = None,
        confirmed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> bool:
        """Update transaction status and confirmation data."""
        try:
            table = self._get_table()
            update_data: dict[str, Any] = {"status": status.value}

            if block_number is not None:
                update_data["block_number"] = block_number
            if confirmed_at is not None:
                update_data["confirmed_at"] = confirmed_at
            if error_message is not None:
                update_data["error_message"] = error_message

            stmt = (
                update(table)
                .where(table.c.id == transaction_id.value)
                .values(**update_data)
            )
            result = await self._session.execute(stmt)
            await self._session.flush()
            return result.rowcount > 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    # ============================================================
    # Analytics Methods (for Admin Metrics)
    # ============================================================

    async def count_all(self) -> int:
        """Count total number of transactions in the system."""
        try:
            table = self._get_table()
            stmt = select(func.count()).select_from(table)
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def count_by_status(self, status: TransactionStatus) -> int:
        """Count transactions by status."""
        try:
            table = self._get_table()
            stmt = (
                select(func.count())
                .select_from(table)
                .where(table.c.status == status.value)
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def count_by_chain(self, chain: ChainType) -> int:
        """Count transactions by chain."""
        try:
            table = self._get_table()
            stmt = (
                select(func.count())
                .select_from(table)
                .where(table.c.chain == chain.value)
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_transaction_counts_by_status(self) -> dict[str, int]:
        """Get transaction counts grouped by status."""
        try:
            table = self._get_table()
            stmt = select(table.c.status, func.count().label("count")).group_by(
                table.c.status
            )
            result = await self._session.execute(stmt)
            rows = result.all()
            # Convert int enum values to string names
            return {TransactionStatus(row.status).name: row.count for row in rows}
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_transaction_counts_by_chain(self) -> dict[str, int]:
        """Get transaction counts grouped by chain."""
        try:
            table = self._get_table()
            stmt = select(table.c.chain, func.count().label("count")).group_by(
                table.c.chain
            )
            result = await self._session.execute(stmt)
            rows = result.all()
            return {row.chain: row.count for row in rows}
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_transaction_counts_by_type(self) -> dict[str, int]:
        """Get transaction counts grouped by transaction type."""
        try:
            table = self._get_table()
            stmt = select(table.c.type, func.count().label("count")).group_by(
                table.c.type
            )
            result = await self._session.execute(stmt)
            rows = result.all()
            # Convert int enum values to string names
            return {TransactionType(row.type).name: row.count for row in rows}
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def count_transactions_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int:
        """Count transactions within a date range with optional filters."""
        try:
            table = self._get_table()
            conditions = [
                table.c.created_at >= start_date,
                table.c.created_at <= end_date,
            ]

            if chain is not None:
                conditions.append(table.c.chain == chain.value)
            if status is not None:
                conditions.append(table.c.status == status.value)
            if tx_type is not None:
                conditions.append(table.c.type == tx_type.value)

            stmt = select(func.count()).select_from(table).where(and_(*conditions))
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_daily_transaction_counts(
        self,
        start_date: datetime,
        end_date: datetime,
        *,
        chain: ChainType | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[tuple[datetime, int]]:
        """Get daily transaction counts for a date range."""
        try:
            table = self._get_table()
            conditions = [
                table.c.created_at >= start_date,
                table.c.created_at <= end_date,
            ]

            if chain is not None:
                conditions.append(table.c.chain == chain.value)
            if tx_type is not None:
                conditions.append(table.c.type == tx_type.value)

            stmt = (
                select(
                    func.date_trunc("day", table.c.created_at).label("date"),
                    func.count().label("count"),
                )
                .where(and_(*conditions))
                .group_by(func.date_trunc("day", table.c.created_at))
                .order_by(func.date_trunc("day", table.c.created_at))
            )
            result = await self._session.execute(stmt)
            rows = result.all()
            return [(row.date, row.count) for row in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_unique_user_count(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Count unique users with transactions."""
        try:
            table = self._get_table()
            conditions: list[Any] = []

            if start_date is not None:
                conditions.append(table.c.created_at >= start_date)
            if end_date is not None:
                conditions.append(table.c.created_at <= end_date)

            stmt = select(func.count(func.distinct(table.c.user_id))).select_from(table)
            if conditions:
                stmt = stmt.where(and_(*conditions))

            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_active_users_per_day(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple[datetime, int]]:
        """Get count of unique active users per day."""
        try:
            table = self._get_table()
            stmt = (
                select(
                    func.date_trunc("day", table.c.created_at).label("date"),
                    func.count(func.distinct(table.c.user_id)).label("count"),
                )
                .where(
                    and_(
                        table.c.created_at >= start_date,
                        table.c.created_at <= end_date,
                    )
                )
                .group_by(func.date_trunc("day", table.c.created_at))
                .order_by(func.date_trunc("day", table.c.created_at))
            )
            result = await self._session.execute(stmt)
            rows = result.all()
            return [(row.date, row.count) for row in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    # ============================================================
    # Volume Analytics Methods
    # ============================================================

    async def get_total_volume(
        self,
        *,
        chain: ChainType | None = None,
        tx_type: TransactionType | None = None,
        status: TransactionStatus | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[float, float]:
        """Get total transaction volume (sum of amount_in) with optional filters."""
        try:
            table = self._get_table()
            conditions: list[Any] = []

            if chain is not None:
                conditions.append(table.c.chain == chain.value)
            if tx_type is not None:
                conditions.append(table.c.type == tx_type.value)
            if status is not None:
                conditions.append(table.c.status == status.value)
            if start_date is not None:
                conditions.append(table.c.created_at >= start_date)
            if end_date is not None:
                conditions.append(table.c.created_at <= end_date)

            stmt = select(
                func.coalesce(func.sum(table.c.amount_in), 0).label("total_volume"),
                func.count().label("tx_count"),
            ).select_from(table)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            result = await self._session.execute(stmt)
            row = result.first()
            if row:
                return (float(row.total_volume), float(row.tx_count))
            return (0.0, 0.0)
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_volume_by_user(
        self,
        user_id: UserId,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> float:
        """Get total transaction volume for a specific user."""
        try:
            table = self._get_table()
            conditions = [table.c.user_id == user_id.value]

            if chain is not None:
                conditions.append(table.c.chain == chain.value)
            if status is not None:
                conditions.append(table.c.status == status.value)
            if start_date is not None:
                conditions.append(table.c.created_at >= start_date)
            if end_date is not None:
                conditions.append(table.c.created_at <= end_date)

            stmt = (
                select(func.coalesce(func.sum(table.c.amount_in), 0).label("total"))
                .select_from(table)
                .where(and_(*conditions))
            )

            result = await self._session.execute(stmt)
            total = result.scalar()
            return float(total) if total else 0.0
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_daily_volume(
        self,
        start_date: datetime,
        end_date: datetime,
        *,
        chain: ChainType | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[tuple[datetime, float]]:
        """Get daily transaction volume for a date range."""
        try:
            table = self._get_table()
            conditions = [
                table.c.created_at >= start_date,
                table.c.created_at <= end_date,
            ]

            if chain is not None:
                conditions.append(table.c.chain == chain.value)
            if tx_type is not None:
                conditions.append(table.c.type == tx_type.value)

            stmt = (
                select(
                    func.date_trunc("day", table.c.created_at).label("date"),
                    func.coalesce(func.sum(table.c.amount_in), 0).label("volume"),
                )
                .where(and_(*conditions))
                .group_by(func.date_trunc("day", table.c.created_at))
                .order_by(func.date_trunc("day", table.c.created_at))
            )
            result = await self._session.execute(stmt)
            rows = result.all()
            return [(row.date, float(row.volume)) for row in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def get_top_senders(
        self,
        *,
        limit: int = 10,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[tuple[int, int, float]]:
        """Get top senders by transaction count and volume."""
        try:
            table = self._get_table()
            conditions: list[Any] = []

            if start_date is not None:
                conditions.append(table.c.created_at >= start_date)
            if end_date is not None:
                conditions.append(table.c.created_at <= end_date)

            stmt = (
                select(
                    table.c.user_id,
                    func.count().label("tx_count"),
                    func.coalesce(func.sum(table.c.amount_in), 0).label("total_volume"),
                )
                .group_by(table.c.user_id)
                .order_by(func.count().desc())
                .limit(limit)
            )

            if conditions:
                stmt = stmt.where(and_(*conditions))

            result = await self._session.execute(stmt)
            rows = result.all()
            return [
                (row.user_id, row.tx_count, float(row.total_volume)) for row in rows
            ]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error
