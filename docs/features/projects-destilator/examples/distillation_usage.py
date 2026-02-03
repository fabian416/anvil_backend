# Distillation Pass - Usage Examples

"""
Example usage of the Distillation Pass system.
"""

import asyncio
from typing import Optional
from dataclasses import dataclass
from enum import Enum

# =============================================================================
# DATA MODELS
# =============================================================================


class RouteType(Enum):
    REJECT = "reject"
    CACHE = "cache"
    STATIC = "static"
    LIGHT_LLM = "light_llm"
    FULL_LLM = "full_llm"


class Intent(Enum):
    PRICE_CHECK = "price_check"
    BALANCE_CHECK = "balance_check"
    SWAP_REQUEST = "swap_request"
    EXPLAIN_CONCEPT = "explain_concept"
    GREETING = "greeting"
    OFF_TOPIC = "off_topic"


class ComplexityLevel(Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class DistillationResult:
    """Result of the distillation pass."""

    should_process: bool
    route_type: RouteType
    intent: Optional[Intent] = None
    complexity: Optional[ComplexityLevel] = None
    suggested_model_tier: Optional[str] = None
    cache_key: Optional[str] = None
    static_response: Optional[str] = None
    cached_response: Optional[str] = None
    rejection_reason: Optional[str] = None
    classification_latency_ms: int = 0


# =============================================================================
# DISTILLATION ENGINE
# =============================================================================


class DistillationEngine:
    """
    Main distillation engine that classifies and routes requests.
    """

    def __init__(
        self,
        intent_classifier,
        complexity_assessor,
        entity_extractor,
        cache_manager,
        static_responder,
        config,
    ):
        self.classifier = intent_classifier
        self.assessor = complexity_assessor
        self.extractor = entity_extractor
        self.cache = cache_manager
        self.static = static_responder
        self.config = config

    async def distill(
        self, query: str, user_id: Optional[str] = None
    ) -> DistillationResult:
        """
        Run the distillation pass on a user query.

        Steps:
        1. Classify intent
        2. Assess complexity
        3. Extract entities
        4. Check cache
        5. Check static responses
        6. Determine routing
        """
        import time

        start_time = time.time()

        # Step 1: Classify intent
        intent, confidence = await self.classifier.classify(query)

        # Early rejection for off-topic
        if intent == Intent.OFF_TOPIC:
            return DistillationResult(
                should_process=False,
                route_type=RouteType.REJECT,
                intent=intent,
                rejection_reason="I specialize in DeFi assistance. How can I help with your crypto needs?",
                classification_latency_ms=int((time.time() - start_time) * 1000),
            )

        # Step 2: Assess complexity
        complexity = self.assessor.assess(query, intent)

        # Step 3: Extract entities
        entities = self.extractor.extract(query)

        # Step 4: Check cache
        cache_key = self._build_cache_key(intent, entities, query)

        cached = await self.cache.get(cache_key)
        if cached:
            return DistillationResult(
                should_process=False,
                route_type=RouteType.CACHE,
                intent=intent,
                complexity=complexity,
                cache_key=cache_key,
                cached_response=cached,
                classification_latency_ms=int((time.time() - start_time) * 1000),
            )

        # Step 5: Check static responses
        static_response = await self.static.get_response(intent, entities)
        if static_response:
            return DistillationResult(
                should_process=False,
                route_type=RouteType.STATIC,
                intent=intent,
                complexity=complexity,
                cache_key=cache_key,
                static_response=static_response,
                classification_latency_ms=int((time.time() - start_time) * 1000),
            )

        # Step 6: Determine LLM routing
        model_tier = self._select_model_tier(intent, complexity)
        route_type = (
            RouteType.LIGHT_LLM
            if complexity in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE]
            else RouteType.FULL_LLM
        )

        return DistillationResult(
            should_process=True,
            route_type=route_type,
            intent=intent,
            complexity=complexity,
            suggested_model_tier=model_tier,
            cache_key=cache_key,
            classification_latency_ms=int((time.time() - start_time) * 1000),
        )

    def _build_cache_key(self, intent, entities, query):
        """Generate cache key."""
        import hashlib

        normalized = query.lower().strip()
        key_str = f"{intent.value}|{','.join(entities.tokens)}|{normalized}"
        return f"distill:{hashlib.sha256(key_str.encode()).hexdigest()[:16]}"

    def _select_model_tier(self, intent, complexity):
        """Select appropriate model tier."""
        high_stakes = {Intent.SWAP_REQUEST}

        if intent in high_stakes:
            return "premium"

        tier_map = {
            ComplexityLevel.TRIVIAL: "economy",
            ComplexityLevel.SIMPLE: "economy",
            ComplexityLevel.MODERATE: "standard",
            ComplexityLevel.COMPLEX: "premium",
        }
        return tier_map.get(complexity, "standard")


# =============================================================================
# INTENT CLASSIFIER
# =============================================================================


class IntentClassifier:
    """Classify user intent using rules and ML model."""

    def __init__(self):
        # Simple rule-based patterns
        self.patterns = {
            r"price|cost|worth|value": Intent.PRICE_CHECK,
            r"balance|holdings|portfolio value": Intent.BALANCE_CHECK,
            r"swap|exchange|trade|convert": Intent.SWAP_REQUEST,
            r"what is|explain|how does|tell me about": Intent.EXPLAIN_CONCEPT,
            r"hello|hi|hey|good morning|good evening": Intent.GREETING,
        }

    async def classify(self, text: str):
        """Classify intent with confidence."""
        import re

        text_lower = text.lower()

        for pattern, intent in self.patterns.items():
            if re.search(pattern, text_lower):
                return intent, 0.9

        # Default to explain concept with lower confidence
        return Intent.EXPLAIN_CONCEPT, 0.6


# =============================================================================
# COMPLEXITY ASSESSOR
# =============================================================================


class ComplexityAssessor:
    """Assess request complexity."""

    def assess(self, text: str, intent: Intent) -> ComplexityLevel:
        """Determine complexity level."""

        # Simple heuristics
        word_count = len(text.split())
        question_count = text.count("?")
        has_and = " and " in text.lower()
        has_comparison = any(
            w in text.lower() for w in ["compare", "vs", "versus", "difference"]
        )

        # Trivial: Very short, single intent
        if word_count < 6 and intent in [Intent.PRICE_CHECK, Intent.GREETING]:
            return ComplexityLevel.TRIVIAL

        # Complex: Multiple questions or comparisons
        if question_count > 1 or has_comparison:
            return ComplexityLevel.COMPLEX

        # Moderate: Has conjunctions or longer
        if has_and or word_count > 15:
            return ComplexityLevel.MODERATE

        return ComplexityLevel.SIMPLE


# =============================================================================
# ENTITY EXTRACTOR
# =============================================================================


@dataclass
class ExtractedEntities:
    tokens: list
    protocols: list
    chains: list
    amounts: list


class EntityExtractor:
    """Extract DeFi entities from text."""

    TOKENS = {"eth", "btc", "usdc", "usdt", "dai", "weth", "wbtc", "steth", "reth"}
    PROTOCOLS = {"aave", "compound", "uniswap", "curve", "lido", "yearn"}
    CHAINS = {"ethereum", "arbitrum", "polygon", "optimism", "base"}

    def extract(self, text: str) -> ExtractedEntities:
        """Extract all relevant entities."""
        import re

        text_lower = text.lower()
        words = set(text_lower.split())

        tokens = [t.upper() for t in words if t in self.TOKENS]
        protocols = [p for p in words if p in self.PROTOCOLS]
        chains = [c for c in words if c in self.CHAINS]

        # Extract amounts (simple pattern)
        amounts = re.findall(r"\d+\.?\d*", text)

        return ExtractedEntities(
            tokens=tokens, protocols=protocols, chains=chains, amounts=amounts
        )


# =============================================================================
# CACHE MANAGER
# =============================================================================


class CacheManager:
    """Manage distillation cache."""

    def __init__(self):
        self._cache = {}

    async def get(self, key: str) -> Optional[str]:
        """Get cached response."""
        return self._cache.get(key)

    async def set(self, key: str, value: str, ttl: int = 3600):
        """Set cache entry."""
        self._cache[key] = value


# =============================================================================
# STATIC RESPONDER
# =============================================================================


class StaticResponder:
    """Handle static responses."""

    RESPONSES = {
        Intent.GREETING: "Hello! I'm Anvil, your DeFi assistant. How can I help you today?",
        Intent.OFF_TOPIC: "I specialize in DeFi assistance. How can I help with your crypto needs?",
    }

    async def get_response(
        self, intent: Intent, entities: ExtractedEntities
    ) -> Optional[str]:
        """Get static response if available."""

        if intent == Intent.GREETING:
            return self.RESPONSES[Intent.GREETING]

        if intent == Intent.PRICE_CHECK and entities.tokens:
            # Would fetch from API in real implementation
            token = entities.tokens[0]
            return f"The current price of {token} is $2,150 (+2.5% 24h)."

        return None


# =============================================================================
# INTEGRATION EXAMPLE
# =============================================================================


class AnvilChatService:
    """Main chat service with distillation integration."""

    def __init__(self, distillation_engine, llm_orchestrator):
        self.distillation = distillation_engine
        self.llm = llm_orchestrator

    async def process_message(self, message: str, user_id: str) -> dict:
        """Process user message with distillation pass."""

        # Run distillation
        result = await self.distillation.distill(message, user_id)

        # Route based on result
        if not result.should_process:
            # Handle non-LLM routes
            if result.route_type == RouteType.REJECT:
                content = result.rejection_reason
            elif result.route_type == RouteType.CACHE:
                content = result.cached_response
            elif result.route_type == RouteType.STATIC:
                content = result.static_response
            else:
                content = "I'm not sure how to help with that."

            return {
                "content": content,
                "route": result.route_type.value,
                "distillation": {
                    "intent": result.intent.value if result.intent else None,
                    "classification_latency_ms": result.classification_latency_ms,
                    "cost_saved_usd": 0.01,  # Estimated
                },
            }

        # Process with LLM
        llm_response = await self.llm.execute(
            request={"messages": [{"role": "user", "content": message}]},
            agent_type=self._get_agent_type(result.intent),
            model_tier=result.suggested_model_tier,
        )

        # Cache the response for future
        if result.cache_key:
            await self.distillation.cache.set(
                result.cache_key, llm_response["content"], ttl=3600
            )

        return {
            "content": llm_response["content"],
            "route": result.route_type.value,
            "model": llm_response.get("model"),
            "distillation": {
                "intent": result.intent.value if result.intent else None,
                "complexity": result.complexity.value if result.complexity else None,
                "classification_latency_ms": result.classification_latency_ms,
            },
        }

    def _get_agent_type(self, intent: Intent) -> str:
        """Map intent to agent type."""
        mapping = {
            Intent.SWAP_REQUEST: "swap_agent",
            Intent.PRICE_CHECK: "researcher",
            Intent.EXPLAIN_CONCEPT: "researcher",
        }
        return mapping.get(intent, "researcher")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


async def main():
    """Demonstrate distillation pass."""

    # Initialize components
    classifier = IntentClassifier()
    assessor = ComplexityAssessor()
    extractor = EntityExtractor()
    cache = CacheManager()
    static = StaticResponder()

    config = {"enabled": True}

    engine = DistillationEngine(
        intent_classifier=classifier,
        complexity_assessor=assessor,
        entity_extractor=extractor,
        cache_manager=cache,
        static_responder=static,
        config=config,
    )

    # Test queries
    test_queries = [
        "Hello!",
        "What's the price of ETH?",
        "Swap 1 ETH to USDC",
        "What is yield farming and how does it compare to staking?",
        "Tell me about the weather today",
    ]

    print("=" * 60)
    print("DISTILLATION PASS DEMONSTRATION")
    print("=" * 60)

    for query in test_queries:
        result = await engine.distill(query)

        print(f"\nQuery: '{query}'")
        print(f"  Route: {result.route_type.value}")
        print(f"  Intent: {result.intent.value if result.intent else 'N/A'}")
        print(
            f"  Complexity: {result.complexity.value if result.complexity else 'N/A'}"
        )
        print(f"  Should Process: {result.should_process}")
        print(f"  Model Tier: {result.suggested_model_tier or 'N/A'}")
        print(f"  Latency: {result.classification_latency_ms}ms")

        if result.static_response:
            print(f"  Static Response: {result.static_response[:50]}...")


if __name__ == "__main__":
    asyncio.run(main())
