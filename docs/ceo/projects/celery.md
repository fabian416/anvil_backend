# Projects & Knowledge Bases Celery Tasks Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Projects & Knowledge Bases system has **4 implemented Celery tasks** for background processing:
1. Knowledge base reindexing
2. Auto-assignment rule evaluation
3. Project analytics aggregation
4. Knowledge base health checks

**Task File**: `src/app/infrastructure/celery/tasks/projects_tasks.py`

---

## 1. Existing Celery Tasks

### 1.1 Reindex Knowledge Base

**Task Name**: `reindex_knowledge_base`  
**Type**: Manual (triggered by admin or configuration change)

**Purpose**: Regenerate embeddings for all documents in a knowledge base.

**Implementation**:
```python
@celery_app.task(name="reindex_knowledge_base")
def reindex_knowledge_base(knowledge_base_id: str):
    """
    Reindex a knowledge base (regenerate embeddings for all documents).
    
    Called manually or when knowledge base configuration changes.
    """
    async def runner(container):
        doc_repo = await container.get(KnowledgeDocumentRepositorySqla)
        processor = await container.get(DocumentProcessor)
        
        kb_uuid = UUID(knowledge_base_id)
        
        # Get all documents in knowledge base
        documents = await doc_repo.list_documents(knowledge_base_id=kb_uuid)
        
        # Reprocess each document
        for doc in documents:
            try:
                chunk_count = await processor.process_document(doc)
                doc.mark_processed(chunk_count)
                await doc_repo.update_document(doc)
            except Exception as e:
                doc.mark_error(str(e))
                await doc_repo.update_document(doc)
    
    asyncio.run(_run_task(runner))
```

**Trigger Events**:
- Admin manually triggers reindex
- Knowledge base embedding model changed
- Chunk size/overlap configuration changed

**Usage**:
```python
from app.infrastructure.celery.tasks.projects_tasks import reindex_knowledge_base

# Trigger reindex
reindex_knowledge_base.delay(str(knowledge_base_id))
```

---

### 1.2 Evaluate Auto-Assignment Rules

**Task Name**: `evaluate_auto_assignment_rules`  
**Type**: Event-driven (triggered on user actions)

**Purpose**: Evaluate auto-assignment rules for a user and assign to matching projects.

**Implementation**:
```python
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
        
        # Check for auto-switch
        if new_assignments:
            for assignment in new_assignments:
                matching_rules = [
                    r for r in all_rules
                    if r.project_id == assignment.project_id
                ]
                if matching_rules and matching_rules[0].auto_switch:
                    await assignment_repo.set_active_project(user_uuid, assignment.project_id)
                    break
    
    asyncio.run(_run_task(runner))
```

**User Context Schema**:
```python
user_context = {
    "portfolio_value_usd": 150000,
    "tokens_held": ["ETH", "BTC", "AAVE", "UNI"],
    "trading_frequency": "daily",
    "risk_preference": "aggressive",
    "chains_used": ["ethereum", "arbitrum"],
    "protocols_used": ["uniswap", "aave"],
}
```

**Trigger Events**:
- User registration (onboarding)
- Portfolio value changes significantly (>10%)
- User connects new wallet
- Daily periodic evaluation

**Usage**:
```python
from app.infrastructure.celery.tasks.projects_tasks import evaluate_auto_assignment_rules

# Trigger evaluation
user_context = {
    "portfolio_value_usd": 150000,
    "tokens_held": ["ETH", "BTC"],
}
evaluate_auto_assignment_rules.delay(str(user_id), user_context)
```

---

### 1.3 Aggregate Project Analytics

**Task Name**: `aggregate_project_analytics`  
**Type**: Scheduled (daily)  
**Schedule**: Daily at 4:00 AM

**Purpose**: Calculate daily analytics for all projects.

**Implementation**:
```python
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
        session = await container.get(MainAsyncSession)
        
        yesterday = datetime.now(UTC).date() - timedelta(days=1)
        
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
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"aggregate-project-analytics": {
    "task": "aggregate_project_analytics",
    "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
},
```

**Metrics Calculated**:
- `active_users`: Distinct users who used the project
- `total_messages`: Total chat messages
- `avg_session_duration_seconds`: Average session length
- `new_users`: Users assigned that day
- `total_sessions`: Number of chat sessions
- `knowledge_queries`: Number of RAG queries
- `knowledge_hit_rate`: Success rate of RAG retrieval
- `tool_usage`: Tool execution counts by type

---

### 1.4 Check Knowledge Base Health

**Task Name**: `check_knowledge_base_health`  
**Type**: Scheduled (weekly)  
**Schedule**: Sundays at 5:00 AM

**Purpose**: Identify issues with knowledge bases.

**Implementation**:
```python
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
        session = await container.get(MainAsyncSession)
        
        # Find documents with errors
        error_query = text("""
            SELECT kb.name, kd.title, kd.processing_error
            FROM project_knowledge_documents kd
            JOIN project_knowledge_bases kb ON kb.id = kd.knowledge_base_id
            WHERE kd.processing_error IS NOT NULL
        """)
        error_result = await session.execute(error_query)
        errors = error_result.all()
        
        # Find documents with low chunk counts
        low_chunk_query = text("""
            SELECT kb.name, kd.title, kd.chunk_count
            FROM project_knowledge_documents kd
            JOIN project_knowledge_bases kb ON kb.id = kd.knowledge_base_id
            WHERE kd.is_processed = true AND kd.chunk_count < 3
        """)
        low_chunk_result = await session.execute(low_chunk_query)
        low_chunks = low_chunk_result.all()
        
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
        
        # Log results
        if errors:
            print(f"[KB Health] Found {len(errors)} documents with processing errors")
        if low_chunks:
            print(f"[KB Health] Found {len(low_chunks)} documents with low chunk counts")
        if stale:
            print(f"[KB Health] Found {len(stale)} stale documents (90+ days old)")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"check-knowledge-base-health": {
    "task": "check_knowledge_base_health",
    "schedule": crontab(hour=5, minute=0, day_of_week=0),  # Sunday at 5 AM
},
```

**Health Checks Performed**:
1. **Processing Errors**: Documents that failed embedding generation
2. **Low Chunk Counts**: Documents with <3 chunks (suspicious)
3. **Stale Documents**: Documents not updated in 90+ days

---

## 2. Complete Beat Schedule

```python
celery_app.conf.beat_schedule.update({
    # Aggregate project analytics daily at 4 AM
    "aggregate-project-analytics": {
        "task": "aggregate_project_analytics",
        "schedule": crontab(hour=4, minute=0),
    },
    
    # Check knowledge base health weekly (Sunday at 5 AM)
    "check-knowledge-base-health": {
        "task": "check_knowledge_base_health",
        "schedule": crontab(hour=5, minute=0, day_of_week=0),
    },
})
```

---

## 3. Recommended Additional Tasks

### 3.1 Sync User Portfolio Context

**Task Name**: `sync_user_portfolio_context`  
**Priority**: HIGH  
**Schedule**: Every 6 hours

**Purpose**: Update user context for assignment rule evaluation.

**Recommendation**:
```python
@celery_app.task(name="sync_user_portfolio_context")
def sync_user_portfolio_context():
    """
    Sync user portfolio context from wallets.
    
    Updates user_context with:
    - Current portfolio value
    - Token holdings
    - Chain activity
    - Protocol usage
    """
    async def runner(container):
        # Get all active users with wallets
        # Update portfolio context
        # Trigger assignment rule evaluation if significant changes
        pass
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"sync-user-portfolio-context": {
    "task": "sync_user_portfolio_context",
    "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
},
```

---

### 3.2 Clean Stale Assignments

**Task Name**: `clean_stale_assignments`  
**Priority**: MEDIUM  
**Schedule**: Weekly

**Purpose**: Deactivate assignments for inactive users.

**Recommendation**:
```python
@celery_app.task(name="clean_stale_assignments")
def clean_stale_assignments():
    """
    Deactivate assignments for users inactive for 90+ days.
    """
    async def runner(container):
        session = await container.get(MainAsyncSession)
        
        stale_threshold = datetime.now(UTC) - timedelta(days=90)
        
        # Mark assignments as inactive for users with no recent activity
        await session.execute(text("""
            UPDATE user_project_assignments
            SET is_active = false, removed_at = NOW()
            WHERE is_active = true
            AND last_active_at < :threshold
        """), {"threshold": stale_threshold})
        
        await session.commit()
    
    asyncio.run(_run_task(runner))
```

---

### 3.3 Refresh Document Embeddings

**Task Name**: `refresh_document_embeddings`  
**Priority**: LOW  
**Schedule**: Monthly

**Purpose**: Refresh embeddings for all documents (model updates).

**Recommendation**:
```python
@celery_app.task(name="refresh_document_embeddings")
def refresh_document_embeddings():
    """
    Refresh embeddings for all knowledge documents monthly.
    
    Useful when:
    - Embedding model is upgraded
    - Chunk configuration is updated
    """
    async def runner(container):
        # Get all knowledge bases
        # Queue reindex_knowledge_base for each
        pass
    
    asyncio.run(_run_task(runner))
```

---

## 4. Task Summary

| Task | Status | Schedule | Description |
|------|--------|----------|-------------|
| `reindex_knowledge_base` | ✅ Done | Manual | Regenerate embeddings |
| `evaluate_auto_assignment_rules` | ✅ Done | Event | Auto-assign users |
| `aggregate_project_analytics` | ✅ Done | Daily 4 AM | Daily analytics |
| `check_knowledge_base_health` | ✅ Done | Sunday 5 AM | Health checks |
| `sync_user_portfolio_context` | ❌ Missing | Every 6h | Update user context |
| `clean_stale_assignments` | ❌ Missing | Weekly | Cleanup inactive |
| `refresh_document_embeddings` | ❌ Missing | Monthly | Refresh embeddings |

---

## References

- **Projects Tasks**: `src/app/infrastructure/celery/tasks/projects_tasks.py`
- **Main Tasks File**: `src/app/infrastructure/celery/tasks.py`
- **Celery App**: `src/app/infrastructure/celery/app.py`
