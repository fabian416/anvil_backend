"""
SQLAlchemy implementation of lending repository.

Adapter that implements ILendingRepository port for PostgreSQL persistence.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.domain.ports.lending_repository import ILendingRepository
from app.domain.entities.lending import (
    LendingPosition,
    SupplyPosition,
    BorrowPosition,
    LendingTransaction,
)


class RepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class SQLAlchemyLendingRepository(ILendingRepository):
    """
    SQLAlchemy implementation of lending repository.

    Uses raw SQL queries via SQLAlchemy Core for performance and CQRS pattern.
    """

    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: AsyncSession for database operations
        """
        self._session = session

    async def save_position(self, position: LendingPosition) -> None:
        """Save or update a lending position."""
        try:
            # Use INSERT ... ON CONFLICT UPDATE for upsert
            query = """
                INSERT INTO lending_positions (
                    id, user_id, protocol, chain, position_type,
                    asset_address, asset_symbol, amount, amount_usd,
                    health_factor, apy, status, created_at, updated_at
                )
                VALUES (
                    :id, :user_id, :protocol, :chain, :position_type,
                    :asset_address, :asset_symbol, :amount, :amount_usd,
                    :health_factor, :apy, :status, :created_at, :updated_at
                )
                ON CONFLICT (id) DO UPDATE SET
                    amount = EXCLUDED.amount,
                    amount_usd = EXCLUDED.amount_usd,
                    health_factor = EXCLUDED.health_factor,
                    apy = EXCLUDED.apy,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at
            """

            await self._session.execute(
                query,
                {
                    "id": position.id,
                    "user_id": position.user_id,
                    "protocol": position.protocol,
                    "chain": position.chain,
                    "position_type": position.position_type,
                    "asset_address": position.asset_address,
                    "asset_symbol": position.asset_symbol,
                    "amount": position.amount,
                    "amount_usd": position.amount_usd,
                    "health_factor": position.health_factor,
                    "apy": position.apy,
                    "status": position.status,
                    "created_at": position.created_at,
                    "updated_at": position.updated_at,
                },
            )
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to save lending position: {str(e)}"
            ) from e

    async def save_supply(self, supply: SupplyPosition) -> None:
        """Save a supply position."""
        try:
            query = """
                INSERT INTO lending_supplies (
                    id, position_id, user_id, protocol, chain,
                    asset_address, asset_symbol, amount, apy,
                    transaction_hash, block_number, gas_used, created_at
                )
                VALUES (
                    :id, :position_id, :user_id, :protocol, :chain,
                    :asset_address, :asset_symbol, :amount, :apy,
                    :transaction_hash, :block_number, :gas_used, :created_at
                )
            """

            await self._session.execute(
                query,
                {
                    "id": supply.id,
                    "position_id": supply.position_id,
                    "user_id": supply.user_id,
                    "protocol": supply.protocol,
                    "chain": supply.chain,
                    "asset_address": supply.asset_address,
                    "asset_symbol": supply.asset_symbol,
                    "amount": supply.amount,
                    "apy": supply.apy,
                    "transaction_hash": supply.transaction_hash,
                    "block_number": supply.block_number,
                    "gas_used": supply.gas_used,
                    "created_at": supply.created_at,
                },
            )
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to save supply position: {str(e)}"
            ) from e

    async def save_borrow(self, borrow: BorrowPosition) -> None:
        """Save a borrow position."""
        try:
            query = """
                INSERT INTO lending_borrows (
                    id, position_id, user_id, protocol, chain,
                    asset_address, asset_symbol, amount, interest_rate,
                    variable_rate, health_factor_at_borrow,
                    transaction_hash, block_number, created_at
                )
                VALUES (
                    :id, :position_id, :user_id, :protocol, :chain,
                    :asset_address, :asset_symbol, :amount, :interest_rate,
                    :variable_rate, :health_factor_at_borrow,
                    :transaction_hash, :block_number, :created_at
                )
            """

            await self._session.execute(
                query,
                {
                    "id": borrow.id,
                    "position_id": borrow.position_id,
                    "user_id": borrow.user_id,
                    "protocol": borrow.protocol,
                    "chain": borrow.chain,
                    "asset_address": borrow.asset_address,
                    "asset_symbol": borrow.asset_symbol,
                    "amount": borrow.amount,
                    "interest_rate": borrow.interest_rate,
                    "variable_rate": borrow.variable_rate,
                    "health_factor_at_borrow": borrow.health_factor_at_borrow,
                    "transaction_hash": borrow.transaction_hash,
                    "block_number": borrow.block_number,
                    "created_at": borrow.created_at,
                },
            )
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to save borrow position: {str(e)}"
            ) from e

    async def save_transaction(self, transaction: LendingTransaction) -> None:
        """Save a lending transaction."""
        try:
            query = """
                INSERT INTO lending_transactions (
                    id, user_id, protocol, chain, action_type,
                    asset_address, asset_symbol, amount, transaction_hash,
                    status, health_factor_before, health_factor_after,
                    metadata, created_at, confirmed_at
                )
                VALUES (
                    :id, :user_id, :protocol, :chain, :action_type,
                    :asset_address, :asset_symbol, :amount, :transaction_hash,
                    :status, :health_factor_before, :health_factor_after,
                    :metadata, :created_at, :confirmed_at
                )
            """

            await self._session.execute(
                query,
                {
                    "id": transaction.id,
                    "user_id": transaction.user_id,
                    "protocol": transaction.protocol,
                    "chain": transaction.chain,
                    "action_type": transaction.action_type,
                    "asset_address": transaction.asset_address,
                    "asset_symbol": transaction.asset_symbol,
                    "amount": transaction.amount,
                    "transaction_hash": transaction.transaction_hash,
                    "status": transaction.status,
                    "health_factor_before": transaction.health_factor_before,
                    "health_factor_after": transaction.health_factor_after,
                    "metadata": transaction.metadata,
                    "created_at": transaction.created_at,
                    "confirmed_at": transaction.confirmed_at,
                },
            )
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to save lending transaction: {str(e)}"
            ) from e

    async def get_user_positions(
        self, user_id: UUID, protocol: Optional[str] = None
    ) -> List[LendingPosition]:
        """Get all lending positions for a user."""
        try:
            query = """
                SELECT id, user_id, protocol, chain, position_type,
                       asset_address, asset_symbol, amount, amount_usd,
                       health_factor, apy, status, created_at, updated_at
                FROM lending_positions
                WHERE user_id = :user_id
                  AND (:protocol IS NULL OR protocol = :protocol)
                  AND status = 'active'
                ORDER BY created_at DESC
            """

            result = await self._session.execute(
                query, {"user_id": user_id, "protocol": protocol}
            )
            rows = result.fetchall()

            return [
                LendingPosition(
                    id=row[0],
                    user_id=row[1],
                    protocol=row[2],
                    chain=row[3],
                    position_type=row[4],
                    asset_address=row[5],
                    asset_symbol=row[6],
                    amount=Decimal(str(row[7])),
                    amount_usd=Decimal(str(row[8])),
                    health_factor=Decimal(str(row[9])) if row[9] else None,
                    apy=Decimal(str(row[10])),
                    status=row[11],
                    created_at=row[12],
                    updated_at=row[13],
                )
                for row in rows
            ]
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to fetch user positions: {str(e)}"
            ) from e

    async def get_position_by_id(
        self, position_id: UUID
    ) -> Optional[LendingPosition]:
        """Get a lending position by ID."""
        try:
            query = """
                SELECT id, user_id, protocol, chain, position_type,
                       asset_address, asset_symbol, amount, amount_usd,
                       health_factor, apy, status, created_at, updated_at
                FROM lending_positions
                WHERE id = :position_id
            """

            result = await self._session.execute(
                query, {"position_id": position_id}
            )
            row = result.fetchone()

            if not row:
                return None

            return LendingPosition(
                id=row[0],
                user_id=row[1],
                protocol=row[2],
                chain=row[3],
                position_type=row[4],
                asset_address=row[5],
                asset_symbol=row[6],
                amount=Decimal(str(row[7])),
                amount_usd=Decimal(str(row[8])),
                health_factor=Decimal(str(row[9])) if row[9] else None,
                apy=Decimal(str(row[10])),
                status=row[11],
                created_at=row[12],
                updated_at=row[13],
            )
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to fetch position by ID: {str(e)}"
            ) from e

    async def get_user_transactions(
        self,
        user_id: UUID,
        protocol: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[LendingTransaction]:
        """Get transaction history for a user."""
        try:
            query = """
                SELECT id, user_id, protocol, chain, action_type,
                       asset_address, asset_symbol, amount, transaction_hash,
                       status, health_factor_before, health_factor_after,
                       metadata, created_at, confirmed_at
                FROM lending_transactions
                WHERE user_id = :user_id
                  AND (:protocol IS NULL OR protocol = :protocol)
                  AND (:action_type IS NULL OR action_type = :action_type)
                ORDER BY created_at DESC
                LIMIT :limit
            """

            result = await self._session.execute(
                query,
                {
                    "user_id": user_id,
                    "protocol": protocol,
                    "action_type": action_type,
                    "limit": limit,
                },
            )
            rows = result.fetchall()

            return [
                LendingTransaction(
                    id=row[0],
                    user_id=row[1],
                    protocol=row[2],
                    chain=row[3],
                    action_type=row[4],
                    asset_address=row[5],
                    asset_symbol=row[6],
                    amount=Decimal(str(row[7])),
                    transaction_hash=row[8],
                    status=row[9],
                    health_factor_before=Decimal(str(row[10]))
                    if row[10]
                    else None,
                    health_factor_after=Decimal(str(row[11]))
                    if row[11]
                    else None,
                    metadata=row[12],
                    created_at=row[13],
                    confirmed_at=row[14],
                )
                for row in rows
            ]
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to fetch user transactions: {str(e)}"
            ) from e

    async def update_transaction_status(
        self,
        transaction_hash: str,
        status: str,
        confirmed_at: Optional[str] = None,
    ) -> None:
        """Update transaction status after on-chain confirmation."""
        try:
            query = """
                UPDATE lending_transactions
                SET status = :status,
                    confirmed_at = :confirmed_at
                WHERE transaction_hash = :transaction_hash
            """

            await self._session.execute(
                query,
                {
                    "transaction_hash": transaction_hash,
                    "status": status,
                    "confirmed_at": confirmed_at,
                },
            )
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to update transaction status: {str(e)}"
            ) from e
