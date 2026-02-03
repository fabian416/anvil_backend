"""
Batch processor for database operations.
"""

import asyncio
import logging
from typing import List, Callable, Any, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class BatchItem(Generic[T]):
    """Item in batch queue."""

    data: T
    timestamp: datetime
    future: asyncio.Future


class BatchProcessor(Generic[T]):
    """
    Batch processor for database operations.

    Collects operations and executes them in batches to reduce
    database load and improve performance.
    """

    def __init__(
        self,
        batch_size: int = 100,
        max_wait_time: float = 1.0,
        processor_func: Callable[[List[T]], Any] = None,
    ):
        """
        Initialize batch processor.

        Args:
            batch_size: Maximum items per batch
            max_wait_time: Max wait time before processing
            processor_func: Function to process batch
        """
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.processor_func = processor_func

        self._queue: List[BatchItem[T]] = []
        self._lock = asyncio.Lock()
        self._processing = False
        self._task: Optional[asyncio.Task] = None

    async def add(self, item: T) -> Any:
        """
        Add item to batch queue.

        Args:
            item: Item to process

        Returns:
            Result from batch processing
        """
        async with self._lock:
            # Create batch item with future
            future = asyncio.Future()
            batch_item = BatchItem(
                data=item,
                timestamp=datetime.now(UTC),
                future=future,
            )

            self._queue.append(batch_item)

            # Start processing if batch is full
            if len(self._queue) >= self.batch_size:
                if not self._processing:
                    self._task = asyncio.create_task(self._process_batch())

            # Start timer for partial batch
            elif not self._processing and not self._task:
                self._task = asyncio.create_task(self._process_after_delay())

        # Wait for result
        return await future

    async def _process_batch(self) -> None:
        """Process current batch."""
        async with self._lock:
            if not self._queue or self._processing:
                return

            self._processing = True

            # Get batch
            batch = self._queue[: self.batch_size]
            self._queue = self._queue[self.batch_size :]

            logger.info(f"Processing batch of {len(batch)} items")

        try:
            # Extract data
            items = [b.data for b in batch]

            # Process batch
            if self.processor_func:
                result = await self.processor_func(items)
            else:
                result = items

            # Set results
            for item in batch:
                if not item.future.done():
                    item.future.set_result(result)

        except Exception as e:
            logger.error(f"Batch processing error: {e}")

            # Set exception for all items
            for item in batch:
                if not item.future.done():
                    item.future.set_exception(e)

        finally:
            async with self._lock:
                self._processing = False
                self._task = None

                # Process remaining if any
                if self._queue:
                    self._task = asyncio.create_task(self._process_batch())

    async def _process_after_delay(self) -> None:
        """Process batch after delay."""
        await asyncio.sleep(self.max_wait_time)
        await self._process_batch()

    async def flush(self) -> None:
        """Force process all pending items."""
        while self._queue:
            await self._process_batch()
            await asyncio.sleep(0.1)


# Example usage for database writes
class MessageBatchProcessor(BatchProcessor):
    """Batch processor for message writes."""

    def __init__(self, repository):
        """
        Initialize message batch processor.

        Args:
            repository: Message repository
        """

        async def process_messages(messages: List[Any]) -> None:
            """Process batch of messages."""
            # Batch insert to database
            for message in messages:
                await repository.save(message)

        super().__init__(
            batch_size=50,
            max_wait_time=0.5,
            processor_func=process_messages,
        )
