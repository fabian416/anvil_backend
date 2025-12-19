"""
Graph Search Controllers

HTTP endpoints for GraphRAG hybrid search.
"""

from typing import Annotated
from fastapi import APIRouter, Security, status
from dishka.integrations.fastapi import FromDishka, inject
import logging

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.graph import HybridRetrievalInteractor
from app.infrastructure.cache.graph_cache import GraphQueryCache
from .schemas import (
    HybridSearchRequest,
    HybridSearchResponse,
    HybridSearchResult,
    SimilarProtocolsRequest,
    SimilarProtocolsResponse,
    ContextualSearchRequest,
    ContextualSearchResponse,
    ProtocolContext,
    RiskInfo,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/user/graph/search", tags=["Graph Search"])


@router.post(
    "/hybrid",
    response_model=HybridSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Hybrid search protocols",
    description="Search protocols using hybrid retrieval (vector + graph)",
)
@inject
async def hybrid_search(
    request: HybridSearchRequest,
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[HybridRetrievalInteractor],
) -> HybridSearchResponse:
    """
    Perform hybrid search combining vector similarity and graph context.
    
    This endpoint provides:
    - Semantic search via embeddings
    - Graph importance scoring
    - Rich context from knowledge graph
    - Risk analysis (optional)
    - Dependency information (optional)
    
    Example:
    ```json
    {
        "query": "decentralized lending protocol",
        "limit": 10,
        "include_risks": true,
        "include_dependencies": true,
        "similarity_threshold": 0.5
    }
    ```
    """
    
    # Execute search
    results = await interactor.search_protocols(
        query=request.query,
        limit=request.limit,
        include_risks=request.include_risks,
        include_dependencies=request.include_dependencies,
        similarity_threshold=request.similarity_threshold,
    )
    
    # Convert to response format
    search_results = []
    for result in results:
        # Build context
        context = ProtocolContext(
            tvl=result.context.get("tvl", 0),
            category=result.context.get("category", "Unknown"),
            dependent_count=result.context.get("dependent_count", 0),
            degree=result.context.get("degree", 0),
            audit_count=result.context.get("audit_count", 0),
            chain_count=result.context.get("chain_count", 0),
            dependencies=result.context.get("dependencies"),
        )
        
        # Build risk info
        risk_info = None
        if result.risk_info:
            risk_info = RiskInfo(
                risk_score=result.risk_info["risk_score"],
                direct_risks=result.risk_info["direct_risks"],
                systemic_risks=result.risk_info["systemic_risks"],
                top_recommendation=result.risk_info.get("top_recommendation"),
            )
        
        search_results.append(HybridSearchResult(
            protocol_id=result.protocol_id,
            protocol_name=result.protocol_name,
            score=result.score,
            vector_similarity=result.vector_similarity,
            graph_importance=result.graph_importance,
            context=context,
            risk_info=risk_info,
        ))
    
    return HybridSearchResponse(
        query=request.query,
        results=search_results,
        total=len(search_results),
        metadata={
            "include_risks": request.include_risks,
            "include_dependencies": request.include_dependencies,
            "similarity_threshold": request.similarity_threshold,
        },
    )


@router.post(
    "/similar",
    response_model=SimilarProtocolsResponse,
    status_code=status.HTTP_200_OK,
    summary="Find similar protocols",
    description="Find protocols similar to a reference protocol",
)
@inject
async def find_similar_protocols(
    request: SimilarProtocolsRequest,
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[HybridRetrievalInteractor],
) -> SimilarProtocolsResponse:
    """
    Find protocols similar to a reference protocol.
    
    Uses the reference protocol's embedding to find semantically similar protocols,
    then enriches with graph context.
    
    Example:
    ```json
    {
        "protocol_id": "123e4567-e89b-12d3-a456-426614174000",
        "limit": 10
    }
    ```
    """
    
    # Execute search
    results = await interactor.find_similar_protocols(
        protocol_id=request.protocol_id,
        limit=request.limit,
    )
    
    # Convert to response format
    search_results = []
    for result in results:
        context = ProtocolContext(
            tvl=result.context.get("tvl", 0),
            category=result.context.get("category", "Unknown"),
            dependent_count=result.context.get("dependent_count", 0),
            degree=result.context.get("degree", 0),
            audit_count=result.context.get("audit_count", 0),
            chain_count=result.context.get("chain_count", 0),
        )
        
        risk_info = None
        if result.risk_info:
            risk_info = RiskInfo(
                risk_score=result.risk_info["risk_score"],
                direct_risks=result.risk_info["direct_risks"],
                systemic_risks=result.risk_info["systemic_risks"],
                top_recommendation=result.risk_info.get("top_recommendation"),
            )
        
        search_results.append(HybridSearchResult(
            protocol_id=result.protocol_id,
            protocol_name=result.protocol_name,
            score=result.score,
            vector_similarity=result.vector_similarity,
            graph_importance=result.graph_importance,
            context=context,
            risk_info=risk_info,
        ))
    
    return SimilarProtocolsResponse(
        reference_protocol_id=request.protocol_id,
        results=search_results,
        total=len(search_results),
    )


@router.post(
    "/contextual",
    response_model=ContextualSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Contextual protocol search",
    description="Search with user preferences and context",
)
@inject
async def contextual_search(
    request: ContextualSearchRequest,
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[HybridRetrievalInteractor],
) -> ContextualSearchResponse:
    """
    Contextual search with user preference filtering.
    
    Combines semantic search with user preferences:
    - Category filtering
    - Risk tolerance
    - Minimum TVL
    
    Example:
    ```json
    {
        "query": "safe lending protocol",
        "preferences": {
            "category": "Lending",
            "max_risk_score": 5.0,
            "min_tvl": 1000000000
        },
        "limit": 5
    }
    ```
    """
    
    # Convert preferences to dict
    preferences = None
    if request.preferences:
        preferences = request.preferences.model_dump(exclude_none=True)
    
    # Execute search
    results = await interactor.get_contextual_protocols(
        query=request.query,
        user_preferences=preferences,
        limit=request.limit,
    )
    
    # Convert to response format
    search_results = []
    for result in results:
        context = ProtocolContext(
            tvl=result.context.get("tvl", 0),
            category=result.context.get("category", "Unknown"),
            dependent_count=result.context.get("dependent_count", 0),
            degree=result.context.get("degree", 0),
            audit_count=result.context.get("audit_count", 0),
            chain_count=result.context.get("chain_count", 0),
            dependencies=result.context.get("dependencies"),
        )
        
        risk_info = None
        if result.risk_info:
            risk_info = RiskInfo(
                risk_score=result.risk_info["risk_score"],
                direct_risks=result.risk_info["direct_risks"],
                systemic_risks=result.risk_info["systemic_risks"],
                top_recommendation=result.risk_info.get("top_recommendation"),
            )
        
        search_results.append(HybridSearchResult(
            protocol_id=result.protocol_id,
            protocol_name=result.protocol_name,
            score=result.score,
            vector_similarity=result.vector_similarity,
            graph_importance=result.graph_importance,
            context=context,
            risk_info=risk_info,
        ))
    
    return ContextualSearchResponse(
        query=request.query,
        preferences=request.preferences,
        results=search_results,
        total=len(search_results),
    )
