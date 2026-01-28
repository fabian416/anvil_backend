from collections.abc import Iterable

from dishka import Provider

from app.setup.ioc.aave import AaveProvider
from app.setup.ioc.application import ApplicationProvider
from app.setup.ioc.distillation import DistillationProvider
from app.setup.ioc.distillation_validation import DistillationValidationProvider
from app.setup.ioc.domain import DomainProvider
from app.setup.ioc.infrastructure import infrastructure_provider
from app.setup.ioc.presentation import PresentationProvider
from app.setup.ioc.settings import SettingsProvider
from app.setup.ioc.agno import AgnoProvider
from app.setup.ioc.graph import GraphProvider
from app.setup.ioc.llm_ranking import LLMRankingProvider
from app.setup.ioc.agent_squad_domain import AgentSquadDomainProvider
from app.setup.ioc.agent_squad_infrastructure import AgentSquadInfrastructureProvider
from app.setup.ioc.agent_squad_application import AgentSquadApplicationProvider
from app.setup.ioc.cache import CacheProvider
from app.setup.ioc.chat_phase2 import ChatPhase2Provider
from app.setup.ioc.morpho import MorphoProvider
from app.setup.ioc.guest import GuestProvider
from app.setup.ioc.chat import ChatProvider
from app.setup.ioc.money_market import MoneyMarketProvider

# TODO: These providers are pending implementation - uncomment when ready
# from app.setup.ioc.curve import CurveProvider
# from app.setup.ioc.hyperliquid import HyperliquidProvider
# from app.setup.ioc.layerzero import LayerZeroProvider
# from app.setup.ioc.axelar import AxelarProvider
# from app.setup.ioc.opensea import OpenSeaProvider


def get_providers() -> Iterable[Provider]:
    return (
        DomainProvider(),
        ApplicationProvider(),
        infrastructure_provider(),
        PresentationProvider(),
        SettingsProvider(),
        DistillationProvider(),
        DistillationValidationProvider(),  # Request validation system
        AgnoProvider(),
        GraphProvider(),
        LLMRankingProvider(),  # LLM Adaptive Ranking System
        AgentSquadDomainProvider(),  # Agent Squad domain services
        AgentSquadInfrastructureProvider(),  # Agent Squad infrastructure adapters
        AgentSquadApplicationProvider(),  # Agent Squad application interactors
        CacheProvider(),  # Cache infrastructure (Redis, ExternalAPICache)
        ChatPhase2Provider(),  # Chat Phase 2 components (WebSocket, Analytics, etc.)
        AaveProvider(),  # Aave V3 lending protocol integration
        MorphoProvider(),  # Morpho Protocol lending vaults integration
        GuestProvider(),  # Guest chat for unauthenticated users
        ChatProvider(),  # Unified chat for guest and authenticated users
        MoneyMarketProvider(),  # Money market rate caching and analytics
        # TODO: Uncomment when implementations are ready
        # CurveProvider(),  # Curve Finance DeFi integration
        # HyperliquidProvider(),  # Hyperliquid perpetual futures integration
        # LayerZeroProvider(),  # LayerZero cross-chain messaging integration
        # AxelarProvider(),  # Axelar cross-chain bridging integration
        # OpenSeaProvider(),  # OpenSea NFT marketplace integration
    )
