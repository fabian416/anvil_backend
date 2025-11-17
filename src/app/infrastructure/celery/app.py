import os
from celery import Celery

from app.setup.config.settings import load_settings


def create_celery() -> Celery:
    settings = load_settings()
    celery_cfg = getattr(settings, "celery", {}) if hasattr(settings, "celery") else {}
    app_name = os.getenv("CELERY_APP_NAME") or celery_cfg.get("app_name", "baseapi_hexagonal")
    broker = os.getenv("CELERY_BROKER_URL") or celery_cfg.get("broker_url", None)
    backend = os.getenv("CELERY_RESULT_BACKEND") or celery_cfg.get("result_backend", None)

    app = Celery(
        app_name,
        broker=broker or "redis://localhost:6379/0",
        backend=backend or "redis://localhost:6379/1",
        include=[
            "app.infrastructure.celery.tasks",
            "app.infrastructure.celery.compat_tasks",
        ],
    )
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_serializer = "json"
    app.conf.timezone = "UTC"
    app.conf.enable_utc = True
    return app


celery_app = create_celery()


