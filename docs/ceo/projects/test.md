# Projects & Knowledge Bases Test Specification

> **Last Updated**: 2026-01-25  
> **Status**: Moderate Coverage  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Projects & Knowledge Bases system has **moderate test coverage** with integration tests for tool execution and templates. Significant gaps exist for endpoint E2E tests and knowledge base services.

**Total Test Files**: ~10 files  
**Estimated Coverage**: ~40%

---

## 1. Existing Tests

### 1.1 Integration Tests

| File | Tests | Coverage |
|------|-------|----------|
| `tests/integration/projects/test_project_tool_integration.py` | Tool execution, templates, risk validation | 20+ tests |
| `tests/integration/projects/test_template_flags.py` | Template configuration flags | ~10 tests |
| `tests/integration/guest/knowledge/*.py` | Knowledge injection tests | 30+ tests |

---

### 1.2 Unit Tests

| File | Tests | Coverage |
|------|-------|----------|
| `tests/unit/infrastructure/repositories/test_project_repository.py` | Repository structure | Basic structure tests |

---

### 1.3 Detailed Test Coverage

#### Project Tool Integration Tests
**File**: `tests/integration/projects/test_project_tool_integration.py`

```python
class TestProjectEntityEnhancements:
    def test_project_hunter_tools_enabled(self)
    def test_project_ultra_tools_enabled(self)
    def test_can_use_hunter_tool(self)

class TestProjectTemplates:
    def test_all_templates_defined(self)
    def test_template_has_required_fields(self)
    def test_defi_swing_trader_template(self)
    def test_arbitrage_hunter_template(self)
    def test_conservative_investor_template(self)
    def test_create_project_from_template(self)

class TestProjectToolExecutor:
    async def test_execute_enabled_tool(self)
    async def test_execute_disabled_tool_raises_error(self)
    async def test_portfolio_risk_tolerance_validation(self)
    async def test_ultra_capital_validation(self)
    async def test_conservative_project_blocks_trading_signals(self)
    async def test_arbitrage_project_allows_ultra_tools(self)

class TestConversationProjectLinking:
    def test_conversation_without_project(self)
    def test_conversation_with_project(self)
```

#### Knowledge Integration Tests
**Path**: `tests/integration/guest/knowledge/`

```python
# test_knowledge_injection.py
- Test basic knowledge injection
- Test context enrichment

# test_knowledge_injection_api.py
- Test knowledge API endpoints

# test_knowledge_quality_assurance.py
- Test retrieval quality

# test_knowledge_advanced_scenarios.py
- Test complex retrieval scenarios

# test_knowledge_error_handling.py
- Test error cases

# test_knowledge_context_enrichment.py
- Test context building

# test_knowledge_source_integration.py
- Test multiple source types

# test_knowledge_compression.py
- Test context compression
```

---

## 2. Missing Tests (Gaps Analysis)

### 2.1 Critical Missing Tests

| Area | Missing Test | Priority | Description |
|------|-------------|----------|-------------|
| **Admin Router** | E2E tests | HIGH | All admin endpoints |
| **User Router** | E2E tests | HIGH | All user endpoints |
| **Project Entity** | Unit tests | HIGH | Entity methods |
| **Knowledge Retriever** | Unit tests | HIGH | Retrieval logic |
| **Document Processor** | Unit tests | MEDIUM | Processing logic |
| **Assignment Service** | Unit tests | MEDIUM | Rule evaluation |
| **Celery Tasks** | Integration tests | MEDIUM | Task execution |

---

### 2.2 Missing Project Entity Tests

```python
# tests/unit/domain/projects/test_project_entity.py (MISSING)

class TestProjectEntity:
    def test_create_project(self):
        """Test project creation with defaults."""
        
    def test_create_project_with_all_fields(self):
        """Test project creation with all fields."""
        
    def test_update_project(self):
        """Test project update."""
        
    def test_activate_project(self):
        """Test project activation."""
        
    def test_pause_project(self):
        """Test project pausing."""
        
    def test_archive_project(self):
        """Test project archival."""
        
    def test_is_active(self):
        """Test is_active property."""
        
    def test_is_public(self):
        """Test is_public property."""
        
    def test_can_accept_users_unlimited(self):
        """Test can_accept_users with no limit."""
        
    def test_can_accept_users_at_limit(self):
        """Test can_accept_users at limit."""
        
    def test_has_protocol(self):
        """Test has_protocol method."""
        
    def test_has_chain(self):
        """Test has_chain method."""
        
    def test_has_tool(self):
        """Test has_tool method."""
```

---

### 2.3 Missing Knowledge Entity Tests

```python
# tests/unit/domain/entities/test_knowledge_entities.py (MISSING)

class TestKnowledgeDocument:
    def test_create_document(self):
        """Test document creation."""
        
    def test_mark_processed(self):
        """Test mark_processed method."""
        
    def test_mark_failed(self):
        """Test mark_failed method."""
        
    def test_update_content_clears_processed(self):
        """Test that update_content resets processing state."""

class TestKnowledgeChunk:
    def test_create_chunk(self):
        """Test chunk creation."""
        
    def test_set_embedding(self):
        """Test embedding assignment."""

class TestKnowledgeBase:
    def test_create_knowledge_base(self):
        """Test knowledge base creation."""
        
    def test_update_stats(self):
        """Test stats update."""
        
    def test_is_active(self):
        """Test is_active property."""
```

---

### 2.4 Missing Knowledge Retriever Tests

```python
# tests/unit/domain/services/knowledge/test_knowledge_retriever.py (MISSING)

class TestKnowledgeRetriever:
    def test_retrieve_returns_top_chunks(self):
        """Test basic retrieval returns top N chunks."""
        
    def test_retrieve_respects_limit(self):
        """Test retrieval respects limit parameter."""
        
    def test_retrieve_filters_by_similarity(self):
        """Test similarity threshold filtering."""
        
    def test_retrieve_empty_result(self):
        """Test retrieval with no matching chunks."""
        
    def test_retrieve_with_reranking(self):
        """Test two-stage retrieval."""
        
    def test_format_context_truncates(self):
        """Test context formatting with max length."""
        
    def test_format_context_empty(self):
        """Test formatting empty chunks list."""
```

---

### 2.5 Missing Admin Router E2E Tests

```python
# tests/e2e/projects/test_admin_projects_api.py (MISSING)

class TestAdminProjectsAPI:
    async def test_create_project(self, client, admin_token):
        """Test POST /admin/projects."""
        
    async def test_create_project_duplicate_slug(self, client, admin_token):
        """Test duplicate slug error."""
        
    async def test_list_projects(self, client, admin_token):
        """Test GET /admin/projects."""
        
    async def test_list_projects_with_filters(self, client, admin_token):
        """Test listing with status/visibility filters."""
        
    async def test_get_project(self, client, admin_token):
        """Test GET /admin/projects/{id}."""
        
    async def test_get_project_not_found(self, client, admin_token):
        """Test 404 for unknown project."""
        
    async def test_update_project(self, client, admin_token):
        """Test PATCH /admin/projects/{id}."""
        
    async def test_delete_project(self, client, admin_token):
        """Test DELETE /admin/projects/{id}."""
        
    async def test_activate_project(self, client, admin_token):
        """Test POST /admin/projects/{id}/activate."""
        
    async def test_create_knowledge_document(self, client, admin_token):
        """Test POST /admin/projects/{id}/knowledge/documents."""
        
    async def test_list_knowledge_documents(self, client, admin_token):
        """Test GET /admin/projects/{id}/knowledge/documents."""
        
    async def test_create_assignment_rule(self, client, admin_token):
        """Test POST /admin/projects/{id}/assignment-rules."""
        
    async def test_assign_user(self, client, admin_token):
        """Test POST /admin/projects/{id}/assignments."""
```

---

### 2.6 Missing User Router E2E Tests

```python
# tests/e2e/projects/test_user_projects_api.py (MISSING)

class TestUserProjectsAPI:
    async def test_get_user_projects(self, client, user_token):
        """Test GET /user/projects."""
        
    async def test_list_available_projects(self, client, user_token):
        """Test GET /user/projects/available."""
        
    async def test_select_project(self, client, user_token):
        """Test POST /user/projects/{id}/select."""
        
    async def test_select_project_not_assigned(self, client, user_token):
        """Test select unassigned private project fails."""
        
    async def test_join_project(self, client, user_token):
        """Test POST /user/projects/{id}/join."""
        
    async def test_join_private_project_fails(self, client, user_token):
        """Test joining private project fails."""
        
    async def test_join_project_at_capacity(self, client, user_token):
        """Test joining project at max_users fails."""
        
    async def test_get_project_by_slug(self, client, user_token):
        """Test GET /user/projects/{slug}."""
```

---

### 2.7 Missing Celery Task Tests

```python
# tests/integration/celery/test_projects_tasks.py (MISSING)

class TestProjectsCeleryTasks:
    def test_reindex_knowledge_base(self):
        """Test reindex_knowledge_base task."""
        
    def test_evaluate_auto_assignment_rules(self):
        """Test evaluate_auto_assignment_rules task."""
        
    def test_aggregate_project_analytics(self):
        """Test aggregate_project_analytics task."""
        
    def test_check_knowledge_base_health(self):
        """Test check_knowledge_base_health task."""
```

---

### 2.8 Missing Assignment Service Tests

```python
# tests/unit/domain/services/assignment/test_assignment_service.py (MISSING)

class TestAssignmentService:
    async def test_auto_assign_matches_portfolio_rule(self):
        """Test matching portfolio_value rule."""
        
    async def test_auto_assign_matches_chain_rule(self):
        """Test matching chain_preference rule."""
        
    async def test_auto_assign_skips_existing(self):
        """Test skipping already assigned projects."""
        
    async def test_auto_assign_priority_ordering(self):
        """Test rule priority affects selection."""

class TestRuleEvaluator:
    def test_evaluate_portfolio_value_rule(self):
        """Test portfolio_value condition."""
        
    def test_evaluate_token_holding_rule(self):
        """Test token_holding condition."""
        
    def test_evaluate_chain_preference_rule(self):
        """Test chain_preference condition."""
```

---

## 3. Test Commands

### Run All Project Tests

```bash
# All project-related tests
pytest -k "project or knowledge" -v

# Integration tests only
pytest tests/integration/projects/ -v

# Knowledge tests
pytest tests/integration/guest/knowledge/ -v

# Unit tests only
pytest tests/unit -k "project" -v
```

### Run with Coverage

```bash
pytest tests/ \
  -k "project or knowledge" \
  --cov=src/app/domain/projects \
  --cov=src/app/application/projects \
  --cov=src/app/domain/services/knowledge \
  --cov=src/app/domain/services/assignment \
  --cov=src/app/presentation/http/controllers/admin/projects_router \
  --cov=src/app/presentation/http/controllers/user/projects_router \
  --cov-report=html
```

---

## 4. Test Coverage Goals

| Layer | Current | Target | Gap |
|-------|---------|--------|-----|
| Project Entity | ~30% | 80% | 50% |
| Knowledge Entities | ~20% | 70% | 50% |
| Knowledge Retriever | ~40% | 80% | 40% |
| Document Processor | ~30% | 70% | 40% |
| Assignment Service | ~10% | 70% | 60% |
| Admin Router | ~10% | 80% | 70% |
| User Router | ~10% | 80% | 70% |
| Celery Tasks | ~20% | 60% | 40% |
| Templates | ~80% | 90% | 10% |
| Tool Executor | ~70% | 90% | 20% |

---

## 5. Test Fixtures

### 5.1 Project Fixtures

```python
@pytest.fixture
def sample_project():
    """Create a sample project."""
    from app.domain.projects.entities.project import Project
    
    return Project.create(
        slug="test-project",
        name="Test Project",
        system_prompt="You are a test assistant.",
        created_by=uuid4(),
        enabled_tools=["hunter_sentiment_analysis"],
        risk_config={"max_risk_tolerance": 0.8},
    )

@pytest.fixture
def swing_trader_project():
    """Create DeFi Swing Trader project from template."""
    from app.application.projects.templates.project_templates import (
        DEFI_SWING_TRADER_TEMPLATE,
        create_project_from_template,
    )
    
    return create_project_from_template(
        DEFI_SWING_TRADER_TEMPLATE,
        created_by=uuid4()
    )
```

### 5.2 Knowledge Fixtures

```python
@pytest.fixture
def sample_knowledge_base():
    """Create a sample knowledge base."""
    from app.domain.entities.knowledge_base import KnowledgeBase
    
    return KnowledgeBase.create(
        project_id=uuid4(),
        name="Test KB",
        description="Test knowledge base",
    )

@pytest.fixture
def sample_knowledge_document(sample_knowledge_base):
    """Create a sample knowledge document."""
    from app.domain.entities.knowledge_base import KnowledgeDocument
    
    return KnowledgeDocument.create(
        knowledge_base_id=sample_knowledge_base.id,
        title="Test Document",
        content="This is test content for the document.",
        doc_type="markdown",
    )
```

### 5.3 Mock Tool Executors

```python
@pytest.fixture
def mock_hunter_executor():
    """Create mock Hunter AI executor."""
    executor = AsyncMock()
    executor.execute_tool.return_value = "Mock Hunter AI response"
    return executor

@pytest.fixture
def mock_ultra_executor():
    """Create mock ULTRA executor."""
    executor = AsyncMock()
    executor.execute_tool.return_value = "Mock ULTRA response"
    return executor
```

---

## 6. Test Markers

```python
# pytest.ini or pyproject.toml markers
markers = [
    "projects: Project tests",
    "knowledge: Knowledge base tests",
    "templates: Template tests",
    "tool_execution: Tool execution tests",
    "assignment: Assignment tests",
    "admin_api: Admin API tests",
    "user_api: User API tests",
]
```

---

## References

- **Integration Tests**: `tests/integration/projects/`
- **Knowledge Tests**: `tests/integration/guest/knowledge/`
- **Unit Tests**: `tests/unit/infrastructure/repositories/test_project_repository.py`
- **Test Fixtures**: `tests/fixtures/`
