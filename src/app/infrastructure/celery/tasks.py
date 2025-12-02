import asyncio
from dishka import Scope
from celery.schedules import crontab

from app.infrastructure.celery.app import celery_app
from app.setup.ioc.provider_registry import get_providers
from app.setup.ioc.application import ApplicationProvider
from app.setup.ioc.infrastructure import infrastructure_provider
from app.setup.ioc.presentation import PresentationProvider
from app.setup.ioc.settings import SettingsProvider
from app.setup.app_factory import create_async_ioc_container
from app.setup.config.settings import load_settings
from app.application.maintenance.tasks import (
    CleanupExpiredPasswordResetsTask,
    CleanupExpiredSessionsTask,
)


async def _run_task(coro_factory):
    settings = load_settings()
    container = create_async_ioc_container(
        providers=(
            ApplicationProvider(),
            infrastructure_provider(),
            PresentationProvider(),
            SettingsProvider(),
        ),
        settings=settings,
    )
    try:
        # Enter request scope so REQUEST-scoped providers can be resolved
        async with container() as request_container:  # type: ignore[misc]
            await coro_factory(request_container)
    finally:
        await container.close()


@celery_app.task(name="cleanup_expired_sessions")
def cleanup_expired_sessions():
    async def runner(container):
        from app.application.maintenance.ports import AuthSessionRepository

        repo = await container.get(AuthSessionRepository)
        task = CleanupExpiredSessionsTask(repo)
        await task.run()

    asyncio.run(_run_task(runner))


@celery_app.task(name="cleanup_expired_password_resets")
def cleanup_expired_password_resets():
    async def runner(container):
        from app.application.maintenance.ports import PasswordResetRepository

        repo = await container.get(PasswordResetRepository)
        task = CleanupExpiredPasswordResetsTask(repo)
        await task.run()

    asyncio.run(_run_task(runner))


@celery_app.task(name="process_agent_response")
def process_agent_response(conversation_id: str, message_id: str):
    """
    Background task to process a user message and generate an AI response.
    """
    async def runner(container):
        from app.domain.ports.ai.agent_gateway import AgentGateway
        from uuid import UUID
        
        # Get Gateway
        gateway = await container.get(AgentGateway)
        
        # Execute (Mock User ID for now, would be passed in task payload in real impl)
        await gateway.process_message(
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            session_id=str(conversation_id),
            message="Task processing..." # In real task, fetch message content from DB
        )

    asyncio.run(_run_task(runner))


@celery_app.task(name="update_agent_stats")
def update_agent_stats():
    """
    Periodic task to aggregate agent performance stats.
    """
    async def runner(container):
        # Logic to query logs and update agent_performance_stats table
        print("Updating agent stats...")
        pass

    asyncio.run(_run_task(runner))


# Import new distillation and projects tasks
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


celery_app.conf.beat_schedule = {
    # Existing maintenance tasks
    "cleanup-expired-sessions": {
        "task": "cleanup_expired_sessions",
        "schedule": crontab(hour=0, minute=0),
    },
    "cleanup-expired-password-resets": {
        "task": "cleanup_expired_password_resets",
        "schedule": crontab(minute=0),
    },
    "update-agent-stats": {
        "task": "update_agent_stats",
        "schedule": crontab(minute="*/5"), # Every 5 minutes
    },
    # New distillation tasks
    "aggregate-distillation-telemetry": {
        "task": "aggregate_distillation_telemetry",
        "schedule": crontab(minute=5),  # Run at :05 of every hour
    },
    "cleanup-expired-cache": {
        "task": "cleanup_expired_cache",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    # New projects tasks
    "aggregate-project-analytics": {
        "task": "aggregate_project_analytics",
        "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
    },
    "check-knowledge-base-health": {
        "task": "check_knowledge_base_health",
        "schedule": crontab(hour=5, minute=0, day_of_week=0),  # Weekly Sunday 5 AM
    },
}
