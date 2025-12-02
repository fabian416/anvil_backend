"""
Graph IoC Provider

Dependency injection configuration for graph-related components.
"""

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession
import os
import redis.asyncio as aioredis

from app.domain.ports.graph import GraphRepository
from app.domain.ports.external_data import DefiDataProvider
from app.domain.ports.embeddings import EmbeddingService
from app.domain.ports.vector import VectorRepository
from app.domain.services.graph import GraphService, RiskAnalysisService
from app.domain.services.ml import RiskPredictionService, NetworkAnalysisService
from app.infrastructure.persistence_age import GraphRepositoryAge
from app.infrastructure.external_data.defillama import DeFiLlamaClient
from app.infrastructure.embeddings import OpenAIEmbeddingService
from app.infrastructure.persistence_sqla.repositories.vector_repository_sqla import VectorRepositorySqla
from app.infrastructure.cache.graph_cache import GraphQueryCache
from app.application.graph import (
    PopulateGraphInteractor,
    ValidateGraphInteractor,
    GraphAnalyticsInteractor,
    GenerateEmbeddingsInteractor,
    HybridRetrievalInteractor,
)
from app.application.ml import (
    PredictRiskInteractor,
    PredictBatchRiskInteractor,
    DetectAnomaliesInteractor,
    ForecastRiskInteractor,
    CalculatePageRankInteractor,
    DetectCommunitiesInteractor,
    CalculateCentralityInteractor,
    SimulateContagionInteractor,
)
from app.application.chat import (
    ChatGraphSearchHandler,
    ChatRiskInsightsHandler,
)
from app.application.portfolio import PortfolioRiskAnalysis
from app.application.alerts import RiskAlertService, RiskAlertMonitor
from app.infrastructure.websocket import GraphEventBroadcaster
from app.application.preferences import UserPreferencesService
from app.application.dashboard import DashboardAggregationService
from app.application.search import SearchHistoryService
from app.application.comparison import ProtocolComparisonService


class GraphProvider(Provider):
    """
    Dishka provider for graph components.
    
    Registers:
    - GraphRepository implementation (Apache AGE)
    - DefiDataProvider implementation (DeFiLlama)
    - EmbeddingService implementation (OpenAI)
    - VectorRepository implementation (PostgreSQL)
    - GraphService
    - RiskAnalysisService
    - PopulateGraphInteractor
    - ValidateGraphInteractor
    - GraphAnalyticsInteractor
    - GenerateEmbeddingsInteractor
    - HybridRetrievalInteractor
    """
    
    scope = Scope.REQUEST
    
    @provide
    def provide_graph_repository(
        self,
        session: AsyncSession,
    ) -> GraphRepository:
        """
        Provide GraphRepository implementation.
        
        Uses Apache AGE adapter with the default graph name.
        """
        return GraphRepositoryAge(
            session=session,
            graph_name="defi_knowledge_graph",
        )
    
    @provide
    def provide_vector_repository(
        self,
        session: AsyncSession,
    ) -> VectorRepository:
        """Provide VectorRepository implementation"""
        return VectorRepositorySqla(session=session)
    
    @provide
    def provide_defi_data_provider(self) -> DefiDataProvider:
        """Provide DeFi data provider implementation"""
        return DeFiLlamaClient(timeout=30, max_retries=3)
    
    @provide
    def provide_embedding_service(self) -> EmbeddingService:
        """Provide Embedding service implementation"""
        openai_key = os.getenv("OPENAI_API_KEY", "")
        return OpenAIEmbeddingService(api_key=openai_key)
    
    @provide
    async def provide_graph_cache(self) -> GraphQueryCache:
        """Provide Graph query cache"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = await aioredis.from_url(redis_url, decode_responses=True)
        return GraphQueryCache(redis_client=redis_client)
    
    @provide
    def provide_graph_service(
        self,
        graph_repo: GraphRepository,
    ) -> GraphService:
        """Provide GraphService for graph operations"""
        return GraphService(graph_repo=graph_repo)
    
    @provide
    def provide_risk_analysis_service(
        self,
        graph_repo: GraphRepository,
    ) -> RiskAnalysisService:
        """Provide RiskAnalysisService for risk analysis"""
        return RiskAnalysisService(graph_repo=graph_repo)
    
    @provide
    def provide_populate_graph_interactor(
        self,
        graph_repo: GraphRepository,
        data_provider: DefiDataProvider,
    ) -> PopulateGraphInteractor:
        """Provide PopulateGraphInteractor for data ingestion"""
        return PopulateGraphInteractor(graph_repo, data_provider)
    
    @provide
    def provide_validate_graph_interactor(
        self,
        graph_repo: GraphRepository,
    ) -> ValidateGraphInteractor:
        """Provide ValidateGraphInteractor for validation"""
        return ValidateGraphInteractor(graph_repo)
    
    @provide
    def provide_graph_analytics_interactor(
        self,
        graph_repo: GraphRepository,
    ) -> GraphAnalyticsInteractor:
        """Provide GraphAnalyticsInteractor for analytics"""
        return GraphAnalyticsInteractor(graph_repo)
    
    @provide
    def provide_generate_embeddings_interactor(
        self,
        graph_repo: GraphRepository,
        embedding_service: EmbeddingService,
        vector_repo: VectorRepository,
    ) -> GenerateEmbeddingsInteractor:
        """Provide GenerateEmbeddingsInteractor for embedding generation"""
        return GenerateEmbeddingsInteractor(graph_repo, embedding_service, vector_repo)
    
    @provide
    def provide_hybrid_retrieval_interactor(
        self,
        graph_repo: GraphRepository,
        embedding_service: EmbeddingService,
        vector_repo: VectorRepository,
        graph_service: GraphService,
        risk_service: RiskAnalysisService,
    ) -> HybridRetrievalInteractor:
        """Provide HybridRetrievalInteractor for hybrid retrieval"""
        return HybridRetrievalInteractor(
            graph_repo,
            embedding_service,
            vector_repo,
            graph_service,
            risk_service,
        )
    
    # ML Services
    
    @provide
    def provide_risk_prediction_service(
        self,
        graph_repo: GraphRepository,
    ) -> RiskPredictionService:
        """Provide ML risk prediction service"""
        return RiskPredictionService(graph_repo)
    
    @provide
    def provide_network_analysis_service(
        self,
        graph_repo: GraphRepository,
    ) -> NetworkAnalysisService:
        """Provide network analysis service"""
        return NetworkAnalysisService(graph_repo)
    
    # ML Interactors
    
    @provide
    def provide_predict_risk_interactor(
        self,
        prediction_service: RiskPredictionService,
    ) -> PredictRiskInteractor:
        """Provide PredictRiskInteractor"""
        return PredictRiskInteractor(prediction_service)
    
    @provide
    def provide_predict_batch_risk_interactor(
        self,
        prediction_service: RiskPredictionService,
    ) -> PredictBatchRiskInteractor:
        """Provide PredictBatchRiskInteractor"""
        return PredictBatchRiskInteractor(prediction_service)
    
    @provide
    def provide_detect_anomalies_interactor(
        self,
        prediction_service: RiskPredictionService,
    ) -> DetectAnomaliesInteractor:
        """Provide DetectAnomaliesInteractor"""
        return DetectAnomaliesInteractor(prediction_service)
    
    @provide
    def provide_forecast_risk_interactor(
        self,
        prediction_service: RiskPredictionService,
    ) -> ForecastRiskInteractor:
        """Provide ForecastRiskInteractor"""
        return ForecastRiskInteractor(prediction_service)
    
    @provide
    def provide_calculate_pagerank_interactor(
        self,
        network_service: NetworkAnalysisService,
    ) -> CalculatePageRankInteractor:
        """Provide CalculatePageRankInteractor"""
        return CalculatePageRankInteractor(network_service)
    
    @provide
    def provide_detect_communities_interactor(
        self,
        network_service: NetworkAnalysisService,
    ) -> DetectCommunitiesInteractor:
        """Provide DetectCommunitiesInteractor"""
        return DetectCommunitiesInteractor(network_service)
    
    @provide
    def provide_calculate_centrality_interactor(
        self,
        network_service: NetworkAnalysisService,
    ) -> CalculateCentralityInteractor:
        """Provide CalculateCentralityInteractor"""
        return CalculateCentralityInteractor(network_service)
    
    @provide
    def provide_simulate_contagion_interactor(
        self,
        network_service: NetworkAnalysisService,
    ) -> SimulateContagionInteractor:
        """Provide SimulateContagionInteractor"""
        return SimulateContagionInteractor(network_service)
    
    # Chat Handlers (NEW: GraphRAG + ML integration for chat)
    
    @provide
    def provide_chat_graph_search_handler(
        self,
        hybrid_retrieval: HybridRetrievalInteractor,
        graph_repo: GraphRepository,
    ) -> ChatGraphSearchHandler:
        """Provide ChatGraphSearchHandler for protocol search from chat"""
        return ChatGraphSearchHandler(hybrid_retrieval, graph_repo)
    
    @provide
    def provide_chat_risk_insights_handler(
        self,
        risk_prediction_service: RiskPredictionService,
        hybrid_retrieval: HybridRetrievalInteractor,
        graph_repo: GraphRepository,
    ) -> ChatRiskInsightsHandler:
        """Provide ChatRiskInsightsHandler for risk analysis from chat"""
        return ChatRiskInsightsHandler(
            risk_prediction_service,
            hybrid_retrieval,
            graph_repo,
        )
    
    # Portfolio Risk Analysis (NEW: Portfolio management)
    
    @provide
    def provide_portfolio_risk_analysis(
        self,
        risk_prediction_service: RiskPredictionService,
        network_service: NetworkAnalysisService,
        graph_repo: GraphRepository,
    ) -> PortfolioRiskAnalysis:
        """Provide PortfolioRiskAnalysis for portfolio risk assessment"""
        return PortfolioRiskAnalysis(
            risk_prediction_service,
            network_service,
            graph_repo,
        )
    
    # Risk Alert System (NEW: Alert management)
    
    @provide
    def provide_event_broadcaster(
        self,
        graph_cache: GraphQueryCache,  # Reuse Redis client
    ) -> GraphEventBroadcaster:
        """Provide GraphEventBroadcaster for real-time events"""
        # Use same Redis client as cache
        return GraphEventBroadcaster(graph_cache._redis)
    
    @provide
    def provide_risk_alert_service(
        self,
        risk_prediction_service: RiskPredictionService,
        event_broadcaster: GraphEventBroadcaster,
    ) -> RiskAlertService:
        """Provide RiskAlertService for alert generation and management"""
        return RiskAlertService(risk_prediction_service, event_broadcaster)
    
    @provide
    def provide_risk_alert_monitor(
        self,
        alert_service: RiskAlertService,
    ) -> RiskAlertMonitor:
        """Provide RiskAlertMonitor for background monitoring"""
        return RiskAlertMonitor(alert_service)
    
    # User Preferences (NEW: Personalization)
    
    @provide
    def provide_user_preferences_service(self) -> UserPreferencesService:
        """Provide UserPreferencesService for user personalization"""
        return UserPreferencesService()
    
    # Dashboard Aggregation (NEW: Dashboard insights)
    
    @provide
    def provide_dashboard_aggregation_service(
        self,
        portfolio_risk: PortfolioRiskAnalysis,
        preferences_service: UserPreferencesService,
        hybrid_retrieval: HybridRetrievalInteractor,
    ) -> DashboardAggregationService:
        """Provide DashboardAggregationService for home dashboard insights"""
        return DashboardAggregationService(
            portfolio_risk,
            preferences_service,
            hybrid_retrieval,
        )
    
    # Search History (NEW: Track user searches)
    
    @provide
    def provide_search_history_service(self) -> SearchHistoryService:
        """Provide SearchHistoryService for tracking user searches"""
        return SearchHistoryService()
    
    # Protocol Comparison (NEW: Side-by-side protocol analysis)
    
    @provide
    def provide_protocol_comparison_service(self) -> ProtocolComparisonService:
        """Provide ProtocolComparisonService for comparing protocols"""
        return ProtocolComparisonService()
