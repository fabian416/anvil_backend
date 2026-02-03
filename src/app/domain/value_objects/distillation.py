"""Distillation system value objects."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID


class RouteType(str, Enum):
    """Route decision types."""

    REJECT = "REJECT"
    CACHE = "CACHE"
    STATIC = "STATIC"
    LIGHT_LLM = "LIGHT_LLM"
    FULL_LLM = "FULL_LLM"


class Intent(str, Enum):
    """Intent categories for user queries."""

    # Informational
    PRICE_CHECK = "price_check"
    BALANCE_CHECK = "balance_check"
    APY_CHECK = "apy_check"
    GAS_CHECK = "gas_check"
    STATUS_CHECK = "status_check"

    # Educational
    EXPLAIN_CONCEPT = "explain_concept"
    HOW_TO = "how_to"
    COMPARE = "compare"

    # Transactional
    SWAP_REQUEST = "swap_request"
    STAKE_REQUEST = "stake_request"
    LEND_REQUEST = "lend_request"
    BORROW_REQUEST = "borrow_request"
    BRIDGE_REQUEST = "bridge_request"

    # Analytical
    PORTFOLIO_ANALYSIS = "portfolio"
    RISK_ASSESSMENT = "risk_assessment"
    YIELD_OPTIMIZATION = "yield_optimize"
    STRATEGY_ADVICE = "strategy"

    # Administrative
    SETTINGS_CHANGE = "settings"
    ALERT_SETUP = "alert_setup"

    # Off-topic / Other
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    OFF_TOPIC = "off_topic"
    UNCLEAR = "unclear"


class ComplexityLevel(str, Enum):
    """Query complexity levels."""

    TRIVIAL = "trivial"  # Single fact lookup, no reasoning
    SIMPLE = "simple"  # Basic query, minimal context
    MODERATE = "moderate"  # Multi-step, some reasoning
    COMPLEX = "complex"  # Deep analysis, tool usage
    EXPERT = "expert"  # Multi-domain, extensive reasoning


class CacheLevel(str, Enum):
    """Cache hit level."""

    NONE = "none"
    EXACT = "exact"
    SEMANTIC = "semantic"


@dataclass(frozen=True)
class ExtractedEntities:
    """Entities extracted from user query."""

    tokens: List[str] = field(default_factory=list)  # ETH, USDC, AAVE
    protocols: List[str] = field(default_factory=list)  # Uniswap, Aave, Compound
    chains: List[str] = field(default_factory=list)  # Ethereum, Arbitrum, Polygon
    amounts: List[Decimal] = field(default_factory=list)  # 100, 0.5, 1000
    addresses: List[str] = field(default_factory=list)  # 0x...
    time_references: List[str] = field(
        default_factory=list
    )  # today, last week, 30 days


@dataclass
class DistillationResult:
    """Result of the distillation pass."""

    # Should we process this request?
    should_process: bool

    # Routing decision
    route_type: RouteType

    # Classification results
    intent: Intent
    complexity: ComplexityLevel
    entities: ExtractedEntities

    # Processing hints
    suggested_model_tier: Optional[str] = None  # economy, standard, premium
    suggested_agent: Optional[str] = None
    cache_key: Optional[str] = None

    # Cache info
    cache_hit: bool = False
    cache_level: CacheLevel = CacheLevel.NONE
    cached_response: Optional[str] = None

    # Static response
    static_response: Optional[str] = None

    # Rejection details (if applicable)
    rejection_reason: Optional[str] = None
    rejection_code: Optional[str] = None

    # Confidence scores
    classification_confidence: float = 0.0
    routing_confidence: float = 0.0

    # Performance
    classification_latency_ms: int = 0

    # Cost savings estimate
    estimated_cost_saved_usd: Decimal = Decimal("0")


@dataclass(frozen=True)
class DistillationConfig:
    """Configuration for distillation system."""

    # Feature flags
    enabled: bool = True
    cache_enabled: bool = True
    static_responses_enabled: bool = True
    semantic_cache_enabled: bool = True

    # Classification thresholds
    min_confidence_threshold: float = 0.7
    semantic_similarity_threshold: float = 0.95

    # Performance limits
    max_classification_latency_ms: int = 100

    # Cache TTLs by intent (seconds)
    cache_ttl_by_intent: Dict[Intent, int] = field(default_factory=dict)

    # Intents that force full LLM (no shortcuts)
    force_full_llm_intents: List[Intent] = field(default_factory=list)


@dataclass(frozen=True)
class StaticResponse:
    """Static response template."""

    id: UUID
    intent: Intent
    variant: str
    response_template: str
    template_variables: List[str]
    data_source: Optional[str]
    conditions: Dict[str, Any]
    priority: int
    is_active: bool


@dataclass
class CachedResponse:
    """Cached distillation response."""

    cache_key: str
    normalized_query: str
    intent: Intent
    entities: ExtractedEntities
    response_content: str
    response_metadata: Dict[str, Any]
    hit_count: int
    created_at: datetime
    last_hit_at: Optional[datetime]
    expires_at: datetime
    source_model: Optional[str]
    cache_level: CacheLevel


@dataclass
class DistillationTelemetry:
    """Telemetry data for distillation request."""

    request_id: str
    user_id: Optional[UUID]
    original_query: str
    normalized_query: str

    # Classification
    intent: Intent
    intent_confidence: float
    complexity: ComplexityLevel
    entities: ExtractedEntities

    # Routing
    route_type: RouteType
    routing_reason: str
    suggested_model_tier: Optional[str]
    suggested_agent: Optional[str]

    # Cache
    cache_key: Optional[str]
    cache_hit: bool
    cache_level: CacheLevel

    # Performance
    classification_latency_ms: int
    total_latency_ms: int

    # Outcome
    was_processed: bool
    llm_request_id: Optional[UUID]

    created_at: datetime


@dataclass
class TelemetryMetrics:
    """Aggregated telemetry metrics."""

    hour_bucket: datetime

    # Counts by route
    total_requests: int
    rejected_count: int
    cache_hit_count: int
    static_response_count: int
    light_llm_count: int
    full_llm_count: int

    # Cache metrics
    exact_cache_hits: int
    semantic_cache_hits: int
    cache_hit_rate: float

    # Classification metrics
    avg_classification_latency_ms: int
    avg_confidence: float

    # Intent distribution
    intent_distribution: Dict[str, int]

    # Cost savings
    estimated_cost_saved_usd: Decimal
