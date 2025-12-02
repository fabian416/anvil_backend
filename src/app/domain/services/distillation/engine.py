"""Main distillation engine orchestrator."""
import time
from datetime import datetime
from typing import Optional
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
            return DistillationResult(
                should_process=True,
                route_type="FULL_LLM",
                intent="UNCLEAR",
                complexity="MODERATE",
                entities={},
            )
        
        # Step 1: Classify intent
        intent, intent_confidence = self.intent_classifier.classify(query)
        
        # Step 2: Assess complexity
        complexity = self.complexity_assessor.assess(query, intent)
        
        # Step 3: Extract entities
        entities = self.entity_extractor.extract(query)
        
        # Step 4: Check cache (if enabled)
        cache_hit_content = None
        cache_level = CacheLevel.NONE
        
        if config.cache_enabled:
            # Generate cache key
            normalized = query.lower().strip()
            import hashlib
            cache_key = f"distill:v1:{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"
            
            # Try cache lookup
            cache_hit_content, cache_level = await self.cache_manager.get(
                cache_key=cache_key,
                query=query,
                semantic_threshold=config.semantic_similarity_threshold,
            )
        else:
            cache_hit_content = None
            cache_level = CacheLevel.NONE
        
        # Step 5: Check static response availability (if enabled)
        static_available = False
        if config.static_responses_enabled and not cache_hit_content:
            static_available = await self.static_responder.check_available(
                intent=intent,
                entities=entities,
            )
        
        # Step 6: Route decision
        result = await self.router.route(
            text=query,
            cache_lookup=cache_hit_content,
            static_available=static_available,
        )
        
        # Step 7: Generate static response if routed
        if result.route_type == "STATIC":
            static_response = await self.static_responder.generate(
                intent=intent,
                entities=entities,
                user_context=user_context,
            )
            result.static_response = static_response
        
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
            created_at=datetime.utcnow(),
        )
        
        await self.telemetry_repo.log_request(telemetry)
