"""
Chat performance value objects.

Enterprise-grade performance optimization with semantic caching,
prefetching, and offline support.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, UTC
from enum import Enum
from uuid import UUID


class CacheStrategy(Enum):
    """Caching strategies."""

    EXACT_MATCH = "exact_match"  # Exact query match
    SEMANTIC_SIMILARITY = "semantic_similarity"  # Similar queries
    CONVERSATION_CONTEXT = "conversation_context"  # Full conversation context
    AGENT_RESPONSE = "agent_response"  # Agent-specific responses
    HYBRID = "hybrid"  # Combination of strategies


class PrefetchPriority(Enum):
    """Priority levels for prefetching."""

    CRITICAL = "critical"  # User is likely to need this immediately
    HIGH = "high"  # High probability of use
    MEDIUM = "medium"  # Moderate probability
    LOW = "low"  # Low probability but worth caching
    BACKGROUND = "background"  # Prefetch during idle time


class PerformanceBudgetStatus(Enum):
    """Performance budget status."""

    EXCELLENT = "excellent"  # Well within budget
    GOOD = "good"  # Within budget
    WARNING = "warning"  # Approaching budget limits
    CRITICAL = "critical"  # Exceeding budget
    VIOLATED = "violated"  # Significantly exceeding budget


@dataclass(frozen=True)
class CacheEntry:
    """Cached query-response pair with metadata."""

    cache_key: str
    query: str
    response: str
    agent_name: str
    conversation_context_hash: Optional[str] = None
    embedding: Optional[List[float]] = None  # For semantic similarity
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ttl_seconds: int = 3600  # 1 hour default
    similarity_threshold: float = 0.85  # For semantic matching

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now(UTC) > expiry_time

    def is_semantically_similar(self, query_embedding: List[float], threshold: Optional[float] = None) -> bool:
        """Check if query is semantically similar to cached query."""
        if not self.embedding or not query_embedding:
            return False

        threshold = threshold or self.similarity_threshold

        # Cosine similarity calculation
        dot_product = sum(a * b for a, b in zip(self.embedding, query_embedding))
        mag_a = sum(a * a for a in self.embedding) ** 0.5
        mag_b = sum(b * b for b in query_embedding) ** 0.5

        if mag_a == 0 or mag_b == 0:
            return False

        similarity = dot_product / (mag_a * mag_b)
        return similarity >= threshold

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "cache_key": self.cache_key,
            "query": self.query,
            "response": self.response,
            "agent_name": self.agent_name,
            "conversation_context_hash": self.conversation_context_hash,
            "hit_count": self.hit_count,
            "last_accessed": self.last_accessed.isoformat(),
            "created_at": self.created_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "is_expired": self.is_expired(),
        }


@dataclass(frozen=True)
class CacheStatistics:
    """Cache performance statistics."""

    total_queries: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    avg_response_time_ms_cached: float
    avg_response_time_ms_uncached: float
    time_saved_ms: float
    cost_saved_usd: float
    memory_usage_mb: float
    eviction_count: int

    @classmethod
    def calculate(
        cls,
        total_queries: int,
        cache_hits: int,
        cache_misses: int,
        avg_cached_time: float,
        avg_uncached_time: float,
        cost_per_query_usd: float,
        memory_usage_mb: float,
        eviction_count: int,
    ) -> "CacheStatistics":
        """Calculate cache statistics."""
        hit_rate = cache_hits / max(total_queries, 1)
        time_saved = (avg_uncached_time - avg_cached_time) * cache_hits
        cost_saved = cost_per_query_usd * cache_hits

        return cls(
            total_queries=total_queries,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate=hit_rate,
            avg_response_time_ms_cached=avg_cached_time,
            avg_response_time_ms_uncached=avg_uncached_time,
            time_saved_ms=time_saved,
            cost_saved_usd=cost_saved,
            memory_usage_mb=memory_usage_mb,
            eviction_count=eviction_count,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.hit_rate,
            "avg_response_time_ms_cached": self.avg_response_time_ms_cached,
            "avg_response_time_ms_uncached": self.avg_response_time_ms_uncached,
            "time_saved_ms": self.time_saved_ms,
            "cost_saved_usd": self.cost_saved_usd,
            "memory_usage_mb": self.memory_usage_mb,
            "eviction_count": self.eviction_count,
        }


@dataclass(frozen=True)
class PrefetchPrediction:
    """Prediction for prefetching agent responses."""

    agent_name: str
    predicted_query: str
    confidence: float  # 0.0 to 1.0
    priority: PrefetchPriority
    reasoning: str
    estimated_response_time_ms: int
    estimated_cost_usd: float
    suggested_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def should_prefetch(self, confidence_threshold: float = 0.7) -> bool:
        """Determine if prefetching is worthwhile."""
        if self.confidence < confidence_threshold:
            return False

        # Don't prefetch low-confidence, expensive queries
        if self.confidence < 0.8 and self.estimated_cost_usd > 0.05:
            return False

        return True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "predicted_query": self.predicted_query,
            "confidence": self.confidence,
            "priority": self.priority.value,
            "reasoning": self.reasoning,
            "estimated_response_time_ms": self.estimated_response_time_ms,
            "estimated_cost_usd": self.estimated_cost_usd,
            "suggested_at": self.suggested_at.isoformat(),
            "should_prefetch": self.should_prefetch(),
        }


@dataclass
class OfflineQueueEntry:
    """Message queued for sending when connection is restored."""

    id: UUID
    user_id: UUID
    conversation_id: UUID
    message: str
    agent_name: Optional[str]
    created_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0  # Higher = more important
    metadata: Dict[str, Any] = field(default_factory=dict)

    def can_retry(self) -> bool:
        """Check if entry can be retried."""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "conversation_id": str(self.conversation_id),
            "message": self.message,
            "agent_name": self.agent_name,
            "created_at": self.created_at.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "priority": self.priority,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PerformanceBudget:
    """Performance budget constraints."""

    max_response_time_ms: int
    max_llm_cost_per_query_usd: float
    max_cache_memory_mb: int
    max_prefetch_cost_per_hour_usd: float
    max_concurrent_agents: int
    target_cache_hit_rate: float

    def check_response_time(self, actual_ms: int) -> PerformanceBudgetStatus:
        """Check response time against budget."""
        ratio = actual_ms / self.max_response_time_ms

        if ratio <= 0.5:
            return PerformanceBudgetStatus.EXCELLENT
        elif ratio <= 0.8:
            return PerformanceBudgetStatus.GOOD
        elif ratio <= 1.0:
            return PerformanceBudgetStatus.WARNING
        elif ratio <= 1.5:
            return PerformanceBudgetStatus.CRITICAL
        else:
            return PerformanceBudgetStatus.VIOLATED

    def check_cost(self, actual_cost_usd: float) -> PerformanceBudgetStatus:
        """Check cost against budget."""
        ratio = actual_cost_usd / self.max_llm_cost_per_query_usd

        if ratio <= 0.5:
            return PerformanceBudgetStatus.EXCELLENT
        elif ratio <= 0.8:
            return PerformanceBudgetStatus.GOOD
        elif ratio <= 1.0:
            return PerformanceBudgetStatus.WARNING
        elif ratio <= 1.5:
            return PerformanceBudgetStatus.CRITICAL
        else:
            return PerformanceBudgetStatus.VIOLATED

    def check_cache_hit_rate(self, actual_rate: float) -> PerformanceBudgetStatus:
        """Check cache hit rate against target."""
        ratio = actual_rate / self.target_cache_hit_rate

        if ratio >= 1.2:
            return PerformanceBudgetStatus.EXCELLENT
        elif ratio >= 1.0:
            return PerformanceBudgetStatus.GOOD
        elif ratio >= 0.8:
            return PerformanceBudgetStatus.WARNING
        elif ratio >= 0.5:
            return PerformanceBudgetStatus.CRITICAL
        else:
            return PerformanceBudgetStatus.VIOLATED

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "max_response_time_ms": self.max_response_time_ms,
            "max_llm_cost_per_query_usd": self.max_llm_cost_per_query_usd,
            "max_cache_memory_mb": self.max_cache_memory_mb,
            "max_prefetch_cost_per_hour_usd": self.max_prefetch_cost_per_hour_usd,
            "max_concurrent_agents": self.max_concurrent_agents,
            "target_cache_hit_rate": self.target_cache_hit_rate,
        }


@dataclass(frozen=True)
class PerformanceAlert:
    """Performance budget violation alert."""

    alert_type: str  # "response_time", "cost", "cache_hit_rate", "memory"
    status: PerformanceBudgetStatus
    metric_name: str
    actual_value: float
    budget_value: float
    threshold_exceeded_by: float
    timestamp: datetime
    recommendation: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "alert_type": self.alert_type,
            "status": self.status.value,
            "metric_name": self.metric_name,
            "actual_value": self.actual_value,
            "budget_value": self.budget_value,
            "threshold_exceeded_by": self.threshold_exceeded_by,
            "timestamp": self.timestamp.isoformat(),
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True)
class LLMProviderFailover:
    """Failover configuration for LLM providers."""

    primary_provider: str
    secondary_providers: List[str]
    max_retry_attempts: int = 3
    timeout_seconds: int = 30
    fallback_delay_seconds: int = 2

    def get_provider_sequence(self) -> List[str]:
        """Get ordered list of providers to try."""
        return [self.primary_provider] + self.secondary_providers

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "primary_provider": self.primary_provider,
            "secondary_providers": self.secondary_providers,
            "max_retry_attempts": self.max_retry_attempts,
            "timeout_seconds": self.timeout_seconds,
            "fallback_delay_seconds": self.fallback_delay_seconds,
        }


@dataclass(frozen=True)
class CDNConfiguration:
    """CDN configuration for global low-latency."""

    enabled: bool
    cdn_provider: str  # "cloudflare", "fastly", "akamai", "aws_cloudfront"
    cache_static_assets: bool
    cache_api_responses: bool
    edge_locations: List[str]  # Geographic regions
    cache_ttl_seconds: int
    purge_on_deploy: bool

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "cdn_provider": self.cdn_provider,
            "cache_static_assets": self.cache_static_assets,
            "cache_api_responses": self.cache_api_responses,
            "edge_locations": self.edge_locations,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "purge_on_deploy": self.purge_on_deploy,
        }
