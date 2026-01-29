"""
Main Celery tasks module.

This module defines:
1. Core maintenance tasks (cleanup sessions, password resets)
2. Agent processing tasks
3. Graph maintenance tasks
4. Risk monitoring tasks
5. Beat schedule for all periodic tasks

Sub-module tasks (distillation, projects, LLM ranking) are imported at the end
to ensure all local tasks are registered first.
"""
import asyncio
from celery.schedules import crontab

from app.infrastructure.celery.app import celery_app
from app.setup.ioc.application import ApplicationProvider
from app.setup.ioc.infrastructure import infrastructure_provider
from app.setup.ioc.presentation import PresentationProvider
from app.setup.ioc.settings import SettingsProvider
from app.setup.ioc.graph import GraphProvider
from app.setup.app_factory import create_async_ioc_container
from app.setup.config.settings import load_settings
from app.application.maintenance.tasks import (
    CleanupExpiredPasswordResetsTask,
    CleanupExpiredSessionsTask,
)


async def _run_task(coro_factory):
    """Helper to run async tasks with DI container."""
    settings = load_settings()
    container = create_async_ioc_container(
        providers=(
            ApplicationProvider(),
            infrastructure_provider(),
            PresentationProvider(),
            SettingsProvider(),
            GraphProvider(),
        ),
        settings=settings,
    )
    try:
        # Enter request scope so REQUEST-scoped providers can be resolved
        async with container() as request_container:  # type: ignore[misc]
            await coro_factory(request_container)
    finally:
        await container.close()


# ============================================================================
# MAINTENANCE TASKS
# ============================================================================

@celery_app.task(name="cleanup_expired_sessions")
def cleanup_expired_sessions():
    """Clean up expired user sessions."""
    async def runner(container):
        from app.application.maintenance.ports import AuthSessionRepository

        repo = await container.get(AuthSessionRepository)
        task = CleanupExpiredSessionsTask(repo)
        await task.run()

    asyncio.run(_run_task(runner))


@celery_app.task(name="cleanup_expired_password_resets")
def cleanup_expired_password_resets():
    """Clean up expired password reset tokens."""
    async def runner(container):
        from app.application.maintenance.ports import PasswordResetRepository

        repo = await container.get(PasswordResetRepository)
        task = CleanupExpiredPasswordResetsTask(repo)
        await task.run()

    asyncio.run(_run_task(runner))


# ============================================================================
# AGENT PROCESSING TASKS
# ============================================================================

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
            message="Task processing..."  # In real task, fetch message content from DB
        )

    asyncio.run(_run_task(runner))


@celery_app.task(name="update_agent_stats")
def update_agent_stats():
    """Periodic task to aggregate agent performance stats."""
    async def runner(container):
        # Logic to query logs and update agent_performance_stats table
        print("Updating agent stats...")
        pass

    asyncio.run(_run_task(runner))


# ============================================================================
# GRAPH MAINTENANCE TASKS
# ============================================================================

@celery_app.task(name="populate_graph_protocols")
def populate_graph_protocols():
    """Populate/update protocols in the knowledge graph."""
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
    """Update graph metadata and statistics."""
    async def runner(container):
        from app.domain.graph.ports import GraphRepository
        
        graph_repo = await container.get(GraphRepository)
        
        # Update graph stats using helper function
        await graph_repo.execute_cypher(
            "SELECT update_graph_stats('defi_knowledge_graph')"
        )
        
        print("Graph metadata updated")
    
    asyncio.run(_run_task(runner))


@celery_app.task(name="validate_graph_integrity")
def validate_graph_integrity():
    """Validate graph integrity and identify issues."""
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
    """Generate embeddings for protocols."""
    async def runner(container):
        from app.application.graph import GenerateEmbeddingsInteractor
        
        interactor = await container.get(GenerateEmbeddingsInteractor)
        stats = await interactor.generate_protocol_embeddings(
            limit=100,
            force_regenerate=False,
        )
        
        print(f"Embedding generation complete: {stats}")
    
    asyncio.run(_run_task(runner))


# ============================================================================
# RISK MONITORING TASKS
# ============================================================================

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


# ============================================================================
# IMPORT SUB-MODULE TASKS
# These imports register additional tasks from specialized modules.
# They are imported at the end to ensure all local tasks are registered first.
# ============================================================================

# Import distillation tasks
from app.infrastructure.celery.tasks.distillation_tasks import (
    aggregate_distillation_telemetry,
    cleanup_expired_cache,
    cache_llm_response,
)

# Import projects tasks
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

# Import LLM orchestration tasks
from app.infrastructure.celery.tasks.llm_orchestration import (
    recalculate_llm_rankings,
    aggregate_llm_telemetry,
    llm_provider_health_checks,
    reset_daily_budgets,
    cleanup_old_llm_data,
)


# ============================================================================
# CONSOLIDATED BEAT SCHEDULE
# All periodic tasks are defined here. This is the single source of truth
# for task scheduling. Sub-modules should NOT define their own beat_schedule.
# ============================================================================
celery_app.conf.beat_schedule = {
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
        "schedule": crontab(minute=5),  # Run at :05 of every hour
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
        "schedule": crontab(hour=5, minute=0, day_of_week=0),  # Weekly Sunday 5 AM
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
        "schedule": crontab(hour=6, minute=0, day_of_week=1),  # Weekly Monday 6 AM
        "options": {"queue": "graph"},
    },
    "generate-protocol-embeddings": {
        "task": "generate_protocol_embeddings",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        "options": {"queue": "graph"},
    },
    
    # =========================
    # Risk Alert Monitoring
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
        "schedule": crontab(hour=4, minute=0, day_of_week=0),  # Weekly Sunday 4 AM
        "options": {"queue": "llm"},
    },
}


# Export all tasks for discovery
__all__ = [
    # Maintenance
    "cleanup_expired_sessions",
    "cleanup_expired_password_resets",
    # Agent
    "process_agent_response",
    "update_agent_stats",
    # Graph
    "populate_graph_protocols",
    "update_graph_metadata",
    "validate_graph_integrity",
    "generate_protocol_embeddings",
    # Risk
    "check_user_risk_alerts",
    # Distillation (from sub-module)
    "aggregate_distillation_telemetry",
    "cleanup_expired_cache",
    "cache_llm_response",
    # Projects (from sub-module)
    "reindex_knowledge_base",
    "evaluate_auto_assignment_rules",
    "aggregate_project_analytics",
    "check_knowledge_base_health",
    # LLM Ranking (from sub-module)
    "recalculate_all_rankings",
    "recalculate_agent_rankings",
    # LLM Orchestration (from sub-module)
    "recalculate_llm_rankings",
    "aggregate_llm_telemetry",
    "llm_provider_health_checks",
    "reset_daily_budgets",
    "cleanup_old_llm_data",
]
