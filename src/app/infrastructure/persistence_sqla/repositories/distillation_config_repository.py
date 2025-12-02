"""SQLAlchemy repository for distillation configuration."""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ports.distillation_repository import DistillationConfigRepository
from app.domain.value_objects.distillation import DistillationConfig, Intent
from app.infrastructure.persistence_sqla.mappings.distillation import (
    distillation_config,
)


class DistillationConfigRepositorySqla(DistillationConfigRepository):
    """SQLAlchemy implementation of config repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_config(self) -> DistillationConfig:
        """Get current distillation configuration."""
        # Fetch all config entries
        query = select(distillation_config)
        result = await self.session.execute(query)
        rows = result.all()
        
        # Build config from database rows
        config_dict = {row.config_key: row.config_value for row in rows}
        
        # Parse feature flags
        feature_flags = config_dict.get("feature_flags", {})
        
        # Parse thresholds
        thresholds = config_dict.get("thresholds", {})
        
        # Parse routing rules
        routing_rules = config_dict.get("routing_rules", {})
        
        # Build cache TTL mapping
        cache_ttl_by_intent = {}
        cache_ttl_config = routing_rules.get("cache_ttl_by_intent", {})
        for intent_str, ttl in cache_ttl_config.items():
            try:
                intent_enum = Intent(intent_str)
                cache_ttl_by_intent[intent_enum] = ttl
            except ValueError:
                continue
        
        # Build force full LLM list
        force_full_llm_intents = []
        force_list = routing_rules.get("force_full_llm_intents", [])
        for intent_str in force_list:
            try:
                intent_enum = Intent(intent_str)
                force_full_llm_intents.append(intent_enum)
            except ValueError:
                continue
        
        return DistillationConfig(
            enabled=feature_flags.get("enabled", True),
            cache_enabled=feature_flags.get("cache_enabled", True),
            static_responses_enabled=feature_flags.get("static_responses_enabled", True),
            semantic_cache_enabled=feature_flags.get("semantic_cache_enabled", True),
            min_confidence_threshold=float(thresholds.get("min_confidence", 0.7)),
            semantic_similarity_threshold=float(thresholds.get("semantic_similarity", 0.95)),
            max_classification_latency_ms=int(thresholds.get("max_latency_ms", 100)),
            cache_ttl_by_intent=cache_ttl_by_intent,
            force_full_llm_intents=force_full_llm_intents,
        )
    
    async def update_config(
        self,
        config_key: str,
        config_value: dict,
        modified_by: Optional[UUID] = None,
    ) -> None:
        """Update specific configuration."""
        from datetime import datetime
        
        query = (
            update(distillation_config)
            .where(distillation_config.c.config_key == config_key)
            .values(
                config_value=config_value,
                modified_by=modified_by,
                modified_at=datetime.utcnow(),
            )
        )
        
        await self.session.execute(query)
        await self.session.commit()
