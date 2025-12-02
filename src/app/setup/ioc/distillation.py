"""Dependency injection providers for distillation system."""
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

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
    
    # Domain services (singleton - stateless)
    @provide(scope=Scope.APP)
    def get_intent_classifier(self) -> IntentClassifier:
        """Get intent classifier."""
        return IntentClassifier()
    
    @provide(scope=Scope.APP)
    def get_complexity_assessor(self) -> ComplexityAssessor:
        """Get complexity assessor."""
        return ComplexityAssessor()
    
    @provide(scope=Scope.APP)
    def get_entity_extractor(self) -> EntityExtractor:
        """Get entity extractor."""
        return EntityExtractor()
    
    @provide(scope=Scope.APP)
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
        session: AsyncSession,
    ) -> CacheRepository:
        """Get cache repository."""
        return DistillationCacheRepositorySqla(session)
    
    @provide(scope=Scope.REQUEST)
    def get_config_repository(
        self,
        session: AsyncSession,
    ) -> DistillationConfigRepository:
        """Get config repository."""
        return DistillationConfigRepositorySqla(session)
    
    @provide(scope=Scope.REQUEST)
    def get_static_response_repository(
        self,
        session: AsyncSession,
    ) -> StaticResponseRepository:
        """Get static response repository."""
        return DistillationStaticRepositorySqla(session)
    
    @provide(scope=Scope.REQUEST)
    def get_telemetry_repository(
        self,
        session: AsyncSession,
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
