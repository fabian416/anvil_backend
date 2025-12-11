"""
Database Query Telemetry.

Enterprise-grade telemetry for database operations:
- Query execution timing
- Connection pool monitoring
- Slow query detection
- Query pattern analysis
- Transaction tracking
- Error monitoring

Usage:
    from app.infrastructure.telemetry.db_telemetry import (
        DatabaseTelemetry,
        setup_engine_telemetry,
        get_db_telemetry,
    )
    
    # Setup engine telemetry
    setup_engine_telemetry(engine, db_telemetry)
    
    # Get metrics
    metrics = db_telemetry.get_query_stats()
"""

import asyncio
import hashlib
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================


class QueryType(str, Enum):
    """Type of database query."""
    
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    ALTER = "alter"
    DROP = "drop"
    TRANSACTION = "transaction"
    OTHER = "other"


class QueryStatus(str, Enum):
    """Status of a query execution."""
    
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    DEADLOCK = "deadlock"


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class DbTelemetryConfig:
    """Configuration for database telemetry."""
    
    enabled: bool = True
    slow_query_threshold_ms: float = 100.0  # 100ms
    very_slow_query_threshold_ms: float = 1000.0  # 1s
    max_query_records: int = 10000
    retention_hours: int = 24
    track_query_patterns: bool = True
    track_connection_pool: bool = True
    log_slow_queries: bool = True
    log_errors: bool = True


@dataclass
class QueryExecution:
    """Record of a query execution."""
    
    query_id: str
    query_hash: str  # Hash of normalized query
    query_type: QueryType
    query_text: str  # Truncated
    start_time: float
    
    # Completed fields
    end_time: Optional[float] = None
    status: QueryStatus = QueryStatus.SUCCESS
    duration_ms: float = 0.0
    rows_affected: int = 0
    error_message: Optional[str] = None
    
    # Context
    table_names: list[str] = field(default_factory=list)
    connection_id: Optional[str] = None
    transaction_id: Optional[str] = None
    
    def complete(
        self,
        status: QueryStatus = QueryStatus.SUCCESS,
        rows_affected: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Mark query as complete."""
        self.end_time = time.time()
        self.status = status
        self.rows_affected = rows_affected
        self.error_message = error_message
        self.duration_ms = (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "query_hash": self.query_hash,
            "query_type": self.query_type.value,
            "query_text": self.query_text[:200],
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status.value,
            "rows_affected": self.rows_affected,
            "table_names": self.table_names,
            "error_message": self.error_message,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat(),
        }


@dataclass
class QueryPattern:
    """Aggregated statistics for a query pattern."""
    
    query_hash: str
    query_template: str  # Normalized query with parameters replaced
    query_type: QueryType
    table_names: list[str]
    
    # Statistics
    execution_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    total_rows: int = 0
    error_count: int = 0
    
    # Timing tracking
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    @property
    def avg_duration_ms(self) -> float:
        if self.execution_count == 0:
            return 0.0
        return self.total_duration_ms / self.execution_count
    
    @property
    def error_rate(self) -> float:
        if self.execution_count == 0:
            return 0.0
        return self.error_count / self.execution_count
    
    def record(self, execution: QueryExecution) -> None:
        """Record an execution of this pattern."""
        now = datetime.utcnow()
        
        self.execution_count += 1
        self.total_duration_ms += execution.duration_ms
        self.min_duration_ms = min(self.min_duration_ms, execution.duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, execution.duration_ms)
        self.total_rows += execution.rows_affected
        
        if execution.status != QueryStatus.SUCCESS:
            self.error_count += 1
        
        if self.first_seen is None:
            self.first_seen = now
        self.last_seen = now
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "query_hash": self.query_hash,
            "query_template": self.query_template[:500],
            "query_type": self.query_type.value,
            "table_names": self.table_names,
            "execution_count": self.execution_count,
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "min_duration_ms": round(self.min_duration_ms, 2),
            "max_duration_ms": round(self.max_duration_ms, 2),
            "total_rows": self.total_rows,
            "error_rate": round(self.error_rate, 4),
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


@dataclass
class ConnectionPoolStats:
    """Connection pool statistics."""
    
    pool_size: int = 0
    checked_out: int = 0
    overflow: int = 0
    checked_in: int = 0
    
    # Event counts
    checkout_count: int = 0
    checkin_count: int = 0
    connect_count: int = 0
    disconnect_count: int = 0
    
    # Timing
    last_checkout_time: Optional[datetime] = None
    last_checkin_time: Optional[datetime] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "pool_size": self.pool_size,
            "checked_out": self.checked_out,
            "overflow": self.overflow,
            "checked_in": self.checked_in,
            "checkout_count": self.checkout_count,
            "checkin_count": self.checkin_count,
            "connect_count": self.connect_count,
            "disconnect_count": self.disconnect_count,
            "last_checkout": self.last_checkout_time.isoformat() if self.last_checkout_time else None,
            "last_checkin": self.last_checkin_time.isoformat() if self.last_checkin_time else None,
        }


@dataclass
class DatabaseMetrics:
    """Aggregated database metrics."""
    
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    slow_queries: int = 0
    very_slow_queries: int = 0
    
    # Duration metrics
    total_duration_ms: float = 0.0
    
    # By type
    queries_by_type: dict[str, int] = field(default_factory=dict)
    duration_by_type: dict[str, float] = field(default_factory=dict)
    
    # By table
    queries_by_table: dict[str, int] = field(default_factory=dict)
    
    # Timestamps
    first_query_at: Optional[datetime] = None
    last_query_at: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_queries == 0:
            return 1.0
        return self.successful_queries / self.total_queries
    
    @property
    def avg_duration_ms(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.total_duration_ms / self.total_queries
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "slow_queries": self.slow_queries,
            "very_slow_queries": self.very_slow_queries,
            "success_rate": round(self.success_rate, 4),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "total_duration_ms": round(self.total_duration_ms, 2),
            "queries_by_type": self.queries_by_type,
            "duration_by_type": {k: round(v, 2) for k, v in self.duration_by_type.items()},
            "queries_by_table": dict(
                sorted(self.queries_by_table.items(), key=lambda x: x[1], reverse=True)[:20]
            ),
            "first_query_at": self.first_query_at.isoformat() if self.first_query_at else None,
            "last_query_at": self.last_query_at.isoformat() if self.last_query_at else None,
        }


# ============================================================================
# DATABASE TELEMETRY SERVICE
# ============================================================================


class DatabaseTelemetry:
    """
    Enterprise telemetry service for database operations.
    
    Features:
    - Query execution timing
    - Slow query detection and logging
    - Query pattern analysis
    - Connection pool monitoring
    - Error tracking
    """
    
    # Patterns for extracting table names
    TABLE_PATTERNS = [
        r'(?:FROM|INTO|UPDATE|JOIN)\s+(?:`|")?(\w+)(?:`|")?',
        r'(?:DELETE\s+FROM)\s+(?:`|")?(\w+)(?:`|")?',
        r'(?:INSERT\s+INTO)\s+(?:`|")?(\w+)(?:`|")?',
    ]
    
    def __init__(self, config: Optional[DbTelemetryConfig] = None):
        self.config = config or DbTelemetryConfig()
        
        # Storage
        self._executions: list[QueryExecution] = []
        self._patterns: dict[str, QueryPattern] = {}
        self._metrics = DatabaseMetrics()
        self._pool_stats = ConnectionPoolStats()
        
        # Slow query tracking
        self._slow_queries: list[QueryExecution] = []
        
        # Active queries (thread-safe tracking)
        self._active_queries: dict[int, QueryExecution] = {}
    
    def start_query(
        self,
        query_text: str,
        connection_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
    ) -> QueryExecution:
        """
        Start tracking a query.
        
        Args:
            query_text: SQL query text
            connection_id: Optional connection identifier
            transaction_id: Optional transaction identifier
            
        Returns:
            QueryExecution context
        """
        query_type = self._detect_query_type(query_text)
        table_names = self._extract_tables(query_text)
        normalized = self._normalize_query(query_text)
        query_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
        
        execution = QueryExecution(
            query_id=str(uuid4()),
            query_hash=query_hash,
            query_type=query_type,
            query_text=query_text[:1000],  # Truncate
            start_time=time.time(),
            table_names=table_names,
            connection_id=connection_id,
            transaction_id=transaction_id,
        )
        
        return execution
    
    def record(self, execution: QueryExecution) -> None:
        """
        Record a completed query execution.
        
        Args:
            execution: Completed query execution
        """
        if not self.config.enabled:
            return
        
        # Store execution
        self._executions.append(execution)
        self._cleanup_old_executions()
        
        # Update metrics
        self._update_metrics(execution)
        
        # Update patterns
        if self.config.track_query_patterns:
            self._update_patterns(execution)
        
        # Track slow queries
        if execution.duration_ms >= self.config.slow_query_threshold_ms:
            self._slow_queries.append(execution)
            self._metrics.slow_queries += 1
            
            if execution.duration_ms >= self.config.very_slow_query_threshold_ms:
                self._metrics.very_slow_queries += 1
            
            if self.config.log_slow_queries:
                logger.warning(
                    f"Slow query ({execution.duration_ms:.1f}ms): "
                    f"{execution.query_text[:100]}..."
                )
        
        # Log errors
        if execution.status != QueryStatus.SUCCESS and self.config.log_errors:
            logger.error(
                f"Query error ({execution.status.value}): {execution.error_message}"
            )
    
    def _detect_query_type(self, query: str) -> QueryType:
        """Detect query type from SQL text."""
        query_upper = query.strip().upper()
        
        if query_upper.startswith("SELECT"):
            return QueryType.SELECT
        if query_upper.startswith("INSERT"):
            return QueryType.INSERT
        if query_upper.startswith("UPDATE"):
            return QueryType.UPDATE
        if query_upper.startswith("DELETE"):
            return QueryType.DELETE
        if query_upper.startswith("CREATE"):
            return QueryType.CREATE
        if query_upper.startswith("ALTER"):
            return QueryType.ALTER
        if query_upper.startswith("DROP"):
            return QueryType.DROP
        if query_upper.startswith(("BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT")):
            return QueryType.TRANSACTION
        
        return QueryType.OTHER
    
    def _extract_tables(self, query: str) -> list[str]:
        """Extract table names from query."""
        tables = set()
        for pattern in self.TABLE_PATTERNS:
            matches = re.findall(pattern, query, re.IGNORECASE)
            tables.update(m.lower() for m in matches)
        return list(tables)
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching."""
        # Remove excess whitespace
        normalized = " ".join(query.split())
        
        # Replace literal values with placeholders
        # Numbers
        normalized = re.sub(r"\b\d+\b", "?", normalized)
        # Quoted strings
        normalized = re.sub(r"'[^']*'", "?", normalized)
        normalized = re.sub(r'"[^"]*"', "?", normalized)
        # UUIDs
        normalized = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "?",
            normalized,
            flags=re.IGNORECASE,
        )
        
        return normalized.lower()
    
    def _update_metrics(self, execution: QueryExecution) -> None:
        """Update aggregate metrics."""
        now = datetime.utcnow()
        
        self._metrics.total_queries += 1
        self._metrics.total_duration_ms += execution.duration_ms
        
        if execution.status == QueryStatus.SUCCESS:
            self._metrics.successful_queries += 1
        else:
            self._metrics.failed_queries += 1
        
        # By type
        type_key = execution.query_type.value
        self._metrics.queries_by_type[type_key] = (
            self._metrics.queries_by_type.get(type_key, 0) + 1
        )
        self._metrics.duration_by_type[type_key] = (
            self._metrics.duration_by_type.get(type_key, 0.0) + execution.duration_ms
        )
        
        # By table
        for table in execution.table_names:
            self._metrics.queries_by_table[table] = (
                self._metrics.queries_by_table.get(table, 0) + 1
            )
        
        # Timestamps
        if self._metrics.first_query_at is None:
            self._metrics.first_query_at = now
        self._metrics.last_query_at = now
    
    def _update_patterns(self, execution: QueryExecution) -> None:
        """Update query pattern statistics."""
        pattern = self._patterns.get(execution.query_hash)
        
        if pattern is None:
            normalized = self._normalize_query(execution.query_text)
            pattern = QueryPattern(
                query_hash=execution.query_hash,
                query_template=normalized,
                query_type=execution.query_type,
                table_names=execution.table_names,
            )
            self._patterns[execution.query_hash] = pattern
        
        pattern.record(execution)
    
    def _cleanup_old_executions(self) -> None:
        """Remove old execution records."""
        if len(self._executions) <= self.config.max_query_records:
            return
        
        cutoff = time.time() - (self.config.retention_hours * 3600)
        self._executions = [e for e in self._executions if e.start_time > cutoff]
        
        # Keep most recent if still too many
        if len(self._executions) > self.config.max_query_records:
            self._executions = self._executions[-self.config.max_query_records:]
        
        # Cleanup slow queries too
        self._slow_queries = [
            e for e in self._slow_queries if e.start_time > cutoff
        ][-100:]
    
    # ========================================================================
    # CONNECTION POOL TRACKING
    # ========================================================================
    
    def on_checkout(self, dbapi_conn: Any, conn_record: Any, conn_proxy: Any) -> None:
        """Called when a connection is checked out from the pool."""
        self._pool_stats.checkout_count += 1
        self._pool_stats.checked_out += 1
        self._pool_stats.last_checkout_time = datetime.utcnow()
    
    def on_checkin(self, dbapi_conn: Any, conn_record: Any) -> None:
        """Called when a connection is returned to the pool."""
        self._pool_stats.checkin_count += 1
        self._pool_stats.checked_out = max(0, self._pool_stats.checked_out - 1)
        self._pool_stats.checked_in += 1
        self._pool_stats.last_checkin_time = datetime.utcnow()
    
    def on_connect(self, dbapi_conn: Any, conn_record: Any) -> None:
        """Called when a new connection is created."""
        self._pool_stats.connect_count += 1
    
    def on_close(self, dbapi_conn: Any, conn_record: Any) -> None:
        """Called when a connection is closed."""
        self._pool_stats.disconnect_count += 1
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def get_metrics(self) -> dict[str, Any]:
        """Get overall database metrics."""
        return self._metrics.to_dict()
    
    def get_pool_stats(self) -> dict[str, Any]:
        """Get connection pool statistics."""
        return self._pool_stats.to_dict()
    
    def get_slow_queries(
        self,
        limit: int = 10,
        threshold_ms: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Get slow queries."""
        threshold = threshold_ms or self.config.slow_query_threshold_ms
        slow = [e for e in self._slow_queries if e.duration_ms >= threshold]
        slow.sort(key=lambda e: e.duration_ms, reverse=True)
        return [e.to_dict() for e in slow[:limit]]
    
    def get_query_patterns(
        self,
        order_by: str = "execution_count",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get query patterns ordered by specified metric."""
        patterns = list(self._patterns.values())
        
        if order_by == "avg_duration":
            patterns.sort(key=lambda p: p.avg_duration_ms, reverse=True)
        elif order_by == "max_duration":
            patterns.sort(key=lambda p: p.max_duration_ms, reverse=True)
        elif order_by == "error_rate":
            patterns.sort(key=lambda p: p.error_rate, reverse=True)
        else:  # execution_count
            patterns.sort(key=lambda p: p.execution_count, reverse=True)
        
        return [p.to_dict() for p in patterns[:limit]]
    
    def get_queries_by_table(self, table: str) -> dict[str, Any]:
        """Get query statistics for a specific table."""
        table_lower = table.lower()
        executions = [
            e for e in self._executions
            if table_lower in e.table_names
        ]
        
        if not executions:
            return {"table": table, "queries": 0}
        
        return {
            "table": table,
            "queries": len(executions),
            "avg_duration_ms": sum(e.duration_ms for e in executions) / len(executions),
            "error_count": sum(1 for e in executions if e.status != QueryStatus.SUCCESS),
            "query_types": {
                t.value: sum(1 for e in executions if e.query_type == t)
                for t in QueryType
                if any(e.query_type == t for e in executions)
            },
        }
    
    def get_recent_errors(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent query errors."""
        errors = [
            e for e in self._executions
            if e.status != QueryStatus.SUCCESS
        ]
        errors.sort(key=lambda e: e.start_time, reverse=True)
        return [e.to_dict() for e in errors[:limit]]
    
    def get_summary(self) -> dict[str, Any]:
        """Get comprehensive telemetry summary."""
        return {
            "metrics": self.get_metrics(),
            "pool_stats": self.get_pool_stats(),
            "slow_query_count": len(self._slow_queries),
            "pattern_count": len(self._patterns),
            "active_queries": len(self._active_queries),
            "top_patterns": self.get_query_patterns(limit=5),
        }
    
    def reset(self) -> None:
        """Reset all telemetry data."""
        self._executions.clear()
        self._patterns.clear()
        self._slow_queries.clear()
        self._metrics = DatabaseMetrics()


# ============================================================================
# ENGINE EVENT LISTENERS
# ============================================================================


def setup_engine_telemetry(
    engine: Engine | AsyncEngine,
    telemetry: DatabaseTelemetry,
) -> None:
    """
    Setup SQLAlchemy event listeners for telemetry.
    
    Args:
        engine: SQLAlchemy engine (sync or async)
        telemetry: Database telemetry instance
    """
    # For async engines, get the sync engine
    sync_engine = engine.sync_engine if hasattr(engine, "sync_engine") else engine
    
    # Query timing context storage
    query_contexts: dict[int, QueryExecution] = {}
    
    @event.listens_for(sync_engine, "before_cursor_execute")
    def before_cursor_execute(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """Record query start time."""
        conn_id = id(conn)
        execution = telemetry.start_query(
            query_text=statement,
            connection_id=str(conn_id),
        )
        query_contexts[conn_id] = execution
    
    @event.listens_for(sync_engine, "after_cursor_execute")
    def after_cursor_execute(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        """Record query completion."""
        conn_id = id(conn)
        execution = query_contexts.pop(conn_id, None)
        
        if execution:
            rows = cursor.rowcount if cursor.rowcount >= 0 else 0
            execution.complete(
                status=QueryStatus.SUCCESS,
                rows_affected=rows,
            )
            telemetry.record(execution)
    
    @event.listens_for(sync_engine, "handle_error")
    def handle_error(exception_context: Any) -> None:
        """Record query errors."""
        conn_id = id(exception_context.connection) if exception_context.connection else 0
        execution = query_contexts.pop(conn_id, None)
        
        if execution:
            error_msg = str(exception_context.original_exception)
            status = QueryStatus.ERROR
            
            # Detect specific error types
            if "deadlock" in error_msg.lower():
                status = QueryStatus.DEADLOCK
            elif "timeout" in error_msg.lower():
                status = QueryStatus.TIMEOUT
            
            execution.complete(
                status=status,
                error_message=error_msg[:500],
            )
            telemetry.record(execution)
    
    # Connection pool events
    if telemetry.config.track_connection_pool:
        event.listen(sync_engine, "checkout", telemetry.on_checkout)
        event.listen(sync_engine, "checkin", telemetry.on_checkin)
        event.listen(sync_engine, "connect", telemetry.on_connect)
        event.listen(sync_engine, "close", telemetry.on_close)


# ============================================================================
# SINGLETON & FACTORY
# ============================================================================


_db_telemetry: Optional[DatabaseTelemetry] = None


def get_db_telemetry() -> DatabaseTelemetry:
    """Get the global database telemetry instance."""
    global _db_telemetry
    if _db_telemetry is None:
        _db_telemetry = DatabaseTelemetry()
    return _db_telemetry


def set_db_telemetry(telemetry: DatabaseTelemetry) -> None:
    """Set the global database telemetry instance."""
    global _db_telemetry
    _db_telemetry = telemetry
