# Projects & Knowledge Bases Services Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Projects & Knowledge Bases system provides:
- **Domain Entities**: Project, KnowledgeBase, KnowledgeDocument, KnowledgeChunk
- **Application Services**: Project CRUD, tool execution, assignment management
- **Domain Services**: Knowledge retrieval, document processing, assignment rules
- **Infrastructure Adapters**: Repository implementations, embedding services

**Total Service Components**: 35+ Python modules

---

## 1. Domain Layer Entities

### 1.1 Project Entity
**Path**: `src/app/domain/projects/entities/project.py`

Admin-configured DeFi assistant project.

```python
class Project:
    """
    Project entity representing an admin-configured DeFi assistant project.
    
    Attributes:
        id: UUID - Project identifier
        slug: str - URL-friendly identifier
        name: str - Display name
        description: str - Project description
        icon: str - Icon/emoji
        color: str - Hex color
        banner_url: str - Banner image URL
        status: str - Project status (draft, active, paused, archived)
        visibility: str - Visibility (public, private, invite_only)
        system_prompt: str - System prompt for AI
        welcome_message: str - Welcome message for users
        enabled_protocols: List[str] - Allowed DeFi protocols
        enabled_chains: List[str] - Allowed blockchain networks
        enabled_tools: List[str] - Allowed tool functions
        risk_config: dict - Risk configuration
        max_users: int - Maximum user limit
        display_order: int - Display order
        is_featured: bool - Featured flag
        created_by: UUID - Creator user ID
    """
    
    @classmethod
    def create(cls, slug, name, system_prompt, created_by, ...) -> "Project"
    
    def update(self, **kwargs) -> None
    def activate(self) -> None
    def pause(self) -> None
    def archive(self) -> None
    def is_active(self) -> bool
    def is_public(self) -> bool
    def can_accept_users(self, current_user_count: int) -> bool
    def has_protocol(self, protocol: str) -> bool
    def has_chain(self, chain: str) -> bool
    def has_tool(self, tool: str) -> bool
    
    # Tool filtering
    @property
    def hunter_tools_enabled(self) -> List[str]
    @property
    def ultra_tools_enabled(self) -> List[str]
    def can_use_hunter_tool(self, tool_name: str) -> bool
    def can_use_ultra_tool(self, tool_name: str) -> bool
```

---

### 1.2 Knowledge Base Entity
**Path**: `src/app/domain/entities/knowledge_base.py`

Project's knowledge base configuration.

```python
class KnowledgeBase:
    """
    Knowledge base entity.
    
    Attributes:
        id: UUID
        project_id: UUID
        name: str
        description: str
        embedding_model: str (default: text-embedding-3-small)
        chunk_size: int (default: 500)
        chunk_overlap: int (default: 50)
        total_documents: int
        total_chunks: int
        status: str
        last_indexed_at: datetime
    """
    
    @classmethod
    def create(cls, project_id, name, ...) -> "KnowledgeBase"
    
    def update_stats(self, total_documents: int, total_chunks: int) -> None
    def is_active(self) -> bool
```

---

### 1.3 Knowledge Document Entity
**Path**: `src/app/domain/entities/knowledge_base.py`

Document in a project's knowledge base.

```python
class KnowledgeDocument:
    """
    Knowledge document entity.
    
    Attributes:
        id: UUID
        knowledge_base_id: UUID
        title: str
        content: str
        doc_type: str
        source_url: str
        source_type: str (manual, api, crawl)
        tags: List[str]
        priority: int
        is_processed: bool
        chunk_count: int
        processing_error: str
    """
    
    @classmethod
    def create(cls, knowledge_base_id, title, content, doc_type, ...) -> "KnowledgeDocument"
    
    def mark_processed(self, chunk_count: int) -> None
    def mark_failed(self, error: str) -> None
    def update_content(self, content: str) -> None
```

---

### 1.4 Knowledge Chunk Entity
**Path**: `src/app/domain/entities/knowledge_base.py`

Chunk of a document with vector embedding.

```python
class KnowledgeChunk:
    """
    Knowledge chunk entity with vector embedding.
    
    Attributes:
        id: UUID
        document_id: UUID
        knowledge_base_id: UUID
        chunk_text: str
        chunk_index: int
        embedding: List[float]
        metadata: dict
    """
    
    @classmethod
    def create(cls, document_id, knowledge_base_id, chunk_text, chunk_index, ...) -> "KnowledgeChunk"
    
    def set_embedding(self, embedding: List[float]) -> None
```

---

## 2. Application Layer Services

### 2.1 Project Commands

**CreateProject**
**Path**: `src/app/application/projects/commands/create_project.py`

```python
class CreateProject:
    """Create a new project."""
    
    def __init__(self, repository: ProjectRepository):
        self._repository = repository
    
    async def execute(
        self,
        slug: str,
        name: str,
        system_prompt: str,
        created_by: UUID,
        **kwargs
    ) -> Project
```

**UpdateProject**
**Path**: `src/app/application/projects/commands/update_project.py`

```python
class UpdateProject:
    """Update project details."""
    
    async def execute(self, project_id: UUID, **kwargs) -> Project
```

**DeleteProject**
**Path**: `src/app/application/projects/commands/delete_project.py`

```python
class DeleteProject:
    """Delete a project."""
    
    async def execute(self, project_id: UUID) -> None
```

**ActivateProject**
**Path**: `src/app/application/projects/commands/activate_project.py`

```python
class ActivateProject:
    """Activate a project."""
    
    async def execute(self, project_id: UUID) -> Project
```

---

### 2.2 Project Queries

**GetProject**
**Path**: `src/app/application/projects/queries/get_project.py`

```python
class GetProject:
    """Get project by ID."""
    
    async def execute(self, project_id: UUID) -> Optional[Project]
```

**ListProjects**
**Path**: `src/app/application/projects/queries/list_projects.py`

```python
class ListProjects:
    """List projects with filters."""
    
    async def execute(
        self,
        status: Optional[str] = None,
        visibility: Optional[str] = None,
        is_featured: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Project]
```

**SearchProjects**
**Path**: `src/app/application/projects/queries/search_projects.py`

```python
class SearchProjects:
    """Search projects by name or description."""
    
    async def execute(
        self,
        query: str,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Project]
```

---

### 2.3 Project Tool Executor
**Path**: `src/app/application/projects/services/project_tool_executor.py`

Execute tools within project scope with configuration and risk limits.

```python
class ProjectToolExecutor:
    """
    Execute tools within project scope with configuration and risk limits.
    
    This executor:
    1. Validates tool is enabled in project
    2. Enforces project risk limits
    3. Delegates to appropriate tool executor
    4. Returns formatted results
    """
    
    def __init__(
        self,
        project: Project,
        hunter_executor: HunterToolExecutor,
        ultra_executor: ULTRAToolExecutor,
        integration_settings: IntegrationSettings,
    ):
        ...
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict,
    ) -> str:
        """
        Execute tool if enabled in project and parameters pass validation.
        
        Raises:
            ToolExecutionError: If tool not enabled or validation fails
        """
        
    def _validate_parameters(self, tool_name: str, parameters: dict) -> None
    def _validate_portfolio_parameters(self, parameters: dict, risk_config: dict) -> None
    def _validate_ultra_parameters(self, parameters: dict, risk_config: dict) -> None
```

---

### 2.4 Project Templates
**Path**: `src/app/application/projects/templates/project_templates.py`

Pre-built project configurations.

```python
# Templates available
DEFI_SWING_TRADER_TEMPLATE = {
    "slug": "defi-swing-trader",
    "name": "DeFi Swing Trader",
    "icon": "📈",
    "enabled_tools": ["hunter_sentiment_analysis", "hunter_trading_signals", ...],
    "risk_config": {"max_risk_tolerance": 0.8, "max_single_asset_percent": 30},
    ...
}

ARBITRAGE_HUNTER_TEMPLATE = {...}
PORTFOLIO_MANAGER_TEMPLATE = {...}
CONSERVATIVE_INVESTOR_TEMPLATE = {...}
DAY_TRADER_TEMPLATE = {...}

ALL_PROJECT_TEMPLATES = [
    DEFI_SWING_TRADER_TEMPLATE,
    ARBITRAGE_HUNTER_TEMPLATE,
    PORTFOLIO_MANAGER_TEMPLATE,
    CONSERVATIVE_INVESTOR_TEMPLATE,
    DAY_TRADER_TEMPLATE,
]

def create_project_from_template(template: dict, created_by: UUID) -> Project
```

---

## 3. Domain Services

### 3.1 Knowledge Retriever
**Path**: `src/app/domain/services/knowledge/retriever.py`

Semantic search with vector similarity.

```python
class KnowledgeRetriever:
    """
    Service for retrieving relevant knowledge chunks.
    Implements semantic search with vector similarity.
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        chunk_repository: KnowledgeChunkRepository,
    ):
        ...
    
    async def retrieve(
        self,
        knowledge_base_id: UUID,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Tuple[KnowledgeChunk, float]]
    
    async def retrieve_with_reranking(
        self,
        knowledge_base_id: UUID,
        query: str,
        initial_limit: int = 20,
        final_limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Tuple[KnowledgeChunk, float]]
    
    def format_context(
        self,
        chunks: List[Tuple[KnowledgeChunk, float]],
        max_context_length: int = 2000,
    ) -> str
```

---

### 3.2 Document Processor
**Path**: `src/app/domain/services/knowledge/document_processor.py`

Process documents into embeddings.

```python
class DocumentProcessor:
    """
    Process documents into chunks with embeddings.
    """
    
    async def process_document(self, document: KnowledgeDocument) -> int:
        """
        Process document and return chunk count.
        """
```

---

### 3.3 Text Chunker
**Path**: `src/app/domain/services/knowledge/text_chunker.py`

Split documents into chunks.

```python
class TextChunker:
    """
    Split documents into chunks for embedding.
    """
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> List[str]
```

---

### 3.4 Assignment Service
**Path**: `src/app/domain/services/assignment/assignment_service.py`

User-project auto-assignment.

```python
class AssignmentService:
    """
    Service for automatic user-project assignment.
    """
    
    async def auto_assign_user(
        self,
        user_id: UUID,
        user_context: dict,
        rules: List[AssignmentRule],
        existing_assignments: List[UUID],
    ) -> List[UserProjectAssignment]
```

---

### 3.5 Rule Evaluator
**Path**: `src/app/domain/services/assignment/rule_evaluator.py`

Evaluate assignment rules.

```python
class RuleEvaluator:
    """
    Evaluate assignment rules against user context.
    """
    
    def evaluate(
        self,
        rule: AssignmentRule,
        user_context: dict,
    ) -> bool
```

---

## 4. Domain Ports (Interfaces)

### 4.1 Project Repository Port
**Path**: `src/app/domain/projects/ports/project_repository.py`

```python
class ProjectRepository(Protocol):
    """Repository interface for projects."""
    
    async def add_project(self, project: Project) -> None
    async def get_project(self, project_id: UUID) -> Optional[Project]
    async def get_project_by_slug(self, slug: str) -> Optional[Project]
    async def list_projects(
        self,
        status: Optional[str] = None,
        visibility: Optional[str] = None,
        is_featured: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Project]
    async def update_project(self, project: Project) -> None
    async def delete_project(self, project_id: UUID) -> None
    async def count_users(self, project_id: UUID) -> int
    async def search_projects(
        self,
        query: str,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Project]
```

---

### 4.2 Knowledge Repository Port
**Path**: `src/app/domain/ports/knowledge_repository.py`

```python
class KnowledgeChunkRepository(Protocol):
    """Repository interface for knowledge chunks."""
    
    async def search_chunks(
        self,
        knowledge_base_id: UUID,
        query_embedding: List[float],
        limit: int,
        similarity_threshold: float,
    ) -> List[Tuple[KnowledgeChunk, float]]
```

---

### 4.3 Embedding Service Port
**Path**: `src/app/domain/ports/embedding_service.py`

```python
class EmbeddingService(Protocol):
    """Interface for embedding generation."""
    
    async def generate_embedding(self, text: str) -> List[float]
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]
```

---

## 5. Infrastructure Adapters

### 5.1 Project Repository SQLAlchemy
**Path**: `src/app/infrastructure/adapters/project_repository_sqla.py`

SQLAlchemy implementation of ProjectRepository.

---

### 5.2 Knowledge Repositories
**Path**: `src/app/infrastructure/persistence_sqla/repositories/knowledge_repository.py`

```python
class KnowledgeDocumentRepositorySqla:
    """SQLAlchemy implementation for knowledge documents."""
    
    async def add_document(self, document: KnowledgeDocument) -> None
    async def update_document(self, document: KnowledgeDocument) -> None
    async def list_documents(self, knowledge_base_id: UUID) -> List[KnowledgeDocument]

class KnowledgeChunkRepositorySqla:
    """SQLAlchemy implementation for knowledge chunks."""
    
    async def search_chunks(
        self,
        knowledge_base_id: UUID,
        query_embedding: List[float],
        limit: int,
        similarity_threshold: float,
    ) -> List[Tuple[KnowledgeChunk, float]]
```

---

### 5.3 Assignment Repositories
**Path**: `src/app/infrastructure/persistence_sqla/repositories/assignment_repository.py`

```python
class AssignmentRuleRepositorySqla:
    """SQLAlchemy implementation for assignment rules."""
    
    async def add_rule(self, rule: AssignmentRule) -> None
    async def get_rule(self, rule_id: UUID) -> Optional[AssignmentRule]
    async def get_rules_by_project(self, project_id: UUID) -> List[AssignmentRule]
    async def get_all_active_rules(self) -> List[AssignmentRule]
    async def update_rule(self, rule: AssignmentRule) -> None

class UserAssignmentRepositorySqla:
    """SQLAlchemy implementation for user assignments."""
    
    async def add_assignment(self, assignment: UserProjectAssignment) -> None
    async def get_assignments_by_user(self, user_id: UUID) -> List[UserProjectAssignment]
    async def get_assignments_by_project(self, project_id: UUID) -> List[UserProjectAssignment]
    async def get_active_project(self, user_id: UUID) -> Optional[UUID]
    async def set_active_project(self, user_id: UUID, project_id: UUID) -> None
```

---

## 6. Service Dependencies Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐        │
│  │    Admin Projects Router     │  │    User Projects Router      │        │
│  │  /admin/projects/*           │  │  /user/projects/*            │        │
│  └──────────────────────────────┘  └──────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Commands                                      │  │
│  │  CreateProject • UpdateProject • DeleteProject • ActivateProject     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          Queries                                      │  │
│  │  GetProject • ListProjects • SearchProjects                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Services                                      │  │
│  │  ProjectToolExecutor • ProjectTemplates                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Entities                                      │  │
│  │  Project • KnowledgeBase • KnowledgeDocument • KnowledgeChunk        │  │
│  │  AssignmentRule • UserProjectAssignment                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Domain Services                                   │  │
│  │  KnowledgeRetriever • DocumentProcessor • TextChunker                │  │
│  │  AssignmentService • RuleEvaluator                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          Ports                                        │  │
│  │  ProjectRepository • KnowledgeChunkRepository • EmbeddingService     │  │
│  │  AssignmentRepository                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       Repositories (SQLAlchemy)                       │  │
│  │  ProjectRepositorySqla • KnowledgeDocumentRepositorySqla             │  │
│  │  KnowledgeChunkRepositorySqla • AssignmentRuleRepositorySqla         │  │
│  │  UserAssignmentRepositorySqla                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       Celery Tasks                                    │  │
│  │  reindex_knowledge_base • evaluate_auto_assignment_rules             │  │
│  │  aggregate_project_analytics • check_knowledge_base_health           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA STORAGE                                        │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        PostgreSQL Tables                              │  │
│  │  projects • project_knowledge_bases • project_knowledge_documents    │  │
│  │  project_knowledge_chunks • project_tool_configs                     │  │
│  │  user_project_assignments • user_active_projects                     │  │
│  │  project_auto_assign_rules • project_invitations                     │  │
│  │  project_chat_sessions • project_analytics_daily                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## References

- **Domain Entities**: `src/app/domain/projects/entities/`
- **Domain Services**: `src/app/domain/services/knowledge/`, `src/app/domain/services/assignment/`
- **Application Commands**: `src/app/application/projects/commands/`
- **Application Queries**: `src/app/application/projects/queries/`
- **Application Services**: `src/app/application/projects/services/`
- **Infrastructure Repositories**: `src/app/infrastructure/persistence_sqla/repositories/`
- **Celery Tasks**: `src/app/infrastructure/celery/tasks/projects_tasks.py`
