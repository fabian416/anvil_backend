"""Main distillation engine orchestrator."""

import time
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from app.domain.ports.distillation_repository import (
    DistillationConfigRepository,
    DistillationTelemetryRepository,
)
from app.domain.services.distillation.complexity_assessor import ComplexityAssessor
from app.domain.services.distillation.entity_extractor import EntityExtractor
from app.domain.services.distillation.intent_classifier import IntentClassifier
from app.domain.services.distillation.router import DistillationRouter
from app.domain.value_objects.distillation import (
    CacheLevel,
    DistillationResult,
    DistillationTelemetry,
    Intent,
)
from app.infrastructure.distillation.cache_manager import CacheManager
from app.infrastructure.distillation.static_responder import StaticResponder


class DistillationEngine:
    """
    Main orchestrator for distillation pass.

    Flow:
    1. Check if distillation is enabled
    2. Classify intent
    3. Assess complexity
    4. Extract entities
    5. Check cache (exact → semantic)
    6. Check static response availability
    7. Route decision
    8. Log telemetry
    """

    def __init__(
        self,
        intent_classifier: IntentClassifier,
        complexity_assessor: ComplexityAssessor,
        entity_extractor: EntityExtractor,
        router: DistillationRouter,
        cache_manager: CacheManager,
        static_responder: StaticResponder,
        config_repo: DistillationConfigRepository,
        telemetry_repo: DistillationTelemetryRepository,
    ):
        self.intent_classifier = intent_classifier
        self.complexity_assessor = complexity_assessor
        self.entity_extractor = entity_extractor
        self.router = router
        self.cache_manager = cache_manager
        self.static_responder = static_responder
        self.config_repo = config_repo
        self.telemetry_repo = telemetry_repo

    async def distill(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        user_context: Optional[dict] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> DistillationResult:
        """
        Run distillation pass on query.

        Args:
            query: User query text
            user_id: Optional user ID
            user_context: Optional user context (time_of_day, etc.)

        Returns:
            DistillationResult with routing decision
        """
        start_time = time.time()
        request_id = str(uuid4())

        # Check if distillation is enabled
        config = await self.config_repo.get_config()
        if not config.enabled:
            # Distillation disabled, pass through
            from app.domain.value_objects.distillation import (
                RouteType,
                ComplexityLevel,
                Intent,
                ExtractedEntities,
            )

            return DistillationResult(
                should_process=True,
                route_type=RouteType.FULL_LLM,
                intent=Intent.UNCLEAR,  # Dummy intent for compatibility
                complexity=ComplexityLevel.MODERATE,
                entities=ExtractedEntities(),
            )

        # ✨ NO INTENT CLASSIFICATION - Direct routing to LLM ✨
        # We don't use intents - everything goes to LLM for natural responses

        from app.domain.value_objects.distillation import (
            RouteType,
            ComplexityLevel,
            Intent,
            ExtractedEntities,
        )

        # Step 1: Assess complexity (without intent - just based on query text)
        # Simple heuristic: short queries are simple, long queries are complex
        query_length = len(query.split())
        if query_length <= 3:
            complexity = ComplexityLevel.SIMPLE
        elif query_length <= 10:
            complexity = ComplexityLevel.MODERATE
        else:
            complexity = ComplexityLevel.COMPLEX

        # Step 2: Extract entities (for cache key generation only)
        entities = self.entity_extractor.extract(query)

        # Step 3: Check cache (if enabled)
        cache_hit_content = None
        cache_level = CacheLevel.NONE
        cache_key = None

        if config.cache_enabled:
            # Generate cache key (without intent)
            normalized = query.lower().strip()
            import hashlib

            # Build key without intent
            key_components = [
                ",".join(sorted(entities.tokens)),
                ",".join(sorted(entities.protocols)),
                normalized,
            ]
            key_string = "|".join(key_components)
            hash_digest = hashlib.sha256(key_string.encode()).hexdigest()
            cache_key = f"distill:v2:{hash_digest[:16]}"

            # Try cache lookup
            cache_hit_content, cache_level = await self.cache_manager.get(
                cache_key=cache_key,
                query=query,
                semantic_threshold=config.semantic_similarity_threshold,
            )
        else:
            cache_hit_content = None
            cache_level = CacheLevel.NONE
            # Still generate cache key for result
            normalized = query.lower().strip()
            import hashlib

            key_components = [
                ",".join(sorted(entities.tokens)),
                ",".join(sorted(entities.protocols)),
                normalized,
            ]
            key_string = "|".join(key_components)
            hash_digest = hashlib.sha256(key_string.encode()).hexdigest()
            cache_key = f"distill:v2:{hash_digest[:16]}"

        # Step 4: Route decision - NO static responses, NO intent-based routing
        # Everything goes to LLM for natural, conversational responses

        # If cache hit, return cached response
        if cache_hit_content:
            result = DistillationResult(
                should_process=False,
                route_type=RouteType.CACHE,
                intent=Intent.UNCLEAR,  # Dummy intent for compatibility (not used)
                complexity=complexity,
                entities=entities,
                cache_key=cache_key,
                cache_hit=True,
                cache_level=cache_level,
                cached_response=cache_hit_content,
                classification_confidence=1.0,
            )
        else:
            # Route to LLM based on complexity only (no intent classification)
            if complexity in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE]:
                route_type = RouteType.LIGHT_LLM
            else:
                route_type = RouteType.FULL_LLM

            result = DistillationResult(
                should_process=True,
                route_type=route_type,
                intent=Intent.UNCLEAR,  # Dummy intent for compatibility (not used)
                complexity=complexity,
                entities=entities,
                suggested_model_tier="economy"
                if complexity in [ComplexityLevel.TRIVIAL, ComplexityLevel.SIMPLE]
                else "standard",
                suggested_agent="chat",  # Default to chat agent
                cache_key=cache_key,
                classification_confidence=1.0,  # No classification, so confidence is 1.0
            )

        # Calculate latency
        end_time = time.time()
        classification_latency_ms = int((end_time - start_time) * 1000)
        result.classification_latency_ms = classification_latency_ms

        # Step 8: Log telemetry
        await self._log_telemetry(
            request_id=request_id,
            user_id=user_id,
            query=query,
            result=result,
        )

        return result

    async def cache_response(
        self,
        query: str,
        intent: str,
        entities: dict,
        response_content: str,
        source_model: Optional[str] = None,
        source_request_id: Optional[UUID] = None,
    ) -> None:
        """
        Cache a response for future requests.

        Args:
            query: Original query
            intent: Classified intent
            entities: Extracted entities
            response_content: Response to cache
            source_model: Model that generated response
            source_request_id: Original request ID
        """
        config = await self.config_repo.get_config()

        if not config.cache_enabled:
            return

        # Get TTL for intent
        from app.domain.value_objects.distillation import Intent

        intent_enum = Intent(intent)
        ttl_seconds = config.cache_ttl_by_intent.get(intent_enum, 3600)

        # Generate cache key
        normalized = query.lower().strip()
        import hashlib

        cache_key = f"distill:v1:{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"

        # Store in cache
        await self.cache_manager.set(
            cache_key=cache_key,
            query=query,
            intent=intent_enum,
            response_content=response_content,
            ttl_seconds=ttl_seconds,
            entities=entities,
            source_model=source_model,
            source_request_id=str(source_request_id) if source_request_id else None,
        )

    async def _log_telemetry(
        self,
        request_id: str,
        user_id: Optional[UUID],
        query: str,
        result: DistillationResult,
    ) -> None:
        """Log distillation telemetry."""
        telemetry = DistillationTelemetry(
            request_id=request_id,
            user_id=user_id,
            original_query=query,
            normalized_query=query.lower().strip(),
            intent=result.intent,
            intent_confidence=result.classification_confidence,
            complexity=result.complexity,
            entities=result.entities,
            route_type=result.route_type,
            routing_reason=result.rejection_reason or f"Routed to {result.route_type}",
            suggested_model_tier=result.suggested_model_tier,
            suggested_agent=result.suggested_agent,
            cache_key=result.cache_key,
            cache_hit=result.cache_hit,
            cache_level=result.cache_level,
            classification_latency_ms=result.classification_latency_ms,
            total_latency_ms=result.classification_latency_ms,  # Same for now
            was_processed=result.should_process,
            llm_request_id=None,  # Will be set later if processed
            created_at=datetime.now(UTC),
        )

        await self.telemetry_repo.log_request(telemetry)
