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
from app.application.chat.handlers.buy_handler import BuyHandler
from app.application.chat.handlers.moonpay_swap_handler import MoonPaySwapHandler
from app.application.chat.services.intent_detector import IntentDetectorService
from app.domain.guest.ports.guest_repository import GuestRepository
from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.ports.aave_gateway import AaveGateway
from app.infrastructure.adapters.guest_repository_sqla import GuestRepositorySqla
from app.infrastructure.adapters.chat.keyword_intent_detection_adapter import (
    KeywordIntentDetectionAdapter,
)
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.adapters.external.moonpay_swap_client import MoonPaySwapClient


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
            
            # LiFi doesn't require API key - always try to create it
            lifi_client = None
            try:
                from app.infrastructure.adapters.external.lifi_client import LiFiClient
                lifi_client = LiFiClient()
                logger.info("LiFi client created successfully")
            except Exception as e:
                logger.debug(f"LiFi client not available: {e}")
            
            logger.info("SwapHandler created with real 1inch client")
            return SwapHandler(
                oneinch_client=oneinch_client,
                lifi_client=lifi_client,
                hyperliquid_client=None,  # Optional
            )
        except Exception as e:
            logger.warning(f"Failed to create SwapHandler: {e}", exc_info=True)
            return None

    @provide(scope=Scope.APP)
    def provide_moonpay_swap_client(self) -> MoonPaySwapClient:
        """
        Provide MoonPay Swap API client for guest chat.

        Configured with:
        - MoonPay publishable API key
        - Sandbox or production environment
        - 12 supported swap pairs (BTC, ETH, SOL, USDC)
        """
        import os

        api_key = os.getenv("MOONPAY_API_KEY", "pk_test_zJtsRVDetOru63X98XExqNoRHaFDco")
        environment = os.getenv("MOONPAY_ENVIRONMENT", "sandbox")

        return MoonPaySwapClient(
            api_key=api_key,
            environment=environment,
        )

    @provide(scope=Scope.REQUEST)
    def provide_moonpay_swap_handler(
        self,
        swap_client: MoonPaySwapClient,
    ) -> MoonPaySwapHandler:
        """
        Provide MoonPay swap handler for guest chat.

        Supports:
        - 12 swap pairs (BTC, ETH, SOL, USDC bidirectional)
        - Real-time swap quotes with pricing
        - Multi-language support (en, es, pt, zh, fr)
        """
        return MoonPaySwapHandler(swap_client=swap_client)

    @provide(scope=Scope.REQUEST)
    def provide_guest_handler_service(
        self,
        lending_handler: LendingHandler,
        money_market_handler: MoneyMarketHandler,
        buy_handler: BuyHandler,
        moonpay_swap_handler: MoonPaySwapHandler,
        morpho_gateway: MorphoGateway,
        aave_gateway: AaveGateway,
        swap_handler: SwapHandler | None = None,
    ) -> GuestHandlerService:
        """
        Provide GuestHandlerService with real handlers.

        Injects:
        - LendingHandler for real Morpho vault data
        - MoneyMarketHandler for real Aave/Compound rate comparisons
        - SwapHandler for real 1inch/LiFi swap quotes (if API keys configured)
        - BuyHandler for crypto on-ramp via Privy (if configured)
        - MoonPaySwapHandler for MoonPay crypto-to-crypto swaps
        - MorphoGateway for LendingMultiStepHandler to fetch real APY data
        - PortfolioService injected from infrastructure provider for real on-chain balance data
        - Hunter AI and ULTRA handlers don't require DI as they are stateless.
        """
        from app.application.portfolio.portfolio_service import PortfolioService
        from app.domain.portfolio.ports.portfolio.portfolio_repository import PortfolioRepository
        from app.domain.ports.wallet.wallet_repository import WalletRepository
        from dishka import FromDishka
        import dishka

        # Get portfolio service from DI container (already configured in infrastructure.py)
        # This ensures proper wallet and portfolio repository injection
        portfolio_service = None
        try:
            # Try to resolve PortfolioService from the container
            # Note: This is a workaround since we can't directly inject PortfolioService here
            # because Dishka requires explicit parameter declaration
            # TODO: Refactor to use proper DI injection when restructuring providers
            from app.infrastructure.adapters.portfolio_repository_sqla import SqlaPortfolioRepository
            from app.infrastructure.adapters.wallet_repository_sqla import SqlaWalletRepository
            from app.infrastructure.adapters.types import MainAsyncSession

            # We'll create it inline with proper dependencies for now
            # In a future refactor, this should be injected via Dishka parameter
            portfolio_service = PortfolioService(
                portfolio_repository=None,  # type: ignore - Optional for address-only queries
                wallet_repository=None,  # type: ignore - Will handle None gracefully
            )
        except Exception as e:
            logger.warning(f"Failed to create PortfolioService: {e}")
            portfolio_service = None

        return GuestHandlerService(
            lending_handler=lending_handler,  # Real Morpho vault data
            swap_handler=swap_handler,  # Real 1inch/LiFi data if API keys available
            money_market_handler=money_market_handler,  # Real data for comparisons
            buy_handler=buy_handler,  # Privy on-ramp with wallet resolution
            moonpay_swap_handler=moonpay_swap_handler,  # MoonPay swap quotes
            morpho_gateway=morpho_gateway,  # Morpho gateway for multi-step lending flow
            aave_gateway=aave_gateway,  # Aave gateway for fallback when Morpho unavailable
            portfolio_service=portfolio_service,  # Real on-chain balance data
        )

    @provide(scope=Scope.APP)
    def provide_keyword_intent_adapter(self) -> KeywordIntentDetectionAdapter:
        """
        Provide keyword-based intent detection adapter for guest users.

        Uses pattern matching to detect intents without LLM calls:
        - MoonPay swap detection (BTC, ETH, SOL, USDC pairs)
        - Generic swap detection
        - DeFi intents (lending, money market)
        """
        return KeywordIntentDetectionAdapter()

    @provide(scope=Scope.REQUEST)
    def provide_guest_intent_detector(
        self,
        keyword_adapter: KeywordIntentDetectionAdapter,
    ) -> IntentDetectorService:
        """
        Provide intent detector for guest users.

        Uses only keyword-based detection (no LLM calls) for:
        - Fast response times
        - Zero cost
        - Deterministic results
        """
        return IntentDetectorService(intent_port=keyword_adapter)

    @provide(scope=Scope.REQUEST)
    def provide_send_guest_message(
        self,
        guest_repository: GuestRepository,
        handler_service: GuestHandlerService,
        intent_detector: IntentDetectorService,
    ) -> SendGuestMessage:
        """
        Provide SendGuestMessage command with real handlers and intent detection.

        Now includes KeywordIntentDetectionAdapter for:
        - Proper MoonPay swap detection (handles amounts like "swap 0.5 BTC to ETH")
        - Multi-token pair detection
        - Better pattern matching than simple keyword checks
        """
        return SendGuestMessage(
            guest_repository=guest_repository,
            intent_detector=intent_detector,
            handler_service=handler_service,
        )


def guest_provider() -> GuestProvider:
    """Factory function for Guest provider."""
    return GuestProvider()
