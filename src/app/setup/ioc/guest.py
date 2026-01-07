"""
Guest Chat Dependency Injection Provider.

Provides DI setup for guest chat components:
- GuestRepository
- GuestHandlerService
- SendGuestMessage command
"""

import logging

from dishka import Provider, Scope, provide

from app.application.guest.commands.send_guest_message import SendGuestMessage

logger = logging.getLogger(__name__)
from app.application.guest.handlers.guest_handler_service import GuestHandlerService
from app.application.chat.handlers.lending_handler import LendingHandler
from app.application.chat.handlers.money_market_handler import MoneyMarketHandler
from app.application.chat.handlers.swap_handler import SwapHandler
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
    def provide_swap_handler(
        self,
    ) -> SwapHandler | None:
        """
        Provide SwapHandler with real 1inch/LiFi clients if API keys are available.
        
        Returns None if no API keys configured (falls back to demo mode).
        """
        import os
        from app.setup.config.loader import load_full_config, get_current_env
        
        # Try to get 1inch API key
        oneinch_api_key = os.getenv("ONEINCH_API_KEY", "").strip()
        if not oneinch_api_key:
            try:
                raw_config = load_full_config(env=get_current_env())
                if 'external_apis' in raw_config and isinstance(raw_config['external_apis'], dict):
                    oneinch_key = raw_config['external_apis'].get('ONEINCH_API_KEY', '')
                    if oneinch_key:
                        oneinch_api_key = str(oneinch_key).strip()
            except Exception:
                pass
        
        # Only create handler if we have at least one API key
        if not oneinch_api_key:
            return None
        
        try:
            from app.infrastructure.adapters.external.oneinch_client import OneInchClient
            
            # OneInchClient uses chain name (not chain_id)
            oneinch_client = OneInchClient(
                api_key=oneinch_api_key,
                chain="ethereum",  # Default to Ethereum mainnet
            )
            
            # LiFi doesn't require API key, but we can add it later if needed
            lifi_client = None
            try:
                from app.infrastructure.adapters.external.lifi_client import LiFiClient
                lifi_client = LiFiClient()
            except Exception:
                pass
            
            return SwapHandler(
                oneinch_client=oneinch_client,
                lifi_client=lifi_client,
                hyperliquid_client=None,  # Optional
            )
        except Exception as e:
            logger.warning(f"Failed to create SwapHandler: {e}")
            return None

    @provide(scope=Scope.REQUEST)
    def provide_guest_handler_service(
        self,
        lending_handler: LendingHandler,
        money_market_handler: MoneyMarketHandler,
        swap_handler: SwapHandler | None = None,
    ) -> GuestHandlerService:
        """
        Provide GuestHandlerService with real handlers.
        
        Injects:
        - LendingHandler for real Morpho vault data
        - MoneyMarketHandler for real Aave/Compound rate comparisons
        - SwapHandler for real 1inch/LiFi swap quotes (if API keys configured)
        - Hunter AI and ULTRA handlers don't require DI as they are stateless.
        """
        return GuestHandlerService(
            lending_handler=lending_handler,  # Real Morpho vault data
            swap_handler=swap_handler,  # Real 1inch/LiFi data if API keys available
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
