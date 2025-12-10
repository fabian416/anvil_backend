"""
Dishka IOC Provider for LLM Ranking System.

Registers all dependencies for the adaptive ranking system.
"""

from dishka import Provider, Scope, provide

from app.domain.ports.llm_ranking_repository import LLMRankingRepository
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.repositories.llm.ranking_repository import (
    SqlaLLMRankingRepository,
)
from app.domain.services.llm.ranking_engine import RankingEngine
from app.application.llm.ranking.recalculate_agent_rankings import (
    RecalculateAgentRankings,
)
from app.application.llm.ranking.recalculate_all_rankings import (
    RecalculateAllRankings,
)
from app.application.llm.ranking.get_rankings import (
    GetRankingsForAgent,
    GetAllRankingsOverview,
)
from app.application.llm.ranking.manage_overrides import (
    SetRankingOverride,
    RemoveRankingOverride,
)
from app.application.llm.ranking.register_model import (
    RegisterVertexAIModel,
    RegisterDeepInfraModel,
)


class LLMRankingProvider(Provider):
    """Provider for LLM Ranking System dependencies."""

    # ========================================================================
    # Domain Services (APP scope - singleton)
    # ========================================================================

    @provide(scope=Scope.APP)
    def provide_ranking_engine(self) -> RankingEngine:
        """Provide ranking calculation engine."""
        return RankingEngine()

    # ========================================================================
    # Repository (REQUEST scope - per request)
    # ========================================================================

    @provide(scope=Scope.REQUEST)
    def provide_ranking_repository(
        self, session: MainAsyncSession
    ) -> LLMRankingRepository:
        """Provide ranking repository."""
        return SqlaLLMRankingRepository(session)

    # ========================================================================
    # Application Interactors (REQUEST scope)
    # ========================================================================

    @provide(scope=Scope.REQUEST)
    def provide_recalculate_agent_rankings(
        self,
        repository: LLMRankingRepository,
        ranking_engine: RankingEngine,
    ) -> RecalculateAgentRankings:
        """Provide recalculate agent rankings interactor."""
        return RecalculateAgentRankings(
            repository=repository,
            ranking_engine=ranking_engine,
        )

    @provide(scope=Scope.REQUEST)
    def provide_recalculate_all_rankings(
        self,
        repository: LLMRankingRepository,
        ranking_engine: RankingEngine,
    ) -> RecalculateAllRankings:
        """Provide recalculate all rankings interactor."""
        return RecalculateAllRankings(
            repository=repository,
            ranking_engine=ranking_engine,
        )

    @provide(scope=Scope.REQUEST)
    def provide_get_rankings_for_agent(
        self,
        repository: LLMRankingRepository,
    ) -> GetRankingsForAgent:
        """Provide get rankings for agent interactor."""
        return GetRankingsForAgent(repository=repository)

    @provide(scope=Scope.REQUEST)
    def provide_get_all_rankings_overview(
        self,
        repository: LLMRankingRepository,
    ) -> GetAllRankingsOverview:
        """Provide get all rankings overview interactor."""
        return GetAllRankingsOverview(repository=repository)

    @provide(scope=Scope.REQUEST)
    def provide_set_ranking_override(
        self,
        repository: LLMRankingRepository,
    ) -> SetRankingOverride:
        """Provide set ranking override interactor."""
        return SetRankingOverride(repository=repository)

    @provide(scope=Scope.REQUEST)
    def provide_remove_ranking_override(
        self,
        repository: LLMRankingRepository,
    ) -> RemoveRankingOverride:
        """Provide remove ranking override interactor."""
        return RemoveRankingOverride(repository=repository)

    @provide(scope=Scope.REQUEST)
    def provide_register_vertex_ai_model(
        self,
        repository: LLMRankingRepository,
    ) -> RegisterVertexAIModel:
        """Provide register Vertex AI model interactor."""
        return RegisterVertexAIModel(repository=repository)

    @provide(scope=Scope.REQUEST)
    def provide_register_deepinfra_model(
        self,
        repository: LLMRankingRepository,
    ) -> RegisterDeepInfraModel:
        """Provide register DeepInfra model interactor."""
        return RegisterDeepInfraModel(repository=repository)
