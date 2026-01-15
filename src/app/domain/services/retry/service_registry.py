"""
Service Registry for Manual Override.

Allows operators to manually enable/disable services when they are
unavailable or during maintenance windows.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, UTC
from uuid import UUID

logger = logging.getLogger(__name__)


class ServiceDisabledError(Exception):
    """Raised when attempting to use a manually disabled service."""
    pass


class ServiceRegistry:
    """
    Registry for service availability and manual overrides.
    
    Allows operators to:
    - Manually disable services (during outages)
    - Re-enable services (after recovery)
    - Set maintenance windows
    - View service health
    
    Usage:
        registry = ServiceRegistry(redis_client, telemetry)
        
        # Check if service is enabled
        if not registry.is_enabled("1inch_mcp"):
            raise ServiceDisabledError("1inch service is disabled")
        
        # Disable service during known outage
        await registry.disable_service(
            "1inch_mcp",
            user_id=admin_user_id,
            reason="1inch API outage - https://status.1inch.io/incidents/123",
            duration_minutes=180,  # Auto re-enable after 3 hours
        )
        
        # Re-enable service when recovered
        await registry.enable_service(
            "1inch_mcp",
            user_id=admin_user_id,
            reason="1inch API back online - verified via status page",
        )
    """
    
    def __init__(
        self,
        redis_client: Any,
        telemetry: Optional[Any] = None,
    ):
        """
        Initialize service registry.
        
        Args:
            redis_client: Redis client for state storage
            telemetry: Telemetry collector (optional)
        """
        self.redis = redis_client
        self.telemetry = telemetry
    
    def is_enabled(self, service_name: str) -> bool:
        """
        Check if service is enabled.
        
        Args:
            service_name: Service name
        
        Returns:
            True if service is enabled, False if manually disabled
        """
        # Check manual override
        override = self.redis.get(f"service:{service_name}:override")
        if override is not None:
            return override.decode() == "enabled"
        
        # Default: enabled
        return True
    
    async def disable_service(
        self,
        service_name: str,
        user_id: UUID,
        reason: str,
        duration_minutes: Optional[int] = None,
    ):
        """
        Manually disable service.
        
        Use cases:
        - Known API outage (1inch down)
        - Maintenance window
        - Rate limit exhausted
        - Cost control
        
        Args:
            service_name: Service name to disable
            user_id: ID of user performing action
            reason: Reason for disabling
            duration_minutes: Auto re-enable after duration (optional)
        
        Example:
            await registry.disable_service(
                "1inch_mcp",
                user_id=admin_user_id,
                reason="1inch API experiencing outage - https://status.1inch.io/incidents/123",
                duration_minutes=180,  # Auto re-enable after 3 hours
            )
        """
        # Set override
        self.redis.set(f"service:{service_name}:override", "disabled")
        
        # Set expiration if duration provided
        if duration_minutes:
            self.redis.expire(
                f"service:{service_name}:override",
                duration_minutes * 60
            )
        
        # Store metadata
        metadata = {
            "user_id": str(user_id),
            "reason": reason,
            "disabled_at": datetime.now(UTC).isoformat(),
            "expires_at": (
                (datetime.now(UTC) + timedelta(minutes=duration_minutes)).isoformat()
                if duration_minutes
                else None
            ),
        }
        self.redis.set(
            f"service:{service_name}:override_metadata",
            self._serialize_metadata(metadata),
        )
        
        if duration_minutes:
            self.redis.expire(
                f"service:{service_name}:override_metadata",
                duration_minutes * 60
            )
        
        logger.warning(
            f"Service '{service_name}' MANUALLY DISABLED by user {user_id}. "
            f"Reason: {reason}"
            + (f" (expires in {duration_minutes} minutes)" if duration_minutes else "")
        )
        
        # Record telemetry
        if self.telemetry:
            await self.telemetry.record_service_override(
                service_name=service_name,
                action="disable",
                user_id=user_id,
                reason=reason,
                duration_minutes=duration_minutes,
            )
    
    async def enable_service(
        self,
        service_name: str,
        user_id: UUID,
        reason: str,
    ):
        """
        Manually enable service.
        
        Args:
            service_name: Service name to enable
            user_id: ID of user performing action
            reason: Reason for enabling
        
        Example:
            await registry.enable_service(
                "1inch_mcp",
                user_id=admin_user_id,
                reason="1inch API back online - verified via status page",
            )
        """
        # Remove override
        self.redis.delete(f"service:{service_name}:override")
        self.redis.delete(f"service:{service_name}:override_metadata")
        
        logger.info(
            f"Service '{service_name}' MANUALLY ENABLED by user {user_id}. "
            f"Reason: {reason}"
        )
        
        # Record telemetry
        if self.telemetry:
            await self.telemetry.record_service_override(
                service_name=service_name,
                action="enable",
                user_id=user_id,
                reason=reason,
            )
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get current service status.
        
        Args:
            service_name: Service name
        
        Returns:
            Status dictionary with:
            - service_name: Name of service
            - enabled: Whether service is enabled
            - override: Override value ('enabled', 'disabled', or None)
            - ttl_seconds: Time until auto re-enable (if set)
            - metadata: Override metadata (if available)
        """
        override = self.redis.get(f"service:{service_name}:override")
        override_value = override.decode() if override else None
        
        ttl = self.redis.ttl(f"service:{service_name}:override")
        if ttl == -2:  # Key doesn't exist
            ttl = None
        elif ttl == -1:  # Key exists but no expiration
            ttl = None
        
        metadata = None
        metadata_raw = self.redis.get(f"service:{service_name}:override_metadata")
        if metadata_raw:
            metadata = self._deserialize_metadata(metadata_raw.decode())
        
        return {
            "service_name": service_name,
            "enabled": self.is_enabled(service_name),
            "override": override_value,
            "ttl_seconds": ttl,
            "metadata": metadata,
        }
    
    def get_all_service_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all services with overrides.
        
        Returns:
            Dictionary of service_name -> status dict
        """
        # Get all override keys from Redis
        pattern = "service:*:override"
        keys = self.redis.keys(pattern)
        
        statuses = {}
        for key in keys:
            # Extract service name from key (service:SERVICE_NAME:override)
            service_name = key.decode().split(":")[1]
            statuses[service_name] = self.get_service_status(service_name)
        
        return statuses
    
    def count_disabled(self) -> int:
        """Count number of disabled services."""
        statuses = self.get_all_service_statuses()
        return sum(1 for status in statuses.values() if not status["enabled"])
    
    def count_total_with_overrides(self) -> int:
        """Count total services with overrides."""
        return len(self.get_all_service_statuses())
    
    # Private helpers
    
    def _serialize_metadata(self, metadata: Dict[str, Any]) -> str:
        """Serialize metadata to JSON string."""
        import json
        return json.dumps(metadata)
    
    def _deserialize_metadata(self, metadata_str: str) -> Dict[str, Any]:
        """Deserialize metadata from JSON string."""
        import json
        try:
            return json.loads(metadata_str)
        except json.JSONDecodeError:
            return {}
