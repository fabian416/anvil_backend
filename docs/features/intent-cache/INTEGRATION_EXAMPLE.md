# Intent Cache Adapter - Integration Example

## Dishka Dependency Injection Setup

### Provider Configuration

Create a provider for intent cache dependencies:

```python
# src/app/setup/ioc/intent_cache.py
from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from app.domain.ports.intent_cache_adapter import IntentCacheAdapter
from app.domain.ports.embedding_service import EmbeddingService
from app.infrastructure.adapters.chat.redis_intent_cache_adapter import (
    RedisIntentCacheAdapter,
)
from app.infrastructure.embeddings.openai_embedding_service import (
    OpenAIEmbeddingService,
)


class IntentCacheProvider(Provider):
    """Provider for intent cache dependencies."""

    scope = Scope.APP

    @provide
    async def provide_intent_cache_adapter(
        self,
        redis_client: Redis,
        embedding_service: EmbeddingService,
    ) -> IntentCacheAdapter:
        """
        Provide intent cache adapter.

        Initializes Redis indices for semantic search on first use.
        """
        adapter = RedisIntentCacheAdapter(
            redis_client=redis_client,
            embedding_service=embedding_service,
            key_prefix="intent:cache:",
            entity_prefix="intent:entity:",
            suggestion_prefix="intent:suggest:",
            stats_key="intent:cache:stats",
            default_ttl_hours=24,
        )

        # Initialize indices
        await adapter.initialize()

        return adapter
```

### Register Provider

Add to main IoC container:

```python
# src/app/setup/ioc/__init__.py
from .intent_cache import IntentCacheProvider

def setup_ioc_container() -> Container:
    container = make_async_container(
        # ... other providers
        IntentCacheProvider(),
    )
    return container
```

## Application Layer Integration

### Intent Detection Interactor

Use the cache in your intent detection logic:

```python
# src/app/application/commands/chat/detect_intent.py
from dataclasses import dataclass
from typing import Optional

from app.domain.ports.intent_cache_adapter import IntentCacheAdapter
from app.domain.ports.embedding_service import EmbeddingService
from app.domain.ports.ai.llm_provider_port import LLMProviderPort
from app.domain.value_objects.chat.intent_prediction import IntentPrediction


@dataclass
class DetectIntentCommand:
    """Command to detect user intent from query."""

    query: str
    user_id: str
    conversation_id: Optional[str] = None
    use_cache: bool = True


class DetectIntentInteractor:
    """
    Detect user intent with caching.

    Uses cache to avoid redundant LLM calls for similar queries.
    """

    def __init__(
        self,
        intent_cache: IntentCacheAdapter,
        embedding_service: EmbeddingService,
        llm_provider: LLMProviderPort,
    ):
        self._cache = intent_cache
        self._embeddings = embedding_service
        self._llm = llm_provider

    async def execute(self, command: DetectIntentCommand) -> IntentPrediction:
        """
        Execute intent detection with caching.

        Flow:
        1. Generate query embedding
        2. Check cache for exact or similar match
        3. If miss, call LLM to detect intent
        4. Cache result for future use
        5. Return intent prediction
        """
        # Generate embedding for semantic matching
        query_embedding = await self._embeddings.generate_embedding(command.query)

        # Try cache first (if enabled)
        if command.use_cache:
            cached_intent = await self._cache.get_intent(
                query=command.query,
                query_embedding=query_embedding,
                similarity_threshold=0.90,
            )

            if cached_intent:
                # Cache hit - return immediately
                return cached_intent

        # Cache miss - detect intent using LLM
        intent = await self._detect_intent_with_llm(
            query=command.query,
            user_id=command.user_id,
            conversation_id=command.conversation_id,
        )

        # Cache the detected intent for future use
        if command.use_cache and intent.is_high_confidence:
            await self._cache.set_intent(
                query=command.query,
                intent=intent,
                query_embedding=query_embedding,
            )

            # Cache extracted entities
            if intent.extracted_entities:
                await self._cache_entities(intent.extracted_entities)

        return intent

    async def _detect_intent_with_llm(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str],
    ) -> IntentPrediction:
        """Detect intent using LLM."""
        # LLM-based intent detection logic
        # ... (existing implementation)
        pass

    async def _cache_entities(self, entities: dict) -> None:
        """Cache extracted entities for suggestions."""
        for entity_type, entity_value in entities.items():
            if isinstance(entity_value, str):
                await self._cache.cache_entity(entity_type, entity_value)
            elif isinstance(entity_value, list):
                for value in entity_value:
                    if isinstance(value, str):
                        await self._cache.cache_entity(entity_type, value)
```

### Query Suggestions Interactor

Provide autocomplete suggestions:

```python
# src/app/application/queries/chat/get_query_suggestions.py
from dataclasses import dataclass
from typing import List

from app.domain.ports.intent_cache_adapter import IntentCacheAdapter
from app.domain.value_objects.chat.agent_suggestion import AutocompleteSuggestion


@dataclass
class GetQuerySuggestionsQuery:
    """Query to get autocomplete suggestions."""

    partial_input: str
    limit: int = 5


class GetQuerySuggestionsInteractor:
    """Get autocomplete suggestions based on cached queries."""

    def __init__(self, intent_cache: IntentCacheAdapter):
        self._cache = intent_cache

    async def execute(
        self, query: GetQuerySuggestionsQuery
    ) -> List[AutocompleteSuggestion]:
        """
        Get query suggestions for partial input.

        Returns suggestions sorted by relevance (usage count + confidence).
        """
        suggestions = await self._cache.get_suggestions(
            partial_input=query.partial_input,
            limit=query.limit,
        )

        return suggestions
```

### Entity Suggestions Interactor

Provide entity autocomplete:

```python
# src/app/application/queries/chat/get_entity_suggestions.py
from dataclasses import dataclass
from typing import List

from app.domain.ports.intent_cache_adapter import IntentCacheAdapter


@dataclass
class GetEntitySuggestionsQuery:
    """Query to get entity autocomplete suggestions."""

    entity_type: str
    partial_value: str
    limit: int = 10


class GetEntitySuggestionsInteractor:
    """Get entity value suggestions for autocomplete."""

    def __init__(self, intent_cache: IntentCacheAdapter):
        self._cache = intent_cache

    async def execute(self, query: GetEntitySuggestionsQuery) -> List[str]:
        """
        Get entity suggestions.

        Returns cached entity values sorted by usage frequency.
        """
        suggestions = await self._cache.get_entity_suggestions(
            entity_type=query.entity_type,
            partial_value=query.partial_value,
            limit=query.limit,
        )

        return suggestions
```

## Presentation Layer Integration

### HTTP Controllers

Expose cache functionality via REST API:

```python
# src/app/presentation/http/controllers/chat/intent_schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional


class QuerySuggestionsRequest(BaseModel):
    """Request for query autocomplete suggestions."""

    partial_input: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=5, ge=1, le=20)


class EntitySuggestionsRequest(BaseModel):
    """Request for entity autocomplete suggestions."""

    entity_type: str = Field(..., min_length=1)
    partial_value: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=50)


class SuggestionResponse(BaseModel):
    """Single suggestion response."""

    completion_text: str
    display_text: str
    confidence: float
    suggestion_type: str
    icon: Optional[str] = None
    metadata: dict = {}


class QuerySuggestionsResponse(BaseModel):
    """Response with query suggestions."""

    suggestions: List[SuggestionResponse]


class EntitySuggestionsResponse(BaseModel):
    """Response with entity suggestions."""

    entity_type: str
    suggestions: List[str]


class CacheStatsResponse(BaseModel):
    """Cache performance statistics."""

    total_requests: int
    cache_hits: int
    semantic_hits: int
    cache_misses: int
    hit_rate: float
    semantic_hit_rate: float
    total_entries: int
    memory_usage_mb: float
    cost_saved_usd: float
    time_saved_ms: int
```

```python
# src/app/presentation/http/controllers/chat/intent_router.py
from fastapi import APIRouter, Depends
from dishka.integrations.fastapi import FromDishka

from app.application.queries.chat.get_query_suggestions import (
    GetQuerySuggestionsInteractor,
    GetQuerySuggestionsQuery,
)
from app.application.queries.chat.get_entity_suggestions import (
    GetEntitySuggestionsInteractor,
    GetEntitySuggestionsQuery,
)
from app.domain.ports.intent_cache_adapter import IntentCacheAdapter
from .intent_schemas import (
    QuerySuggestionsRequest,
    QuerySuggestionsResponse,
    EntitySuggestionsRequest,
    EntitySuggestionsResponse,
    CacheStatsResponse,
    SuggestionResponse,
)


router = APIRouter(prefix="/chat/intent", tags=["Chat Intent"])


@router.post("/suggestions", response_model=QuerySuggestionsResponse)
async def get_query_suggestions(
    request: QuerySuggestionsRequest,
    interactor: FromDishka[GetQuerySuggestionsInteractor],
) -> QuerySuggestionsResponse:
    """
    Get autocomplete suggestions for partial query.

    Returns cached query patterns that match the partial input,
    sorted by relevance (usage count and confidence).
    """
    query = GetQuerySuggestionsQuery(
        partial_input=request.partial_input,
        limit=request.limit,
    )

    suggestions = await interactor.execute(query)

    return QuerySuggestionsResponse(
        suggestions=[
            SuggestionResponse(
                completion_text=s.completion_text,
                display_text=s.display_text,
                confidence=s.confidence,
                suggestion_type=s.suggestion_type,
                icon=s.icon,
                metadata=s.metadata or {},
            )
            for s in suggestions
        ]
    )


@router.post("/entity-suggestions", response_model=EntitySuggestionsResponse)
async def get_entity_suggestions(
    request: EntitySuggestionsRequest,
    interactor: FromDishka[GetEntitySuggestionsInteractor],
) -> EntitySuggestionsResponse:
    """
    Get autocomplete suggestions for entity values.

    Returns cached entity values (protocols, tokens, etc.) that match
    the partial value, sorted by usage frequency.
    """
    query = GetEntitySuggestionsQuery(
        entity_type=request.entity_type,
        partial_value=request.partial_value,
        limit=request.limit,
    )

    suggestions = await interactor.execute(query)

    return EntitySuggestionsResponse(
        entity_type=request.entity_type,
        suggestions=suggestions,
    )


@router.get("/cache-stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    cache: FromDishka[IntentCacheAdapter],
) -> CacheStatsResponse:
    """
    Get intent cache performance statistics.

    Returns metrics about cache hit rate, cost savings, and memory usage.
    """
    stats = await cache.get_cache_stats()

    return CacheStatsResponse(**stats)
```

## Cache Warming on Startup

Pre-populate cache with common patterns:

```python
# src/app/setup/startup.py
from typing import List, Tuple
from app.domain.ports.intent_cache_adapter import IntentCacheAdapter
from app.domain.value_objects.chat.intent_prediction import (
    IntentPrediction,
    IntentType,
)


async def warm_intent_cache(cache: IntentCacheAdapter) -> int:
    """
    Warm intent cache on application startup.

    Pre-populates cache with common query patterns to improve
    initial response times.
    """
    common_patterns: List[Tuple[str, IntentPrediction]] = [
        # Portfolio queries
        (
            "show my portfolio",
            IntentPrediction.create(
                IntentType.PORTFOLIO_REVIEW,
                0.95,
                suggested_agent="portfolio_agent",
            ),
        ),
        (
            "what are my holdings",
            IntentPrediction.create(
                IntentType.PORTFOLIO_REVIEW,
                0.93,
                suggested_agent="portfolio_agent",
            ),
        ),
        (
            "check my balance",
            IntentPrediction.create(
                IntentType.PORTFOLIO_REVIEW,
                0.92,
                suggested_agent="portfolio_agent",
            ),
        ),
        # Risk queries
        (
            "analyze my risk",
            IntentPrediction.create(
                IntentType.RISK_ANALYSIS,
                0.94,
                suggested_agent="risk_analyzer_agent",
            ),
        ),
        (
            "how risky is my portfolio",
            IntentPrediction.create(
                IntentType.RISK_ANALYSIS,
                0.91,
                suggested_agent="risk_analyzer_agent",
            ),
        ),
        # Yield queries
        (
            "find best yield",
            IntentPrediction.create(
                IntentType.YIELD_OPTIMIZATION,
                0.95,
                suggested_agent="defi_yield_agent",
            ),
        ),
        (
            "optimize my returns",
            IntentPrediction.create(
                IntentType.YIELD_OPTIMIZATION,
                0.93,
                suggested_agent="defi_yield_agent",
            ),
        ),
        # Market analysis
        (
            "what's happening in defi",
            IntentPrediction.create(
                IntentType.MARKET_ANALYSIS,
                0.90,
                suggested_agent="research_agent",
            ),
        ),
        # Actions
        (
            "swap 100 USDC for ETH",
            IntentPrediction.create(
                IntentType.EXECUTE_TRADE,
                0.94,
                suggested_agent="execution_agent",
                extracted_entities={
                    "amount": "100",
                    "from_token": "USDC",
                    "to_token": "ETH",
                    "action": "swap",
                },
            ),
        ),
    ]

    # Warm cache with patterns
    cached_count = await cache.warm_cache(common_patterns)

    # Pre-cache common entities
    common_entities = [
        ("protocol", "Aave"),
        ("protocol", "Compound"),
        ("protocol", "Uniswap"),
        ("protocol", "Curve"),
        ("token", "ETH"),
        ("token", "USDC"),
        ("token", "DAI"),
        ("token", "WBTC"),
        ("action", "swap"),
        ("action", "stake"),
        ("action", "withdraw"),
    ]

    for entity_type, entity_value in common_entities:
        await cache.cache_entity(entity_type, entity_value)

    return cached_count


# In main application startup
async def startup_event(container):
    """Run startup tasks."""
    # ... other startup tasks

    # Warm intent cache
    async with container() as request_container:
        cache = await request_container.get(IntentCacheAdapter)
        cached_count = await warm_intent_cache(cache)
        print(f"Warmed intent cache with {cached_count} patterns")
```

## Background Tasks

### Cache Maintenance

Periodic cache cleanup and monitoring:

```python
# src/app/infrastructure/celery/tasks/cache_tasks.py
from celery import shared_task
from app.setup.ioc import get_container
from app.domain.ports.intent_cache_adapter import IntentCacheAdapter


@shared_task(name="intent_cache.maintenance")
async def maintain_intent_cache():
    """
    Periodic intent cache maintenance.

    Runs every 6 hours to:
    - Clear low-confidence intents
    - Log performance metrics
    - Alert on degraded performance
    """
    container = get_container()

    async with container() as request_container:
        cache = await request_container.get(IntentCacheAdapter)

        # Clear unknown/ambiguous intents (low value)
        cleared = await cache.clear_intent_cache(intent_type="unknown")

        # Get performance stats
        stats = await cache.get_cache_stats()

        # Log metrics
        print(f"Intent Cache Maintenance:")
        print(f"  - Cleared {cleared} low-confidence entries")
        print(f"  - Hit rate: {stats['hit_rate']:.2%}")
        print(f"  - Total entries: {stats['total_entries']}")
        print(f"  - Memory usage: {stats['memory_usage_mb']:.2f} MB")
        print(f"  - Cost saved: ${stats['cost_saved_usd']:.2f}")

        # Alert if performance is degraded
        if stats["hit_rate"] < 0.50:
            # Send alert to monitoring system
            print("WARNING: Intent cache hit rate below 50%")


@shared_task(name="intent_cache.refresh_warm_cache")
async def refresh_warm_cache():
    """
    Refresh cache warming patterns weekly.

    Updates cached common patterns to ensure they don't expire.
    """
    from app.setup.startup import warm_intent_cache

    container = get_container()

    async with container() as request_container:
        cache = await request_container.get(IntentCacheAdapter)
        cached_count = await warm_intent_cache(cache)
        print(f"Refreshed warm cache with {cached_count} patterns")
```

## Frontend Integration

### TypeScript/React Example

```typescript
// services/intentCacheService.ts
export interface QuerySuggestion {
  completion_text: string;
  display_text: string;
  confidence: number;
  suggestion_type: string;
  icon?: string;
  metadata: Record<string, any>;
}

export interface EntitySuggestion {
  entity_type: string;
  suggestions: string[];
}

export class IntentCacheService {
  async getQuerySuggestions(
    partialInput: string,
    limit: number = 5
  ): Promise<QuerySuggestion[]> {
    const response = await fetch('/api/chat/intent/suggestions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ partial_input: partialInput, limit }),
    });

    const data = await response.json();
    return data.suggestions;
  }

  async getEntitySuggestions(
    entityType: string,
    partialValue: string,
    limit: number = 10
  ): Promise<string[]> {
    const response = await fetch('/api/chat/intent/entity-suggestions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entity_type: entityType,
        partial_value: partialValue,
        limit,
      }),
    });

    const data = await response.json();
    return data.suggestions;
  }
}
```

```tsx
// components/ChatInput.tsx
import { useState, useEffect } from 'react';
import { IntentCacheService } from '../services/intentCacheService';

const cacheService = new IntentCacheService();

export function ChatInput() {
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    // Debounce suggestion fetching
    const timer = setTimeout(async () => {
      if (input.length >= 3) {
        const results = await cacheService.getQuerySuggestions(input);
        setSuggestions(results);
      } else {
        setSuggestions([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [input]);

  return (
    <div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask me anything..."
      />
      {suggestions.length > 0 && (
        <div className="suggestions">
          {suggestions.map((s) => (
            <div
              key={s.completion_text}
              onClick={() => setInput(s.completion_text)}
            >
              {s.display_text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

## Monitoring Dashboard

Track cache performance:

```python
# Dashboard endpoint
@router.get("/admin/intent-cache-dashboard")
async def get_intent_cache_dashboard(
    cache: FromDishka[IntentCacheAdapter],
):
    """Get comprehensive cache dashboard data."""
    stats = await cache.get_cache_stats()

    return {
        "performance": {
            "hit_rate": stats["hit_rate"],
            "semantic_hit_rate": stats["semantic_hit_rate"],
            "avg_response_time_cached_ms": stats["avg_cached_response_time_ms"],
            "avg_response_time_uncached_ms": stats["avg_uncached_response_time_ms"],
        },
        "savings": {
            "cost_saved_usd": stats["cost_saved_usd"],
            "time_saved_ms": stats["time_saved_ms"],
            "requests_saved": stats["cache_hits"] + stats["semantic_hits"],
        },
        "resources": {
            "total_entries": stats["total_entries"],
            "memory_usage_mb": stats["memory_usage_mb"],
        },
        "traffic": {
            "total_requests": stats["total_requests"],
            "cache_hits": stats["cache_hits"],
            "semantic_hits": stats["semantic_hits"],
            "cache_misses": stats["cache_misses"],
        },
    }
```
