"""
Dependency injection configuration for notification services.

Provides notification adapter with Redis-based multi-channel delivery.
"""

from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from app.domain.ports.notification_adapter import NotificationAdapter
from app.infrastructure.adapters.chat.notification_adapter import RedisNotificationAdapter


class NotificationProvider(Provider):
    """
    Dishka provider for notification services.

    Scope: REQUEST - New instance per request for proper async handling
    """

    scope = Scope.REQUEST

    @provide
    async def notification_adapter(self, redis: Redis) -> NotificationAdapter:
        """
        Provide notification adapter with Redis client.

        Args:
            redis: Redis async client from infrastructure provider

        Returns:
            NotificationAdapter implementation
        """
        return RedisNotificationAdapter(
            redis_client=redis,
            key_prefix="notifications:",
            queue_key="notifications:queue",
            history_ttl_days=30,
        )
