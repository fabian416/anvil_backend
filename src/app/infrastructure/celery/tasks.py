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
# Import LLM ranking tasks
from app.infrastructure.celery.tasks.llm_ranking import (
    recalculate_all_rankings,
    recalculate_agent_rankings,
)


@celery_app.task(name="populate_graph_protocols")
def populate_graph_protocols():
    """
    Populate/update protocols in the knowledge graph.
    """
    async def runner(container):
        from app.application.graph import PopulateGraphInteractor
        from app.domain.graph.ports import GraphRepository
        from app.domain.ports.external_data import DefiDataProvider
        
        graph_repo = await container.get(GraphRepository)
        data_provider = await container.get(DefiDataProvider)
        
        interactor = PopulateGraphInteractor(graph_repo, data_provider)
        stats = await interactor.populate_protocols(limit=100)
        
        print(f"Graph population complete: {stats}")
    
    asyncio.run(_run_task(runner))


@celery_app.task(name="update_graph_metadata")
def update_graph_metadata():
    """
    Update graph metadata and statistics.
    """
    async def runner(container):
        from app.domain.graph.ports import GraphRepository
        from sqlalchemy import text
        
        graph_repo = await container.get(GraphRepository)
        
        # Update graph stats using helper function
        await graph_repo.execute_cypher(
            "SELECT update_graph_stats('defi_knowledge_graph')"
        )
        
        print("Graph metadata updated")
    
    asyncio.run(_run_task(runner))


@celery_app.task(name="validate_graph_integrity")
def validate_graph_integrity():
    """
    Validate graph integrity and identify issues.
    """
    async def runner(container):
        from app.domain.graph.services import GraphService
        from app.domain.graph.ports import GraphRepository
        
        graph_repo = await container.get(GraphRepository)
        graph_service = GraphService(graph_repo)
        
        # Find circular dependencies
        cycles = await graph_service.find_circular_dependencies()
        
        if cycles:
            print(f"⚠️ Found {len(cycles)} circular dependencies!")
            for cycle in cycles[:5]:  # Log first 5
                names = [n.properties.get('name', 'Unknown') for n in cycle]
                print(f"  Cycle: {' -> '.join(names)}")
        else:
            print("✅ No circular dependencies found")
    
    asyncio.run(_run_task(runner))


@celery_app.task(name="generate_protocol_embeddings")
def generate_protocol_embeddings():
    """
    Generate embeddings for protocols.
    """
    async def runner(container):
        from app.application.graph import GenerateEmbeddingsInteractor
        
        interactor = await container.get(GenerateEmbeddingsInteractor)
        stats = await interactor.generate_protocol_embeddings(
            limit=100,
            force_regenerate=False,
        )
        
        print(f"Embedding generation complete: {stats}")
    
    asyncio.run(_run_task(runner))


@celery_app.task(name="check_user_risk_alerts")
def check_user_risk_alerts():
    """
    Check all users' protocols for risk changes and generate alerts.
    
    Runs every 15 minutes to monitor for:
    - Risk score increases
    - Anomaly detection
    - Critical risk levels
    - Dependency risks
    """
    async def runner(container):
        from app.application.alerts import RiskAlertMonitor
        
        monitor = await container.get(RiskAlertMonitor)
        alert_count = await monitor.check_all_users()
        
        print(f"Risk alert check complete: {alert_count} alerts generated")
    
    asyncio.run(_run_task(runner))


@celery_app.task(name="archive_guest_conversations")
def archive_guest_conversations():
    """
    Archive inactive guest conversations.
    
    Runs every hour at :00 to archive conversations that have been
    inactive for more than 1 hour. This keeps the guest_conversations
    table clean and ensures new sessions get fresh conversations.
    """
    async def runner(container):
        from datetime import datetime, UTC, timedelta
        from app.domain.guest.ports.guest_repository import GuestRepository
        
        repository = await container.get(GuestRepository)
        
        # Archive conversations older than 1 hour
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        archived_count = await repository.archive_inactive_conversations(one_hour_ago)
        
        print(f"Guest conversation archival complete: {archived_count} conversations archived")
    
    asyncio.run(_run_task(runner))


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
    # Graph maintenance tasks
    "populate-graph-protocols": {
        "task": "populate_graph_protocols",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "update-graph-metadata": {
        "task": "update_graph_metadata",
        "schedule": crontab(hour="*/6", minute=30),  # Every 6 hours
    },
    "validate-graph-integrity": {
        "task": "validate_graph_integrity",
        "schedule": crontab(hour=6, minute=0, day_of_week=1),  # Weekly Monday 6 AM
    },
    "generate-protocol-embeddings": {
        "task": "generate_protocol_embeddings",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    # Risk alert monitoring
    "check-user-risk-alerts": {
        "task": "check_user_risk_alerts",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    # LLM Ranking recalculation
    "recalculate-llm-rankings": {
        "task": "llm_ranking.recalculate_all_rankings",
        "schedule": crontab(hour=2, minute=0),  # Daily at 02:00 UTC
    },
    # Guest conversation archival
    "archive-guest-conversations": {
        "task": "archive_guest_conversations",
        "schedule": crontab(minute=0),  # Every hour at :00
    },
}
