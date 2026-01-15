"""WebSocket event broadcaster for real-time updates.

This module handles broadcasting of various event types to WebSocket
subscribers, including protocol updates, risk alerts, and graph changes.
"""

import json
import logging
from datetime import datetime, UTC
from typing import Any, Dict, Optional
from uuid import UUID

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class GraphEventBroadcaster:
    """
    Broadcast graph-related events to WebSocket subscribers.

    Uses Redis Pub/Sub for scalable real-time event distribution.
    Events are published to channels that WebSocket handlers subscribe to.
    """

    def __init__(self, redis_client: aioredis.Redis):
        """
        Initialize broadcaster with Redis client.

        Args:
            redis_client: Redis client for pub/sub
        """
        self._redis = redis_client

    async def broadcast_protocol_update(
        self,
        protocol_id: UUID,
        protocol_name: str,
        changes: Dict[str, Any],
        change_type: str = "update",
    ) -> None:
        """
        Broadcast protocol update event.

        Args:
            protocol_id: Protocol UUID
            protocol_name: Protocol name
            changes: Dictionary of what changed
            change_type: Type of change (update/audit/incident)

        Example changes:
            {
                "tvl": {"old": 1000000, "new": 1200000},
                "risk_score": {"old": 3.2, "new": 2.8},
                "audit_added": "Trail of Bits"
            }
        """
        event = {
            "type": "protocol:update",
            "protocol_id": str(protocol_id),
            "protocol_name": protocol_name,
            "change_type": change_type,
            "changes": changes,
            "timestamp": datetime.now(UTC).timestamp(),
        }

        await self._publish("graph:updates", event)
        logger.info(
            f"Broadcasted protocol update: {protocol_name} ({change_type})",
            extra={"protocol_id": str(protocol_id), "changes": changes},
        )

    async def broadcast_risk_alert(
        self,
        protocol_id: UUID,
        protocol_name: str,
        severity: str,
        message: str,
        risk_score: float,
        risk_change: Optional[float] = None,
        affected_users: Optional[list] = None,
    ) -> None:
        """
        Broadcast risk alert event.

        Args:
            protocol_id: Protocol UUID
            protocol_name: Protocol name
            severity: LOW/MEDIUM/HIGH/CRITICAL
            message: Alert message
            risk_score: Current risk score
            risk_change: Change in risk score (optional)
            affected_users: List of affected user IDs (optional)

        Publishes to both general channel and user-specific channels.
        """
        event = {
            "type": "risk:alert",
            "protocol_id": str(protocol_id),
            "protocol_name": protocol_name,
            "severity": severity,
            "message": message,
            "risk_score": risk_score,
            "risk_change": risk_change,
            "timestamp": datetime.now(UTC).timestamp(),
        }

        # Broadcast to general channel
        await self._publish("graph:risk_alerts", event)

        # Broadcast to specific users if provided
        if affected_users:
            for user_id in affected_users:
                user_channel = f"user:{user_id}:alerts"
                await self._publish(user_channel, event)

        logger.warning(
            f"Broadcasted risk alert: {protocol_name} - {severity}",
            extra={
                "protocol_id": str(protocol_id),
                "severity": severity,
                "affected_users": len(affected_users) if affected_users else 0,
            },
        )

    async def broadcast_graph_change(
        self,
        change_type: str,
        entity_type: str,
        entity_id: UUID,
        entity_name: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Broadcast graph structural change event.

        Args:
            change_type: node_added/node_removed/edge_added/edge_removed
            entity_type: Protocol/Token/Chain/etc.
            entity_id: Entity UUID
            entity_name: Entity name
            details: Additional details about the change

        Example:
            change_type: "edge_added"
            entity_type: "Protocol"
            details: {
                "relationship": "DEPENDS_ON",
                "target": "Chainlink",
                "target_id": "uuid..."
            }
        """
        event = {
            "type": "graph:change",
            "change_type": change_type,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "entity_name": entity_name,
            "details": details or {},
            "timestamp": datetime.now(UTC).timestamp(),
        }

        await self._publish("graph:changes", event)
        logger.info(
            f"Broadcasted graph change: {change_type} - {entity_type} {entity_name}",
            extra={"entity_id": str(entity_id), "change_type": change_type},
        )

    async def broadcast_price_update(
        self,
        token_symbol: str,
        price_usd: float,
        price_change_24h: float,
        volume_24h: Optional[float] = None,
    ) -> None:
        """
        Broadcast token price update event.

        Args:
            token_symbol: Token symbol (ETH, USDC, etc.)
            price_usd: Current price in USD
            price_change_24h: 24h price change percentage
            volume_24h: 24h volume (optional)
        """
        event = {
            "type": "price:update",
            "token_symbol": token_symbol,
            "price_usd": price_usd,
            "price_change_24h": price_change_24h,
            "volume_24h": volume_24h,
            "timestamp": datetime.now(UTC).timestamp(),
        }

        await self._publish("price:updates", event)
        logger.debug(
            f"Broadcasted price update: {token_symbol} ${price_usd}",
            extra={"token": token_symbol, "price": price_usd},
        )

    async def broadcast_transaction_status(
        self,
        user_id: UUID,
        transaction_id: str,
        status: str,
        tx_hash: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Broadcast transaction status update to specific user.

        Args:
            user_id: User UUID
            transaction_id: Transaction identifier
            status: pending/success/failed
            tx_hash: Blockchain transaction hash (optional)
            details: Additional transaction details
        """
        event = {
            "type": "transaction:status",
            "transaction_id": transaction_id,
            "status": status,
            "tx_hash": tx_hash,
            "details": details or {},
            "timestamp": datetime.now(UTC).timestamp(),
        }

        # Publish to user-specific channel
        user_channel = f"user:{user_id}:transactions"
        await self._publish(user_channel, event)

        logger.info(
            f"Broadcasted transaction status: {transaction_id} - {status}",
            extra={
                "user_id": str(user_id),
                "transaction_id": transaction_id,
                "status": status,
            },
        )

    async def broadcast_anomaly_detected(
        self,
        protocol_id: UUID,
        protocol_name: str,
        anomaly_type: str,
        severity: str,
        description: str,
        metrics: Dict[str, Any],
    ) -> None:
        """
        Broadcast anomaly detection event.

        Args:
            protocol_id: Protocol UUID
            protocol_name: Protocol name
            anomaly_type: Type of anomaly
            severity: LOW/MEDIUM/HIGH/CRITICAL
            description: Human-readable description
            metrics: Anomaly metrics and scores
        """
        event = {
            "type": "anomaly:detected",
            "protocol_id": str(protocol_id),
            "protocol_name": protocol_name,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "description": description,
            "metrics": metrics,
            "timestamp": datetime.now(UTC).timestamp(),
        }

        await self._publish("graph:anomalies", event)
        logger.warning(
            f"Broadcasted anomaly: {protocol_name} - {anomaly_type}",
            extra={
                "protocol_id": str(protocol_id),
                "anomaly_type": anomaly_type,
                "severity": severity,
            },
        )

    async def broadcast_to_user(
        self,
        user_id: UUID,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Broadcast custom event to specific user.

        Args:
            user_id: User UUID
            event_type: Custom event type
            data: Event data
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(UTC).timestamp(),
        }

        user_channel = f"user:{user_id}:events"
        await self._publish(user_channel, event)

    async def broadcast_to_channel(
        self,
        channel: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Broadcast custom event to specific channel.

        Args:
            channel: Channel name
            event_type: Event type
            data: Event data
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(UTC).timestamp(),
        }

        await self._publish(channel, event)

    async def _publish(self, channel: str, event: Dict[str, Any]) -> None:
        """
        Publish event to Redis channel.

        Args:
            channel: Channel name
            event: Event data (will be JSON serialized)
        """
        try:
            message = json.dumps(event, default=str)
            await self._redis.publish(channel, message)
        except Exception as e:
            logger.error(
                f"Failed to publish to channel {channel}: {e}",
                extra={"channel": channel, "event_type": event.get("type")},
                exc_info=True,
            )


# Helper function for easy access
async def create_event_broadcaster(
    redis_url: str = "redis://localhost:6379/0",
) -> GraphEventBroadcaster:
    """
    Create and return an event broadcaster instance.

    Args:
        redis_url: Redis connection URL

    Returns:
        Configured GraphEventBroadcaster
    """
    redis_client = await aioredis.from_url(redis_url, decode_responses=True)
    return GraphEventBroadcaster(redis_client)
