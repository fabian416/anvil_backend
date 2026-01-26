# Projects & Knowledge Bases Metadata & Architecture

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Anvil Projects & Knowledge Bases system provides admin-configured DeFi assistant projects with:
- **Custom Branding**: Icons, colors, banners
- **Specialized Prompts**: Per-project system prompts
- **Tool Control**: Enabled protocols, chains, and tools
- **Knowledge Bases**: RAG-powered document retrieval
- **User Assignment**: Manual and automatic user-project linking
- **Risk Management**: Per-project risk configuration

**Database Tables**: 11 tables  
**Total Modules**: 35+ Python files

---

## 1. Module Status

| Component | Status | Health | Notes |
|-----------|--------|--------|-------|
| Project Entity | ✅ Production | Healthy | Full CRUD |
| Knowledge Base | ✅ Production | Healthy | RAG ready |
| Document Processing | ✅ Production | Healthy | Embedding generation |
| Knowledge Retrieval | ✅ Production | Healthy | Semantic search |
| Admin Router | ✅ Production | Healthy | 15+ endpoints |
| User Router | ✅ Production | Healthy | 5+ endpoints |
| Project Templates | ✅ Production | Healthy | 5 templates |
| Tool Executor | ✅ Production | Healthy | Risk validation |
| Assignment Rules | ✅ Production | Healthy | Auto-assignment |
| Celery Tasks | ✅ Production | Healthy | 4 tasks |
| Test Coverage | ⚠️ Moderate | ~40% | Gaps in E2E tests |

---

## 2. File Reference Index

### 2.1 Domain Layer

```
src/app/domain/projects/
├── __init__.py
├── entities/
│   ├── __init__.py
│   └── project.py             # Project entity
├── ports/
│   ├── __init__.py
│   └── project_repository.py  # ProjectRepository protocol
├── services/
│   └── __init__.py
└── value_objects/
    └── __init__.py

src/app/domain/entities/
├── knowledge_base.py          # KnowledgeBase, KnowledgeDocument, KnowledgeChunk
├── assignment_rule.py         # AssignmentRule, UserProjectAssignment
└── project.py                 # Legacy project entity (duplicate)

src/app/domain/services/knowledge/
├── retriever.py               # KnowledgeRetriever - semantic search
├── document_processor.py      # DocumentProcessor - embedding generation
└── text_chunker.py            # TextChunker - document splitting

src/app/domain/services/assignment/
├── assignment_service.py      # AssignmentService - auto-assignment
└── rule_evaluator.py          # RuleEvaluator - rule evaluation

src/app/domain/ports/
├── project_repository.py      # ProjectRepository port
├── knowledge_repository.py    # KnowledgeChunkRepository port
├── assignment_repository.py   # AssignmentRepository port
└── embedding_service.py       # EmbeddingService port
```

### 2.2 Application Layer

```
src/app/application/projects/
├── commands/
│   ├── create_project.py      # CreateProject interactor
│   ├── update_project.py      # UpdateProject interactor
│   ├── delete_project.py      # DeleteProject interactor
│   └── activate_project.py    # ActivateProject interactor
├── queries/
│   ├── get_project.py         # GetProject interactor
│   ├── list_projects.py       # ListProjects interactor
│   └── search_projects.py     # SearchProjects interactor
├── services/
│   ├── __init__.py
│   └── project_tool_executor.py  # ProjectToolExecutor
└── templates/
    ├── __init__.py
    └── project_templates.py   # Pre-built templates
```

### 2.3 Presentation Layer

```
src/app/presentation/http/controllers/
├── admin/
│   └── projects_router.py     # Admin project endpoints
├── user/
│   └── projects_router.py     # User project endpoints
└── schemas/
    └── projects.py            # Pydantic schemas (assumed location)
```

### 2.4 Infrastructure Layer

```
src/app/infrastructure/persistence_sqla/
├── mappings/
│   └── projects.py            # SQLAlchemy table definitions
├── repositories/
│   ├── knowledge_repository.py  # Knowledge document/chunk repos
│   └── assignment_repository.py # Assignment rule/user repos
└── alembic/versions/
    └── 20251201_002_add_projects_system.py  # Migration

src/app/infrastructure/celery/tasks/
└── projects_tasks.py          # Celery background tasks

src/app/infrastructure/adapters/
└── project_repository_sqla.py # Project repository (assumed)
```

### 2.5 Tests

```
tests/integration/projects/
├── test_project_tool_integration.py  # Tool execution tests
└── test_template_flags.py            # Template tests

tests/integration/guest/knowledge/
├── test_knowledge_injection.py
├── test_knowledge_injection_api.py
├── test_knowledge_quality_assurance.py
├── test_knowledge_advanced_scenarios.py
├── test_knowledge_error_handling.py
├── test_knowledge_context_enrichment.py
├── test_knowledge_source_integration.py
└── test_knowledge_compression.py

tests/unit/infrastructure/repositories/
└── test_project_repository.py
```

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│                                                                              │
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐      │
│  │       Admin Dashboard         │  │        User Interface         │      │
│  │  (Project Management)         │  │  (Project Selection/Chat)     │      │
│  └───────────────────────────────┘  └───────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐        │
│  │   Admin Projects Router      │  │    User Projects Router      │        │
│  │  /admin/projects/*           │  │  /user/projects/*            │        │
│  │                              │  │                              │        │
│  │  • POST / (create)           │  │  • GET / (user projects)     │        │
│  │  • GET / (list)              │  │  • GET /available            │        │
│  │  • GET /{id}                 │  │  • POST /{id}/select         │        │
│  │  • PATCH /{id}               │  │  • POST /{id}/join           │        │
│  │  • DELETE /{id}              │  │  • GET /{slug}               │        │
│  │  • POST /{id}/activate       │  │                              │        │
│  │  • POST /{id}/knowledge/docs │  └──────────────────────────────┘        │
│  │  • GET /{id}/knowledge/docs  │                                          │
│  │  • POST /{id}/rules          │                                          │
│  │  • POST /{id}/assignments    │                                          │
│  └──────────────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                                      │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           Commands                                   │   │
│  │  CreateProject • UpdateProject • DeleteProject • ActivateProject    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                            Queries                                   │   │
│  │  GetProject • ListProjects • SearchProjects                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           Services                                   │   │
│  │  ProjectToolExecutor • ProjectTemplates (5 templates)               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          Entities                                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │   Project    │  │ KnowledgeBase │  │   AssignmentRule        │  │   │
│  │  │              │  │              │  │                          │  │   │
│  │  │ • slug       │  │ • project_id │  │ • condition_type         │  │   │
│  │  │ • name       │  │ • name       │  │ • condition_params       │  │   │
│  │  │ • system_    │  │ • embedding_ │  │ • priority               │  │   │
│  │  │   prompt     │  │   model      │  │ • auto_switch            │  │   │
│  │  │ • enabled_   │  │ • chunk_size │  │                          │  │   │
│  │  │   tools      │  │              │  └──────────────────────────┘  │   │
│  │  │ • risk_      │  └──────────────┘                                │   │
│  │  │   config     │                                                   │   │
│  │  └──────────────┘  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │                     │ Knowledge    │  │   UserProjectAssignment │  │   │
│  │                     │ Document     │  │                          │  │   │
│  │                     │              │  │ • user_id                │  │   │
│  │                     │ • title      │  │ • project_id             │  │   │
│  │                     │ • content    │  │ • assignment_type        │  │   │
│  │                     │ • doc_type   │  │                          │  │   │
│  │                     └──────────────┘  └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       Domain Services                                │   │
│  │  KnowledgeRetriever • DocumentProcessor • TextChunker               │   │
│  │  AssignmentService • RuleEvaluator                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                            Ports                                     │   │
│  │  ProjectRepository • KnowledgeChunkRepository • EmbeddingService    │   │
│  │  AssignmentRuleRepository • UserAssignmentRepository                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                  SQLAlchemy Repositories                             │   │
│  │  ProjectRepositorySqla • KnowledgeDocumentRepositorySqla            │   │
│  │  KnowledgeChunkRepositorySqla • AssignmentRuleRepositorySqla        │   │
│  │  UserAssignmentRepositorySqla                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       Celery Tasks                                   │   │
│  │  reindex_knowledge_base • evaluate_auto_assignment_rules            │   │
│  │  aggregate_project_analytics • check_knowledge_base_health          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA STORAGE                                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      PostgreSQL Tables (11)                          │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐             │   │
│  │  │    projects     │───▶│  project_knowledge_bases    │             │   │
│  │  │                 │    │                             │             │   │
│  │  │ • id            │    │ • project_id                │             │   │
│  │  │ • slug          │    │ • name                      │             │   │
│  │  │ • name          │    │ • embedding_model           │             │   │
│  │  │ • system_prompt │    │ • chunk_size                │             │   │
│  │  │ • enabled_tools │    └─────────────────────────────┘             │   │
│  │  │ • risk_config   │              │                                  │   │
│  │  │ • max_users     │              ▼                                  │   │
│  │  └─────────────────┘    ┌─────────────────────────────┐             │   │
│  │         │               │ project_knowledge_documents │             │   │
│  │         │               │                             │             │   │
│  │         │               │ • knowledge_base_id         │             │   │
│  │         │               │ • title, content            │             │   │
│  │         │               │ • is_processed              │             │   │
│  │         │               └─────────────────────────────┘             │   │
│  │         │                         │                                  │   │
│  │         │                         ▼                                  │   │
│  │         │               ┌─────────────────────────────┐             │   │
│  │         │               │  project_knowledge_chunks   │             │   │
│  │         │               │                             │             │   │
│  │         │               │ • document_id               │             │   │
│  │         │               │ • chunk_text                │             │   │
│  │         │               │ • embedding (vector)        │             │   │
│  │         │               └─────────────────────────────┘             │   │
│  │         │                                                            │   │
│  │         ▼                                                            │   │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐             │   │
│  │  │ project_tool_   │    │ project_auto_assign_rules   │             │   │
│  │  │ configs         │    │                             │             │   │
│  │  │                 │    │ • condition_type            │             │   │
│  │  │ • is_enabled    │    │ • condition_params          │             │   │
│  │  │ • restrictions  │    │ • auto_switch               │             │   │
│  │  └─────────────────┘    └─────────────────────────────┘             │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐             │   │
│  │  │ user_project_   │    │   user_active_projects      │             │   │
│  │  │ assignments     │    │                             │             │   │
│  │  │                 │    │ • user_id (PK)              │             │   │
│  │  │ • assignment_   │    │ • project_id                │             │   │
│  │  │   type          │    │ • session_count             │             │   │
│  │  └─────────────────┘    └─────────────────────────────┘             │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐             │   │
│  │  │ project_        │    │  project_analytics_daily    │             │   │
│  │  │ invitations     │    │                             │             │   │
│  │  │                 │    │ • active_users              │             │   │
│  │  │ • email         │    │ • total_messages            │             │   │
│  │  │ • invitation_   │    │ • knowledge_queries         │             │   │
│  │  │   code          │    │ • tool_usage                │             │   │
│  │  └─────────────────┘    └─────────────────────────────┘             │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────┐            │   │
│  │  │              project_chat_sessions                  │            │   │
│  │  │                                                     │            │   │
│  │  │ • session_id • project_id • user_id                │            │   │
│  │  │ • knowledge_chunks_used • tools_used               │            │   │
│  │  └─────────────────────────────────────────────────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Project Templates

| Template | Slug | Icon | Key Tools | Risk Config |
|----------|------|------|-----------|-------------|
| DeFi Swing Trader | `defi-swing-trader` | 📈 | sentiment, signals, prediction, risk, portfolio | max_risk: 0.8, max_single_asset: 30% |
| Arbitrage Hunter | `arbitrage-hunter` | ⚡ | sentiment, flash_loans, arbitrage, mev, executor | max_capital: $500K |
| Portfolio Manager | `portfolio-manager` | 💼 | sentiment, risk, portfolio | max_risk: 0.6, max_single_asset: 25% |
| Conservative Investor | `conservative-investor` | 🛡️ | sentiment, risk, portfolio (NO signals) | max_risk: 50, min_stablecoin: 30% |
| Day Trader | `day-trader` | ⚡ | sentiment, signals, prediction, patterns, risk | max_risk: 0.9, max_single_asset: 40% |

---

## 5. Improvements Roadmap

### 5.1 High Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Vector DB Integration** | Use pgvector or Pinecone for embeddings | High | Better RAG performance |
| **E2E Test Coverage** | Add admin/user router tests | Medium | Code quality |
| **User Context Sync** | Celery task for portfolio sync | Medium | Auto-assignment |

### 5.2 Medium Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Project Analytics Dashboard** | Admin UI for analytics | High | UX |
| **Cross-Encoder Reranking** | Two-stage retrieval | Medium | RAG quality |
| **Invitation System** | Email-based project invites | Medium | Feature |

### 5.3 Low Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Project Versioning** | System prompt version history | Medium | Feature |
| **Knowledge Source Sync** | Auto-sync from URLs | High | Feature |
| **Multi-language Support** | Translated system prompts | Medium | Feature |

---

## 6. Security Considerations

### 6.1 Implemented

- ✅ Admin-only project CRUD
- ✅ User can only access assigned projects
- ✅ Risk limits enforced per-project
- ✅ Tool access controlled by project config
- ✅ Max users per project

### 6.2 Recommendations

- ⚠️ Add rate limiting on project switching
- ⚠️ Audit logging for admin actions
- ⚠️ Knowledge document content scanning
- ⚠️ Validate embedding model names

---

## References

- **Endpoints Spec**: `docs/ceo/projects/endpoints.md`
- **Services Spec**: `docs/ceo/projects/services.md`
- **Celery Spec**: `docs/ceo/projects/celery.md`
- **Test Spec**: `docs/ceo/projects/test.md`
- **Database Migration**: `src/app/infrastructure/persistence_sqla/alembic/versions/20251201_002_add_projects_system.py`
