"""Celery tasks for background processing."""

# Import all tasks to register them with Celery
from app.infrastructure.celery.tasks.distillation_tasks import (
    aggregate_distillation_telemetry,
    cleanup_expired_cache,
    cache_llm_response,
)

from app.infrastructure.celery.tasks.projects_tasks import (
    reindex_knowledge_base,
    evaluate_auto_assignment_rules,
    aggregate_project_analytics,
    check_knowledge_base_health,
)

__all__ = [
    # Distillation tasks
    "aggregate_distillation_telemetry",
    "cleanup_expired_cache",
    "cache_llm_response",
    
    # Projects tasks
    "reindex_knowledge_base",
    "evaluate_auto_assignment_rules",
    "aggregate_project_analytics",
    "check_knowledge_base_health",
]
