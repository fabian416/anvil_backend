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
    sync_etherscan_transactions,
    sync_all_tokens_etherscan,
    sync_single_wallet_etherscan,
    verify_test_wallet,
)

# Lending, guest archival, and withdraw confirmation tasks
# These were previously in the shadowed tasks.py file and never loaded
from app.infrastructure.celery.tasks.lending_and_guest_tasks import (
    archive_guest_conversations,
    monitor_lending_health_factors,
    check_user_lending_health,
    refresh_lending_positions,
    confirm_withdraw_transaction,
)

# Earn position tasks (Aave V3 / Compound V3)
from app.infrastructure.celery.tasks.earn_position_tasks import (
    refresh_earn_positions,
    confirm_earn_transaction,
    reconcile_earn_transactions,
    recover_earn_positions,
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
    # Etherscan tasks
    "sync_etherscan_transactions",
    "sync_etherscan_balances",
    "sync_all_tokens_etherscan",
    "sync_single_wallet_etherscan",
    "verify_test_wallet",
    # Lending, guest, and withdraw tasks
    "archive_guest_conversations",
    "monitor_lending_health_factors",
    "check_user_lending_health",
    "refresh_lending_positions",
    "confirm_withdraw_transaction",
    # Earn position tasks (Aave V3 / Compound V3)
    "refresh_earn_positions",
    "confirm_earn_transaction",
    "reconcile_earn_transactions",
    "recover_earn_positions",
]
