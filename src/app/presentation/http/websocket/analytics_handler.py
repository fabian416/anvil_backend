"""Analytics WebSocket Handler.

Real-time analytics and metrics streaming for dashboards.

Features:
    - Real-time metrics updates
    - Performance alerts
    - Cost threshold notifications
    - Dashboard data streaming
    - Aggregate analytics broadcasting

Message Types:
    Client → Server:
        - subscribe: Subscribe to analytics updates
        - unsubscribe: Unsubscribe from updates
        - request_snapshot: Request current analytics snapshot
        - ping: Heartbeat

    Server → Client:
        - metrics_update: Real-time metrics update
        - performance_alert: Performance threshold breach
        - cost_alert: Cost threshold breach
        - snapshot: Full analytics snapshot
        - error: Error message
        - pong: Heartbeat response
"""

from typing import Optional, Dict, Any, Set
from uuid import UUID
import logging
import json
from datetime import datetime, timedelta, UTC

from fastapi import WebSocket, WebSocketDisconnect, status
from dishka.integrations.fastapi import FromDishka

from app.presentation.http.websocket.connection_manager import ConnectionManager
from app.domain.ports.analytics_repository import AnalyticsRepository
from app.domain.entities.chat.conversation_analytics import ConversationAnalytics
from app.presentation.http.auth.access_token_processor_jwt import (
    JwtAccessTokenProcessor,
)


logger = logging.getLogger(__name__)


class AnalyticsWebSocketHandler:
    """
    WebSocket handler for real-time analytics streaming.

    Manages connections, subscriptions, and broadcasts analytics updates
    to connected clients. Supports real-time metrics, alerts, and snapshots.

    Usage:
        handler = AnalyticsWebSocketHandler(analytics_repo, jwt_processor)
        await handler.handle_connection(websocket, user_id, token)
    """

    def __init__(
        self,
        analytics_repository: AnalyticsRepository,
        jwt_processor: JwtAccessTokenProcessor,
        connection_manager: Optional[ConnectionManager] = None,
    ):
        """
        Initialize analytics WebSocket handler.

        Args:
            analytics_repository: Repository for analytics data
            jwt_processor: JWT token processor for authentication
            connection_manager: Optional connection manager (creates new if not provided)
        """
        self.analytics_repo = analytics_repository
        self.jwt_processor = jwt_processor
        self.connection_manager = connection_manager or ConnectionManager()

        # Track subscriptions: {user_id: set of subscription types}
        self.subscriptions: Dict[str, Set[str]] = {}

        # Alert thresholds
        self.cost_threshold_usd = 10.0  # Alert when conversation cost exceeds $10
        self.response_time_threshold_ms = 5000.0  # Alert when response > 5s
        self.quality_threshold = 0.5  # Alert when quality score < 0.5

    async def authenticate_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user from JWT token.

        Args:
            token: JWT token from query parameter

        Returns:
            User info dict or None if invalid
        """
        try:
            auth_session_id = self.jwt_processor.decode_auth_session_id(token)
            if not auth_session_id:
                logger.warning("Invalid or expired token")
                return None

            # For WebSocket, we'll use session_id as user_id
            # In production, fetch full user details from session
            return {
                "user_id": auth_session_id,
                "session_id": auth_session_id,
            }

        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            return None

    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        token: str,
    ) -> None:
        """
        Handle WebSocket connection lifecycle.

        Args:
            websocket: WebSocket connection
            user_id: User identifier from path parameter
            token: JWT token from query parameter
        """
        # Authenticate user
        user = await self.authenticate_user(token)
        if not user or user["user_id"] != user_id:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid authentication token",
            )
            return

        # Connect to manager
        session_id = f"analytics_{user_id}"
        await self.connection_manager.connect(
            websocket,
            user_id=user_id,
            session_id=session_id,
            metadata={
                "type": "analytics",
                "connected_at": datetime.now(UTC).isoformat(),
            },
        )

        # Initialize subscriptions for user
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = set()

        # Send welcome message with connection info
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to analytics stream",
            "user_id": user_id,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        try:
            # Message loop
            while True:
                # Receive message from client
                data = await websocket.receive_json()

                message_type = data.get("type")

                # Handle ping
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                # Handle subscribe
                if message_type == "subscribe":
                    await self._handle_subscribe(websocket, user_id, data)
                    continue

                # Handle unsubscribe
                if message_type == "unsubscribe":
                    await self._handle_unsubscribe(websocket, user_id, data)
                    continue

                # Handle snapshot request
                if message_type == "request_snapshot":
                    await self._handle_snapshot_request(websocket, user_id, data)
                    continue

                # Unknown message type
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}",
                    "code": "unknown_type",
                })

        except WebSocketDisconnect:
            logger.info(f"Analytics WebSocket disconnected: user={user_id}")

        except Exception as e:
            logger.error(f"Analytics WebSocket error: {e}", exc_info=True)
            try:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "code": "internal_error",
                })
            except Exception:
                pass  # Connection already closed

        finally:
            # Clean up subscriptions
            if user_id in self.subscriptions:
                del self.subscriptions[user_id]

            # Disconnect from manager
            await self.connection_manager.disconnect(websocket, user_id, session_id)

    async def _handle_subscribe(
        self,
        websocket: WebSocket,
        user_id: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Handle subscription request.

        Args:
            websocket: WebSocket connection
            user_id: User identifier
            data: Message data with subscription types
        """
        subscription_types = data.get("subscriptions", [])

        # Validate subscription types
        valid_types = {"metrics", "alerts", "performance", "costs", "quality"}
        invalid_types = set(subscription_types) - valid_types

        if invalid_types:
            await websocket.send_json({
                "type": "error",
                "error": f"Invalid subscription types: {invalid_types}",
                "code": "invalid_subscription",
            })
            return

        # Add subscriptions
        self.subscriptions[user_id].update(subscription_types)

        await websocket.send_json({
            "type": "subscribed",
            "subscriptions": list(self.subscriptions[user_id]),
            "message": "Successfully subscribed to analytics updates",
        })

        logger.info(f"User {user_id} subscribed to: {subscription_types}")

    async def _handle_unsubscribe(
        self,
        websocket: WebSocket,
        user_id: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Handle unsubscribe request.

        Args:
            websocket: WebSocket connection
            user_id: User identifier
            data: Message data with subscription types
        """
        subscription_types = data.get("subscriptions", [])

        # Remove subscriptions
        if user_id in self.subscriptions:
            self.subscriptions[user_id] -= set(subscription_types)

        await websocket.send_json({
            "type": "unsubscribed",
            "subscriptions": list(self.subscriptions.get(user_id, [])),
            "message": "Successfully unsubscribed from analytics updates",
        })

        logger.info(f"User {user_id} unsubscribed from: {subscription_types}")

    async def _handle_snapshot_request(
        self,
        websocket: WebSocket,
        user_id: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Handle analytics snapshot request.

        Args:
            websocket: WebSocket connection
            user_id: User identifier
            data: Message data with optional date range
        """
        try:
            # Parse date range if provided
            start_date = data.get("start_date")
            end_date = data.get("end_date")

            if start_date:
                start_date = datetime.fromisoformat(start_date)
            else:
                # Default to last 30 days
                start_date = datetime.now(UTC) - timedelta(days=30)

            if end_date:
                end_date = datetime.fromisoformat(end_date)
            else:
                end_date = datetime.now(UTC)

            # Get aggregate analytics
            user_uuid = UUID(user_id)
            aggregate = await self.analytics_repo.get_aggregate_by_user(
                user_id=user_uuid,
                start_date=start_date,
                end_date=end_date,
            )

            # Get daily analytics
            daily_analytics = await self.analytics_repo.get_daily_analytics(
                user_id=user_uuid,
                start_date=start_date,
                end_date=end_date,
            )

            # Get agent usage stats
            agent_stats = await self.analytics_repo.get_agent_usage_stats(
                user_id=user_uuid,
                start_date=start_date,
                end_date=end_date,
            )

            # Get cost breakdown
            cost_breakdown = await self.analytics_repo.get_cost_breakdown_by_agent(
                user_id=user_uuid,
                start_date=start_date,
                end_date=end_date,
            )

            # Send snapshot
            await websocket.send_json({
                "type": "snapshot",
                "data": {
                    "aggregate": aggregate,
                    "daily": daily_analytics,
                    "agent_stats": agent_stats,
                    "cost_breakdown": cost_breakdown,
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                    },
                },
                "timestamp": datetime.now(UTC).isoformat(),
            })

            logger.info(f"Sent analytics snapshot to user {user_id}")

        except ValueError as e:
            await websocket.send_json({
                "type": "error",
                "error": f"Invalid date format: {str(e)}",
                "code": "invalid_date",
            })

        except Exception as e:
            logger.error(f"Error generating snapshot: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "error": "Failed to generate analytics snapshot",
                "code": "snapshot_error",
            })

    async def broadcast_metrics_update(
        self,
        analytics: ConversationAnalytics,
    ) -> None:
        """
        Broadcast metrics update to subscribed users.

        Args:
            analytics: Updated analytics entity
        """
        user_id = str(analytics.user_id)

        # Check if user has active subscriptions
        if user_id not in self.subscriptions:
            return

        subscriptions = self.subscriptions[user_id]

        # Check for metrics subscription
        if "metrics" in subscriptions:
            await self.connection_manager.send_to_user(
                user_id=user_id,
                message={
                    "type": "metrics_update",
                    "data": analytics.to_dict(),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )

        # Check for alerts and send if thresholds breached
        await self._check_and_send_alerts(user_id, analytics, subscriptions)

    async def _check_and_send_alerts(
        self,
        user_id: str,
        analytics: ConversationAnalytics,
        subscriptions: Set[str],
    ) -> None:
        """
        Check analytics for threshold breaches and send alerts.

        Args:
            user_id: User identifier
            analytics: Analytics entity to check
            subscriptions: User's active subscriptions
        """
        # Cost alert
        if (
            "alerts" in subscriptions or "costs" in subscriptions
        ) and analytics.total_cost_usd > self.cost_threshold_usd:
            await self.connection_manager.send_to_user(
                user_id=user_id,
                message={
                    "type": "cost_alert",
                    "severity": "warning",
                    "message": (
                        f"Conversation cost (${analytics.total_cost_usd:.2f}) "
                        f"exceeded threshold (${self.cost_threshold_usd:.2f})"
                    ),
                    "data": {
                        "conversation_id": str(analytics.conversation_id),
                        "total_cost": analytics.total_cost_usd,
                        "threshold": self.cost_threshold_usd,
                        "cost_by_agent": analytics.cost_by_agent,
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )

        # Performance alert (high response time)
        if (
            ("alerts" in subscriptions or "performance" in subscriptions)
            and analytics.p95_response_time_ms
            and analytics.p95_response_time_ms > self.response_time_threshold_ms
        ):
            await self.connection_manager.send_to_user(
                user_id=user_id,
                message={
                    "type": "performance_alert",
                    "severity": "warning",
                    "message": (
                        f"P95 response time ({analytics.p95_response_time_ms:.0f}ms) "
                        f"exceeded threshold ({self.response_time_threshold_ms:.0f}ms)"
                    ),
                    "data": {
                        "conversation_id": str(analytics.conversation_id),
                        "p95_response_time_ms": analytics.p95_response_time_ms,
                        "avg_response_time_ms": analytics.avg_response_time_ms,
                        "threshold": self.response_time_threshold_ms,
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )

        # Quality alert
        if (
            ("alerts" in subscriptions or "quality" in subscriptions)
            and analytics.quality_score
            and analytics.quality_score < self.quality_threshold
        ):
            await self.connection_manager.send_to_user(
                user_id=user_id,
                message={
                    "type": "quality_alert",
                    "severity": "info",
                    "message": (
                        f"Quality score ({analytics.quality_score:.2f}) "
                        f"below threshold ({self.quality_threshold:.2f})"
                    ),
                    "data": {
                        "conversation_id": str(analytics.conversation_id),
                        "quality_score": analytics.quality_score,
                        "sentiment_score": analytics.sentiment_score,
                        "satisfaction_score": analytics.user_satisfaction_score,
                        "threshold": self.quality_threshold,
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )

    async def broadcast_to_all(
        self,
        message: Dict[str, Any],
        subscription_filter: Optional[str] = None,
    ) -> None:
        """
        Broadcast message to all connected analytics clients.

        Args:
            message: Message to broadcast
            subscription_filter: Optional subscription type filter
        """
        for user_id, subscriptions in self.subscriptions.items():
            # Filter by subscription if specified
            if subscription_filter and subscription_filter not in subscriptions:
                continue

            await self.connection_manager.send_to_user(
                user_id=user_id,
                message=message,
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get handler statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "active_connections": self.connection_manager.get_active_count(),
            "total_subscriptions": sum(
                len(subs) for subs in self.subscriptions.values()
            ),
            "users_with_subscriptions": len(self.subscriptions),
            "connection_manager_stats": self.connection_manager.get_statistics(),
        }
