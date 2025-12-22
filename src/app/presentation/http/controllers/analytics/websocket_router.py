"""
Analytics WebSocket router.

Provides WebSocket endpoints for real-time analytics streaming.
"""

from fastapi import APIRouter, WebSocket, Query, Depends
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.websocket.analytics_handler import (
    AnalyticsWebSocketHandler,
)


def create_analytics_websocket_router() -> APIRouter:
    """
    Create WebSocket router for analytics.

    Returns:
        APIRouter with WebSocket endpoint
    """
    router = APIRouter(
        prefix="/analytics",
        tags=["analytics-websocket"],
    )

    @router.websocket("/ws/{user_id}")
    @inject
    async def analytics_websocket(
        websocket: WebSocket,
        user_id: str,
        token: str = Query(..., description="JWT authentication token"),
        handler: FromDishka[AnalyticsWebSocketHandler] = None,
    ):
        """
        WebSocket endpoint for real-time analytics streaming.

        Connect to receive real-time analytics updates, alerts, and metrics.

        Path Parameters:
        - user_id: User identifier

        Query Parameters:
        - token: JWT authentication token

        Client Messages:
        ```json
        // Subscribe to updates
        {
            "type": "subscribe",
            "subscriptions": ["metrics", "alerts", "performance", "costs", "quality"]
        }

        // Unsubscribe
        {
            "type": "unsubscribe",
            "subscriptions": ["metrics"]
        }

        // Request snapshot
        {
            "type": "request_snapshot",
            "start_date": "2025-01-01T00:00:00Z",  // optional
            "end_date": "2025-12-16T00:00:00Z"      // optional
        }

        // Heartbeat
        {
            "type": "ping"
        }
        ```

        Server Messages:
        ```json
        // Metrics update
        {
            "type": "metrics_update",
            "data": {
                "conversation_id": "uuid",
                "total_cost_usd": 5.23,
                "avg_response_time_ms": 1234.5,
                ...
            },
            "timestamp": "2025-12-16T12:00:00Z"
        }

        // Cost alert
        {
            "type": "cost_alert",
            "severity": "warning",
            "message": "Conversation cost exceeded threshold",
            "data": {...},
            "timestamp": "2025-12-16T12:00:00Z"
        }

        // Performance alert
        {
            "type": "performance_alert",
            "severity": "warning",
            "message": "P95 response time exceeded threshold",
            "data": {...},
            "timestamp": "2025-12-16T12:00:00Z"
        }

        // Quality alert
        {
            "type": "quality_alert",
            "severity": "info",
            "message": "Quality score below threshold",
            "data": {...},
            "timestamp": "2025-12-16T12:00:00Z"
        }

        // Snapshot response
        {
            "type": "snapshot",
            "data": {
                "aggregate": {...},
                "daily": [...],
                "agent_stats": {...},
                "cost_breakdown": {...}
            },
            "timestamp": "2025-12-16T12:00:00Z"
        }
        ```

        Subscription Types:
        - metrics: Real-time metrics updates
        - alerts: All alert types (cost, performance, quality)
        - performance: Performance-related alerts only
        - costs: Cost-related alerts only
        - quality: Quality-related alerts only
        """
        await handler.handle_connection(websocket, user_id, token)

    @router.get("/ws/stats")
    @inject
    async def get_analytics_websocket_stats(
        handler: FromDishka[AnalyticsWebSocketHandler] = None,
    ):
        """
        Get analytics WebSocket connection statistics.

        Returns:
            Connection and subscription statistics
        """
        return handler.get_statistics()

    return router
