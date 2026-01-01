"""
Guest Chat Dependency Injection Provider.

Provides DI setup for guest chat components:
- GuestRepository
- SendGuestMessage command
"""

from dishka import Provider, Scope, provide

from app.application.guest.commands.send_guest_message import SendGuestMessage
from app.domain.guest.ports.guest_repository import GuestRepository
from app.infrastructure.adapters.guest_repository_sqla import GuestRepositorySqla
from app.infrastructure.adapters.types import MainAsyncSession


class GuestProvider(Provider):
    """Dependency injection provider for guest chat components."""

    @provide(scope=Scope.REQUEST)
    def provide_guest_repository(
        self,
        session: MainAsyncSession,
    ) -> GuestRepository:
        """Provide GuestRepository implementation."""
        return GuestRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def provide_send_guest_message(
        self,
        guest_repository: GuestRepository,
    ) -> SendGuestMessage:
        """
        Provide SendGuestMessage command.
        
        Note: IntentDetectorService is not injected here to avoid
        Dishka resolution issues with optional dependencies.
        The command handles None intent_detector gracefully.
        """
        return SendGuestMessage(
            guest_repository=guest_repository,
            intent_detector=None,
        )


def guest_provider() -> GuestProvider:
    """Factory function for Guest provider."""
    return GuestProvider()
