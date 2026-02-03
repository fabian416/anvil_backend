"""
Graph API Schemas

Request/Response models for GraphRAG endpoints.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# Search Request/Response
class HybridSearchRequest(BaseModel):
    """Request for hybrid search"""

    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    limit: int = Field(10, description="Maximum results", ge=1, le=50)
    include_risks: bool = Field(True, description="Include risk analysis")
    include_dependencies: bool = Field(True, description="Include dependency info")
    similarity_threshold: float = Field(
        0.5, description="Minimum similarity", ge=0.0, le=1.0
    )


class ProtocolContext(BaseModel):
    """Protocol context information"""

    tvl: float
    category: str
    dependent_count: int
    degree: int
    audit_count: int
    chain_count: int
    dependencies: Optional[Dict[str, List[str]]] = None


class RiskInfo(BaseModel):
    """Risk information"""

    risk_score: float
    direct_risks: int
    systemic_risks: int
    top_recommendation: Optional[str]


class HybridSearchResult(BaseModel):
    """Single search result"""

    protocol_id: UUID
    protocol_name: str
    score: float
    vector_similarity: float
    graph_importance: float
    context: ProtocolContext
    risk_info: Optional[RiskInfo]


class HybridSearchResponse(BaseModel):
    """Response for hybrid search"""

    query: str
    results: List[HybridSearchResult]
    total: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Similar Protocols Request/Response
class SimilarProtocolsRequest(BaseModel):
    """Request for similar protocols"""

    protocol_id: UUID = Field(..., description="Reference protocol ID")
    limit: int = Field(10, description="Maximum results", ge=1, le=50)


class SimilarProtocolsResponse(BaseModel):
    """Response for similar protocols"""

    reference_protocol_id: UUID
    results: List[HybridSearchResult]
    total: int


# Contextual Search Request/Response
class UserPreferences(BaseModel):
    """User preferences for filtering"""

    category: Optional[str] = None
    max_risk_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    min_tvl: Optional[float] = Field(None, ge=0.0)


class ContextualSearchRequest(BaseModel):
    """Request for contextual search"""

    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    preferences: Optional[UserPreferences] = None
    limit: int = Field(5, description="Maximum results", ge=1, le=20)


class ContextualSearchResponse(BaseModel):
    """Response for contextual search"""

    query: str
    preferences: Optional[UserPreferences]
    results: List[HybridSearchResult]
    total: int


# Graph Analytics Response
class GraphOverviewStats(BaseModel):
    """Graph overview statistics"""

    timestamp: str
    nodes: Dict[str, int]
    edges: Dict[str, int]
    health: Dict[str, float]


class TopProtocol(BaseModel):
    """Top protocol info"""

    name: str
    slug: str
    tvl: float
    category: str
    change_24h: float


class GraphAnalyticsResponse(BaseModel):
    """Response for graph analytics"""

    overview: GraphOverviewStats
    top_protocols: List[TopProtocol]
    category_distribution: Dict[str, int]
    chain_distribution: Dict[str, int]


# Embedding Generation Response
class EmbeddingGenerationRequest(BaseModel):
    """Request for embedding generation"""

    limit: Optional[int] = Field(None, description="Maximum protocols to process")
    force_regenerate: bool = Field(False, description="Force regenerate existing")


class EmbeddingGenerationResponse(BaseModel):
    """Response for embedding generation"""

    protocols_fetched: int
    embeddings_generated: int
    embeddings_skipped: int
    errors: int


# Graph Validation Response
class ValidationIssue(BaseModel):
    """Validation issue"""

    count: int
    issues: List[Dict[str, Any]]
    severity: str
    message: str


class GraphValidationResponse(BaseModel):
    """Response for graph validation"""

    timestamp: str
    checks: Dict[str, ValidationIssue]
    total_issues: int
    is_valid: bool
