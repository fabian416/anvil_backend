# Deprecation Cleanup Specification

**Status**: 📋 Planning
**Target Date**: 2026-06-01
**Created**: 2026-01-25
**Author**: @tech-lead-orchestrator @backend-engineer

---

## Executive Summary

This specification documents all deprecated components scheduled for removal from the Anvil Backend codebase. The cleanup consolidates the chat system from multiple fragmented implementations into a single unified system, removes legacy session management, and cleans up unused database tables.

**Impact Summary**:
- 🔴 **8 Database Tables** to be dropped
- 🔴 **3 Router Files** to be removed
- 🔴 **4 Mapping Files** to be deprecated
- 🔴 **~2,500 Lines of Code** to be removed
- ✅ **Unified Chat System** as single source of truth

---

## Phase 1: Database Tables for Removal

### 1.1 Legacy Chat System Tables (Priority: HIGH)

These tables are replaced by the unified `chat_*` tables.

| Table | Rows | Replacement | Status |
|-------|------|-------------|--------|
| `conversations` | 230 | `chat_conversations` (981) | 🔴 Deprecated |
| `messages` | 603 | `chat_messages` (5370) | 🔴 Deprecated |

**Data Migration Status**: ✅ Complete (62 conversations migrated)

**Foreign Key Dependencies**:
```
conversations → users.id (INTEGER)
messages → conversations.id (UUID)
```

**Removal SQL**:
```sql
-- Step 1: Backup tables before dropping
CREATE TABLE _backup_conversations_20260601 AS SELECT * FROM conversations;
CREATE TABLE _backup_messages_20260601 AS SELECT * FROM messages;

-- Step 2: Drop dependent tables first
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
```

### 1.2 Legacy Guest System Tables (Priority: HIGH)

These tables are replaced by the unified `chat_*` tables with `user_type='guest'`.

| Table | Rows | Replacement | Status |
|-------|------|-------------|--------|
| `guest_users` | 1,165 | `chat_users` (user_type='guest') | 🔴 Deprecated |
| `guest_conversations` | 1,165 | `chat_conversations` | 🔴 Deprecated |
| `guest_messages` | 7,975 | `chat_messages` | 🔴 Deprecated |
| `guest_telemetry` | TBD | Analytics snapshots | 🔴 Deprecated |

**Foreign Key Dependencies**:
```
guest_conversations → guest_users.id
guest_messages → guest_conversations.id
guest_telemetry → guest_users.id, guest_conversations.id
```

**Removal SQL**:
```sql
-- Step 1: Backup tables before dropping
CREATE TABLE _backup_guest_users_20260601 AS SELECT * FROM guest_users;
CREATE TABLE _backup_guest_conversations_20260601 AS SELECT * FROM guest_conversations;
CREATE TABLE _backup_guest_messages_20260601 AS SELECT * FROM guest_messages;
CREATE TABLE _backup_guest_telemetry_20260601 AS SELECT * FROM guest_telemetry;

-- Step 2: Drop dependent tables first (order matters)
DROP TABLE IF EXISTS guest_telemetry CASCADE;
DROP TABLE IF EXISTS guest_messages CASCADE;
DROP TABLE IF EXISTS guest_conversations CASCADE;
DROP TABLE IF EXISTS guest_users CASCADE;
```

### 1.3 Legacy Session Management (Priority: MEDIUM)

The `sessions` table is replaced by `auth_sessions` with improved JWT handling.

| Table | Rows | Replacement | Status |
|-------|------|-------------|--------|
| `sessions` | 310 | `auth_sessions` (17) | 🔴 Deprecated |

**Note**: The `sessions` table uses INTEGER-based user_id while `auth_sessions` is the current authentication system.

**Removal SQL**:
```sql
CREATE TABLE _backup_sessions_20260601 AS SELECT * FROM sessions;
DROP TABLE IF EXISTS sessions CASCADE;
```

### 1.4 Unused Tables (Priority: LOW)

These tables have 0 rows and appear to be from abandoned features.

| Table | Rows | Description | Status |
|-------|------|-------------|--------|
| `llm_conversations` | 0 | LLM orchestration (unused) | 🔴 Remove |
| `user_chat_preferences` | 0 | Replaced by `chat_users.metadata` | 🔴 Remove |
| `models` | 0 | Unused model registry | 🔴 Review |
| `settings` | 0 | Unused settings table | 🔴 Review |

**Removal SQL**:
```sql
DROP TABLE IF EXISTS llm_conversations CASCADE;
DROP TABLE IF EXISTS user_chat_preferences CASCADE;
DROP TABLE IF EXISTS models CASCADE;
DROP TABLE IF EXISTS settings CASCADE;
```

---

## Phase 2: API Endpoints for Removal

### 2.1 Legacy Chat Router (Priority: HIGH)

**File**: `src/app/presentation/http/controllers/chat/router.py`
**Base Path**: `/api/v1/user/chat/*`
**Lines of Code**: ~1,070

| Endpoint | Method | Replacement |
|----------|--------|-------------|
| `/user/chat/conversations` | POST | `/conversations` |
| `/user/chat/conversations` | GET | `/conversations` |
| `/user/chat/conversations/{id}` | GET | `/conversations/{id}` |
| `/user/chat/conversations/{id}` | PATCH | `/conversations/{id}` |
| `/user/chat/conversations/{id}` | DELETE | `/conversations/{id}` |
| `/user/chat/conversations/{id}/messages` | POST | `/conversations/{id}/messages` |
| `/user/chat/conversations/{id}/messages` | GET | `/conversations/{id}/messages` |
| `/user/chat/conversations/{id}/execute` | POST | `/conversations/{id}/messages` (with metadata) |

**Current State**: 
- ✅ Deprecation headers implemented
- ✅ Warning logs enabled
- ⏳ Usage monitoring active

### 2.2 Files to Remove

| File | Description | Lines |
|------|-------------|-------|
| `src/app/presentation/http/controllers/chat/router.py` | Legacy chat router | ~1,070 |
| `src/app/infrastructure/persistence_sqla/mappings/conversation.py` | Legacy mapping | ~37 |
| `src/app/infrastructure/persistence_sqla/mappings/message.py` | Legacy mapping | ~43 |
| `src/app/infrastructure/persistence_sqla/mappings/guest.py` | Legacy guest mapping | ~136 |
| `src/app/infrastructure/persistence_sqla/mappings/session.py` | Legacy sessions | ~42 |

**Total Lines to Remove**: ~1,328

---

## Phase 3: Code Dependencies to Update

### 3.1 Import Updates Required

**File**: `src/app/presentation/http/controllers/api_v1_router.py`

Remove:
```python
from app.presentation.http.controllers.chat.router import create_chat_router
# Line 43 and 165
```

### 3.2 Mapping Registry Updates

**File**: `src/app/infrastructure/persistence_sqla/mappings/all.py`

Remove calls to:
```python
map_conversation_table()
map_message_table()
map_guest_tables()
map_sessions_table()
```

### 3.3 Domain Entity Review

| Entity | File | Status |
|--------|------|--------|
| `Conversation` | `src/app/domain/chat/entities/conversation.py` | 🔴 Review - may be deprecated |
| `Message` (legacy) | Used by legacy router | 🔴 Remove |

---

## Phase 4: Tables to Keep (Verification)

### 4.1 Active Chat System (KEEP)

| Table | Rows | Purpose |
|-------|------|---------|
| `chat_users` | 15 | Unified user table (guest + authenticated) |
| `chat_conversations` | 981 | Active conversations |
| `chat_messages` | 5,370 | Chat messages with metadata |
| `chat_rate_limits` | TBD | Rate limiting |

### 4.2 Active Authentication (KEEP)

| Table | Rows | Purpose |
|-------|------|---------|
| `auth_sessions` | 17 | Active JWT sessions |
| `users` | TBD | Core user table |

### 4.3 Context-Aware System (KEEP)

| Table | Rows | Purpose |
|-------|------|---------|
| `user_context_aware` | TBD | User classification data |
| `analytics_snapshots` | TBD | Analytics aggregations |

---

## Phase 5: Migration Alembic Script

Create a single migration for the complete cleanup:

```python
"""Remove deprecated chat and session tables.

Revision ID: cleanup_deprecated_20260601
Revises: <previous_revision>
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'cleanup_deprecated_20260601'
down_revision = '<previous>'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Create backup schema
    op.execute("CREATE SCHEMA IF NOT EXISTS deprecated_backup")
    
    # Step 2: Move tables to backup schema
    op.execute("ALTER TABLE IF EXISTS conversations SET SCHEMA deprecated_backup")
    op.execute("ALTER TABLE IF EXISTS messages SET SCHEMA deprecated_backup")
    op.execute("ALTER TABLE IF EXISTS guest_users SET SCHEMA deprecated_backup")
    op.execute("ALTER TABLE IF EXISTS guest_conversations SET SCHEMA deprecated_backup")
    op.execute("ALTER TABLE IF EXISTS guest_messages SET SCHEMA deprecated_backup")
    op.execute("ALTER TABLE IF EXISTS guest_telemetry SET SCHEMA deprecated_backup")
    op.execute("ALTER TABLE IF EXISTS sessions SET SCHEMA deprecated_backup")
    op.execute("ALTER TABLE IF EXISTS llm_conversations SET SCHEMA deprecated_backup")
    op.execute("ALTER TABLE IF EXISTS user_chat_preferences SET SCHEMA deprecated_backup")
    op.execute("ALTER TABLE IF EXISTS models SET SCHEMA deprecated_backup")
    op.execute("ALTER TABLE IF EXISTS settings SET SCHEMA deprecated_backup")


def downgrade() -> None:
    # Restore tables from backup schema
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.conversations SET SCHEMA public")
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.messages SET SCHEMA public")
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.guest_users SET SCHEMA public")
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.guest_conversations SET SCHEMA public")
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.guest_messages SET SCHEMA public")
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.guest_telemetry SET SCHEMA public")
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.sessions SET SCHEMA public")
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.llm_conversations SET SCHEMA public")
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.user_chat_preferences SET SCHEMA public")
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.models SET SCHEMA public")
    op.execute("ALTER TABLE IF EXISTS deprecated_backup.settings SET SCHEMA public")
```

---

## Implementation Timeline

### Pre-Cleanup (Now - 2026-05-01)
- [ ] Monitor deprecated endpoint usage
- [ ] Send migration reminders to API consumers
- [ ] Verify all data migrated to new system
- [ ] Update frontend to use new endpoints

### Cleanup Phase 1 (2026-06-01)
- [ ] Remove legacy router from `api_v1_router.py`
- [ ] Return HTTP 410 Gone for legacy endpoints
- [ ] Run database backup
- [ ] Execute Alembic migration

### Cleanup Phase 2 (2026-06-08)
- [ ] Remove mapping files
- [ ] Remove domain entities if unused
- [ ] Update tests
- [ ] Remove from mapping registry

### Post-Cleanup (2026-06-15)
- [ ] Verify system stability
- [ ] Drop backup schema after 30 days retention
- [ ] Update documentation

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| API consumers not migrated | HIGH | Email notifications, banner warnings |
| Data loss | HIGH | Backup schema with 30-day retention |
| Foreign key issues | MEDIUM | CASCADE deletes, careful ordering |
| Test failures | LOW | Update tests before removal |

---

## Verification Checklist

Before executing removal:

```bash
# 1. Check deprecated endpoint usage
grep "DEPRECATED ENDPOINT USED" logs/fastapi.log | wc -l

# 2. Verify data migration complete
psql -c "SELECT COUNT(*) FROM conversations WHERE id NOT IN (SELECT id FROM chat_conversations)"

# 3. Verify no active sessions in legacy table
psql -c "SELECT COUNT(*) FROM sessions WHERE is_active = true AND expires_at > NOW()"

# 4. Run test suite
pytest tests/integration/user/ -v
```

---

## Appendix: Table Row Counts Summary

| Category | Table | Rows | Action |
|----------|-------|------|--------|
| **ACTIVE** | chat_conversations | 981 | KEEP |
| **ACTIVE** | chat_messages | 5,370 | KEEP |
| **ACTIVE** | chat_users | 15 | KEEP |
| **ACTIVE** | auth_sessions | 17 | KEEP |
| **DEPRECATED** | conversations | 230 | REMOVE |
| **DEPRECATED** | messages | 603 | REMOVE |
| **DEPRECATED** | guest_users | 1,165 | REMOVE |
| **DEPRECATED** | guest_conversations | 1,165 | REMOVE |
| **DEPRECATED** | guest_messages | 7,975 | REMOVE |
| **DEPRECATED** | sessions | 310 | REMOVE |
| **UNUSED** | llm_conversations | 0 | REMOVE |
| **UNUSED** | user_chat_preferences | 0 | REMOVE |
| **UNUSED** | models | 0 | REVIEW |
| **UNUSED** | settings | 0 | REVIEW |

---

## References

- [DEPRECATION_PLAN.md](../../DEPRECATION_PLAN.md) - Original deprecation plan
- [GUEST_CHAT_SYSTEM.md](../../GUEST_CHAT_SYSTEM.md) - Guest system documentation
- [UNIFIED_CHAT_ROUTING_PROPOSAL.md](../../UNIFIED_CHAT_ROUTING_PROPOSAL.md) - Chat unification proposal
