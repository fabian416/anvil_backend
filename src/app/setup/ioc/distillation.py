"""Dependency injection providers for distillation system."""

from dishka import Provider, Scope, provide, from_context
from typing import Optional, Any

from app.infrastructure.adapters.types import MainAsyncSession

from app.domain.ports.distillation_repository import (
    CacheRepository,
    DistillationConfigRepository,
    DistillationTelemetryRepository,
    StaticResponseRepository,
)
from app.domain.services.distillation.complexity_assessor import ComplexityAssessor
from app.domain.services.distillation.engine import DistillationEngine
from app.domain.services.distillation.entity_extractor import EntityExtractor
from app.domain.services.distillation.intent_classifier import IntentClassifier
from app.domain.services.distillation.router import DistillationRouter
from app.infrastructure.distillation.cache_manager import CacheManager
from app.infrastructure.distillation.static_responder import (
    StaticResponder,
    CoinGeckoDataFetcher,
    GasDataFetcher,
    PortfolioDataFetcher,
)
from app.infrastructure.persistence_sqla.repositories.distillation_cache_repository import (
    DistillationCacheRepositorySqla,
)
from app.infrastructure.persistence_sqla.repositories.distillation_config_repository import (
    DistillationConfigRepositorySqla,
)
from app.infrastructure.persistence_sqla.repositories.distillation_static_repository import (
    DistillationStaticRepositorySqla,
)
from app.infrastructure.persistence_sqla.repositories.distillation_telemetry_repository import (
    DistillationTelemetryRepositorySqla,
)


class DistillationProvider(Provider):
    """Provider for distillation system dependencies."""

    # Domain services (request-scoped to allow optional LLM client injection)
    @provide(scope=Scope.REQUEST)
    def get_intent_classifier(
        self,
    ) -> IntentClassifier:
        """
        Get intent classifier without LLM client (rule-based only for now).

        Note: LLM client injection will be handled separately if needed.
        For now, IntentClassifier works in rule-based mode only.
        This avoids DI resolution issues with optional dependencies.

        Returns:
            IntentClassifier instance (rule-based only)
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            "⚠️ IntentClassifier initialized without LLM client (rule-based only)"
        )

        return IntentClassifier(
            llm_client=None,  # No LLM client for now (rule-based only)
            use_llm_for_ambiguous=False,  # Disable LLM until we fix DI injection
            llm_confidence_threshold=0.85,
        )

    @provide(scope=Scope.APP)
    def get_complexity_assessor(self) -> ComplexityAssessor:
        """Get complexity assessor."""
        return ComplexityAssessor()

    @provide(scope=Scope.APP)
    def get_entity_extractor(self) -> EntityExtractor:
        """Get entity extractor."""
        return EntityExtractor()

    @provide(scope=Scope.REQUEST)
    async def get_router(
        self,
        intent_classifier: IntentClassifier,
        complexity_assessor: ComplexityAssessor,
        entity_extractor: EntityExtractor,
        config_repo: DistillationConfigRepository,
    ) -> DistillationRouter:
        """Get distillation router."""
        config = await config_repo.get_config()
        return DistillationRouter(
            intent_classifier=intent_classifier,
            complexity_assessor=complexity_assessor,
            entity_extractor=entity_extractor,
            config=config,
        )

    # Repositories (request-scoped)
    @provide(scope=Scope.REQUEST)
    def get_cache_repository(
        self,
        session: MainAsyncSession,
    ) -> CacheRepository:
        """Get cache repository."""
        return DistillationCacheRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def get_config_repository(
        self,
        session: MainAsyncSession,
    ) -> DistillationConfigRepository:
        """Get config repository."""
        return DistillationConfigRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def get_static_response_repository(
        self,
        session: MainAsyncSession,
    ) -> StaticResponseRepository:
        """Get static response repository."""
        return DistillationStaticRepositorySqla(session)

    @provide(scope=Scope.REQUEST)
    def get_telemetry_repository(
        self,
        session: MainAsyncSession,
    ) -> DistillationTelemetryRepository:
        """Get telemetry repository."""
        return DistillationTelemetryRepositorySqla(session)

    # Infrastructure services
    @provide(scope=Scope.REQUEST)
    def get_cache_manager(
        self,
        cache_repo: CacheRepository,
    ) -> CacheManager:
        """Get cache manager."""
        # TODO: Add embedding service when available
        return CacheManager(
            cache_repository=cache_repo,
            embedding_service=None,  # Will add later
        )

    @provide(scope=Scope.REQUEST)
    def get_static_responder(
        self,
        static_repo: StaticResponseRepository,
    ) -> StaticResponder:
        """Get static responder."""
        # Initialize data sources
        data_sources = {
            "coingecko_api": CoinGeckoDataFetcher(),
            "gas_api": GasDataFetcher(),
            "portfolio_service": PortfolioDataFetcher(),
        }

        return StaticResponder(
            static_response_repo=static_repo,
            data_sources=data_sources,
        )

    # Main engine
    @provide(scope=Scope.REQUEST)
    def get_distillation_engine(
        self,
        intent_classifier: IntentClassifier,
        complexity_assessor: ComplexityAssessor,
        entity_extractor: EntityExtractor,
        router: DistillationRouter,
        cache_manager: CacheManager,
        static_responder: StaticResponder,
        config_repo: DistillationConfigRepository,
        telemetry_repo: DistillationTelemetryRepository,
    ) -> DistillationEngine:
        """Get distillation engine."""
        return DistillationEngine(
            intent_classifier=intent_classifier,
            complexity_assessor=complexity_assessor,
            entity_extractor=entity_extractor,
            router=router,
            cache_manager=cache_manager,
            static_responder=static_responder,
            config_repo=config_repo,
            telemetry_repo=telemetry_repo,
        )

    # Optional engine for guest chat (allows None)
    @provide(scope=Scope.REQUEST)
    def get_optional_distillation_engine(
        self,
        engine: DistillationEngine,
    ) -> DistillationEngine | None:
        """Get optional distillation engine (allows None for backwards compatibility)."""
        return engine
