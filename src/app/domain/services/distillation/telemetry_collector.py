"""
Distillation telemetry collector.

Collects and records metrics for all distillation operations.
"""
import asyncio
import hashlib
import logging
from datetime import datetime, UTC
from typing import List, Optional
from uuid import UUID

from app.domain.entities.distillation import DistillationRequest, DistillationResult
from app.setup.config.distillation import DistillationTelemetrySettings

logger = logging.getLogger(__name__)


class DistillationTelemetryRecord:
    """
    Single telemetry record.
    
    Represents one distillation validation operation.
    """
    
    def __init__(
        self,
        user_id: UUID,
        conversation_id: UUID,
        request_hash: str,
        detected_language: str,
        provider: str,
        model: str,
        success: bool,
        reason: str,
        confidence: float,
        latency_ms: float,
        tokens_used: int,
        cost_usd: float,
        fallback_used: bool = False,
        error: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Initialize telemetry record."""
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.request_hash = request_hash
        self.detected_language = detected_language
        self.provider = provider
        self.model = model
        self.success = success
        self.reason = reason
        self.confidence = confidence
        self.latency_ms = latency_ms
        self.tokens_used = tokens_used
        self.cost_usd = cost_usd
        self.fallback_used = fallback_used
        self.error = error
        self.timestamp = timestamp or datetime.now(UTC)


class DistillationTelemetryCollector:
    """
    Collects and batches telemetry for distillation operations.
    
    Provides async recording with configurable batching.
    """
    
    def __init__(
        self,
        settings: DistillationTelemetrySettings,
        repository: "DistillationTelemetryRepository",  # Forward reference
    ):
        """
        Initialize telemetry collector.
        
        Args:
            settings: Telemetry settings
            repository: Repository for persisting telemetry
        """
        self.settings = settings
        self.repository = repository
        self.enabled = settings.enabled
        
        # Batching state
        self._batch: List[DistillationTelemetryRecord] = []
        self._batch_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        
        # Start background flush if async recording enabled
        if self.enabled and settings.async_recording:
            self._start_flush_loop()
        
        logger.info(
            f"Telemetry collector initialized: "
            f"enabled={self.enabled}, "
            f"async={settings.async_recording}, "
            f"batch_size={settings.batch_size}"
        )
    
    async def record(
        self,
        request: DistillationRequest,
        result: DistillationResult,
    ) -> None:
        """
        Record a distillation operation.
        
        Args:
            request: The original request
            result: The validation result
        """
        if not self.enabled:
            return
        
        # Create telemetry record
        record = self._create_record(request, result)
        
        # Record synchronously or batch
        if self.settings.async_recording:
            await self._add_to_batch(record)
        else:
            await self._record_immediately(record)
    
    def _create_record(
        self,
        request: DistillationRequest,
        result: DistillationResult,
    ) -> DistillationTelemetryRecord:
        """
        Create telemetry record from request and result.
        
        Args:
            request: The distillation request
            result: The distillation result
        
        Returns:
            Telemetry record
        """
        # Hash user message for privacy
        request_hash = hashlib.sha256(
            request.user_message.encode('utf-8')
        ).hexdigest()
        
        return DistillationTelemetryRecord(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            request_hash=request_hash,
            detected_language=result.detected_language,
            provider=result.provider,
            model=result.model,
            success=result.success,
            reason=result.reason,
            confidence=result.confidence,
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_used,
            cost_usd=result.cost_usd,
            fallback_used=result.fallback_used,
            error=result.error,
            timestamp=result.timestamp,
        )
    
    async def _add_to_batch(self, record: DistillationTelemetryRecord) -> None:
        """
        Add record to batch.
        
        Args:
            record: Telemetry record to add
        """
        async with self._batch_lock:
            self._batch.append(record)
            
            # Flush if batch is full
            if len(self._batch) >= self.settings.batch_size:
                await self._flush_batch()
    
    async def _record_immediately(self, record: DistillationTelemetryRecord) -> None:
        """
        Record telemetry immediately (synchronous mode).
        
        Args:
            record: Telemetry record
        """
        try:
            await self.repository.save(record)
            logger.debug("Telemetry recorded immediately")
        except Exception as e:
            logger.error(f"Failed to record telemetry: {e}")
    
    async def _flush_batch(self) -> None:
        """Flush current batch to repository."""
        if not self._batch:
            return
        
        batch = self._batch.copy()
        self._batch.clear()
        
        try:
            await self.repository.save_batch(batch)
            logger.debug(f"Flushed {len(batch)} telemetry records")
        except Exception as e:
            logger.error(f"Failed to flush telemetry batch: {e}")
    
    def _start_flush_loop(self) -> None:
        """Start background flush loop."""
        async def flush_loop():
            while True:
                try:
                    await asyncio.sleep(self.settings.flush_interval_seconds)
                    async with self._batch_lock:
                        await self._flush_batch()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in flush loop: {e}")
        
        self._flush_task = asyncio.create_task(flush_loop())
        logger.info(
            f"Started telemetry flush loop: "
            f"interval={self.settings.flush_interval_seconds}s"
        )
    
    async def flush(self) -> None:
        """Force flush of pending records."""
        async with self._batch_lock:
            await self._flush_batch()
    
    async def close(self) -> None:
        """Close collector and flush pending records."""
        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self.flush()
        
        logger.info("Telemetry collector closed")
