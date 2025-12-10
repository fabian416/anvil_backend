"""
Network Analysis API Endpoints

Advanced graph algorithms for DeFi ecosystem analysis.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, status, Security, Query
from dishka.integrations.fastapi import FromDishka, inject
from uuid import UUID

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.controllers.ml.schemas import (
    PageRankListResponse,
    PageRankResponse,
    CommunityListResponse,
    CommunityResponse,
    CentralityListResponse,
    CentralityResponse,
    ContagionSimulationResponse,
)
from app.application.ml import (
    CalculatePageRankInteractor,
    DetectCommunitiesInteractor,
    CalculateCentralityInteractor,
    SimulateContagionInteractor,
)

router = APIRouter(prefix="/ml/network", tags=["Network Analysis"])


@router.get(
    "/pagerank",
    response_model=PageRankListResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate PageRank",
    description="Calculate PageRank importance scores for all protocols",
)
@inject
async def calculate_pagerank(
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[CalculatePageRankInteractor],
    damping_factor: float = Query(0.85, ge=0.0, le=1.0, description="Damping factor"),
    max_iterations: int = Query(100, ge=10, le=500, description="Max iterations"),
) -> PageRankListResponse:
    """Calculate PageRank for protocols"""
    
    results = await interactor.execute(
        damping_factor=damping_factor,
        max_iterations=max_iterations,
    )
    
    return PageRankListResponse(
        results=[
            PageRankResponse(
                protocol_id=str(r.protocol_id),
                protocol_name=r.protocol_name,
                pagerank_score=r.pagerank_score,
                rank=r.rank,
                in_degree=r.in_degree,
                out_degree=r.out_degree,
            )
            for r in results
        ],
        total=len(results),
    )


@router.get(
    "/communities",
    response_model=CommunityListResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect communities",
    description="Detect communities (clusters) in the protocol network",
)
@inject
async def detect_communities(
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[DetectCommunitiesInteractor],
    algorithm: str = Query("label_propagation", description="Detection algorithm"),
) -> CommunityListResponse:
    """Detect protocol communities"""
    
    communities = await interactor.execute(algorithm=algorithm)
    
    return CommunityListResponse(
        communities=[
            CommunityResponse(
                community_id=c.community_id,
                protocols=c.protocols,
                size=c.size,
                density=c.density,
                description=c.description,
            )
            for c in communities
        ],
        total_communities=len(communities),
    )


@router.get(
    "/centrality",
    response_model=CentralityListResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate centrality",
    description="Calculate centrality metrics for protocols (degree, betweenness, closeness, eigenvector)",
)
@inject
async def calculate_centrality(
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[CalculateCentralityInteractor],
    protocol_id: Optional[UUID] = Query(None, description="Specific protocol (optional)"),
) -> CentralityListResponse:
    """Calculate centrality metrics"""
    
    results = await interactor.execute(protocol_id=protocol_id)
    
    return CentralityListResponse(
        results=[
            CentralityResponse(
                protocol_id=str(r.protocol_id),
                protocol_name=r.protocol_name,
                degree_centrality=r.degree_centrality,
                betweenness_centrality=r.betweenness_centrality,
                closeness_centrality=r.closeness_centrality,
                eigenvector_centrality=r.eigenvector_centrality,
                importance_score=r.importance_score,
            )
            for r in results
        ],
        total=len(results),
    )


@router.get(
    "/contagion/{protocol_id}",
    response_model=ContagionSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate contagion",
    description="Simulate cascade risk from protocol failure using network propagation",
)
@inject
async def simulate_contagion(
    protocol_id: UUID,
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[SimulateContagionInteractor],
    propagation_probability: float = Query(0.8, ge=0.0, le=1.0, description="Cascade probability"),
    max_depth: int = Query(5, ge=1, le=10, description="Max cascade depth"),
) -> ContagionSimulationResponse:
    """Simulate contagion cascade"""
    
    result = await interactor.execute(
        origin_protocol_id=protocol_id,
        propagation_probability=propagation_probability,
        max_depth=max_depth,
    )
    
    return ContagionSimulationResponse(
        origin_protocol_id=str(result.origin_protocol_id),
        origin_protocol_name=result.origin_protocol_name,
        affected_protocols=result.affected_protocols,
        cascade_depth=result.cascade_depth,
        total_affected=result.total_affected,
        total_tvl_at_risk=result.total_tvl_at_risk,
        risk_score=result.risk_score,
    )
