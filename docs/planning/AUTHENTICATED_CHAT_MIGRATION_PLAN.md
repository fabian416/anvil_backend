# Authenticated User Chat Migration Plan

**Date:** 2026-01-11
**Based On:** Guest Chat System (Phases 1-3 Complete)
**Target:** Migrate authenticated users to new conversation/message flow
**Estimated Duration:** 3-4 weeks

---

## Executive Summary

This plan outlines the migration of authenticated user chat to follow the proven architecture and patterns established in the guest chat system. The goal is to provide authenticated users with an enhanced experience while maintaining consistency with the guest flow.

**Current State:**
- Legacy system: `/api/v1/user/chat/*` (DEPRECATED, removal date: 2026-06-01)
- New system: `/api/v1/conversations/*` (exists but incomplete)
- Guest chat: Fully implemented with 100% test coverage

**Target State:**
- Unified conversation/message architecture for both guest and authenticated users
- Enhanced features for authenticated users (unlimited rate, history, preferences)
- Same Hunter AI integration and caching strategy
- Premium features (more intents, advanced analytics)
- Backward compatible API during migration period

---

## Table of Contents

1. [Current System Analysis](#current-system-analysis)
2. [Architecture Design](#architecture-design)
3. [Implementation Phases](#implementation-phases)
4. [Database Schema](#database-schema)
5. [API Design](#api-design)
6. [Migration Strategy](#migration-strategy)
7. [Testing Strategy](#testing-strategy)
8. [Success Criteria](#success-criteria)

---

## Current System Analysis

### Existing Tables (New System)

**From migration files and CLAUDE.md:**
```sql
-- chat_users (UUID-based, for authenticated users)
CREATE TABLE chat_users (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,  -- References auth.users
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- chat_conversations
CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY,
    chat_user_id UUID REFERENCES chat_users(id),
    status VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    metadata JSONB
);

-- messages table (assumed to exist)
-- Need to verify schema
```

### Guest Chat Tables (Reference)

```sql
-- guest_users (IP-based identification)
CREATE TABLE guest_users (
    id UUID PRIMARY KEY,
    ip_address VARCHAR(255) UNIQUE NOT NULL,
    is_blocked BOOLEAN DEFAULT false,
    message_count INTEGER DEFAULT 0,
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL
);

-- guest_conversations
CREATE TABLE guest_conversations (
    id UUID PRIMARY KEY,
    guest_user_id UUID REFERENCES guest_users(id),
    status VARCHAR(50) DEFAULT 'active',
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- guest_messages
CREATE TABLE guest_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES guest_conversations(id),
    role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    intent VARCHAR(100),
    enrichment JSONB,
    requires_registration BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL
);
```

### Feature Comparison

| Feature | Guest Chat | Authenticated Chat (Target) |
|---------|-----------|----------------------------|
| **Identification** | IP address | UUID (user_id) |
| **Rate Limiting** | 20 msg/hour | Unlimited (or 1000/hour) |
| **History** | 90 days | Permanent (or configurable) |
| **Intents** | 6 Hunter AI tools | All tools + premium features |
| **Caching** | Redis (5-10 min TTL) | Redis (same strategy) |
| **Multi-language** | en, es, pt, zh | Same + more |
| **Preferences** | Session-based | Persistent (saved in DB) |
| **Export** | Not available | Export conversation history |
| **Premium Features** | Limited | Full access |

---

## Architecture Design

### Unified Architecture Pattern

Both guest and authenticated users will share:
- Same Hunter AI handler infrastructure
- Same Redis caching strategy
- Same message/conversation entities (different tables)
- Same intent routing logic
- Same multi-language support

**Differences:**
```
┌─────────────────────────────────────────────────────────────┐
│                     Chat API Layer                          │
├──────────────────────┬──────────────────────────────────────┤
│   Guest Flow         │   Authenticated Flow                 │
├──────────────────────┼──────────────────────────────────────┤
│ IP-based ID          │ UUID-based ID                        │
│ guest_users table    │ chat_users table                     │
│ guest_conversations  │ chat_conversations                   │
│ guest_messages       │ chat_messages (new)                  │
│ 20 msg/hour limit    │ 1000 msg/hour (configurable)        │
│ 90-day retention     │ Permanent storage                    │
│ Basic features       │ Premium features                     │
└──────────────────────┴──────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           Shared Hunter AI Handler Service                  │
│  (Sentiment, Trading Signals, Patterns, Portfolio, etc.)    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis Cache Layer                        │
│      (Shared cache for both guest & authenticated)          │
└─────────────────────────────────────────────────────────────┘
```

### Domain Layer

**Entities:**
```python
# src/app/domain/chat/entities.py

@dataclass
class ChatUser:
    """Authenticated chat user (corresponds to chat_users table)."""
    id: UUID
    user_id: UUID  # References auth user
    preferred_language: str = "en"
    favorite_tokens: list[str] = field(default_factory=list)
    settings: dict = field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

@dataclass
class ChatConversation:
    """Authenticated user conversation."""
    id: UUID
    chat_user_id: UUID
    status: ConversationStatus  # active, archived, deleted
    language: str
    title: Optional[str] = None  # Auto-generated or user-set
    metadata: dict = field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

@dataclass
class ChatMessage:
    """Message in authenticated conversation."""
    id: UUID
    conversation_id: UUID
    role: MessageRole  # user, assistant, system
    content: str
    intent: Optional[str] = None
    enrichment: Optional[dict] = None
    tokens_used: int = 0  # For usage tracking
    created_at: datetime
```

**Value Objects:**
```python
class ConversationStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass(frozen=True)
class UserPreferences:
    """User chat preferences."""
    language: str
    favorite_tokens: list[str]
    notification_enabled: bool
    export_format: str  # json, csv, pdf
```

### Application Layer

**Commands (Write Operations):**
```python
# src/app/application/chat/commands/

class CreateConversationCommand:
    """Create new conversation for authenticated user."""
    user_id: UUID
    language: str = "en"
    title: Optional[str] = None

class SendMessageCommand:
    """Send message in conversation."""
    user_id: UUID
    conversation_id: UUID
    content: str
    language: str = "en"

class UpdatePreferencesCommand:
    """Update user chat preferences."""
    user_id: UUID
    preferences: UserPreferences

class ArchiveConversationCommand:
    """Archive conversation."""
    user_id: UUID
    conversation_id: UUID

class ExportConversationCommand:
    """Export conversation history."""
    user_id: UUID
    conversation_id: UUID
    format: str  # json, csv, pdf
```

**Queries (Read Operations):**
```python
# src/app/application/chat/queries/

class GetConversationsQuery:
    """Get user's conversations."""
    user_id: UUID
    status: Optional[ConversationStatus] = None
    limit: int = 50
    offset: int = 0

class GetConversationHistoryQuery:
    """Get conversation messages."""
    user_id: UUID
    conversation_id: UUID
    limit: int = 100
    offset: int = 0

class SearchConversationsQuery:
    """Search user's conversations."""
    user_id: UUID
    query: str
    limit: int = 20
```

**Handlers:**
```python
# src/app/application/chat/handlers/

class ChatHandlerService:
    """
    Authenticated user chat handler (extends guest handler logic).

    Differences from guest:
    - No rate limiting (or higher limits)
    - Persistent storage
    - User preferences
    - Premium features
    """

    async def handle_message(
        self,
        user_id: UUID,
        conversation_id: UUID,
        content: str,
        language: str = "en"
    ) -> ChatMessage:
        """Handle authenticated user message."""
        # 1. Get or create chat user
        chat_user = await self._get_or_create_chat_user(user_id)

        # 2. Validate conversation ownership
        conversation = await self._validate_conversation(
            conversation_id,
            chat_user.id
        )

        # 3. Route to appropriate handler (same as guest)
        intent = await self._classify_intent(content)

        # 4. Check cache (same key pattern as guest)
        cached = await self._check_cache(intent, content, language)
        if cached:
            return await self._create_message(
                conversation_id,
                content,
                cached
            )

        # 5. Process with Hunter AI (same as guest)
        response = await self._process_hunter_ai(
            intent,
            content,
            language,
            is_authenticated=True  # Enable premium features
        )

        # 6. Cache response (same strategy as guest)
        await self._cache_response(intent, content, language, response)

        # 7. Save message to database
        message = await self._create_message(
            conversation_id,
            content,
            response
        )

        return message
```

---

## Implementation Phases

### Phase 1: Database & Infrastructure (Week 1)

**Objectives:**
- Create chat_messages table
- Add missing columns to chat_conversations
- Create performance indexes
- Set up Alembic migrations

**Tasks:**

1. **Database Schema Updates** (2 days)
   ```sql
   -- Create chat_messages table
   CREATE TABLE chat_messages (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
       role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
       content TEXT NOT NULL,
       intent VARCHAR(100),
       enrichment JSONB,
       tokens_used INTEGER DEFAULT 0,
       created_at TIMESTAMP NOT NULL DEFAULT NOW(),

       -- Indexes
       INDEX idx_chat_messages_conversation_created (conversation_id, created_at),
       INDEX idx_chat_messages_intent (intent),
       INDEX idx_chat_messages_created_at (created_at)
   );

   -- Update chat_conversations
   ALTER TABLE chat_conversations
       ADD COLUMN language VARCHAR(10) DEFAULT 'en',
       ADD COLUMN title VARCHAR(255),
       ADD COLUMN is_deleted BOOLEAN DEFAULT false,
       ADD COLUMN deleted_at TIMESTAMP;

   -- Update chat_users (add preferences)
   ALTER TABLE chat_users
       ADD COLUMN preferred_language VARCHAR(10) DEFAULT 'en',
       ADD COLUMN favorite_tokens JSONB DEFAULT '[]',
       ADD COLUMN settings JSONB DEFAULT '{}',
       ADD COLUMN last_seen_at TIMESTAMP;

   -- Performance indexes
   CREATE INDEX idx_chat_conversations_user_status ON chat_conversations(chat_user_id, status, created_at DESC);
   CREATE INDEX idx_chat_conversations_user_deleted ON chat_conversations(chat_user_id, is_deleted) WHERE is_deleted = false;
   CREATE INDEX idx_chat_users_user_id ON chat_users(user_id);
   ```

2. **Domain Entities** (1 day)
   - Create ChatUser, ChatConversation, ChatMessage entities
   - Create value objects (ConversationStatus, MessageRole, UserPreferences)
   - Add validation rules

3. **Repository Layer** (2 days)
   - ChatUserRepository (CRUD operations)
   - ChatConversationRepository (with ownership validation)
   - ChatMessageRepository (with pagination)
   - Add unit tests for repositories

**Deliverables:**
- [ ] Alembic migration for chat_messages table
- [ ] Updated domain entities
- [ ] Repository implementations
- [ ] Unit tests (>90% coverage)

**Estimated Time:** 5 days

---

### Phase 2: Application Layer (Week 2)

**Objectives:**
- Implement commands and queries
- Create chat handler service for authenticated users
- Integrate with existing Hunter AI handlers
- Add caching layer

**Tasks:**

1. **Commands Implementation** (2 days)
   - CreateConversationCommand + handler
   - SendMessageCommand + handler
   - UpdatePreferencesCommand + handler
   - ArchiveConversationCommand + handler
   - ExportConversationCommand + handler

2. **Queries Implementation** (2 days)
   - GetConversationsQuery + handler
   - GetConversationHistoryQuery + handler
   - SearchConversationsQuery + handler
   - GetUserPreferencesQuery + handler

3. **Chat Handler Service** (3 days)
   - Adapt GuestHandlerService for authenticated users
   - Add premium feature flags
   - Integrate with user preferences
   - Add conversation title auto-generation
   - Implement rate limiting (1000 msg/hour)

**Code Example:**
```python
# src/app/application/chat/handlers/chat_handler_service.py

class ChatHandlerService:
    """Authenticated user chat handler."""

    def __init__(
        self,
        user_gateway: ChatUserCommandGateway,
        conversation_gateway: ChatConversationCommandGateway,
        message_gateway: ChatMessageCommandGateway,
        cache: GuestCache,  # Reuse same cache
        hunter_service: Any,  # Reuse Hunter AI service
    ):
        self._user_gateway = user_gateway
        self._conversation_gateway = conversation_gateway
        self._message_gateway = message_gateway
        self._cache = cache
        self._hunter_service = hunter_service

    async def handle_message(
        self,
        user_id: UUID,
        conversation_id: UUID,
        content: str,
    ) -> ChatMessage:
        """Handle authenticated user message."""

        # 1. Get chat user and preferences
        chat_user = await self._get_or_create_chat_user(user_id)
        preferences = await self._get_preferences(chat_user.id)

        # 2. Validate conversation ownership
        conversation = await self._conversation_gateway.get_by_id(
            conversation_id
        )
        if conversation.chat_user_id != chat_user.id:
            raise UnauthorizedError("Not your conversation")

        # 3. Check rate limiting (authenticated users have higher limits)
        await self._check_rate_limit(chat_user.id)

        # 4. Classify intent and route
        intent = await self._classify_intent(content)
        language = preferences.language or conversation.language

        # 5. Check cache (same as guest)
        token = self._extract_token(content)
        cached = await self._cache.get_hunter_response(
            intent, token, language
        )

        if cached:
            # Create message from cache
            return await self._create_message(
                conversation_id,
                "user",
                content,
                intent,
                cached
            )

        # 6. Process with Hunter AI (premium features enabled)
        response = await self._process_hunter_ai(
            intent,
            token or "BTC",
            language,
            is_authenticated=True,  # Enables premium features
            user_preferences=preferences,
        )

        # 7. Cache response
        await self._cache.set_hunter_response(
            intent, token or "BTC", language, response
        )

        # 8. Save message
        message = await self._create_message(
            conversation_id,
            "user",
            content,
            intent,
            response
        )

        # 9. Update conversation title if needed
        if await self._should_update_title(conversation):
            await self._auto_generate_title(conversation, content)

        return message
```

**Deliverables:**
- [ ] Command handlers implemented
- [ ] Query handlers implemented
- [ ] ChatHandlerService complete
- [ ] Integration tests (>85% coverage)

**Estimated Time:** 7 days

---

### Phase 3: API Layer (Week 3)

**Objectives:**
- Create REST API endpoints
- Add authentication middleware
- Implement request/response models
- Add API documentation

**Tasks:**

1. **API Endpoints** (3 days)
   ```python
   # src/app/presentation/http/controllers/chat/authenticated_chat_router.py

   router = APIRouter(prefix="/api/v1/chat", tags=["Authenticated Chat"])

   @router.post("/conversations", response_model=ConversationResponse)
   async def create_conversation(
       request: CreateConversationRequest,
       current_user: User = Depends(get_current_user),
   ):
       """Create new conversation."""
       pass

   @router.get("/conversations", response_model=List[ConversationResponse])
   async def get_conversations(
       status: Optional[str] = None,
       limit: int = 50,
       offset: int = 0,
       current_user: User = Depends(get_current_user),
   ):
       """Get user's conversations."""
       pass

   @router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
   async def get_conversation(
       conversation_id: UUID,
       current_user: User = Depends(get_current_user),
   ):
       """Get conversation with messages."""
       pass

   @router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
   async def send_message(
       conversation_id: UUID,
       request: SendMessageRequest,
       current_user: User = Depends(get_current_user),
   ):
       """Send message in conversation."""
       pass

   @router.patch("/conversations/{conversation_id}/archive")
   async def archive_conversation(
       conversation_id: UUID,
       current_user: User = Depends(get_current_user),
   ):
       """Archive conversation."""
       pass

   @router.get("/conversations/{conversation_id}/export")
   async def export_conversation(
       conversation_id: UUID,
       format: str = "json",
       current_user: User = Depends(get_current_user),
   ):
       """Export conversation history."""
       pass

   @router.get("/preferences", response_model=PreferencesResponse)
   async def get_preferences(
       current_user: User = Depends(get_current_user),
   ):
       """Get user preferences."""
       pass

   @router.put("/preferences", response_model=PreferencesResponse)
   async def update_preferences(
       request: UpdatePreferencesRequest,
       current_user: User = Depends(get_current_user),
   ):
       """Update user preferences."""
       pass
   ```

2. **Request/Response Models** (1 day)
   ```python
   # src/app/presentation/http/schemas/chat.py

   class CreateConversationRequest(BaseModel):
       language: str = Field("en", pattern="^(en|es|pt|zh)$")
       title: Optional[str] = Field(None, max_length=255)

   class SendMessageRequest(BaseModel):
       content: str = Field(..., min_length=1, max_length=2000)

   class ConversationResponse(BaseModel):
       id: UUID
       status: str
       language: str
       title: Optional[str]
       message_count: int
       last_message_at: Optional[datetime]
       created_at: datetime

   class MessageResponse(BaseModel):
       id: UUID
       role: str
       content: str
       intent: Optional[str]
       enrichment: Optional[dict]
       created_at: datetime

   class ConversationDetailResponse(BaseModel):
       conversation: ConversationResponse
       messages: List[MessageResponse]
       has_more: bool
   ```

3. **Authentication Integration** (1 day)
   - Use existing JWT authentication
   - Add user context to requests
   - Validate ownership on all operations

4. **API Documentation** (1 day)
   - OpenAPI/Swagger documentation
   - Request/response examples
   - Authentication guide
   - Migration guide from legacy API

**Deliverables:**
- [ ] REST API endpoints implemented
- [ ] Authentication integrated
- [ ] API documentation complete
- [ ] Postman collection created

**Estimated Time:** 6 days

---

### Phase 4: Testing & Migration (Week 4)

**Objectives:**
- Comprehensive testing
- Data migration from legacy system
- Performance testing
- Documentation

**Tasks:**

1. **Testing** (3 days)
   - Unit tests (target: >90% coverage)
   - Integration tests (all API endpoints)
   - E2E tests (user flows)
   - Load testing (1000 concurrent users)
   - Security testing (OWASP Top 10)

2. **Data Migration** (2 days)
   ```python
   # scripts/migrate_legacy_chat.py

   async def migrate_legacy_conversations():
       """Migrate conversations from legacy system."""
       # Read from old tables (conversations, users with INTEGER user_id)
       # Transform to new schema (UUID user_id, new structure)
       # Insert into new tables (chat_users, chat_conversations, chat_messages)
       pass
   ```

3. **Performance Testing** (1 day)
   - Load test with realistic traffic
   - Cache performance validation
   - Database query optimization
   - Target: P95 <500ms, error rate <1%

4. **Documentation** (1 day)
   - API migration guide
   - Feature comparison doc
   - User guide
   - Developer guide

**Deliverables:**
- [ ] Test suite complete (>90% coverage)
- [ ] Migration script tested
- [ ] Performance validated
- [ ] Documentation complete

**Estimated Time:** 7 days

---

## Database Schema

### Complete Schema

```sql
-- ============================================
-- AUTHENTICATED USER CHAT TABLES
-- ============================================

-- Chat users (authenticated)
CREATE TABLE chat_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,  -- References auth.users
    preferred_language VARCHAR(10) DEFAULT 'en',
    favorite_tokens JSONB DEFAULT '[]',
    settings JSONB DEFAULT '{}',
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_chat_users_user_id FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Conversations
CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_user_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    language VARCHAR(10) DEFAULT 'en',
    title VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_chat_conversations_user FOREIGN KEY (chat_user_id) REFERENCES chat_users(id) ON DELETE CASCADE,
    CONSTRAINT chk_status CHECK (status IN ('active', 'archived', 'deleted'))
);

-- Messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(100),
    enrichment JSONB,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_chat_messages_conversation FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE,
    CONSTRAINT chk_role CHECK (role IN ('user', 'assistant', 'system'))
);

-- ============================================
-- PERFORMANCE INDEXES
-- ============================================

-- Chat users
CREATE INDEX idx_chat_users_user_id ON chat_users(user_id);
CREATE INDEX idx_chat_users_last_seen ON chat_users(last_seen_at);

-- Conversations
CREATE INDEX idx_chat_conversations_user_status ON chat_conversations(chat_user_id, status, created_at DESC);
CREATE INDEX idx_chat_conversations_user_active ON chat_conversations(chat_user_id, created_at DESC) WHERE status = 'active' AND is_deleted = false;
CREATE INDEX idx_chat_conversations_created ON chat_conversations(created_at DESC);

-- Messages
CREATE INDEX idx_chat_messages_conversation_created ON chat_messages(conversation_id, created_at ASC);
CREATE INDEX idx_chat_messages_intent ON chat_messages(intent);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at DESC);

-- Full-text search (optional, for advanced features)
CREATE INDEX idx_chat_messages_content_fts ON chat_messages USING gin(to_tsvector('english', content));
```

---

## API Design

### Endpoint Summary

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/chat/conversations` | POST | Create conversation | ✅ |
| `/api/v1/chat/conversations` | GET | List conversations | ✅ |
| `/api/v1/chat/conversations/{id}` | GET | Get conversation detail | ✅ |
| `/api/v1/chat/conversations/{id}` | PATCH | Update conversation | ✅ |
| `/api/v1/chat/conversations/{id}` | DELETE | Delete conversation | ✅ |
| `/api/v1/chat/conversations/{id}/archive` | PATCH | Archive conversation | ✅ |
| `/api/v1/chat/conversations/{id}/messages` | GET | Get messages | ✅ |
| `/api/v1/chat/conversations/{id}/messages` | POST | Send message | ✅ |
| `/api/v1/chat/conversations/{id}/export` | GET | Export conversation | ✅ |
| `/api/v1/chat/preferences` | GET | Get preferences | ✅ |
| `/api/v1/chat/preferences` | PUT | Update preferences | ✅ |
| `/api/v1/chat/search` | GET | Search conversations | ✅ |

### API Examples

**Create Conversation:**
```bash
POST /api/v1/chat/conversations
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "language": "en",
  "title": "BTC Analysis"
}

# Response
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "language": "en",
  "title": "BTC Analysis",
  "message_count": 0,
  "created_at": "2026-01-11T10:00:00Z"
}
```

**Send Message:**
```bash
POST /api/v1/chat/conversations/{id}/messages
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "content": "What is the sentiment for BTC?"
}

# Response
{
  "id": "456e7890-e89b-12d3-a456-426614174001",
  "role": "assistant",
  "content": "📊 **Sentiment Analysis for BTC**...",
  "intent": "hunter_sentiment",
  "enrichment": {
    "token": "BTC",
    "overall_score": 0.45,
    "classification": "bullish",
    ...
  },
  "created_at": "2026-01-11T10:01:00Z"
}
```

---

## Migration Strategy

### Legacy to New System Migration

**Phase 1: Dual Write (Weeks 1-2)**
- Write to both legacy and new system
- Read from legacy system (no user impact)
- Validate data consistency

**Phase 2: Gradual Read Migration (Weeks 3-4)**
- 10% of reads from new system
- Monitor performance and errors
- Increase to 50%, then 100%

**Phase 3: Deprecate Legacy (Week 5)**
- All traffic to new system
- Keep legacy read-only for 30 days
- Mark legacy endpoints as deprecated

**Phase 4: Legacy Removal (2026-06-01)**
- Remove legacy endpoints
- Archive legacy data
- Clean up database

### Data Migration Script

```python
# scripts/migrate_legacy_chat.py

async def migrate_user_conversations(user_id: int):
    """Migrate single user's conversations."""

    # 1. Get legacy user data
    legacy_user = await legacy_db.execute(
        "SELECT * FROM users WHERE id = :id",
        {"id": user_id}
    )

    # 2. Create or get chat_user
    chat_user = await new_db.execute(
        """
        INSERT INTO chat_users (user_id, created_at, updated_at)
        VALUES (:user_id, :created_at, :updated_at)
        ON CONFLICT (user_id) DO UPDATE SET updated_at = :updated_at
        RETURNING *
        """,
        {
            "user_id": legacy_user.uuid,  # Convert to UUID
            "created_at": legacy_user.created_at,
            "updated_at": datetime.utcnow(),
        }
    )

    # 3. Migrate conversations
    legacy_conversations = await legacy_db.execute(
        "SELECT * FROM conversations WHERE user_id = :id",
        {"id": user_id}
    )

    for conv in legacy_conversations:
        new_conv = await new_db.execute(
            """
            INSERT INTO chat_conversations
            (id, chat_user_id, status, language, created_at, updated_at)
            VALUES (:id, :chat_user_id, :status, :language, :created_at, :updated_at)
            RETURNING *
            """,
            {
                "id": conv.uuid or uuid4(),
                "chat_user_id": chat_user.id,
                "status": "active",  # Default status
                "language": conv.language or "en",
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
            }
        )

        # 4. Migrate messages
        legacy_messages = await legacy_db.execute(
            "SELECT * FROM messages WHERE conversation_id = :id",
            {"id": conv.id}
        )

        for msg in legacy_messages:
            await new_db.execute(
                """
                INSERT INTO chat_messages
                (conversation_id, role, content, intent, enrichment, created_at)
                VALUES (:conv_id, :role, :content, :intent, :enrichment, :created_at)
                """,
                {
                    "conv_id": new_conv.id,
                    "role": msg.role,
                    "content": msg.content,
                    "intent": msg.intent,
                    "enrichment": msg.enrichment,
                    "created_at": msg.created_at,
                }
            )
```

---

## Testing Strategy

### Unit Tests (Target: >90% Coverage)

```python
# tests/unit/domain/chat/test_entities.py
def test_chat_user_creation():
    """Test ChatUser entity creation."""
    pass

# tests/unit/application/chat/test_commands.py
async def test_create_conversation_command():
    """Test CreateConversationCommand handler."""
    pass

# tests/unit/application/chat/test_handlers.py
async def test_chat_handler_message_processing():
    """Test ChatHandlerService message processing."""
    pass
```

### Integration Tests (Target: >85% Coverage)

```python
# tests/integration/chat/test_conversation_flow.py
async def test_full_conversation_flow():
    """Test create conversation → send message → get history."""
    # 1. Create conversation
    # 2. Send message
    # 3. Verify response
    # 4. Get conversation history
    # 5. Verify message in history
    pass
```

### E2E Tests

```python
# tests/e2e/chat/test_authenticated_chat.py
async def test_authenticated_user_chat_journey():
    """Test full authenticated user journey."""
    # 1. Login
    # 2. Create conversation
    # 3. Send multiple messages
    # 4. Test caching (second request faster)
    # 5. Archive conversation
    # 6. Export conversation
    pass
```

### Load Tests

```python
# tests/load/authenticated_chat_load_test.py
async def test_authenticated_chat_load():
    """Load test authenticated chat with 1000 concurrent users."""
    # Target metrics:
    # - P95 response time <500ms
    # - Error rate <1%
    # - Cache hit rate >80%
    # - Throughput >100 req/s
    pass
```

---

## Success Criteria

### Functional Requirements ✅

- [ ] Users can create conversations
- [ ] Users can send messages with all Hunter AI intents
- [ ] Users can view conversation history
- [ ] Users can archive/delete conversations
- [ ] Users can export conversation history
- [ ] Users can set preferences (language, favorite tokens)
- [ ] Multi-language support works
- [ ] Premium features available for authenticated users

### Performance Requirements ✅

- [ ] P95 response time <500ms
- [ ] P99 response time <1000ms
- [ ] Error rate <1%
- [ ] Cache hit rate >80%
- [ ] Database queries <50ms average
- [ ] Support 1000 concurrent users

### Quality Requirements ✅

- [ ] Unit test coverage >90%
- [ ] Integration test coverage >85%
- [ ] All E2E tests passing
- [ ] Load tests passing
- [ ] Security audit passed (OWASP Top 10)
- [ ] Code review completed

### Migration Requirements ✅

- [ ] All legacy data migrated successfully
- [ ] No data loss during migration
- [ ] Backward compatible API during migration
- [ ] Legacy system deprecated gracefully
- [ ] Documentation updated

---

## Timeline

### Week 1: Database & Infrastructure
- Days 1-2: Database schema updates
- Day 3: Domain entities
- Days 4-5: Repository layer + tests

### Week 2: Application Layer
- Days 1-2: Commands implementation
- Days 3-4: Queries implementation
- Days 5-7: Chat handler service + integration

### Week 3: API Layer
- Days 1-3: REST API endpoints
- Day 4: Authentication integration
- Day 5: Request/response models
- Day 6: API documentation

### Week 4: Testing & Migration
- Days 1-3: Comprehensive testing
- Days 4-5: Data migration script + testing
- Day 6: Performance testing
- Day 7: Documentation + deployment prep

**Total Duration: 4 weeks (20 working days)**

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Data migration fails | High | Low | Thorough testing, rollback plan |
| Performance degradation | High | Medium | Load testing, caching, indexes |
| Cache key conflicts | Medium | Low | Separate namespaces for guest/auth |
| Legacy system dependencies | Medium | Medium | Gradual migration, dual write |

### Business Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| User confusion during migration | Medium | Medium | Clear communication, docs |
| Feature parity delays | Low | Low | Reuse guest chat patterns |
| Increased support load | Medium | Medium | Self-service docs, FAQs |

---

## Dependencies

### External Dependencies
- ✅ Guest chat system (Phase 3 complete)
- ✅ Authentication system (JWT, existing)
- ✅ Hunter AI handlers (existing)
- ✅ Redis cache (configured)
- ✅ PostgreSQL database (configured)

### Internal Dependencies
- Domain models for authenticated users
- Repository pattern implementation
- Dishka dependency injection setup

---

## Next Steps

1. **Review & Approval**
   - Review plan with team
   - Get stakeholder sign-off
   - Prioritize features

2. **Kickoff (Week 1)**
   - Create Jira tickets
   - Set up project tracking
   - Assign team members
   - Begin Phase 1 implementation

3. **Regular Check-ins**
   - Daily standups
   - Weekly progress reviews
   - Bi-weekly stakeholder updates

---

## Appendix

### Related Documents
- `docs/GUEST_CHAT_SYSTEM.md` - Guest chat reference
- `docs/GUEST_CHAT_PHASE3_PERFORMANCE.md` - Performance benchmarks
- `docs/api/GUEST_CHAT_API.md` - API design reference
- `docs/DEPRECATION_PLAN.md` - Legacy system deprecation

### Team
- **Lead Engineer:** TBD
- **Backend Engineers:** TBD (2-3 developers)
- **QA Engineer:** TBD
- **DevOps:** TBD

---

**Plan Created:** 2026-01-11
**Last Updated:** 2026-01-11
**Status:** Draft - Awaiting Approval
**Version:** 1.0
