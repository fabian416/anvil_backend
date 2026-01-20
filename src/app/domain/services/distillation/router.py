"""Distillation routing service."""
import hashlib
from decimal import Decimal
from typing import Optional, List, Dict, Any

from app.domain.services.distillation.complexity_assessor import ComplexityAssessor
from app.domain.services.distillation.entity_extractor import EntityExtractor
from app.domain.services.distillation.intent_classifier import IntentClassifier
from app.domain.value_objects.distillation import (
    CacheLevel,
    ComplexityLevel,
    DistillationConfig,
    DistillationResult,
    ExtractedEntities,
    Intent,
    RouteType,
)


class DistillationRouter:
    """
    Route requests based on classification results.
    
    Decision Matrix:
    - REJECT: Off-topic, harmful, policy violations
    - STATIC: Pre-defined templates (greeting, price, gas, balance)
    - CACHE: Previously seen queries (exact or semantic match)
    - LIGHT_LLM: Simple queries with fast models
    - FULL_LLM: Complex queries requiring full orchestration
    """
    
    def __init__(
        self,
        intent_classifier: IntentClassifier,
        complexity_assessor: ComplexityAssessor,
        entity_extractor: EntityExtractor,
        config: DistillationConfig,
    ):
        self.intent_classifier = intent_classifier
        self.complexity_assessor = complexity_assessor
        self.entity_extractor = entity_extractor
        self.config = config
    
    async def route(
        self,
        text: str,
        cache_lookup: Optional[str] = None,
        static_available: bool = False,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> DistillationResult:
        """
        Determine optimal route for request.
        
        Args:
            text: User query text
            cache_lookup: Cache hit content (if any)
            static_available: Whether static response is available
            
        Returns:
            DistillationResult with routing decision
        """
        # Normalize query
        normalized_query = self._normalize_query(text)
        
        # Step 1: Classify intent (async, supports LLM-based classification with conversation history)
        intent, intent_confidence = await self.intent_classifier.classify(
            text=text,
            conversation_history=conversation_history,  # Pass conversation history for context-aware classification
        )
        
        # Step 2: Assess complexity
        complexity = self.complexity_assessor.assess(text, intent)
        
        # Step 3: Extract entities
        entities = self.entity_extractor.extract(text)
        
        # Step 4: Generate cache key
        cache_key = self._build_cache_key(intent, entities, normalized_query)
        
        # Step 5: Check for rejection
        if self._should_reject(intent, text):
            return DistillationResult(
                should_process=False,
                route_type=RouteType.REJECT,
                intent=intent,
                complexity=complexity,
                entities=entities,
                rejection_reason=self._get_rejection_reason(intent),
                rejection_code="DISTILL_REJECTED",
                classification_confidence=intent_confidence,
            )
        
        # Step 6: Check cache hit
        if cache_lookup is not None:
            return DistillationResult(
                should_process=False,
                route_type=RouteType.CACHE,
                intent=intent,
                complexity=complexity,
                entities=entities,
                cache_key=cache_key,
                cache_hit=True,
                cache_level=CacheLevel.EXACT,  # Will be updated by cache manager
                cached_response=cache_lookup,
                classification_confidence=intent_confidence,
                estimated_cost_saved_usd=self._estimate_cost_saved(complexity),
            )
        
        # Step 7: Check static response availability
        if static_available:
            return DistillationResult(
                should_process=False,
                route_type=RouteType.STATIC,
                intent=intent,
                complexity=complexity,
                entities=entities,
                cache_key=cache_key,
                classification_confidence=intent_confidence,
                estimated_cost_saved_usd=self._estimate_cost_saved(complexity),
            )
        
        # Step 8: Check if forced to full LLM
        if intent in self.config.force_full_llm_intents:
            return DistillationResult(
                should_process=True,
                route_type=RouteType.FULL_LLM,
                intent=intent,
                complexity=complexity,
                entities=entities,
                suggested_model_tier="premium",
                suggested_agent=self._suggest_agent(intent),
                cache_key=cache_key,
                classification_confidence=intent_confidence,
            )
        
        # Step 9: Route based on complexity
        model_tier = self._select_model_tier(intent, complexity)
        
        if complexity in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE]:
            route_type = RouteType.LIGHT_LLM
        else:
            route_type = RouteType.FULL_LLM
        
        return DistillationResult(
            should_process=True,
            route_type=route_type,
            intent=intent,
            complexity=complexity,
            entities=entities,
            suggested_model_tier=model_tier,
            suggested_agent=self._suggest_agent(intent),
            cache_key=cache_key,
            classification_confidence=intent_confidence,
        )
    
    def _should_reject(self, intent: Intent, text: str) -> bool:
        """Check if request should be rejected."""
        # Reject off-topic
        if intent == Intent.OFF_TOPIC:
            return True
        
        # Reject harmful/policy violations (basic patterns)
        harmful_patterns = [
            r"(how to|teach me|explain).*(hack|exploit|attack)",
            r"(generate|create).*(illegal|fake|fraudulent)",
            r"(bypass|circumvent).*(security|authentication)",
        ]
        
        import re
        for pattern in harmful_patterns:
            if re.search(pattern, text.lower()):
                return True
        
        return False
    
    def _get_rejection_reason(self, intent: Intent) -> str:
        """Get human-readable rejection reason."""
        if intent == Intent.OFF_TOPIC:
            return "I'm specialized in DeFi and crypto assistance. I can help you with swaps, staking, lending, and other DeFi operations. What would you like to do?"
        
        return "I cannot assist with that request."
    
    def _normalize_query(self, text: str) -> str:
        """Normalize query for caching."""
        # Convert to lowercase
        normalized = text.lower().strip()
        
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        
        # Remove punctuation at end
        normalized = normalized.rstrip("?!.,")
        
        return normalized
    
    def _build_cache_key(
        self,
        intent: Intent,
        entities: ExtractedEntities,
        normalized_query: str,
    ) -> str:
        """Generate cache key from distillation results."""
        # Build key components
        components = [
            intent.value,
            ",".join(sorted(entities.tokens)),
            ",".join(sorted(entities.protocols)),
            normalized_query,
        ]
        
        # Hash for compact key
        key_string = "|".join(components)
        hash_digest = hashlib.sha256(key_string.encode()).hexdigest()
        
        return f"distill:v1:{hash_digest[:16]}"
    
    def _select_model_tier(
        self,
        intent: Intent,
        complexity: ComplexityLevel,
    ) -> str:
        """Select appropriate model tier based on intent and complexity."""
        # High-stakes intents always get premium
        high_stakes = {
            Intent.SWAP_REQUEST,
            Intent.BORROW_REQUEST,
            Intent.RISK_ASSESSMENT,
            Intent.STRATEGY_ADVICE,
        }
        
        if intent in high_stakes:
            return "premium"
        
        # Complexity-based selection
        tier_map = {
            ComplexityLevel.TRIVIAL: "economy",
            ComplexityLevel.SIMPLE: "economy",
            ComplexityLevel.MODERATE: "standard",
            ComplexityLevel.COMPLEX: "premium",
            ComplexityLevel.EXPERT: "premium",
        }
        
        return tier_map.get(complexity, "standard")
    
    def _suggest_agent(self, intent: Intent) -> str:
        """Suggest appropriate agent for intent."""
        # Map intents to agents
        agent_map = {
            Intent.SWAP_REQUEST: "trading",
            Intent.STAKE_REQUEST: "staking",
            Intent.LEND_REQUEST: "savings",
            Intent.BORROW_REQUEST: "aave",
            Intent.BRIDGE_REQUEST: "bridge",
            Intent.PORTFOLIO_ANALYSIS: "portfolio",
            Intent.RISK_ASSESSMENT: "risk",
            Intent.YIELD_OPTIMIZATION: "earning",
        }
        
        return agent_map.get(intent, "general")
    
    def _estimate_cost_saved(self, complexity: ComplexityLevel) -> Decimal:
        """Estimate cost saved by routing decision."""
        # Cost estimates per complexity level (avoided)
        cost_map = {
            ComplexityLevel.TRIVIAL: Decimal("0.002"),
            ComplexityLevel.SIMPLE: Decimal("0.005"),
            ComplexityLevel.MODERATE: Decimal("0.010"),
            ComplexityLevel.COMPLEX: Decimal("0.020"),
            ComplexityLevel.EXPERT: Decimal("0.050"),
        }
        
        return cost_map.get(complexity, Decimal("0.010"))
