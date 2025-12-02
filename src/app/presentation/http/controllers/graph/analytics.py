"""
Graph Analytics Controllers

HTTP endpoints for graph statistics and insights.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, Security, status
from dishka.integrations.fastapi import FromDishka

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.graph import (
    GraphAnalyticsInteractor,
    ValidateGraphInteractor,
    GenerateEmbeddingsInteractor,
)
from .schemas import (
    GraphAnalyticsResponse,
    GraphOverviewStats,
    TopProtocol,
    GraphValidationResponse,
    ValidationIssue,
    EmbeddingGenerationRequest,
    EmbeddingGenerationResponse,
)


router = APIRouter(prefix="/graph/analytics", tags=["Graph Analytics"])


@router.get(
    "/overview",
    response_model=GraphAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get graph analytics",
    description="Get comprehensive graph statistics and insights",
)
async def get_graph_analytics(
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[GraphAnalyticsInteractor],
) -> GraphAnalyticsResponse:
    """
    Get comprehensive graph analytics.
    
    Provides:
    - Overview statistics (node/edge counts)
    - Top protocols by TVL
    - Category distribution
    - Chain distribution
    - Health metrics
    """
    
    # Get overview stats
    overview = await interactor.get_overview_stats()
    
    # Get top protocols
    top_protocols_data = await interactor.get_top_protocols(limit=10)
    top_protocols = [
        TopProtocol(
            name=p["name"],
            slug=p["slug"],
            tvl=p["tvl"],
            category=p["category"],
            change_24h=p["change_24h"],
        )
        for p in top_protocols_data
    ]
    
    # Get distributions
    category_dist = await interactor.get_category_distribution()
    chain_dist = await interactor.get_chain_distribution()
    
    return GraphAnalyticsResponse(
        overview=GraphOverviewStats(**overview),
        top_protocols=top_protocols,
        category_distribution=category_dist,
        chain_distribution=chain_dist,
    )


@router.post(
    "/validate",
    response_model=GraphValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate graph integrity",
    description="Run validation checks on the knowledge graph",
)
async def validate_graph(
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[ValidateGraphInteractor],
) -> GraphValidationResponse:
    """
    Validate graph integrity.
    
    Runs checks for:
    - Orphaned nodes (no relationships)
    - Circular dependencies
    - Missing required properties
    - Duplicate protocols
    - Invalid relationships
    """
    
    report = await interactor.validate_all()
    
    # Convert to response format
    checks = {}
    for check_name, check_result in report["checks"].items():
        checks[check_name] = ValidationIssue(**check_result)
    
    return GraphValidationResponse(
        timestamp=report["timestamp"],
        checks=checks,
        total_issues=report["total_issues"],
        is_valid=report["is_valid"],
    )


@router.post(
    "/embeddings/generate",
    response_model=EmbeddingGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate embeddings",
    description="Generate embeddings for protocols (admin only)",
)
async def generate_embeddings(
    request: EmbeddingGenerationRequest,
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[GenerateEmbeddingsInteractor],
) -> EmbeddingGenerationResponse:
    """
    Generate embeddings for protocols.
    
    This endpoint triggers embedding generation for protocols.
    Embeddings are used for semantic search in hybrid retrieval.
    
    Note: This can be a long-running operation.
    Consider running as a background task for production.
    
    Example:
    ```json
    {
        "limit": 100,
        "force_regenerate": false
    }
    ```
    """
    
    stats = await interactor.generate_protocol_embeddings(
        limit=request.limit,
        force_regenerate=request.force_regenerate,
    )
    
    return EmbeddingGenerationResponse(**stats)
