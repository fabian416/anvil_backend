"""
Offline queue adapter implementation using Redis.

Redis-based implementation of OfflineQueueAdapter for high-performance
message queuing with priority support and retry management.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
import json

from redis.asyncio import Redis

from app.domain.ports.offline_queue_adapter import OfflineQueueAdapter
from app.domain.value_objects.chat.performance import OfflineQueueEntry


class RedisOfflineQueueAdapter(OfflineQueueAdapter):
    """
    Redis adapter for offline message queuing.

    Uses Redis sorted sets for priority-based ordering and retry management.
    Stores message data in Redis hashes for efficient access.

    Architecture:
    - Sorted Set (user:{user_id}:offline_queue): Queue with priority scores
    - Hash (offline_entry:{entry_id}): Entry data storage
    - Sorted Set (user:{user_id}:failed_queue): Failed entries tracking
    """

    def __init__(self, redis_client: Redis, key_prefix: str = "chat:offline") -> None:
        """
        Initialize Redis offline queue adapter.

        Args:
            redis_client: Async Redis client instance
            key_prefix: Redis key prefix for namespacing
        """
        self._redis = redis_client
        self._prefix = key_prefix

    def _queue_key(self, user_id: UUID) -> str:
        """Get Redis key for user's queue."""
        return f"{self._prefix}:queue:{user_id}"

    def _failed_key(self, user_id: UUID) -> str:
        """Get Redis key for user's failed entries."""
        return f"{self._prefix}:failed:{user_id}"

    def _entry_key(self, entry_id: UUID) -> str:
        """Get Redis key for entry data."""
        return f"{self._prefix}:entry:{entry_id}"

    def _calculate_score(self, entry: OfflineQueueEntry) -> float:
        """
        Calculate score for sorted set ordering.

        Score = priority (higher = better) + timestamp (older = better)
        Uses negative timestamp so older entries come first within same priority.
        """
        # Priority ranges from 0-10 (higher = more important)
        # Timestamp component ensures FIFO within same priority
        priority_score = entry.priority * 1_000_000
        timestamp_score = -entry.created_at.timestamp()
        return priority_score + timestamp_score

    async def enqueue(self, entry: OfflineQueueEntry) -> bool:
        """
        Add message to offline queue.

        Args:
            entry: Queue entry to add

        Returns:
            True if enqueued successfully
        """
        try:
            # Serialize entry to JSON
            entry_data = {
                "id": str(entry.id),
                "user_id": str(entry.user_id),
                "conversation_id": str(entry.conversation_id),
                "message": entry.message,
                "agent_name": entry.agent_name,
                "created_at": entry.created_at.isoformat(),
                "retry_count": entry.retry_count,
                "max_retries": entry.max_retries,
                "priority": entry.priority,
                "metadata": json.dumps(entry.metadata),
            }

            # Store entry data in hash
            entry_key = self._entry_key(entry.id)
            await self._redis.hset(entry_key, mapping=entry_data)  # type: ignore

            # Set expiration (7 days for pending entries)
            await self._redis.expire(entry_key, 7 * 24 * 3600)

            # Add to sorted set with priority-based score
            queue_key = self._queue_key(entry.user_id)
            score = self._calculate_score(entry)
            await self._redis.zadd(queue_key, {str(entry.id): score})

            return True

        except Exception:
            return False

    async def dequeue(self, user_id: UUID, limit: int = 10) -> List[OfflineQueueEntry]:
        """
        Get messages from queue for user.

        Args:
            user_id: User identifier
            limit: Maximum number of entries to retrieve

        Returns:
            List of queued entries (ordered by priority, then creation time)
        """
        try:
            queue_key = self._queue_key(user_id)

            # Get top entries from sorted set (highest scores first)
            entry_ids = await self._redis.zrevrange(queue_key, 0, limit - 1)

            if not entry_ids:
                return []

            # Fetch entry data
            entries: List[OfflineQueueEntry] = []
            for entry_id_bytes in entry_ids:
                entry_id = entry_id_bytes.decode()
                entry_key = self._entry_key(UUID(entry_id))

                # Get entry data from hash
                entry_data = await self._redis.hgetall(entry_key)
                if not entry_data:
                    # Entry expired or deleted, remove from queue
                    await self._redis.zrem(queue_key, entry_id)
                    continue

                # Deserialize entry
                entry = OfflineQueueEntry(
                    id=UUID(entry_data[b"id"].decode()),
                    user_id=UUID(entry_data[b"user_id"].decode()),
                    conversation_id=UUID(entry_data[b"conversation_id"].decode()),
                    message=entry_data[b"message"].decode(),
                    agent_name=(
                        entry_data[b"agent_name"].decode()
                        if entry_data.get(b"agent_name")
                        else None
                    ),
                    created_at=datetime.fromisoformat(
                        entry_data[b"created_at"].decode()
                    ),
                    retry_count=int(entry_data[b"retry_count"]),
                    max_retries=int(entry_data[b"max_retries"]),
                    priority=int(entry_data[b"priority"]),
                    metadata=json.loads(entry_data[b"metadata"].decode()),
                )
                entries.append(entry)

            return entries

        except Exception:
            return []

    async def remove(self, entry_id: UUID) -> bool:
        """
        Remove entry from queue.

        Args:
            entry_id: Entry identifier

        Returns:
            True if removed, False if not found
        """
        try:
            entry_key = self._entry_key(entry_id)

            # Get user_id from entry data
            entry_data = await self._redis.hgetall(entry_key)
            if not entry_data:
                return False

            user_id = UUID(entry_data[b"user_id"].decode())

            # Remove from queue
            queue_key = self._queue_key(user_id)
            removed_from_queue = await self._redis.zrem(queue_key, str(entry_id))

            # Remove from failed queue if present
            failed_key = self._failed_key(user_id)
            await self._redis.zrem(failed_key, str(entry_id))

            # Delete entry data
            await self._redis.delete(entry_key)

            return removed_from_queue > 0

        except Exception:
            return False

    async def get_queue_size(self, user_id: UUID) -> int:
        """
        Get number of pending messages for user.

        Args:
            user_id: User identifier

        Returns:
            Number of queued messages
        """
        try:
            queue_key = self._queue_key(user_id)
            size = await self._redis.zcard(queue_key)
            return size or 0

        except Exception:
            return 0

    async def clear_user_queue(self, user_id: UUID) -> int:
        """
        Clear all queued messages for user.

        Args:
            user_id: User identifier

        Returns:
            Number of entries cleared
        """
        try:
            queue_key = self._queue_key(user_id)
            failed_key = self._failed_key(user_id)

            # Get all entry IDs
            entry_ids = await self._redis.zrange(queue_key, 0, -1)
            failed_ids = await self._redis.zrange(failed_key, 0, -1)

            all_ids = list(set(entry_ids + failed_ids))

            # Delete all entry data
            if all_ids:
                entry_keys = [
                    self._entry_key(UUID(entry_id.decode())) for entry_id in all_ids
                ]
                await self._redis.delete(*entry_keys)

            # Delete queues
            await self._redis.delete(queue_key, failed_key)

            return len(all_ids)

        except Exception:
            return 0

    async def update_retry_count(
        self, entry_id: UUID
    ) -> Optional[OfflineQueueEntry]:
        """
        Increment retry count for entry.

        Args:
            entry_id: Entry identifier

        Returns:
            Updated entry or None if not found
        """
        try:
            entry_key = self._entry_key(entry_id)

            # Get entry data
            entry_data = await self._redis.hgetall(entry_key)
            if not entry_data:
                return None

            # Increment retry count
            retry_count = int(entry_data[b"retry_count"]) + 1
            max_retries = int(entry_data[b"max_retries"])

            # Update retry count
            await self._redis.hset(entry_key, "retry_count", retry_count)

            # If exceeded max retries, move to failed queue
            if retry_count >= max_retries:
                user_id = UUID(entry_data[b"user_id"].decode())
                queue_key = self._queue_key(user_id)
                failed_key = self._failed_key(user_id)

                # Move from active queue to failed queue
                score = await self._redis.zscore(queue_key, str(entry_id))
                if score is not None:
                    await self._redis.zrem(queue_key, str(entry_id))
                    await self._redis.zadd(failed_key, {str(entry_id): score})

            # Return updated entry
            entry = OfflineQueueEntry(
                id=UUID(entry_data[b"id"].decode()),
                user_id=UUID(entry_data[b"user_id"].decode()),
                conversation_id=UUID(entry_data[b"conversation_id"].decode()),
                message=entry_data[b"message"].decode(),
                agent_name=(
                    entry_data[b"agent_name"].decode()
                    if entry_data.get(b"agent_name")
                    else None
                ),
                created_at=datetime.fromisoformat(entry_data[b"created_at"].decode()),
                retry_count=retry_count,
                max_retries=max_retries,
                priority=int(entry_data[b"priority"]),
                metadata=json.loads(entry_data[b"metadata"].decode()),
            )

            return entry

        except Exception:
            return None

    async def get_failed_entries(self, user_id: UUID) -> List[OfflineQueueEntry]:
        """
        Get entries that have exceeded max retries.

        Args:
            user_id: User identifier

        Returns:
            List of failed entries
        """
        try:
            failed_key = self._failed_key(user_id)

            # Get failed entry IDs
            entry_ids = await self._redis.zrevrange(failed_key, 0, -1)

            if not entry_ids:
                return []

            # Fetch entry data
            entries: List[OfflineQueueEntry] = []
            for entry_id_bytes in entry_ids:
                entry_id = entry_id_bytes.decode()
                entry_key = self._entry_key(UUID(entry_id))

                entry_data = await self._redis.hgetall(entry_key)
                if not entry_data:
                    # Entry expired, remove from failed queue
                    await self._redis.zrem(failed_key, entry_id)
                    continue

                entry = OfflineQueueEntry(
                    id=UUID(entry_data[b"id"].decode()),
                    user_id=UUID(entry_data[b"user_id"].decode()),
                    conversation_id=UUID(entry_data[b"conversation_id"].decode()),
                    message=entry_data[b"message"].decode(),
                    agent_name=(
                        entry_data[b"agent_name"].decode()
                        if entry_data.get(b"agent_name")
                        else None
                    ),
                    created_at=datetime.fromisoformat(
                        entry_data[b"created_at"].decode()
                    ),
                    retry_count=int(entry_data[b"retry_count"]),
                    max_retries=int(entry_data[b"max_retries"]),
                    priority=int(entry_data[b"priority"]),
                    metadata=json.loads(entry_data[b"metadata"].decode()),
                )
                entries.append(entry)

            return entries

        except Exception:
            return []
