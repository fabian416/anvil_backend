import os

from celery import Celery

from app.setup.config.settings import load_settings


def create_celery() -> Celery:
    settings = load_settings()
    celery_cfg = getattr(settings, "celery", {}) if hasattr(settings, "celery") else {}
    app_name = (
        os.getenv("CELERY_APP_NAME")
        or celery_cfg.get("app_name", "baseapi_hexagonal")
    )
    broker = os.getenv("CELERY_BROKER_URL") or celery_cfg.get("broker_url", None)
    backend = (
        os.getenv("CELERY_RESULT_BACKEND") or celery_cfg.get("result_backend", None)
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
        # Transaction Confirmation Worker - runs every N seconds
        # Confirms pending blockchain transactions and updates DB status
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
        # Money Market - Cache Warming (every 60 seconds)
        # Pre-fetches popular asset/chain combinations to ensure cache never expires
        "money-market-warm-cache": {
            "task": "money_market.warm_cache",
            "schedule": 60.0,  # Every 60 seconds (sync with cache TTL)
            "options": {"queue": "money_market"},
        },
        # Money Market - Rate Alerts (every 5 minutes)
        # Checks alert conditions and sends notifications
        "money-market-check-alerts": {
            "task": "money_market.check_alerts",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "money_market"},
        },
        # Money Market - Analytics Aggregation (every hour)
        # Aggregates comparison logs for analytics dashboard
        "money-market-aggregate-analytics": {
            "task": "money_market.aggregate_analytics",
            "schedule": crontab(minute=0),  # Every hour at :00
            "options": {"queue": "money_market"},
        },
        # Money Market - Cache Cleanup (daily at 3 AM)
        # Removes expired cache entries and old logs
        "money-market-cleanup-cache": {
            "task": "money_market.cleanup_cache",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3:00 AM UTC
            "options": {"queue": "maintenance"},
        },
    }

    # Disable the task if transaction confirmation is disabled
    if not tx_conf.enabled:
        app.conf.beat_schedule = {}

    return app


celery_app = create_celery()
