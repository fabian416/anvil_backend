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
    Intent,  # Kept for compatibility but not used for routing
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
        # ✨ NO INTENT CLASSIFICATION - Direct routing to LLM ✨
        # We don't use intents - everything goes to LLM for natural responses
        
        # Normalize query
        normalized_query = self._normalize_query(text)
        
        # Step 1: Assess complexity (without intent - just based on query text)
        # Simple heuristic: short queries are simple, long queries are complex
        query_length = len(text.split())
        if query_length <= 3:
            complexity = ComplexityLevel.SIMPLE
        elif query_length <= 10:
            complexity = ComplexityLevel.MODERATE
        else:
            complexity = ComplexityLevel.COMPLEX
        
        # Step 2: Extract entities (for cache key generation only)
        entities = self.entity_extractor.extract(text)
        
        # Step 3: Generate cache key (without intent)
        cache_key = self._build_cache_key_no_intent(entities, normalized_query)
        
        # Step 4: Check cache hit
        if cache_lookup is not None:
            return DistillationResult(
                should_process=False,
                route_type=RouteType.CACHE,
                intent=Intent.UNCLEAR,  # Dummy intent for compatibility (not used)
                complexity=complexity,
                entities=entities,
                cache_key=cache_key,
                cache_hit=True,
                cache_level=CacheLevel.EXACT,
                cached_response=cache_lookup,
                classification_confidence=1.0,
                estimated_cost_saved_usd=self._estimate_cost_saved(complexity),
            )
        
        # Step 5: Route based on complexity only (NO intent-based routing)
        # Everything goes to LLM for natural, conversational responses
        if complexity in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE]:
            route_type = RouteType.LIGHT_LLM
            model_tier = "economy"
        else:
            route_type = RouteType.FULL_LLM
            model_tier = "standard"
        
        return DistillationResult(
            should_process=True,
            route_type=route_type,
            intent=Intent.UNCLEAR,  # Dummy intent for compatibility (not used)
            complexity=complexity,
            entities=entities,
            suggested_model_tier=model_tier,
            suggested_agent="chat",  # Default to chat agent
            cache_key=cache_key,
            classification_confidence=1.0,  # No classification, so confidence is 1.0
        )
    
    def _should_reject(self, intent: Intent, text: str) -> bool:
        """Check if request should be rejected (NO INTENT-BASED - pattern-based only)."""
        # Reject harmful/policy violations (basic patterns only - no intent classification)
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
        return "I'm specialized in DeFi and crypto assistance. I can help you with swaps, staking, lending, and other DeFi operations. What would you like to do?"
    
    def _normalize_query(self, text: str) -> str:
        """Normalize query for caching."""
        # Convert to lowercase
        normalized = text.lower().strip()
        
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        
        # Remove punctuation at end
        normalized = normalized.rstrip("?!.,")
        
        return normalized
    
    def _build_cache_key_no_intent(
        self,
        entities: ExtractedEntities,
        normalized_query: str,
    ) -> str:
        """Generate cache key without intent (intent-free routing)."""
        # Build key components (no intent)
        components = [
            ",".join(sorted(entities.tokens)),
            ",".join(sorted(entities.protocols)),
            normalized_query,
        ]
        
        # Hash for compact key
        key_string = "|".join(components)
        hash_digest = hashlib.sha256(key_string.encode()).hexdigest()
        
        return f"distill:v2:{hash_digest[:16]}"
    
    def _build_cache_key(
        self,
        intent: Intent,
        entities: ExtractedEntities,
        normalized_query: str,
    ) -> str:
        """Generate cache key from distillation results (legacy - not used)."""
        # This method is kept for compatibility but not used
        return self._build_cache_key_no_intent(entities, normalized_query)
    
    def _select_model_tier(
        self,
        intent: Intent,
        complexity: ComplexityLevel,
    ) -> str:
        """Select appropriate model tier based on complexity only (NO INTENT)."""
        # Complexity-based selection only
        tier_map = {
            ComplexityLevel.TRIVIAL: "economy",
            ComplexityLevel.SIMPLE: "economy",
            ComplexityLevel.MODERATE: "standard",
            ComplexityLevel.COMPLEX: "premium",
            ComplexityLevel.EXPERT: "premium",
        }
        
        return tier_map.get(complexity, "standard")
    
    def _suggest_agent(self, intent: Intent) -> str:
        """Suggest appropriate agent (default to chat - NO INTENT-BASED ROUTING)."""
        # Always default to chat agent - Supervisor Coordinator will route correctly
        return "chat"
    
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
