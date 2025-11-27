"""
SQLAlchemy mapping for DeFi Operations tables metadata.
"""

from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey, Numeric, UniqueConstraint, Boolean
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa

from app.domain.enums.side import Side
from app.domain.enums.position_status import PositionStatus
from app.domain.enums.chain_type import ChainType
from app.domain.enums.earn_status import EarnStatus
from app.domain.enums.frequency import Frequency
from app.domain.enums.schedule_status import ScheduleStatus
from app.infrastructure.persistence_sqla.registry import mapping_registry

def map_defi_operations_tables() -> None:
    """Map DeFi Operations entities to database tables (idempotent)."""
    
    # --- Hyperliquid Positions ---
    if "hyperliquid_positions" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class HyperliquidPositionsTable:
            __tablename__ = "hyperliquid_positions"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(Integer, primary_key=True, autoincrement=True)
            user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
            wallet_id = mapped_column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
            
            symbol = mapped_column(String(20), nullable=False, index=True)
            side = mapped_column(Enum(Side, values_callable=lambda x: [e.value for e in x]), nullable=False)
            leverage = mapped_column(Numeric(5, 2), nullable=False)
            size = mapped_column(Numeric(30, 18), nullable=False)
            entry_price = mapped_column(Numeric(20, 8), nullable=False)
            mark_price = mapped_column(Numeric(20, 8), nullable=True)
            liquidation_price = mapped_column(Numeric(20, 8), nullable=True)
            
            unrealized_pnl = mapped_column(Numeric(20, 8), nullable=True)
            realized_pnl = mapped_column(Numeric(20, 8), default=0)
            margin = mapped_column(Numeric(20, 8), nullable=False)
            funding_rate = mapped_column(Numeric(10, 6), nullable=True)
            last_funding_payment = mapped_column(Numeric(20, 8), nullable=True)
            
            status = mapped_column(Enum(PositionStatus, values_callable=lambda x: [e.value for e in x]), default=PositionStatus.OPEN, index=True)
            hyperliquid_order_id = mapped_column(String(100), nullable=True)
            
            opened_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)
            closed_at = mapped_column(DateTime(timezone=True), nullable=True)
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))

    # --- Earn Positions ---
    if "earn_positions" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class EarnPositionsTable:
            __tablename__ = "earn_positions"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(Integer, primary_key=True, autoincrement=True)
            user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
            wallet_id = mapped_column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
            
            chain = mapped_column(Enum(ChainType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
            protocol = mapped_column(String(50), nullable=False, index=True)
            asset = mapped_column(String(20), nullable=False)
            amount_deposited = mapped_column(Numeric(30, 18), nullable=False)
            current_value = mapped_column(Numeric(30, 18), nullable=True)
            
            apy = mapped_column(Numeric(8, 4), nullable=True)
            current_apy = mapped_column(Numeric(8, 4), nullable=True)
            rewards_earned = mapped_column(Numeric(30, 18), default=0)
            rewards_earned_usd = mapped_column(Numeric(20, 2), default=0)
            
            status = mapped_column(Enum(EarnStatus, values_callable=lambda x: [e.value for e in x]), default=EarnStatus.ACTIVE, index=True)
            
            transaction_hash = mapped_column(String(66), nullable=True)
            deposit_tx_hash = mapped_column(String(66), nullable=True)
            withdraw_tx_hash = mapped_column(String(66), nullable=True)
            
            deposited_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), index=True)
            withdrawn_at = mapped_column(DateTime(timezone=True), nullable=True)
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))

    # --- Save Schedules ---
    if "save_schedules" not in mapping_registry.metadata.tables:
        @mapping_registry.mapped
        class SaveSchedulesTable:
            __tablename__ = "save_schedules"
            __table_args__ = {"extend_existing": True}
            
            id = mapped_column(Integer, primary_key=True, autoincrement=True)
            user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
            wallet_id = mapped_column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
            
            chain = mapped_column(Enum(ChainType, values_callable=lambda x: [e.value for e in x]), nullable=False)
            asset = mapped_column(String(20), nullable=False)
            amount = mapped_column(Numeric(30, 18), nullable=False)
            
            frequency = mapped_column(Enum(Frequency, values_callable=lambda x: [e.value for e in x]), nullable=False)
            day_of_week = mapped_column(Integer, nullable=True)
            day_of_month = mapped_column(Integer, nullable=True)
            destination_protocol = mapped_column(String(50), nullable=True)
            
            status = mapped_column(Enum(ScheduleStatus, values_callable=lambda x: [e.value for e in x]), default=ScheduleStatus.ACTIVE, index=True)
            
            next_execution_at = mapped_column(DateTime(timezone=True), nullable=False, index=True)
            last_execution_at = mapped_column(DateTime(timezone=True), nullable=True)
            
            total_saved = mapped_column(Numeric(30, 18), default=0)
            execution_count = mapped_column(Integer, default=0)
            max_executions = mapped_column(Integer, nullable=True)
            
            created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
            updated_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'))
