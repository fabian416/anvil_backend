"""
SQLAlchemy repository adapter for UserContextAware entity.

Implements the UserContextRepository protocol for PostgreSQL persistence.
"""

import logging
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select, delete, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.domain.chat.entities.user_context_aware import UserContextAware
from app.domain.chat.ports.user_context_repository import UserContextRepository

logger = logging.getLogger(__name__)


class UserContextRepositorySqla:
    """
    SQLAlchemy implementation of UserContextRepository.
    
    This adapter handles persistence of user context data used for
    context-aware agent responses.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self._session = session
    
    async def get_by_id(self, context_id: UUID) -> UserContextAware | None:
        """Get user context by its ID."""
        stmt = select(self._get_table()).where(
            self._get_table().c.id == context_id
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return None
        
        return self._row_to_entity(row._mapping)
    
    async def get_by_chat_user_id(self, chat_user_id: UUID) -> UserContextAware | None:
        """Get user context by chat user ID."""
        stmt = select(self._get_table()).where(
            self._get_table().c.chat_user_id == chat_user_id
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return None
        
        return self._row_to_entity(row._mapping)
    
    async def get_by_legacy_user_id(self, legacy_user_id: int) -> UserContextAware | None:
        """Get user context by legacy user ID."""
        stmt = select(self._get_table()).where(
            self._get_table().c.legacy_user_id == legacy_user_id
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return None
        
        return self._row_to_entity(row._mapping)
    
    async def save(self, context: UserContextAware) -> UserContextAware:
        """Save or update user context."""
        table = self._get_table()
        
        # Prepare data for upsert
        data = self._entity_to_dict(context)
        data["updated_at"] = datetime.now(UTC)
        
        # Use PostgreSQL upsert (INSERT ... ON CONFLICT UPDATE)
        stmt = insert(table).values(**data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["chat_user_id"],
            set_={
                key: stmt.excluded[key]
                for key in data.keys()
                if key not in ("id", "chat_user_id", "created_at")
            },
        )
        
        await self._session.execute(stmt)
        await self._session.commit()
        
        # Fetch the updated record
        return await self.get_by_chat_user_id(context.chat_user_id) or context
    
    async def delete(self, context_id: UUID) -> bool:
        """Delete user context by ID."""
        stmt = delete(self._get_table()).where(
            self._get_table().c.id == context_id
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        
        return result.rowcount > 0
    
    async def get_eligible_for_update(
        self,
        before: datetime,
        limit: int = 100,
    ) -> list[UserContextAware]:
        """Get user contexts eligible for update."""
        table = self._get_table()
        
        stmt = (
            select(table)
            .where(table.c.next_update_eligible_at <= before)
            .order_by(table.c.context_updated_at.asc())
            .limit(limit)
        )
        
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return [self._row_to_entity(row._mapping) for row in rows]
    
    async def get_by_portfolio_state(
        self,
        portfolio_state: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserContextAware]:
        """Get user contexts by portfolio state."""
        table = self._get_table()
        
        stmt = (
            select(table)
            .where(table.c.portfolio_state == portfolio_state)
            .order_by(table.c.context_updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return [self._row_to_entity(row._mapping) for row in rows]
    
    async def get_by_activity_level(
        self,
        activity_level: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserContextAware]:
        """Get user contexts by activity level."""
        table = self._get_table()
        
        stmt = (
            select(table)
            .where(table.c.activity_level == activity_level)
            .order_by(table.c.context_updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return [self._row_to_entity(row._mapping) for row in rows]
    
    async def get_by_user_type(
        self,
        user_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UserContextAware]:
        """Get user contexts by user type."""
        table = self._get_table()
        
        stmt = (
            select(table)
            .where(table.c.user_type == user_type)
            .order_by(table.c.context_updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return [self._row_to_entity(row._mapping) for row in rows]
    
    async def count_by_portfolio_state(self) -> dict[str, int]:
        """Count users by portfolio state."""
        table = self._get_table()
        
        stmt = (
            select(
                table.c.portfolio_state,
                func.count().label("count"),
            )
            .group_by(table.c.portfolio_state)
        )
        
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return {row.portfolio_state: row.count for row in rows}
    
    async def count_by_activity_level(self) -> dict[str, int]:
        """Count users by activity level."""
        table = self._get_table()
        
        stmt = (
            select(
                table.c.activity_level,
                func.count().label("count"),
            )
            .group_by(table.c.activity_level)
        )
        
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return {row.activity_level: row.count for row in rows}
    
    async def count_by_user_type(self) -> dict[str, int]:
        """Count users by user type."""
        table = self._get_table()
        
        stmt = (
            select(
                table.c.user_type,
                func.count().label("count"),
            )
            .group_by(table.c.user_type)
        )
        
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return {row.user_type: row.count for row in rows}
    
    async def get_inactive_users(
        self,
        days_inactive: int = 30,
        limit: int = 100,
    ) -> list[UserContextAware]:
        """Get users who have been inactive for specified days."""
        table = self._get_table()
        cutoff = datetime.now(UTC) - timedelta(days=days_inactive)
        
        stmt = (
            select(table)
            .where(
                and_(
                    table.c.last_active_at < cutoff,
                    table.c.activity_level == "inactive",
                )
            )
            .order_by(table.c.last_active_at.asc())
            .limit(limit)
        )
        
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return [self._row_to_entity(row._mapping) for row in rows]
    
    async def exists_for_chat_user(self, chat_user_id: UUID) -> bool:
        """Check if context exists for a chat user."""
        table = self._get_table()
        
        stmt = select(func.count()).where(
            table.c.chat_user_id == chat_user_id
        )
        
        result = await self._session.execute(stmt)
        count = result.scalar()
        
        return count > 0
    
    def _get_table(self):
        """Get the user_context_aware table from metadata."""
        from app.infrastructure.persistence_sqla.registry import mapping_registry
        return mapping_registry.metadata.tables["user_context_aware"]
    
    def _row_to_entity(self, row: dict[str, Any]) -> UserContextAware:
        """Convert database row to domain entity."""
        return UserContextAware(
            id=row["id"],
            chat_user_id=row["chat_user_id"],
            legacy_user_id=row.get("legacy_user_id"),
            portfolio_state=row["portfolio_state"],
            total_balance_usd=Decimal(str(row["total_balance_usd"])),
            token_count=row["token_count"],
            primary_chain=row.get("primary_chain"),
            activity_level=row["activity_level"],
            last_active_at=row.get("last_active_at"),
            first_active_at=row["first_active_at"],
            chat_sessions_30d=row["chat_sessions_30d"],
            messages_sent_30d=row["messages_sent_30d"],
            user_type=row["user_type"],
            swap_count=row["swap_count"],
            buy_count=row["buy_count"],
            cashout_count=row["cashout_count"],
            lending_count=row["lending_count"],
            money_market_count=row["money_market_count"],
            transfer_count=row["transfer_count"],
            total_executions=row["total_executions"],
            failed_executions=row["failed_executions"],
            execution_success_rate=Decimal(str(row["execution_success_rate"])),
            total_conversations=row["total_conversations"],
            total_messages=row["total_messages"],
            shortcuts_used_count=row["shortcuts_used_count"],
            multi_step_completed_count=row["multi_step_completed_count"],
            avg_messages_per_session=Decimal(str(row["avg_messages_per_session"])),
            detected_language=row["detected_language"],
            language_history=row.get("language_history") or [],
            most_used_agents=row.get("most_used_agents") or [],
            agent_usage_counts=row.get("agent_usage_counts") or {},
            wallet_count=row["wallet_count"],
            has_connected_wallet=row["has_connected_wallet"],
            primary_wallet_address=row.get("primary_wallet_address"),
            wallet_provider=row.get("wallet_provider"),
            wallet_total_usd=Decimal(str(row.get("wallet_total_usd") or 0)),
            wallet_chain_breakdown=row.get("wallet_chain_breakdown") or {},
            wallet_last_sync_at=row.get("wallet_last_sync_at"),
            context_updated_at=row["context_updated_at"],
            next_update_eligible_at=row["next_update_eligible_at"],
            update_count=row["update_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
    
    def _entity_to_dict(self, entity: UserContextAware) -> dict[str, Any]:
        """Convert domain entity to database row dict."""
        return {
            "id": entity.id,
            "chat_user_id": entity.chat_user_id,
            "legacy_user_id": entity.legacy_user_id,
            "portfolio_state": entity.portfolio_state,
            "total_balance_usd": entity.total_balance_usd,
            "token_count": entity.token_count,
            "primary_chain": entity.primary_chain,
            "activity_level": entity.activity_level,
            "last_active_at": entity.last_active_at,
            "first_active_at": entity.first_active_at,
            "chat_sessions_30d": entity.chat_sessions_30d,
            "messages_sent_30d": entity.messages_sent_30d,
            "user_type": entity.user_type,
            "swap_count": entity.swap_count,
            "buy_count": entity.buy_count,
            "cashout_count": entity.cashout_count,
            "lending_count": entity.lending_count,
            "money_market_count": entity.money_market_count,
            "transfer_count": entity.transfer_count,
            "total_executions": entity.total_executions,
            "failed_executions": entity.failed_executions,
            "execution_success_rate": entity.execution_success_rate,
            "total_conversations": entity.total_conversations,
            "total_messages": entity.total_messages,
            "shortcuts_used_count": entity.shortcuts_used_count,
            "multi_step_completed_count": entity.multi_step_completed_count,
            "avg_messages_per_session": entity.avg_messages_per_session,
            "detected_language": entity.detected_language,
            "language_history": entity.language_history,
            "most_used_agents": entity.most_used_agents,
            "agent_usage_counts": entity.agent_usage_counts,
            "wallet_count": entity.wallet_count,
            "has_connected_wallet": entity.has_connected_wallet,
            "primary_wallet_address": entity.primary_wallet_address,
            "wallet_provider": entity.wallet_provider,
            "wallet_total_usd": entity.wallet_total_usd,
            "wallet_chain_breakdown": entity.wallet_chain_breakdown,
            "wallet_last_sync_at": entity.wallet_last_sync_at,
            "context_updated_at": entity.context_updated_at,
            "next_update_eligible_at": entity.next_update_eligible_at,
            "update_count": entity.update_count,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }
    
    # ═══════════════════════════════════════════════════════════════
    # ANALYTICS AGGREGATIONS
    # ═══════════════════════════════════════════════════════════════
    
    async def get_execution_stats(self) -> dict[str, int]:
        """
        Get aggregated execution statistics across all users.
        
        Returns:
            Dictionary with execution counts by type
        """
        table = self._get_table()
        
        stmt = select(
            func.sum(table.c.total_executions).label("total"),
            func.sum(table.c.swap_count).label("swap"),
            func.sum(table.c.buy_count).label("buy"),
            func.sum(table.c.lending_count).label("lending"),
            func.sum(table.c.transfer_count).label("transfer"),
            func.sum(table.c.cashout_count).label("cashout"),
        )
        
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return {
                "total": 0,
                "swap": 0,
                "buy": 0,
                "lending": 0,
                "transfer": 0,
                "cashout": 0,
            }
        
        return {
            "total": int(row.total or 0),
            "swap": int(row.swap or 0),
            "buy": int(row.buy or 0),
            "lending": int(row.lending or 0),
            "transfer": int(row.transfer or 0),
            "cashout": int(row.cashout or 0),
        }
    
    async def get_total_balance(self) -> Decimal:
        """
        Get sum of all user wallet balances.
        
        Returns:
            Total USD balance across all users
        """
        table = self._get_table()
        
        stmt = select(func.sum(table.c.wallet_total_usd))
        result = await self._session.execute(stmt)
        total = result.scalar()
        
        return Decimal(str(total or 0))
