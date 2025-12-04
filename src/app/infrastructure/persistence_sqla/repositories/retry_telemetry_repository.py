"""
Retry telemetry repository.

SQLAlchemy implementation for retry telemetry data persistence.
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta, date as Date
from sqlalchemy import select, func, and_, text, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

# Import table definitions (will be created in mappings)
from app.infrastructure.persistence_sqla.mappings.retry_telemetry import (
    retry_attempts,
    circuit_breaker_events,
    service_override_events,
    retry_metrics_aggregate,
)


class RetryTelemetryRepository:
    """Repository for retry telemetry data."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create_attempt(
        self,
        service_name: str,
        attempt_number: int,
        latency_ms: Optional[int] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        request_context: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
    ) -> None:
        """Create a retry attempt record."""
        query = insert(retry_attempts).values(
            service_name=service_name,
            attempt_number=attempt_number,
            latency_ms=latency_ms,
            error_type=error_type,
            error_message=error_message,
            request_context=request_context or {},
            success=success,
            created_at=datetime.utcnow(),
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def create_circuit_event(
        self,
        service_name: str,
        from_state: str,
        to_state: str,
        reason: str,
        failure_count: int = 0,
        success_count: int = 0,
    ) -> None:
        """Create a circuit breaker event record."""
        query = insert(circuit_breaker_events).values(
            service_name=service_name,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            failure_count=failure_count,
            success_count=success_count,
            created_at=datetime.utcnow(),
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def create_override_event(
        self,
        service_name: str,
        action: str,
        user_id: UUID,
        reason: str,
        duration_minutes: Optional[int] = None,
    ) -> None:
        """Create a service override event record."""
        query = insert(service_override_events).values(
            service_name=service_name,
            action=action,
            user_id=user_id,
            reason=reason,
            duration_minutes=duration_minutes,
            created_at=datetime.utcnow(),
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def increment_success(
        self,
        service_name: str,
        latency_ms: int,
    ) -> None:
        """Increment success count in daily aggregate."""
        today = datetime.utcnow().date()
        
        # Get or create aggregate
        aggregate = await self._get_or_create_aggregate(service_name, today)
        
        # Update counts
        aggregate['total_requests'] += 1
        aggregate['successful_requests'] += 1
        
        # Update average latency
        total = aggregate['total_requests']
        current_avg = aggregate['avg_latency_ms'] or 0
        new_avg = ((current_avg * (total - 1)) + latency_ms) / total
        aggregate['avg_latency_ms'] = new_avg
        aggregate['updated_at'] = datetime.utcnow()
        
        # Upsert
        query = insert(retry_metrics_aggregate).values(**aggregate)
        query = query.on_conflict_do_update(
            index_elements=['service_name', 'date'],
            set_=dict(
                total_requests=aggregate['total_requests'],
                successful_requests=aggregate['successful_requests'],
                avg_latency_ms=aggregate['avg_latency_ms'],
                updated_at=aggregate['updated_at'],
            )
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def increment_failure(
        self,
        service_name: str,
    ) -> None:
        """Increment failure count in daily aggregate."""
        today = datetime.utcnow().date()
        
        aggregate = await self._get_or_create_aggregate(service_name, today)
        
        aggregate['total_requests'] += 1
        aggregate['failed_requests'] += 1
        aggregate['retry_attempts'] += 1
        aggregate['updated_at'] = datetime.utcnow()
        
        query = insert(retry_metrics_aggregate).values(**aggregate)
        query = query.on_conflict_do_update(
            index_elements=['service_name', 'date'],
            set_=dict(
                total_requests=aggregate['total_requests'],
                failed_requests=aggregate['failed_requests'],
                retry_attempts=aggregate['retry_attempts'],
                updated_at=aggregate['updated_at'],
            )
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def increment_circuit_open(
        self,
        service_name: str,
    ) -> None:
        """Increment circuit breaker open count."""
        today = datetime.utcnow().date()
        
        aggregate = await self._get_or_create_aggregate(service_name, today)
        
        aggregate['circuit_breaker_opens'] += 1
        aggregate['updated_at'] = datetime.utcnow()
        
        query = insert(retry_metrics_aggregate).values(**aggregate)
        query = query.on_conflict_do_update(
            index_elements=['service_name', 'date'],
            set_=dict(
                circuit_breaker_opens=aggregate['circuit_breaker_opens'],
                updated_at=aggregate['updated_at'],
            )
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def get_aggregated_metrics(
        self,
        service_name: str,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Get aggregated metrics for a service."""
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        query = (
            select(retry_metrics_aggregate)
            .where(
                and_(
                    retry_metrics_aggregate.c.service_name == service_name,
                    retry_metrics_aggregate.c.date >= start_date,
                )
            )
            .order_by(desc(retry_metrics_aggregate.c.date))
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [
            {
                "date": row.date.isoformat(),
                "total_requests": row.total_requests,
                "successful_requests": row.successful_requests,
                "failed_requests": row.failed_requests,
                "retry_attempts": row.retry_attempts,
                "avg_latency_ms": float(row.avg_latency_ms) if row.avg_latency_ms else 0,
                "circuit_breaker_opens": row.circuit_breaker_opens,
                "success_rate": (
                    row.successful_requests / row.total_requests
                    if row.total_requests > 0
                    else 0
                ),
            }
            for row in rows
        ]
    
    async def _get_or_create_aggregate(
        self,
        service_name: str,
        date: Date,
    ) -> Dict[str, Any]:
        """Get or create daily aggregate."""
        query = select(retry_metrics_aggregate).where(
            and_(
                retry_metrics_aggregate.c.service_name == service_name,
                retry_metrics_aggregate.c.date == date,
            )
        )
        
        result = await self.session.execute(query)
        row = result.one_or_none()
        
        if row:
            return {
                'service_name': row.service_name,
                'date': row.date,
                'total_requests': row.total_requests,
                'successful_requests': row.successful_requests,
                'failed_requests': row.failed_requests,
                'retry_attempts': row.retry_attempts,
                'avg_latency_ms': float(row.avg_latency_ms) if row.avg_latency_ms else 0.0,
                'circuit_breaker_opens': row.circuit_breaker_opens,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
            }
        else:
            return {
                'service_name': service_name,
                'date': date,
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'retry_attempts': 0,
                'avg_latency_ms': 0.0,
                'circuit_breaker_opens': 0,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
            }
