"""
Performance optimization service for chat.

Implements smart caching, prefetching, offline mode, and performance monitoring
for enterprise-grade chat performance.
"""

import logging
import hashlib
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from app.domain.value_objects.chat.performance import (
    CacheEntry,
    CacheStrategy,
    CacheStatistics,
    PrefetchPrediction,
    PrefetchPriority,
    OfflineQueueEntry,
    PerformanceBudget,
    PerformanceBudgetStatus,
    PerformanceAlert,
    LLMProviderFailover,
)
from app.domain.entities.chat.message import Message
from app.domain.entities.chat.conversation import Conversation
from app.domain.ports.cache_adapter import CacheAdapter
from app.domain.ports.offline_queue_adapter import OfflineQueueAdapter
from app.domain.exceptions.chat import (
    CacheError,
    PerformanceBudgetViolation,
)

logger = logging.getLogger(__name__)


class PerformanceOptimizationService:
    """
    Comprehensive performance optimization for chat.

    Features:
    - Smart caching with semantic similarity
    - Predictive prefetching based on conversation patterns
    - Offline mode with message queuing
    - Performance budget monitoring and alerting
    - LLM provider failover
    - Cost and latency tracking
    """

    def __init__(
        self,
        cache_adapter: CacheAdapter,
        offline_queue_adapter: OfflineQueueAdapter,
        performance_budget: PerformanceBudget,
        llm_failover: LLMProviderFailover,
    ):
        """
        Initialize performance optimization service.

        Args:
            cache_adapter: Cache adapter for storing responses
            offline_queue_adapter: Queue adapter for offline messages
            performance_budget: Performance budget constraints
            llm_failover: Failover configuration for LLM providers
        """
        self._cache = cache_adapter
        self._offline_queue = offline_queue_adapter
        self._budget = performance_budget
        self._failover = llm_failover

        # Performance tracking
        self._query_count = 0
        self._total_response_time_ms = 0.0
        self._total_cost_usd = 0.0

    # ========== CACHING METHODS ==========

    async def get_cached_response(
        self,
        query: str,
        agent_name: str,
        conversation_context: Optional[List[Message]] = None,
        strategy: CacheStrategy = CacheStrategy.SEMANTIC_SIMILARITY,
    ) -> Optional[str]:
        """
        Get cached response for query.

        Args:
            query: User query
            agent_name: Agent to query
            conversation_context: Conversation context for context-aware caching
            strategy: Caching strategy to use

        Returns:
            Cached response or None if cache miss
        """
        try:
            # Generate cache key based on strategy
            cache_key = self._generate_cache_key(query, agent_name, conversation_context, strategy)

            # Exact match lookup
            cached = await self._cache.get(cache_key)
            if cached and not cached.is_expired():
                await self._cache.increment_hit_count(cache_key)
                logger.info(f"Cache HIT (exact): {agent_name} - {query[:50]}...")
                return cached.response

            # Semantic similarity search if enabled
            if strategy in [CacheStrategy.SEMANTIC_SIMILARITY, CacheStrategy.HYBRID]:
                similar_entries = await self._find_similar_cached_queries(
                    query, agent_name, conversation_context
                )
                if similar_entries:
                    best_match = similar_entries[0]
                    await self._cache.increment_hit_count(best_match.cache_key)
                    logger.info(
                        f"Cache HIT (semantic): {agent_name} - {query[:50]}... "
                        f"(similarity: {best_match.similarity_threshold:.2f})"
                    )
                    return best_match.response

            logger.info(f"Cache MISS: {agent_name} - {query[:50]}...")
            return None

        except Exception as e:
            logger.error(f"Cache lookup failed: {e}", exc_info=True)
            return None  # Fail gracefully

    async def cache_response(
        self,
        query: str,
        response: str,
        agent_name: str,
        conversation_context: Optional[List[Message]] = None,
        query_embedding: Optional[List[float]] = None,
        ttl_seconds: int = 3600,
    ) -> bool:
        """
        Cache agent response for future queries.

        Args:
            query: User query
            response: Agent response
            agent_name: Agent name
            conversation_context: Conversation context
            query_embedding: Query embedding for semantic similarity
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        try:
            cache_key = self._generate_cache_key(
                query, agent_name, conversation_context, CacheStrategy.HYBRID
            )

            context_hash = None
            if conversation_context:
                context_hash = self._hash_conversation_context(conversation_context)

            entry = CacheEntry(
                cache_key=cache_key,
                query=query,
                response=response,
                agent_name=agent_name,
                conversation_context_hash=context_hash,
                embedding=query_embedding,
                hit_count=0,
                last_accessed=datetime.utcnow(),
                created_at=datetime.utcnow(),
                ttl_seconds=ttl_seconds,
            )

            success = await self._cache.set(cache_key, entry)

            if success:
                logger.info(f"Cached response: {agent_name} - {query[:50]}...")
            else:
                logger.warning(f"Failed to cache response: {agent_name}")

            return success

        except Exception as e:
            logger.error(f"Cache write failed: {e}", exc_info=True)
            return False

    async def invalidate_agent_cache(self, agent_name: str) -> int:
        """
        Invalidate all cached responses for an agent.

        Useful when agent logic changes or knowledge is updated.

        Args:
            agent_name: Agent name

        Returns:
            Number of entries invalidated
        """
        try:
            count = await self._cache.clear_agent_cache(agent_name)
            logger.info(f"Invalidated {count} cache entries for {agent_name}")
            return count
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}", exc_info=True)
            return 0

    async def get_cache_statistics(self) -> CacheStatistics:
        """
        Get current cache performance statistics.

        Returns:
            CacheStatistics
        """
        return await self._cache.get_statistics()

    # ========== PREFETCHING METHODS ==========

    async def predict_next_queries(
        self,
        conversation: Conversation,
        user_id: UUID,
    ) -> List[PrefetchPrediction]:
        """
        Predict likely next queries based on conversation patterns.

        Uses conversation context and historical patterns to predict
        what the user might ask next, enabling proactive prefetching.

        Args:
            conversation: Current conversation
            user_id: User identifier

        Returns:
            List of prefetch predictions
        """
        predictions: List[PrefetchPrediction] = []

        # Analyze conversation context
        recent_messages = conversation.messages[-5:] if len(conversation.messages) >= 5 else conversation.messages

        # Pattern 1: If user asked about risk, predict they'll ask about yield
        if self._conversation_mentions_risk(recent_messages):
            predictions.append(
                PrefetchPrediction(
                    agent_name="yield_optimizer",
                    predicted_query="What yield opportunities are available given this risk profile?",
                    confidence=0.75,
                    priority=PrefetchPriority.HIGH,
                    reasoning="User discussed risk; likely to explore yield next",
                    estimated_response_time_ms=2500,
                    estimated_cost_usd=0.015,
                )
            )

        # Pattern 2: If user asked about a protocol, predict they'll ask about alternatives
        mentioned_protocols = self._extract_mentioned_protocols(recent_messages)
        if mentioned_protocols:
            predictions.append(
                PrefetchPrediction(
                    agent_name="protocol_analyzer",
                    predicted_query=f"What are alternatives to {mentioned_protocols[0]}?",
                    confidence=0.68,
                    priority=PrefetchPriority.MEDIUM,
                    reasoning=f"User mentioned {mentioned_protocols[0]}; may want alternatives",
                    estimated_response_time_ms=2000,
                    estimated_cost_usd=0.012,
                )
            )

        # Pattern 3: Portfolio health checks often lead to rebalancing questions
        if self._conversation_mentions_portfolio_health(recent_messages):
            predictions.append(
                PrefetchPrediction(
                    agent_name="portfolio_manager",
                    predicted_query="How should I rebalance my portfolio?",
                    confidence=0.82,
                    priority=PrefetchPriority.HIGH,
                    reasoning="Portfolio health discussed; rebalancing often follows",
                    estimated_response_time_ms=3000,
                    estimated_cost_usd=0.020,
                )
            )

        return predictions

    async def execute_prefetch(self, prediction: PrefetchPrediction) -> bool:
        """
        Execute prefetch prediction.

        Proactively runs agent query and caches result.

        Args:
            prediction: Prefetch prediction

        Returns:
            True if prefetch succeeded
        """
        if not prediction.should_prefetch():
            logger.debug(f"Skipping prefetch: {prediction.predicted_query[:50]}... (low confidence)")
            return False

        try:
            # Check if already cached
            cached = await self.get_cached_response(
                prediction.predicted_query,
                prediction.agent_name,
            )

            if cached:
                logger.debug(f"Prefetch unnecessary (already cached): {prediction.predicted_query[:50]}...")
                return True

            # TODO: Invoke agent with predicted query
            # For now, simulate prefetch
            logger.info(
                f"Prefetching: {prediction.agent_name} - {prediction.predicted_query[:50]}... "
                f"(confidence: {prediction.confidence:.0%})"
            )

            # Placeholder: In production, invoke agent and cache result
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"Prefetch failed: {e}", exc_info=True)
            return False

    # ========== OFFLINE MODE METHODS ==========

    async def queue_offline_message(
        self,
        user_id: UUID,
        conversation_id: UUID,
        message: str,
        agent_name: Optional[str] = None,
        priority: int = 0,
    ) -> bool:
        """
        Queue message for sending when connection is restored.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            message: Message text
            agent_name: Target agent (if any)
            priority: Message priority (higher = more important)

        Returns:
            True if queued successfully
        """
        from uuid import uuid4

        entry = OfflineQueueEntry(
            id=uuid4(),
            user_id=user_id,
            conversation_id=conversation_id,
            message=message,
            agent_name=agent_name,
            created_at=datetime.utcnow(),
            priority=priority,
        )

        success = await self._offline_queue.enqueue(entry)

        if success:
            logger.info(f"Queued offline message for user {user_id}")
        else:
            logger.error(f"Failed to queue offline message for user {user_id}")

        return success

    async def process_offline_queue(self, user_id: UUID) -> Tuple[int, int]:
        """
        Process queued messages when connection is restored.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (messages_sent, messages_failed)
        """
        entries = await self._offline_queue.dequeue(user_id, limit=50)

        sent = 0
        failed = 0

        for entry in entries:
            try:
                # TODO: Send message via conversation service
                # For now, simulate sending
                logger.info(f"Sending queued message: {entry.message[:50]}...")
                await asyncio.sleep(0.05)

                # Remove from queue on success
                await self._offline_queue.remove(entry.id)
                sent += 1

            except Exception as e:
                logger.error(f"Failed to send queued message: {e}")

                # Update retry count
                if entry.can_retry():
                    await self._offline_queue.update_retry_count(entry.id)
                else:
                    logger.warning(f"Message exceeded max retries: {entry.id}")
                    failed += 1

        return sent, failed

    async def get_offline_queue_size(self, user_id: UUID) -> int:
        """
        Get number of queued messages for user.

        Args:
            user_id: User identifier

        Returns:
            Queue size
        """
        return await self._offline_queue.get_queue_size(user_id)

    # ========== PERFORMANCE MONITORING METHODS ==========

    async def check_performance_budget(
        self, response_time_ms: int, cost_usd: float
    ) -> List[PerformanceAlert]:
        """
        Check if response meets performance budget.

        Args:
            response_time_ms: Actual response time
            cost_usd: Actual cost

        Returns:
            List of performance alerts (empty if within budget)
        """
        alerts: List[PerformanceAlert] = []

        # Check response time
        time_status = self._budget.check_response_time(response_time_ms)
        if time_status in [PerformanceBudgetStatus.CRITICAL, PerformanceBudgetStatus.VIOLATED]:
            alerts.append(
                PerformanceAlert(
                    alert_type="response_time",
                    status=time_status,
                    metric_name="Response Time",
                    actual_value=response_time_ms,
                    budget_value=self._budget.max_response_time_ms,
                    threshold_exceeded_by=response_time_ms - self._budget.max_response_time_ms,
                    timestamp=datetime.utcnow(),
                    recommendation="Consider enabling more aggressive caching or reducing agent complexity",
                )
            )

        # Check cost
        cost_status = self._budget.check_cost(cost_usd)
        if cost_status in [PerformanceBudgetStatus.CRITICAL, PerformanceBudgetStatus.VIOLATED]:
            alerts.append(
                PerformanceAlert(
                    alert_type="cost",
                    status=cost_status,
                    metric_name="LLM Cost",
                    actual_value=cost_usd,
                    budget_value=self._budget.max_llm_cost_per_query_usd,
                    threshold_exceeded_by=cost_usd - self._budget.max_llm_cost_per_query_usd,
                    timestamp=datetime.utcnow(),
                    recommendation="Consider using smaller LLM models or increasing cache hit rate",
                )
            )

        # Check cache hit rate
        cache_stats = await self.get_cache_statistics()
        cache_status = self._budget.check_cache_hit_rate(cache_stats.hit_rate)
        if cache_status in [PerformanceBudgetStatus.WARNING, PerformanceBudgetStatus.CRITICAL]:
            alerts.append(
                PerformanceAlert(
                    alert_type="cache_hit_rate",
                    status=cache_status,
                    metric_name="Cache Hit Rate",
                    actual_value=cache_stats.hit_rate,
                    budget_value=self._budget.target_cache_hit_rate,
                    threshold_exceeded_by=self._budget.target_cache_hit_rate - cache_stats.hit_rate,
                    timestamp=datetime.utcnow(),
                    recommendation="Enable semantic similarity caching or adjust TTL values",
                )
            )

        return alerts

    # ========== PRIVATE HELPER METHODS ==========

    def _generate_cache_key(
        self,
        query: str,
        agent_name: str,
        conversation_context: Optional[List[Message]],
        strategy: CacheStrategy,
    ) -> str:
        """Generate cache key based on strategy."""
        components = [agent_name, query.strip().lower()]

        if strategy in [CacheStrategy.CONVERSATION_CONTEXT, CacheStrategy.HYBRID]:
            if conversation_context:
                context_hash = self._hash_conversation_context(conversation_context)
                components.append(context_hash)

        key_str = "|".join(components)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _hash_conversation_context(self, messages: List[Message]) -> str:
        """Hash conversation context for cache keying."""
        # Use last 3 messages for context
        recent = messages[-3:] if len(messages) >= 3 else messages
        context_str = "|".join(f"{m.role.value}:{m.content}" for m in recent)
        return hashlib.md5(context_str.encode()).hexdigest()

    async def _find_similar_cached_queries(
        self,
        query: str,
        agent_name: str,
        conversation_context: Optional[List[Message]],
        threshold: float = 0.85,
    ) -> List[CacheEntry]:
        """Find semantically similar cached queries."""
        # TODO: Generate query embedding using embedding model
        # For now, return empty list (placeholder)
        query_embedding: List[float] = []

        if not query_embedding:
            return []

        return await self._cache.find_similar(
            query_embedding=query_embedding,
            agent_name=agent_name,
            threshold=threshold,
            limit=5,
        )

    def _conversation_mentions_risk(self, messages: List[Message]) -> bool:
        """Check if conversation mentions risk-related topics."""
        risk_keywords = ["risk", "volatile", "volatility", "exposure", "hedge", "safety"]
        content = " ".join(m.content.lower() for m in messages)
        return any(keyword in content for keyword in risk_keywords)

    def _conversation_mentions_portfolio_health(self, messages: List[Message]) -> bool:
        """Check if conversation mentions portfolio health."""
        health_keywords = ["portfolio health", "performance", "allocation", "diversification"]
        content = " ".join(m.content.lower() for m in messages)
        return any(keyword in content for keyword in health_keywords)

    def _extract_mentioned_protocols(self, messages: List[Message]) -> List[str]:
        """Extract DeFi protocols mentioned in conversation."""
        protocols = ["Aave", "Curve", "Morpho", "Uniswap", "Compound", "Lido", "Balancer"]
        content = " ".join(m.content for m in messages)

        mentioned = [p for p in protocols if p in content]
        return mentioned

    def format_cache_statistics_response(self, stats: CacheStatistics) -> str:
        """Format cache statistics for chat display."""
        lines = [
            "┌─ 📊 Cache Performance Statistics ─┐",
            "",
            "**Cache Efficiency:**",
            f"  • Total queries: {stats.total_queries:,}",
            f"  • Cache hits: {stats.cache_hits:,}",
            f"  • Cache misses: {stats.cache_misses:,}",
            f"  • Hit rate: {stats.hit_rate:.1%}",
            "",
            "**Performance Impact:**",
            f"  • Avg response time (cached): {stats.avg_response_time_ms_cached:.0f}ms",
            f"  • Avg response time (uncached): {stats.avg_response_time_ms_uncached:.0f}ms",
            f"  • Time saved: {stats.time_saved_ms / 1000:.1f}s",
            "",
            "**Cost Savings:**",
            f"  • Cost saved: ${stats.cost_saved_usd:.2f}",
            "",
            "**Resource Usage:**",
            f"  • Memory usage: {stats.memory_usage_mb:.1f} MB",
            f"  • Evictions: {stats.eviction_count:,}",
            "",
            "└─────────────────────────────────────┘",
        ]

        return "\n".join(lines)
