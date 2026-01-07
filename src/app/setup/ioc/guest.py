"""
Guest Chat Dependency Injection Provider.

Provides DI setup for guest chat components:
- GuestRepository
- GuestHandlerService
- SendGuestMessage command
"""

from dishka import Provider, Scope, provide

from app.application.guest.commands.send_guest_message import SendGuestMessage
from app.application.guest.handlers.guest_handler_service import GuestHandlerService
from app.application.chat.handlers.lending_handler import LendingHandler
from app.application.chat.handlers.swap_handler import SwapHandler
from app.application.chat.handlers.money_market_handler import MoneyMarketHandler
from app.domain.guest.ports.guest_repository import GuestRepository
from app.domain.ports.morpho_gateway import MorphoGateway
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
    def provide_lending_handler(
        self,
        morpho_gateway: MorphoGateway,
    ) -> LendingHandler:
        """
        Provide lending handler for Morpho vault operations.
        
        Uses real Morpho GraphQL API for vault data.
        """
        return LendingHandler(morpho_gateway=morpho_gateway)

    @provide(scope=Scope.REQUEST)
    def provide_guest_handler_service(
        self,
        lending_handler: LendingHandler,
        money_market_handler: MoneyMarketHandler,
    ) -> GuestHandlerService:
        """
        Provide GuestHandlerService with real handlers.
        
        Injects:
        - LendingHandler for real Morpho vault data
        - MoneyMarketHandler for real Aave/Compound rate comparisons
        - SwapHandler is optional (can be None for demo mode)
        - Hunter AI and ULTRA handlers don't require DI as they are stateless.
        """
        return GuestHandlerService(
            lending_handler=lending_handler,  # Real Morpho vault data
            swap_handler=None,  # Optional - demo mode supported
            money_market_handler=money_market_handler,  # Real data for comparisons
        )

    @provide(scope=Scope.REQUEST)
    def provide_send_guest_message(
        self,
        guest_repository: GuestRepository,
        handler_service: GuestHandlerService,
    ) -> SendGuestMessage:
        """
        Provide SendGuestMessage command with real handler service.
        
        Note: IntentDetectorService is not injected here to avoid
        Dishka resolution issues with optional dependencies.
        The command handles None intent_detector gracefully.
        """
        return SendGuestMessage(
            guest_repository=guest_repository,
            intent_detector=None,
            handler_service=handler_service,
        )


def guest_provider() -> GuestProvider:
    """Factory function for Guest provider."""
    return GuestProvider()
