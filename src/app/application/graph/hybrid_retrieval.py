"""
Hybrid Retrieval Interactor

Combines vector similarity search with graph traversal for powerful context retrieval.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from uuid import UUID
import logging

from app.domain.graph.ports import GraphRepository, TraversalDirection
from app.domain.ports.embeddings import EmbeddingService
from app.domain.ports.vector import VectorRepository, SimilarityResult
from app.domain.graph.services import GraphService, RiskAnalysisService


logger = logging.getLogger(__name__)


@dataclass
class HybridRetrievalResult:
    """Result of hybrid retrieval"""
    protocol_id: UUID
    protocol_name: str
    score: float  # Combined score
    vector_similarity: float
    graph_importance: float
    context: Dict[str, Any]  # Rich context from graph
    risk_info: Optional[Dict[str, Any]] = None


class HybridRetrievalInteractor:
    """
    Hybrid retrieval: Vector similarity + Graph context.
    
    Workflow:
    1. Embed query text
    2. Find similar protocols (vector search)
    3. Enrich with graph context (dependencies, risks, etc.)
    4. Re-rank by combined score
    5. Return enriched results
    """
    
    def __init__(
        self,
        graph_repo: GraphRepository,
        embedding_service: EmbeddingService,
        vector_repo: VectorRepository,
        graph_service: GraphService,
        risk_service: RiskAnalysisService,
    ):
        """
        Initialize hybrid retrieval.
        
        Args:
            graph_repo: Graph repository
            embedding_service: Embedding service
            vector_repo: Vector repository
            graph_service: Graph service
            risk_service: Risk analysis service
        """
        self._graph_repo = graph_repo
        self._embedding_service = embedding_service
        self._vector_repo = vector_repo
        self._graph_service = graph_service
        self._risk_service = risk_service
    
    async def search_protocols(
        self,
        query: str,
        limit: int = 10,
        include_risks: bool = True,
        include_dependencies: bool = True,
        similarity_threshold: float = 0.5,
    ) -> List[HybridRetrievalResult]:
        """
        Search protocols using hybrid retrieval.
        
        Args:
            query: Search query
            limit: Maximum results
            include_risks: Include risk analysis
            include_dependencies: Include dependency info
            similarity_threshold: Minimum similarity
            
        Returns:
            List of enriched results
        """
        
        logger.info(f"Hybrid search: '{query}' (limit={limit})")
        
        # Step 1: Embed query
        query_embedding = await self._embedding_service.embed_text(query)
        
        # Step 2: Vector similarity search
        similar_results = await self._vector_repo.find_similar(
            query_embedding=query_embedding,
            entity_type="Protocol",
            limit=limit * 2,  # Fetch more for re-ranking
            similarity_threshold=similarity_threshold,
        )
        
        logger.info(f"Found {len(similar_results)} similar protocols")
        
        # Step 3: Enrich with graph context
        enriched_results = []
        
        for result in similar_results:
            try:
                enriched = await self._enrich_result(
                    result,
                    include_risks=include_risks,
                    include_dependencies=include_dependencies,
                )
                enriched_results.append(enriched)
            except Exception as e:
                logger.error(f"Error enriching result {result.document.entity_id}: {e}")
        
        # Step 4: Re-rank by combined score
        enriched_results.sort(key=lambda x: x.score, reverse=True)
        
        # Step 5: Return top results
        return enriched_results[:limit]
    
    async def _enrich_result(
        self,
        similarity_result: SimilarityResult,
        include_risks: bool,
        include_dependencies: bool,
    ) -> HybridRetrievalResult:
        """Enrich a similarity result with graph context"""
        
        protocol_id = similarity_result.document.entity_id
        protocol_name = similarity_result.document.entity_name
        vector_similarity = similarity_result.similarity
        
        # Get graph importance
        importance_info = await self._graph_service.calculate_protocol_importance(
            protocol_id=protocol_id
        )
        graph_importance = importance_info["score"] / 10.0  # Normalize to 0-1
        
        # Build context
        context = {
            "tvl": importance_info.get("tvl", 0),
            "category": importance_info.get("category", "Unknown"),
            "dependent_count": importance_info.get("dependent_count", 0),
            "degree": importance_info.get("degree", 0),
            "audit_count": importance_info.get("audit_count", 0),
            "chain_count": importance_info.get("chain_count", 0),
        }
        
        # Add dependencies if requested
        if include_dependencies:
            try:
                deps = await self._graph_service.get_protocol_dependencies(
                    protocol_id=protocol_id,
                    max_depth=2,
                )
                
                context["dependencies"] = {
                    "direct": [d.properties.get("name", "Unknown") for d in deps.direct],
                    "indirect": [d.properties.get("name", "Unknown") for d in deps.indirect],
                    "critical": [d.properties.get("name", "Unknown") for d in deps.critical],
                }
            except Exception as e:
                logger.warning(f"Could not fetch dependencies: {e}")
        
        # Add risk info if requested
        risk_info = None
        if include_risks:
            try:
                risk_analysis = await self._risk_service.analyze_systemic_risk(
                    protocol_id=protocol_id
                )
                
                risk_info = {
                    "risk_score": risk_analysis.risk_score,
                    "direct_risks": len(risk_analysis.direct_risks),
                    "systemic_risks": len(risk_analysis.systemic_risks),
                    "top_recommendation": (
                        risk_analysis.recommendations[0]
                        if risk_analysis.recommendations
                        else None
                    ),
                }
            except Exception as e:
                logger.warning(f"Could not fetch risk analysis: {e}")
        
        # Calculate combined score
        # Weight: 60% vector similarity, 40% graph importance
        combined_score = (vector_similarity * 0.6) + (graph_importance * 0.4)
        
        return HybridRetrievalResult(
            protocol_id=protocol_id,
            protocol_name=protocol_name,
            score=combined_score,
            vector_similarity=vector_similarity,
            graph_importance=graph_importance,
            context=context,
            risk_info=risk_info,
        )
    
    async def find_similar_protocols(
        self,
        protocol_id: UUID,
        limit: int = 10,
    ) -> List[HybridRetrievalResult]:
        """
        Find protocols similar to a given protocol.
        
        Args:
            protocol_id: Reference protocol
            limit: Maximum results
            
        Returns:
            List of similar protocols
        """
        
        logger.info(f"Finding similar protocols to {protocol_id}")
        
        # Get embedding of reference protocol
        embedding_doc = await self._vector_repo.get_embedding(protocol_id)
        
        if not embedding_doc:
            logger.warning(f"No embedding found for protocol {protocol_id}")
            return []
        
        # Use embedding to find similar
        similar_results = await self._vector_repo.find_similar(
            query_embedding=embedding_doc.embedding,
            entity_type="Protocol",
            limit=limit + 1,  # +1 because reference will be included
            similarity_threshold=0.3,  # Lower threshold for similar protocols
        )
        
        # Filter out the reference protocol itself
        similar_results = [
            r for r in similar_results
            if r.document.entity_id != protocol_id
        ][:limit]
        
        # Enrich results
        enriched = []
        for result in similar_results:
            try:
                enriched_result = await self._enrich_result(
                    result,
                    include_risks=True,
                    include_dependencies=False,
                )
                enriched.append(enriched_result)
            except Exception as e:
                logger.error(f"Error enriching result: {e}")
        
        return enriched
    
    async def get_contextual_protocols(
        self,
        query: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 5,
    ) -> List[HybridRetrievalResult]:
        """
        Get contextual protocol recommendations.
        
        Considers:
        - Query relevance (vector)
        - Graph importance
        - User preferences (category, risk tolerance)
        
        Args:
            query: User query
            user_preferences: User preferences for filtering
            limit: Maximum results
            
        Returns:
            Contextual recommendations
        """
        
        logger.info(f"Contextual search: '{query}'")
        
        # Perform hybrid search
        results = await self.search_protocols(
            query=query,
            limit=limit * 2,  # Fetch more for filtering
            include_risks=True,
            include_dependencies=True,
        )
        
        # Apply user preferences if provided
        if user_preferences:
            filtered_results = []
            
            preferred_category = user_preferences.get("category")
            max_risk_score = user_preferences.get("max_risk_score", 10.0)
            min_tvl = user_preferences.get("min_tvl", 0)
            
            for result in results:
                # Category filter
                if preferred_category:
                    if result.context.get("category") != preferred_category:
                        continue
                
                # Risk filter
                if result.risk_info:
                    if result.risk_info["risk_score"] > max_risk_score:
                        continue
                
                # TVL filter
                if result.context.get("tvl", 0) < min_tvl:
                    continue
                
                filtered_results.append(result)
            
            results = filtered_results
        
        # Return top results
        return results[:limit]
