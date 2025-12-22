"""
WebSocket Session Management IOC Provider.

Provides Redis-based WebSocket session store with connection pooling.
"""

import os
from dishka import Provider, Scope, provide
from redis.asyncio import Redis, ConnectionPool

from app.domain.ports.session_store import SessionStore
from app.infrastructure.adapters.chat.redis_session_store_adapter import (
    RedisSessionStoreAdapter,
)


class WebSocketSessionProvider(Provider):
    """Provider for WebSocket session management dependencies."""

    scope = Scope.APP

    @provide(scope=Scope.APP)
    async def provide_redis_session_client(self) -> Redis:
        """
        Provide Redis async client for WebSocket sessions.

        Uses connection pooling for optimal performance.
        Separate from other Redis clients to avoid resource contention.

        Returns:
            Redis async client with connection pool
        """
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")

        # Create connection pool for session management
        pool = ConnectionPool.from_url(
            redis_url,
            max_connections=20,  # Pool size for WebSocket session operations
            decode_responses=False,  # We handle encoding/decoding manually
        )

        return Redis(connection_pool=pool)

    @provide(scope=Scope.APP)
    def provide_websocket_session_store(
        self,
        redis_session_client: Redis,
    ) -> SessionStore:
        """
        Provide WebSocket session store adapter.

        Args:
            redis_session_client: Redis client with connection pool

        Returns:
            SessionStore implementation using Redis
        """
        return RedisSessionStoreAdapter(
            redis_client=redis_session_client,
            key_prefix="ws",
            pool_size=20,
        )
