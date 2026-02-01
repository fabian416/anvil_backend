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

from app.infrastructure.celery.tasks.privy_balance_tasks import (
    sync_wallet_balances,
    sync_single_wallet_balance,
)

from app.infrastructure.celery.tasks.etherscan_balance_tasks import (
    sync_etherscan_balances,
    sync_single_wallet_etherscan,
    verify_test_wallet,
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

    # Privy balance tasks
    "sync_wallet_balances",
    "sync_single_wallet_balance",

    # Etherscan balance tasks
    "sync_etherscan_balances",
    "sync_single_wallet_etherscan",
    "verify_test_wallet",
]
