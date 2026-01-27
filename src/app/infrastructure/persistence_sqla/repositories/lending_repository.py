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
    UserLendingPreferences,
    LendingHealthCheck,
    LeverageLoopExecution,
    LendingAlert,
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

    # =========================================================================
    # USER PREFERENCES
    # =========================================================================

    async def save_user_preferences(
        self, preferences: UserLendingPreferences
    ) -> None:
        """Save or update user lending preferences."""
        try:
            query = """
                INSERT INTO user_lending_preferences (
                    id, user_id, risk_tolerance, min_health_factor, max_leverage,
                    preferred_protocol, auto_rebalance, notification_health_threshold,
                    notification_email, notification_enabled, created_at, updated_at
                )
                VALUES (
                    :id, :user_id, :risk_tolerance, :min_health_factor, :max_leverage,
                    :preferred_protocol, :auto_rebalance, :notification_health_threshold,
                    :notification_email, :notification_enabled, :created_at, :updated_at
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    risk_tolerance = EXCLUDED.risk_tolerance,
                    min_health_factor = EXCLUDED.min_health_factor,
                    max_leverage = EXCLUDED.max_leverage,
                    preferred_protocol = EXCLUDED.preferred_protocol,
                    auto_rebalance = EXCLUDED.auto_rebalance,
                    notification_health_threshold = EXCLUDED.notification_health_threshold,
                    notification_email = EXCLUDED.notification_email,
                    notification_enabled = EXCLUDED.notification_enabled,
                    updated_at = EXCLUDED.updated_at
            """

            await self._session.execute(
                query,
                {
                    "id": preferences.id,
                    "user_id": preferences.user_id,
                    "risk_tolerance": preferences.risk_tolerance,
                    "min_health_factor": preferences.min_health_factor,
                    "max_leverage": preferences.max_leverage,
                    "preferred_protocol": preferences.preferred_protocol,
                    "auto_rebalance": preferences.auto_rebalance,
                    "notification_health_threshold": preferences.notification_health_threshold,
                    "notification_email": preferences.notification_email,
                    "notification_enabled": preferences.notification_enabled,
                    "created_at": preferences.created_at,
                    "updated_at": preferences.updated_at,
                },
            )
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to save user preferences: {str(e)}"
            ) from e

    async def get_user_preferences(
        self, user_id: UUID
    ) -> Optional[UserLendingPreferences]:
        """Get user lending preferences."""
        try:
            query = """
                SELECT id, user_id, risk_tolerance, min_health_factor, max_leverage,
                       preferred_protocol, auto_rebalance, notification_health_threshold,
                       notification_email, notification_enabled, created_at, updated_at
                FROM user_lending_preferences
                WHERE user_id = :user_id
            """

            result = await self._session.execute(query, {"user_id": user_id})
            row = result.fetchone()

            if not row:
                return None

            return UserLendingPreferences(
                id=row[0],
                user_id=row[1],
                risk_tolerance=row[2],
                min_health_factor=Decimal(str(row[3])),
                max_leverage=Decimal(str(row[4])),
                preferred_protocol=row[5],
                auto_rebalance=row[6],
                notification_health_threshold=Decimal(str(row[7]))
                if row[7]
                else None,
                notification_email=row[8],
                notification_enabled=row[9],
                created_at=row[10],
                updated_at=row[11],
            )
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to fetch user preferences: {str(e)}"
            ) from e

    # =========================================================================
    # HEALTH CHECKS
    # =========================================================================

    async def save_health_check(self, check: LendingHealthCheck) -> None:
        """Save a health factor check snapshot."""
        try:
            query = """
                INSERT INTO lending_health_checks (
                    id, user_id, protocol, chain, health_factor, health_factor_level,
                    total_collateral_usd, total_debt_usd, available_to_borrow_usd,
                    liquidation_price, checked_at
                )
                VALUES (
                    :id, :user_id, :protocol, :chain, :health_factor, :health_factor_level,
                    :total_collateral_usd, :total_debt_usd, :available_to_borrow_usd,
                    :liquidation_price, :checked_at
                )
            """

            await self._session.execute(
                query,
                {
                    "id": check.id,
                    "user_id": check.user_id,
                    "protocol": check.protocol,
                    "chain": check.chain,
                    "health_factor": check.health_factor,
                    "health_factor_level": check.health_factor_level,
                    "total_collateral_usd": check.total_collateral_usd,
                    "total_debt_usd": check.total_debt_usd,
                    "available_to_borrow_usd": check.available_to_borrow_usd,
                    "liquidation_price": check.liquidation_price,
                    "checked_at": check.checked_at,
                },
            )
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to save health check: {str(e)}"
            ) from e

    async def get_recent_health_checks(
        self, user_id: UUID, protocol: Optional[str] = None, limit: int = 10
    ) -> List[LendingHealthCheck]:
        """Get recent health checks for a user."""
        try:
            query = """
                SELECT id, user_id, protocol, chain, health_factor, health_factor_level,
                       total_collateral_usd, total_debt_usd, available_to_borrow_usd,
                       liquidation_price, checked_at
                FROM lending_health_checks
                WHERE user_id = :user_id
                  AND (:protocol IS NULL OR protocol = :protocol)
                ORDER BY checked_at DESC
                LIMIT :limit
            """

            result = await self._session.execute(
                query,
                {"user_id": user_id, "protocol": protocol, "limit": limit},
            )
            rows = result.fetchall()

            return [
                LendingHealthCheck(
                    id=row[0],
                    user_id=row[1],
                    protocol=row[2],
                    chain=row[3],
                    health_factor=Decimal(str(row[4])),
                    health_factor_level=row[5],
                    total_collateral_usd=Decimal(str(row[6])),
                    total_debt_usd=Decimal(str(row[7])),
                    available_to_borrow_usd=Decimal(str(row[8]))
                    if row[8]
                    else None,
                    liquidation_price=Decimal(str(row[9])) if row[9] else None,
                    checked_at=row[10],
                )
                for row in rows
            ]
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to fetch recent health checks: {str(e)}"
            ) from e

    # =========================================================================
    # LEVERAGE LOOP EXECUTIONS
    # =========================================================================

    async def save_loop_execution(self, execution: LeverageLoopExecution) -> None:
        """Save a leverage loop execution."""
        try:
            query = """
                INSERT INTO leverage_loop_executions (
                    id, user_id, protocol, chain, asset_address, asset_symbol,
                    initial_amount, target_leverage, actual_leverage, total_steps,
                    current_step, steps_completed, status, final_health_factor,
                    final_collateral_usd, final_debt_usd, total_gas_used, total_cost_usd,
                    error_message, metadata, created_at, updated_at, completed_at
                )
                VALUES (
                    :id, :user_id, :protocol, :chain, :asset_address, :asset_symbol,
                    :initial_amount, :target_leverage, :actual_leverage, :total_steps,
                    :current_step, :steps_completed, :status, :final_health_factor,
                    :final_collateral_usd, :final_debt_usd, :total_gas_used, :total_cost_usd,
                    :error_message, :metadata, :created_at, :updated_at, :completed_at
                )
            """

            await self._session.execute(
                query,
                {
                    "id": execution.id,
                    "user_id": execution.user_id,
                    "protocol": execution.protocol,
                    "chain": execution.chain,
                    "asset_address": execution.asset_address,
                    "asset_symbol": execution.asset_symbol,
                    "initial_amount": execution.initial_amount,
                    "target_leverage": execution.target_leverage,
                    "actual_leverage": execution.actual_leverage,
                    "total_steps": execution.total_steps,
                    "current_step": execution.current_step,
                    "steps_completed": execution.steps_completed,
                    "status": execution.status,
                    "final_health_factor": execution.final_health_factor,
                    "final_collateral_usd": execution.final_collateral_usd,
                    "final_debt_usd": execution.final_debt_usd,
                    "total_gas_used": execution.total_gas_used,
                    "total_cost_usd": execution.total_cost_usd,
                    "error_message": execution.error_message,
                    "metadata": execution.metadata,
                    "created_at": execution.created_at,
                    "updated_at": execution.updated_at,
                    "completed_at": execution.completed_at,
                },
            )
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to save loop execution: {str(e)}"
            ) from e

    async def get_loop_execution(
        self, loop_id: UUID
    ) -> Optional[LeverageLoopExecution]:
        """Get a leverage loop execution by ID."""
        try:
            query = """
                SELECT id, user_id, protocol, chain, asset_address, asset_symbol,
                       initial_amount, target_leverage, actual_leverage, total_steps,
                       current_step, steps_completed, status, final_health_factor,
                       final_collateral_usd, final_debt_usd, total_gas_used, total_cost_usd,
                       error_message, metadata, created_at, updated_at, completed_at
                FROM leverage_loop_executions
                WHERE id = :loop_id
            """

            result = await self._session.execute(query, {"loop_id": loop_id})
            row = result.fetchone()

            if not row:
                return None

            return LeverageLoopExecution(
                id=row[0],
                user_id=row[1],
                protocol=row[2],
                chain=row[3],
                asset_address=row[4],
                asset_symbol=row[5],
                initial_amount=Decimal(str(row[6])),
                target_leverage=Decimal(str(row[7])),
                actual_leverage=Decimal(str(row[8])) if row[8] else None,
                total_steps=row[9],
                current_step=row[10],
                steps_completed=row[11] or [],
                status=row[12],
                final_health_factor=Decimal(str(row[13])) if row[13] else None,
                final_collateral_usd=Decimal(str(row[14])) if row[14] else None,
                final_debt_usd=Decimal(str(row[15])) if row[15] else None,
                total_gas_used=Decimal(str(row[16])) if row[16] else None,
                total_cost_usd=Decimal(str(row[17])) if row[17] else None,
                error_message=row[18],
                metadata=row[19],
                created_at=row[20],
                updated_at=row[21],
                completed_at=row[22],
            )
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to fetch loop execution: {str(e)}"
            ) from e

    async def update_loop_execution(self, execution: LeverageLoopExecution) -> None:
        """Update a leverage loop execution (progress, status, results)."""
        try:
            query = """
                UPDATE leverage_loop_executions
                SET current_step = :current_step,
                    steps_completed = :steps_completed,
                    status = :status,
                    actual_leverage = :actual_leverage,
                    final_health_factor = :final_health_factor,
                    final_collateral_usd = :final_collateral_usd,
                    final_debt_usd = :final_debt_usd,
                    total_gas_used = :total_gas_used,
                    total_cost_usd = :total_cost_usd,
                    error_message = :error_message,
                    metadata = :metadata,
                    updated_at = :updated_at,
                    completed_at = :completed_at
                WHERE id = :id
            """

            await self._session.execute(
                query,
                {
                    "id": execution.id,
                    "current_step": execution.current_step,
                    "steps_completed": execution.steps_completed,
                    "status": execution.status,
                    "actual_leverage": execution.actual_leverage,
                    "final_health_factor": execution.final_health_factor,
                    "final_collateral_usd": execution.final_collateral_usd,
                    "final_debt_usd": execution.final_debt_usd,
                    "total_gas_used": execution.total_gas_used,
                    "total_cost_usd": execution.total_cost_usd,
                    "error_message": execution.error_message,
                    "metadata": execution.metadata,
                    "updated_at": execution.updated_at,
                    "completed_at": execution.completed_at,
                },
            )
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to update loop execution: {str(e)}"
            ) from e

    async def get_user_loop_executions(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[LeverageLoopExecution]:
        """Get leverage loop executions for a user."""
        try:
            query = """
                SELECT id, user_id, protocol, chain, asset_address, asset_symbol,
                       initial_amount, target_leverage, actual_leverage, total_steps,
                       current_step, steps_completed, status, final_health_factor,
                       final_collateral_usd, final_debt_usd, total_gas_used, total_cost_usd,
                       error_message, metadata, created_at, updated_at, completed_at
                FROM leverage_loop_executions
                WHERE user_id = :user_id
                  AND (:status IS NULL OR status = :status)
                ORDER BY created_at DESC
                LIMIT :limit
            """

            result = await self._session.execute(
                query,
                {"user_id": user_id, "status": status, "limit": limit},
            )
            rows = result.fetchall()

            return [
                LeverageLoopExecution(
                    id=row[0],
                    user_id=row[1],
                    protocol=row[2],
                    chain=row[3],
                    asset_address=row[4],
                    asset_symbol=row[5],
                    initial_amount=Decimal(str(row[6])),
                    target_leverage=Decimal(str(row[7])),
                    actual_leverage=Decimal(str(row[8])) if row[8] else None,
                    total_steps=row[9],
                    current_step=row[10],
                    steps_completed=row[11] or [],
                    status=row[12],
                    final_health_factor=Decimal(str(row[13])) if row[13] else None,
                    final_collateral_usd=Decimal(str(row[14]))
                    if row[14]
                    else None,
                    final_debt_usd=Decimal(str(row[15])) if row[15] else None,
                    total_gas_used=Decimal(str(row[16])) if row[16] else None,
                    total_cost_usd=Decimal(str(row[17])) if row[17] else None,
                    error_message=row[18],
                    metadata=row[19],
                    created_at=row[20],
                    updated_at=row[21],
                    completed_at=row[22],
                )
                for row in rows
            ]
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to fetch user loop executions: {str(e)}"
            ) from e

    # =========================================================================
    # ALERTS
    # =========================================================================

    async def create_alert(self, alert: LendingAlert) -> None:
        """Create a lending alert."""
        try:
            query = """
                INSERT INTO lending_alerts (
                    id, user_id, position_id, alert_type, severity, title, message,
                    health_factor, threshold_value, current_value, is_read, sent_at,
                    metadata, created_at
                )
                VALUES (
                    :id, :user_id, :position_id, :alert_type, :severity, :title, :message,
                    :health_factor, :threshold_value, :current_value, :is_read, :sent_at,
                    :metadata, :created_at
                )
            """

            await self._session.execute(
                query,
                {
                    "id": alert.id,
                    "user_id": alert.user_id,
                    "position_id": alert.position_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "title": alert.title,
                    "message": alert.message,
                    "health_factor": alert.health_factor,
                    "threshold_value": alert.threshold_value,
                    "current_value": alert.current_value,
                    "is_read": alert.is_read,
                    "sent_at": alert.sent_at,
                    "metadata": alert.metadata,
                    "created_at": alert.created_at,
                },
            )
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to create alert: {str(e)}") from e

    async def get_unread_alerts(
        self, user_id: UUID, severity: Optional[str] = None
    ) -> List[LendingAlert]:
        """Get unread alerts for a user."""
        try:
            query = """
                SELECT id, user_id, position_id, alert_type, severity, title, message,
                       health_factor, threshold_value, current_value, is_read, sent_at,
                       metadata, created_at
                FROM lending_alerts
                WHERE user_id = :user_id
                  AND is_read = false
                  AND (:severity IS NULL OR severity = :severity)
                ORDER BY created_at DESC
            """

            result = await self._session.execute(
                query, {"user_id": user_id, "severity": severity}
            )
            rows = result.fetchall()

            return [
                LendingAlert(
                    id=row[0],
                    user_id=row[1],
                    position_id=row[2],
                    alert_type=row[3],
                    severity=row[4],
                    title=row[5],
                    message=row[6],
                    health_factor=Decimal(str(row[7])) if row[7] else None,
                    threshold_value=Decimal(str(row[8])) if row[8] else None,
                    current_value=Decimal(str(row[9])) if row[9] else None,
                    is_read=row[10],
                    sent_at=row[11],
                    metadata=row[12],
                    created_at=row[13],
                )
                for row in rows
            ]
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to fetch unread alerts: {str(e)}"
            ) from e

    async def mark_alert_as_read(self, alert_id: UUID) -> None:
        """Mark an alert as read."""
        try:
            query = """
                UPDATE lending_alerts
                SET is_read = true
                WHERE id = :alert_id
            """

            await self._session.execute(query, {"alert_id": alert_id})
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryError(
                f"Failed to mark alert as read: {str(e)}"
            ) from e

    async def get_user_alerts(
        self,
        user_id: UUID,
        include_read: bool = False,
        limit: int = 50,
    ) -> List[LendingAlert]:
        """Get alerts for a user."""
        try:
            query = """
                SELECT id, user_id, position_id, alert_type, severity, title, message,
                       health_factor, threshold_value, current_value, is_read, sent_at,
                       metadata, created_at
                FROM lending_alerts
                WHERE user_id = :user_id
                  AND (:include_read OR is_read = false)
                ORDER BY created_at DESC
                LIMIT :limit
            """

            result = await self._session.execute(
                query,
                {
                    "user_id": user_id,
                    "include_read": include_read,
                    "limit": limit,
                },
            )
            rows = result.fetchall()

            return [
                LendingAlert(
                    id=row[0],
                    user_id=row[1],
                    position_id=row[2],
                    alert_type=row[3],
                    severity=row[4],
                    title=row[5],
                    message=row[6],
                    health_factor=Decimal(str(row[7])) if row[7] else None,
                    threshold_value=Decimal(str(row[8])) if row[8] else None,
                    current_value=Decimal(str(row[9])) if row[9] else None,
                    is_read=row[10],
                    sent_at=row[11],
                    metadata=row[12],
                    created_at=row[13],
                )
                for row in rows
            ]
        except SQLAlchemyError as e:
            raise RepositoryError(
                f"Failed to fetch user alerts: {str(e)}"
            ) from e
