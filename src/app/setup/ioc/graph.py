"""
Graph IoC Provider

Dependency injection configuration for graph-related components.
"""

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.domain.ports.graph import GraphRepository
from app.domain.ports.external_data import DefiDataProvider
from app.domain.ports.embeddings import EmbeddingService
from app.domain.ports.vector import VectorRepository
from app.domain.services.graph import GraphService, RiskAnalysisService
from app.infrastructure.persistence_age import GraphRepositoryAge
from app.infrastructure.external_data.defillama import DeFiLlamaClient
from app.infrastructure.embeddings import OpenAIEmbeddingService
from app.infrastructure.persistence_sqla.repositories.vector_repository_sqla import VectorRepositorySqla
from app.application.graph import (
    PopulateGraphInteractor,
    ValidateGraphInteractor,
    GraphAnalyticsInteractor,
    GenerateEmbeddingsInteractor,
    HybridRetrievalInteractor,
)


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
