"""Celery background tasks for projects system."""
import asyncio
from datetime import datetime, timedelta, UTC
from celery import Task
from celery.schedules import crontab

from app.infrastructure.celery.app import celery_app
from app.setup.config.settings import load_settings
from app.setup.app_factory import create_async_ioc_container
from app.setup.ioc.provider_registry import get_providers


async def _run_task(coro_factory):
    """Helper to run async tasks with DI container."""
    settings = load_settings()
    container = create_async_ioc_container(
        providers=get_providers(),
        settings=settings,
    )
    try:
        async with container() as request_container:
            await coro_factory(request_container)
    finally:
        await container.close()


# ==================== Knowledge Base Reindexing ====================

@celery_app.task(name="reindex_knowledge_base")
def reindex_knowledge_base(knowledge_base_id: str):
    """
    Reindex a knowledge base (regenerate embeddings for all documents).
    
    Called manually or when knowledge base configuration changes.
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.repositories.knowledge_repository import (
            KnowledgeDocumentRepositorySqla,
            KnowledgeChunkRepositorySqla,
        )
        from app.domain.services.knowledge.document_processor import DocumentProcessor
        from uuid import UUID
        
        doc_repo = await container.get(KnowledgeDocumentRepositorySqla)
        processor = await container.get(DocumentProcessor)
        
        kb_uuid = UUID(knowledge_base_id)
        
        # Get all documents in knowledge base
        documents = await doc_repo.list_documents(knowledge_base_id=kb_uuid)
        
        print(f"[Reindex] Starting reindex for KB {knowledge_base_id} ({len(documents)} docs)")
        
        # Reprocess each document
        for doc in documents:
            try:
                chunk_count = await processor.process_document(doc)
                doc.mark_processed(chunk_count)
                await doc_repo.update_document(doc)
                print(f"[Reindex] Processed document {doc.id}: {chunk_count} chunks")
            except Exception as e:
                doc.mark_error(str(e))
                await doc_repo.update_document(doc)
                print(f"[Reindex] Error processing document {doc.id}: {e}")
        
        print(f"[Reindex] Completed reindex for KB {knowledge_base_id}")
    
    asyncio.run(_run_task(runner))


# ==================== Auto-Assignment Rule Evaluation ====================

@celery_app.task(name="evaluate_auto_assignment_rules")
def evaluate_auto_assignment_rules(user_id: str, user_context: dict):
    """
    Evaluate auto-assignment rules for a user.
    
    Called when:
    - User signs up (onboarding)
    - User makes significant portfolio changes
    - Periodic evaluation (daily)
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.repositories.assignment_repository import (
            AssignmentRuleRepositorySqla,
            UserAssignmentRepositorySqla,
        )
        from app.domain.services.assignment.assignment_service import AssignmentService
        from uuid import UUID
        
        rule_repo = await container.get(AssignmentRuleRepositorySqla)
        assignment_repo = await container.get(UserAssignmentRepositorySqla)
        assignment_service = await container.get(AssignmentService)
        
        user_uuid = UUID(user_id)
        
        # Get all active rules
        all_rules = await rule_repo.get_all_active_rules()
        
        # Get user's existing assignments
        existing_assignments = await assignment_repo.get_assignments_by_user(user_uuid)
        existing_project_ids = [a.project_id for a in existing_assignments if a.is_active]
        
        # Evaluate rules
        new_assignments = await assignment_service.auto_assign_user(
            user_id=user_uuid,
            user_context=user_context,
            rules=all_rules,
            existing_assignments=existing_project_ids,
        )
        
        # Save new assignments
        for assignment in new_assignments:
            await assignment_repo.add_assignment(assignment)
        
        print(f"[Auto-Assignment] User {user_id}: {len(new_assignments)} new assignments")
        
        # Check for auto-switch
        if new_assignments:
            for assignment in new_assignments:
                # Find the rule that triggered this assignment
                matching_rules = [
                    r for r in all_rules
                    if r.project_id == assignment.project_id
                ]
                if matching_rules and matching_rules[0].auto_switch:
                    # Auto-switch to this project
                    await assignment_repo.set_active_project(user_uuid, assignment.project_id)
                    print(f"[Auto-Assignment] Auto-switched user {user_id} to project {assignment.project_id}")
                    break
    
    asyncio.run(_run_task(runner))


# ==================== Project Analytics Aggregation ====================

@celery_app.task(name="aggregate_project_analytics")
def aggregate_project_analytics():
    """
    Aggregate project analytics (daily).
    
    Calculates:
    - Active users per project
    - Total messages per project
    - Average session duration
    """
    async def runner(container):
        from sqlalchemy import text
        from sqlalchemy.exc import ProgrammingError
        from psycopg.errors import UndefinedTable
        from app.infrastructure.adapters.types import MainAsyncSession

        session = await container.get(MainAsyncSession)
        
        try:
            # Calculate yesterday's date
            yesterday = datetime.now(UTC).date() - timedelta(days=1)
            
            # Aggregate query
            query = text("""
                INSERT INTO project_analytics_daily (
                    date,
                    project_id,
                    active_users,
                    total_messages,
                    avg_session_duration_seconds,
                    created_at
                )
                SELECT
                    :date as date,
                    uap.project_id,
                    COUNT(DISTINCT uap.user_id) as active_users,
                    COUNT(m.id) as total_messages,
                    AVG(EXTRACT(EPOCH FROM (m.created_at - c.created_at))) as avg_session_duration_seconds,
                    NOW() as created_at
                FROM user_active_projects uap
                LEFT JOIN conversations c ON c.user_id = uap.user_id
                LEFT JOIN messages m ON m.conversation_id = c.id
                WHERE DATE(c.created_at) = :date
                GROUP BY uap.project_id
                ON CONFLICT (date, project_id) DO UPDATE SET
                    active_users = EXCLUDED.active_users,
                    total_messages = EXCLUDED.total_messages,
                    avg_session_duration_seconds = EXCLUDED.avg_session_duration_seconds
            """)
            
            await session.execute(query, {"date": yesterday})
            await session.commit()
            
            print(f"[Analytics] Aggregated project analytics for {yesterday}")
        except ProgrammingError as e:
            if isinstance(e.orig, UndefinedTable) and "project_analytics_daily" in str(e):
                print(f"[Analytics] Skipping aggregation - table 'project_analytics_daily' does not exist yet. Run migrations to create it.")
            else:
                raise
        except Exception as e:
            print(f"[Analytics] Error aggregating project analytics: {e}")
            raise
    
    asyncio.run(_run_task(runner))


# ==================== Knowledge Base Health Check ====================

@celery_app.task(name="check_knowledge_base_health")
def check_knowledge_base_health():
    """
    Check health of knowledge bases (weekly).
    
    Identifies:
    - Documents with processing errors
    - Documents with low chunk counts (potential issues)
    - Stale documents (not updated in 90+ days)
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.repositories.knowledge_repository import (
            KnowledgeDocumentRepositorySqla,
        )
        from sqlalchemy import text
        from sqlalchemy.exc import ProgrammingError
        from psycopg.errors import UndefinedTable
        from app.infrastructure.adapters.types import MainAsyncSession

        session = await container.get(MainAsyncSession)
        
        try:
            # Find documents with errors
            error_query = text("""
                SELECT kb.name, kd.title, kd.processing_error
                FROM project_knowledge_documents kd
                JOIN project_knowledge_bases kb ON kb.id = kd.knowledge_base_id
                WHERE kd.processing_error IS NOT NULL
            """)
            error_result = await session.execute(error_query)
            errors = error_result.all()
            
            if errors:
                print(f"[KB Health] Found {len(errors)} documents with processing errors:")
                for row in errors:
                    print(f"  - KB: {row.name}, Doc: {row.title}, Error: {row.processing_error}")
            
            # Find documents with low chunk counts
            low_chunk_query = text("""
                SELECT kb.name, kd.title, kd.chunk_count
                FROM project_knowledge_documents kd
                JOIN project_knowledge_bases kb ON kb.id = kd.knowledge_base_id
                WHERE kd.is_processed = true AND kd.chunk_count < 3
            """)
            low_chunk_result = await session.execute(low_chunk_query)
            low_chunks = low_chunk_result.all()
            
            if low_chunks:
                print(f"[KB Health] Found {len(low_chunks)} documents with low chunk counts:")
                for row in low_chunks:
                    print(f"  - KB: {row.name}, Doc: {row.title}, Chunks: {row.chunk_count}")
            
            # Find stale documents
            stale_threshold = datetime.now(UTC) - timedelta(days=90)
            stale_query = text("""
                SELECT kb.name, kd.title, kd.updated_at
                FROM project_knowledge_documents kd
                JOIN project_knowledge_bases kb ON kb.id = kd.knowledge_base_id
                WHERE kd.updated_at < :threshold
            """)
            stale_result = await session.execute(stale_query, {"threshold": stale_threshold})
            stale = stale_result.all()
            
            if stale:
                print(f"[KB Health] Found {len(stale)} stale documents (90+ days old):")
                for row in stale:
                    print(f"  - KB: {row.name}, Doc: {row.title}, Updated: {row.updated_at}")
            
            print(f"[KB Health] Health check complete")
        except ProgrammingError as e:
            if isinstance(e.orig, UndefinedTable) and "project_knowledge_documents" in str(e):
                print(f"[KB Health] Skipping health check - table 'project_knowledge_documents' does not exist yet. Run migrations to create it.")
            else:
                raise
        except Exception as e:
            print(f"[KB Health] Error checking knowledge base health: {e}")
            raise
    
    asyncio.run(_run_task(runner))


# ==================== Register Periodic Tasks ====================

celery_app.conf.beat_schedule.update({
    # Aggregate project analytics daily at 4 AM
    "aggregate-project-analytics": {
        "task": "aggregate_project_analytics",
        "schedule": crontab(hour=4, minute=0),
    },
    
    # Check knowledge base health weekly (Sunday at 5 AM)
    "check-knowledge-base-health": {
        "task": "check_knowledge_base_health",
        "schedule": crontab(hour=5, minute=0, day_of_week=0),  # Sunday
    },
})
