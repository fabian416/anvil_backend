"""
Disable Service Interactor.

Manually disables a service in the retry system.
"""
from typing import Optional
from uuid import UUID

from app.domain.services.retry import ServiceRegistry


class DisableService:
    """Interactor to disable a service manually."""
    
    # Default admin user ID (should be from auth context in production)
    DEFAULT_ADMIN_ID = UUID("00000000-0000-0000-0000-000000000001")
    
    def __init__(
        self,
        service_registry: ServiceRegistry,
    ):
        """
        Initialize interactor.
        
        Args:
            service_registry: Service registry
        """
        self.service_registry = service_registry
    
    async def execute(
        self,
        service_name: str,
        reason: str,
        duration_minutes: Optional[int] = None,
        user_id: Optional[UUID] = None,
    ) -> None:
        """
        Execute interactor.
        
        Args:
            service_name: Name of the service to disable
            reason: Reason for disabling
            duration_minutes: Auto re-enable after duration (None = permanent)
            user_id: User performing the action (defaults to admin)
        """
        await self.service_registry.disable_service(
            service_name=service_name,
            user_id=user_id or self.DEFAULT_ADMIN_ID,
            reason=reason,
            duration_minutes=duration_minutes,
        )
