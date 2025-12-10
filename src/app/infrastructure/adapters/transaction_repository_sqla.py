"""
SQLAlchemy implementation of TransactionRepository.

Handles CRUD operations for transactions stored locally in the database.
Transactions represent on-chain operations initiated by users via Privy.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, delete, func, select, update
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
from app.infrastructure.persistence_sqla.mappings.transaction import map_transaction_table
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

        return Transaction(
            id_=TransactionId(row["id"]),
            user_id=UserId(row["user_id"]),
            wallet_id=WalletId(row["wallet_id"]),
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
        )

    def _transaction_to_dict(self, transaction: Transaction) -> dict[str, Any]:
        """Convert a Transaction entity to a dictionary for database insert."""
        return {
            "user_id": transaction.user_id.value,
            "wallet_id": transaction.wallet_id.value,
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
        """Get transaction by blockchain hash."""
        try:
            table = self._get_table()
            stmt: Select = select(table).where(table.c.tx_hash == tx_hash.lower())
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
            await self._session.flush()

            # Return the saved transaction with the new ID
            return Transaction(
                id_=TransactionId(new_id),
                user_id=transaction.user_id,
                wallet_id=transaction.wallet_id,
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
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update(self, transaction: Transaction) -> Transaction:
        """Update an existing transaction."""
        try:
            table = self._get_table()
            data = self._transaction_to_dict(transaction)

            stmt = (
                update(table)
                .where(table.c.id == transaction.id_.value)
                .values(**data)
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
