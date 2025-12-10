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
            "app.infrastructure.celery.tasks",
            "app.infrastructure.celery.compat_tasks",
            "app.infrastructure.celery.tasks.transaction_confirmation_tasks",
        ],
    )
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_serializer = "json"
    app.conf.timezone = "UTC"
    app.conf.enable_utc = True

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
            "options": {"queue": "default"},
        },
    }

    # Disable the task if transaction confirmation is disabled
    if not tx_conf.enabled:
        app.conf.beat_schedule = {}

    return app


celery_app = create_celery()
