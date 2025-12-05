"""
SQLAlchemy implementation of distillation telemetry repository.

Persists telemetry data to PostgreSQL.
"""
import logging
from typing import List, Dict, Any
from datetime import date

from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.services.distillation.telemetry_collector import DistillationTelemetryRecord
from app.infrastructure.persistence_sqla.mappings.distillation_telemetry import (
    distillation_telemetry_table,
)

logger = logging.getLogger(__name__)


class DistillationTelemetryRepositorySqla:
    """
    SQLAlchemy implementation of distillation telemetry repository.
    
    Handles persistence of telemetry data.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def save(self, record: DistillationTelemetryRecord) -> None:
        """
        Save single telemetry record.
        
        Args:
            record: Telemetry record to save
        """
        try:
            stmt = distillation_telemetry_table.insert().values(
                user_id=record.user_id,
                conversation_id=record.conversation_id,
                request_hash=record.request_hash,
                detected_language=record.detected_language,
                provider=record.provider,
                model=record.model,
                success=record.success,
                reason=record.reason,
                confidence=record.confidence,
                latency_ms=record.latency_ms,
                tokens_used=record.tokens_used,
                cost_usd=record.cost_usd,
                fallback_used=record.fallback_used,
                error=record.error,
                timestamp=record.timestamp,
            )
            
            await self.session.execute(stmt)
            await self.session.commit()
            
            logger.debug("Telemetry record saved")
        
        except Exception as e:
            logger.error(f"Failed to save telemetry record: {e}")
            await self.session.rollback()
            raise
    
    async def save_batch(self, records: List[DistillationTelemetryRecord]) -> None:
        """
        Save multiple telemetry records in batch.
        
        Args:
            records: List of telemetry records
        """
        if not records:
            return
        
        try:
            values = [
                {
                    "user_id": record.user_id,
                    "conversation_id": record.conversation_id,
                    "request_hash": record.request_hash,
                    "detected_language": record.detected_language,
                    "provider": record.provider,
                    "model": record.model,
                    "success": record.success,
                    "reason": record.reason,
                    "confidence": record.confidence,
                    "latency_ms": record.latency_ms,
                    "tokens_used": record.tokens_used,
                    "cost_usd": record.cost_usd,
                    "fallback_used": record.fallback_used,
                    "error": record.error,
                    "timestamp": record.timestamp,
                }
                for record in records
            ]
            
            stmt = distillation_telemetry_table.insert().values(values)
            
            await self.session.execute(stmt)
            await self.session.commit()
            
            logger.info(f"Saved batch of {len(records)} telemetry records")
        
        except Exception as e:
            logger.error(f"Failed to save telemetry batch: {e}")
            await self.session.rollback()
            raise
    
    async def get_daily_metrics(
        self,
        start_date: date,
        end_date: date,
        provider: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Get daily aggregated metrics from materialized view.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            provider: Optional provider filter
        
        Returns:
            List of daily metrics
        """
        try:
            # Query materialized view
            query = """
                SELECT
                    date,
                    provider,
                    total_requests,
                    successful_requests,
                    avg_latency_ms,
                    avg_confidence,
                    total_tokens,
                    total_cost_usd,
                    unique_users
                FROM distillation_metrics_daily
                WHERE date >= :start_date AND date <= :end_date
            """
            
            params = {
                "start_date": start_date,
                "end_date": end_date,
            }
            
            if provider:
                query += " AND provider = :provider"
                params["provider"] = provider
            
            query += " ORDER BY date DESC, provider"
            
            result = await self.session.execute(text(query), params)
            
            rows = result.fetchall()
            
            return [
                {
                    "date": row.date,
                    "provider": row.provider,
                    "total_requests": row.total_requests,
                    "successful_requests": row.successful_requests,
                    "avg_latency_ms": float(row.avg_latency_ms),
                    "avg_confidence": float(row.avg_confidence),
                    "total_tokens": row.total_tokens,
                    "total_cost_usd": float(row.total_cost_usd),
                    "unique_users": row.unique_users,
                }
                for row in rows
            ]
        
        except Exception as e:
            logger.error(f"Failed to get daily metrics: {e}")
            raise
    
    async def refresh_materialized_view(self) -> None:
        """Refresh the materialized view for daily metrics."""
        try:
            await self.session.execute(
                text("REFRESH MATERIALIZED VIEW CONCURRENTLY distillation_metrics_daily")
            )
            await self.session.commit()
            
            logger.info("Refreshed distillation metrics materialized view")
        
        except Exception as e:
            logger.error(f"Failed to refresh materialized view: {e}")
            await self.session.rollback()
            raise
