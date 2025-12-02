"""
Graph IoC Provider

Dependency injection configuration for graph-related components.
"""

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ports.graph import GraphRepository
from app.domain.services.graph import GraphService, RiskAnalysisService
from app.infrastructure.persistence_age import GraphRepositoryAge


class GraphProvider(Provider):
    """
    Dishka provider for graph components.
    
    Registers:
    - GraphRepository implementation (Apache AGE)
    - GraphService
    - RiskAnalysisService
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
