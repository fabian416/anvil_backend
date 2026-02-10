import os

from celery import Celery
from celery.schedules import crontab

from app.setup.config.settings import load_settings


def create_celery() -> Celery:
    settings = load_settings()
    celery_cfg = getattr(settings, "celery", {}) if hasattr(settings, "celery") else {}
    app_name = os.getenv("CELERY_APP_NAME") or celery_cfg.get(
        "app_name", "baseapi_hexagonal"
    )
    broker = os.getenv("CELERY_BROKER_URL") or celery_cfg.get("broker_url", None)
    backend = os.getenv("CELERY_RESULT_BACKEND") or celery_cfg.get(
        "result_backend", None
    )

    app = Celery(
        app_name,
        broker=broker or "redis://localhost:6379/0",
        backend=backend or "redis://localhost:6379/1",
        include=[
            "app.infrastructure.celery.main_tasks",
            "app.infrastructure.celery.tasks",
            "app.infrastructure.celery.compat_tasks",
            "app.infrastructure.celery.tasks.transaction_confirmation_tasks",
            "app.infrastructure.celery.tasks.money_market_tasks",
            "app.infrastructure.celery.tasks.privy_balance_tasks",
            "app.infrastructure.celery.tasks.etherscan_balance_tasks",
            "app.infrastructure.celery.tasks.user_context_tasks",
            "app.infrastructure.celery.tasks.wallet_qr_tasks",
        ],
    )
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_serializer = "json"
    app.conf.timezone = "UTC"
    app.conf.enable_utc = True

    # Celery 6.0+ compatibility: Explicitly enable broker connection retry on startup
    # Maintains current behavior and silences CPendingDeprecationWarning
    app.conf.broker_connection_retry_on_startup = True

    # =========================================================================
    # Task Routing Configuration
    # Workers especializados para evitar latencia y mejorar performance
    # =========================================================================

    # Definir colas especializadas
    app.conf.task_routes = {
        # Maintenance tasks - baja prioridad, puede esperar
        "cleanup_expired_sessions": {"queue": "maintenance"},
        "cleanup_expired_password_resets": {"queue": "maintenance"},
        "invalidate_all_sessions": {"queue": "maintenance"},
        # Agent tasks - alta prioridad, tiempo real
        "process_agent_response": {"queue": "agents"},
        "update_agent_stats": {"queue": "agents"},
        # Graph tasks - procesamiento pesado, puede ser lento
        "populate_graph_protocols": {"queue": "graph"},
        "update_graph_metadata": {"queue": "graph"},
        "validate_graph_integrity": {"queue": "graph"},
        "generate_protocol_embeddings": {"queue": "graph"},
        # Distillation tasks - procesamiento de LLM
        "aggregate_distillation_telemetry": {"queue": "distillation"},
        "cleanup_expired_cache": {"queue": "distillation"},
        "cache_llm_response": {"queue": "distillation"},
        # Projects tasks - procesamiento de knowledge base
        "reindex_knowledge_base": {"queue": "projects"},
        "evaluate_auto_assignment_rules": {"queue": "projects"},
        "aggregate_project_analytics": {"queue": "projects"},
        "check_knowledge_base_health": {"queue": "projects"},
        # LLM tasks - ranking y orchestration
        "recalculate_all_rankings": {"queue": "llm"},
        "recalculate_agent_rankings": {"queue": "llm"},
        "recalculate_llm_rankings": {"queue": "llm"},
        "aggregate_llm_telemetry": {"queue": "llm"},
        "llm_provider_health_checks": {"queue": "llm"},
        "reset_daily_budgets": {"queue": "llm"},
        "cleanup_old_llm_data": {"queue": "llm"},
        # Transaction confirmation - crítico, alta prioridad
        "confirm_pending_transactions": {"queue": "transactions"},
        "confirm_pending_transactions_mainnet": {"queue": "transactions"},
        "confirm_pending_transactions_testnet": {"queue": "transactions"},
        # Risk monitoring
        "check_user_risk_alerts": {"queue": "risk"},
        # Email tasks
        "send_email": {"queue": "email"},
        "tasks.email_tasks.*": {"queue": "email"},
        # Money market tasks - cache warming (alta prioridad, latencia crítica)
        "money_market.warm_cache": {"queue": "money_market"},
        "money_market.check_alerts": {"queue": "money_market"},
        "money_market.aggregate_analytics": {"queue": "money_market"},
        "money_market.cleanup_cache": {"queue": "maintenance"},
        # Lending tasks - health monitoring and position refresh
        "monitor_lending_health_factors": {"queue": "risk"},
        "refresh_lending_positions": {"queue": "maintenance"},
        "check_user_lending_health": {"queue": "risk"},
        # Privy wallet balance sync
        "privy.sync_wallet_balances": {"queue": "maintenance"},
        "privy.sync_single_wallet_balance": {"queue": "maintenance"},
        # Etherscan sync (transactions first, then balance/token)
        "etherscan.sync_transactions": {"queue": "maintenance"},
        "etherscan.sync_balances": {"queue": "maintenance"},
        "etherscan.sync_single_wallet": {"queue": "maintenance"},
        "etherscan.verify_test_wallet": {"queue": "maintenance"},
        # Wallet QR code generation
        "generate_wallet_qr_codes": {"queue": "maintenance"},
    }

    # Configuración de colas con prioridades
    app.conf.task_default_queue = "default"
    app.conf.task_default_exchange = "tasks"
    app.conf.task_default_exchange_type = "direct"
    app.conf.task_default_routing_key = "default"

    # Configuración de workers (concurrency por tipo de worker)
    app.conf.worker_prefetch_multiplier = 4  # Prefetch 4 tasks at a time
    app.conf.worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks

    # =========================================================================
    # Celery Beat Schedule (Periodic Tasks)
    # =========================================================================
    # Get transaction confirmation settings
    tx_conf = settings.transaction_confirmation
    tx_interval = tx_conf.interval_seconds if tx_conf.enabled else 0

    app.conf.beat_schedule = {
        # =========================
        # Transaction Confirmation
        # =========================
        "confirm-pending-transactions": {
            "task": "confirm_pending_transactions",
            "schedule": float(tx_interval) if tx_interval > 0 else 30.0,
            "kwargs": {
                "limit": tx_conf.batch_limit,
                "older_than_seconds": tx_conf.older_than_seconds,
                "use_testnet": tx_conf.use_testnet,
            },
            "options": {"queue": "transactions"},
        },
        # =========================
        # Money Market Tasks
        # =========================
        "money-market-warm-cache": {
            "task": "money_market.warm_cache",
            "schedule": 60.0,  # Every 60 seconds
            "options": {"queue": "money_market"},
        },
        "money-market-check-alerts": {
            "task": "money_market.check_alerts",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "money_market"},
        },
        "money-market-aggregate-analytics": {
            "task": "money_market.aggregate_analytics",
            "schedule": crontab(minute=0),  # Every hour at :00
            "options": {"queue": "money_market"},
        },
        "money-market-cleanup-cache": {
            "task": "money_market.cleanup_cache",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3:00 AM
            "options": {"queue": "maintenance"},
        },
        # =========================
        # Lending Tasks
        # =========================
        "monitor-lending-health-factors": {
            "task": "monitor_lending_health_factors",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
            "options": {"queue": "risk"},
        },
        "refresh-lending-positions": {
            "task": "refresh_lending_positions",
            "schedule": crontab(minute=30),  # Every hour at :30
            "options": {"queue": "maintenance"},
        },
        # =========================
        # Wallet Balance Sync
        # =========================
        "privy-sync-wallet-balances": {
            "task": "privy.sync_wallet_balances",
            "schedule": 30.0,  # Every 30 seconds
            "options": {"queue": "maintenance"},
        },
        # Etherscan: sync transactions first, then balance, then tokens (same 5-min window; order in schedule)
        "etherscan-sync-transactions": {
            "task": "etherscan.sync_transactions",
            "schedule": 300.0,  # Every 5 minutes (runs before balance/token in same cycle)
            "options": {"queue": "maintenance"},
        },
        "etherscan-sync-balances": {
            "task": "etherscan.sync_balances",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "maintenance"},
        },
        "sync-all-tokens-etherscan": {
            "task": "etherscan.sync_all_tokens",
            "schedule": 30.0,  # Every 30 seconds (3-min freshness filter)
            "options": {"queue": "maintenance"},
        },
        # =========================
        # Wallet QR Code Generation
        # =========================
        "generate-wallet-qr-codes": {
            "task": "generate_wallet_qr_codes",
            "schedule": 180.0,  # Every 3 minutes
            "options": {"queue": "maintenance"},
        },
        # =========================
        # User Context & Portfolio
        # =========================
        "update-user-context": {
            "task": "update_user_context",
            "schedule": 30.0,  # Every 30 seconds
            "options": {"queue": "maintenance"},
        },
        "user-context-analytics": {
            "task": "user_context_analytics",
            "schedule": crontab(hour=6, minute=0),  # Daily at 6 AM
            "options": {"queue": "maintenance"},
        },
        # =========================
        # Maintenance Tasks
        # =========================
        "cleanup-expired-sessions": {
            "task": "cleanup_expired_sessions",
            "schedule": crontab(hour=0, minute=0),  # Daily at midnight
            "options": {"queue": "maintenance"},
        },
        "cleanup-expired-password-resets": {
            "task": "cleanup_expired_password_resets",
            "schedule": crontab(minute=0),  # Every hour
            "options": {"queue": "maintenance"},
        },
        "archive-guest-conversations": {
            "task": "archive_guest_conversations",
            "schedule": crontab(minute=0),  # Every hour at :00
            "options": {"queue": "maintenance"},
        },
        # =========================
        # Agent Tasks
        # =========================
        "update-agent-stats": {
            "task": "update_agent_stats",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
            "options": {"queue": "agents"},
        },
        # =========================
        # Distillation Tasks
        # =========================
        "aggregate-distillation-telemetry": {
            "task": "aggregate_distillation_telemetry",
            "schedule": crontab(minute=5),  # Every hour at :05
            "options": {"queue": "distillation"},
        },
        "cleanup-expired-cache": {
            "task": "cleanup_expired_cache",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
            "options": {"queue": "distillation"},
        },
        # =========================
        # Projects Tasks
        # =========================
        "aggregate-project-analytics": {
            "task": "aggregate_project_analytics",
            "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
            "options": {"queue": "projects"},
        },
        "check-knowledge-base-health": {
            "task": "check_knowledge_base_health",
            "schedule": crontab(hour=5, minute=0, day_of_week=0),  # Sunday 5 AM
            "options": {"queue": "projects"},
        },
        # =========================
        # Graph Maintenance Tasks
        # =========================
        "populate-graph-protocols": {
            "task": "populate_graph_protocols",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
            "options": {"queue": "graph"},
        },
        "update-graph-metadata": {
            "task": "update_graph_metadata",
            "schedule": crontab(hour="*/6", minute=30),  # Every 6 hours
            "options": {"queue": "graph"},
        },
        "validate-graph-integrity": {
            "task": "validate_graph_integrity",
            "schedule": crontab(hour=6, minute=0, day_of_week=1),  # Monday 6 AM
            "options": {"queue": "graph"},
        },
        "generate-protocol-embeddings": {
            "task": "generate_protocol_embeddings",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
            "options": {"queue": "graph"},
        },
        # =========================
        # Risk Monitoring Tasks
        # =========================
        "check-user-risk-alerts": {
            "task": "check_user_risk_alerts",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
            "options": {"queue": "risk"},
        },
        # =========================
        # LLM Orchestration Tasks
        # =========================
        "recalculate-llm-rankings": {
            "task": "recalculate_llm_rankings",
            "schedule": crontab(hour="*/1", minute=0),  # Every hour
            "options": {"queue": "llm"},
        },
        "aggregate-llm-telemetry": {
            "task": "aggregate_llm_telemetry",
            "schedule": crontab(hour="*/1", minute=10),  # Every hour at :10
            "options": {"queue": "llm"},
        },
        "llm-provider-health-checks": {
            "task": "llm_provider_health_checks",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
            "options": {"queue": "llm"},
        },
        "reset-daily-budgets": {
            "task": "reset_daily_budgets",
            "schedule": crontab(hour=0, minute=0),  # Daily at midnight
            "options": {"queue": "llm"},
        },
        "cleanup-old-llm-data": {
            "task": "cleanup_old_llm_data",
            "schedule": crontab(hour=4, minute=0, day_of_week=0),  # Sunday 4 AM
            "options": {"queue": "llm"},
        },
    }

    # If transaction confirmation is disabled, remove only that task
    if not tx_conf.enabled:
        app.conf.beat_schedule.pop("confirm-pending-transactions", None)

    return app


celery_app = create_celery()
