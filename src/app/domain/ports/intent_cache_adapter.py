"""
Intent cache adapter port.

Domain-defined interface for caching intent detection results with
semantic similarity matching and auto-suggestion support.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import timedelta

from app.domain.value_objects.chat.intent_prediction import IntentPrediction
from app.domain.value_objects.chat.agent_suggestion import AutocompleteSuggestion


class IntentCacheAdapter(ABC):
    """
    Port for intent detection caching.

    Provides semantic caching of intent detection results to reduce
    LLM API calls and improve response times. Supports:
    - Query pattern -> Intent caching
    - Auto-suggestions based on partial inputs
    - Entity extraction caching (protocols, tokens, amounts)
    - Semantic similarity matching for cache hits
    """

    @abstractmethod
    async def get_intent(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        similarity_threshold: float = 0.90,
    ) -> Optional[IntentPrediction]:
        """
        Get cached intent prediction for a query.

        Uses semantic similarity if embedding is provided, otherwise
        falls back to exact match.

        Args:
            query: User query text
            query_embedding: Optional embedding for semantic matching
            similarity_threshold: Minimum similarity for semantic match (0.0-1.0)

        Returns:
            IntentPrediction if found, None otherwise
        """
        pass

    @abstractmethod
    async def set_intent(
        self,
        query: str,
        intent: IntentPrediction,
        query_embedding: Optional[List[float]] = None,
        ttl: Optional[timedelta] = None,
    ) -> bool:
        """
        Cache intent prediction for a query.

        Args:
            query: User query text
            intent: Predicted intent to cache
            query_embedding: Optional embedding for semantic matching
            ttl: Time-to-live (default: 24 hours)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_suggestions(
        self,
        partial_input: str,
        limit: int = 5,
    ) -> List[AutocompleteSuggestion]:
        """
        Get auto-complete suggestions based on partial input.

        Returns cached query patterns and common intents that match
        the partial input.

        Args:
            partial_input: Partial user input (e.g., "show my port")
            limit: Maximum number of suggestions

        Returns:
            List of autocomplete suggestions
        """
        pass

    @abstractmethod
    async def get_entity_suggestions(
        self,
        entity_type: str,
        partial_value: str,
        limit: int = 10,
    ) -> List[str]:
        """
        Get cached entity value suggestions.

        Provides autocomplete for common entities like protocols,
        tokens, wallet addresses, etc.

        Args:
            entity_type: Type of entity ("protocol", "token", "amount", etc.)
            partial_value: Partial entity value
            limit: Maximum number of suggestions

        Returns:
            List of matching entity values
        """
        pass

    @abstractmethod
    async def cache_entity(
        self,
        entity_type: str,
        entity_value: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Cache an extracted entity for future suggestions.

        Args:
            entity_type: Type of entity
            entity_value: Entity value
            metadata: Optional metadata about the entity

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def find_similar_queries(
        self,
        query_embedding: List[float],
        intent_type: Optional[str] = None,
        threshold: float = 0.85,
        limit: int = 10,
    ) -> List[tuple[str, IntentPrediction, float]]:
        """
        Find semantically similar cached queries.

        Args:
            query_embedding: Query embedding vector
            intent_type: Optional filter by intent type
            threshold: Similarity threshold (0.0 to 1.0)
            limit: Maximum number of results

        Returns:
            List of (query, intent, similarity_score) tuples
        """
        pass

    @abstractmethod
    async def warm_cache(
        self,
        common_patterns: List[tuple[str, IntentPrediction]],
    ) -> int:
        """
        Warm cache with common query patterns.

        Pre-populates cache with frequently asked queries to
        improve initial performance.

        Args:
            common_patterns: List of (query, intent) tuples

        Returns:
            Number of patterns cached
        """
        pass

    @abstractmethod
    async def get_cache_stats(self) -> dict:
        """
        Get cache performance statistics.

        Returns:
            Dictionary with cache statistics (hits, misses, hit_rate, etc.)
        """
        pass

    @abstractmethod
    async def clear_intent_cache(self, intent_type: Optional[str] = None) -> int:
        """
        Clear cached intents.

        Args:
            intent_type: Optional filter to clear specific intent type only

        Returns:
            Number of entries cleared
        """
        pass

    @abstractmethod
    async def increment_hit_count(self, query: str) -> int:
        """
        Increment cache hit counter for a query.

        Args:
            query: Query text

        Returns:
            New hit count
        """
        pass
