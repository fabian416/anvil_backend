# Deprecation Cleanup - Implementation Tasks

**Spec**: [requirements.md](./requirements.md)
**Target Date**: 2026-06-01

---

## Task Overview

| Phase | Tasks | Priority | Status |
|-------|-------|----------|--------|
| Phase 1 | Pre-Cleanup Preparation | HIGH | [ ] Pending |
| Phase 2 | Database Table Removal | HIGH | [ ] Pending |
| Phase 3 | API Router Removal | HIGH | [ ] Pending |
| Phase 4 | Code Cleanup | MEDIUM | [ ] Pending |
| Phase 5 | Testing & Verification | HIGH | [ ] Pending |
| Phase 6 | Documentation Update | LOW | [ ] Pending |

---

## Phase 1: Pre-Cleanup Preparation

### 1.1 Monitor Deprecated Endpoint Usage
- [ ] **Task 1.1.1**: Create monitoring dashboard for deprecated endpoints
  - File: `src/app/presentation/http/controllers/admin/deprecation_monitor.py`
  - Track: `/user/chat/*` endpoint usage
  - Alert: When usage > 0 in last 24 hours

- [ ] **Task 1.1.2**: Add structured logging for deprecation tracking
  ```python
  logger.warning(
      "DEPRECATED_ENDPOINT_USED",
      extra={
          "endpoint": request.url.path,
          "user_id": current_user.id,
          "timestamp": datetime.now(UTC).isoformat()
      }
  )
  ```

### 1.2 Data Migration Verification
- [ ] **Task 1.2.1**: Verify all conversations migrated
  ```sql
  SELECT COUNT(*) as unmigrated 
  FROM conversations c 
  WHERE NOT EXISTS (
      SELECT 1 FROM chat_conversations cc 
      WHERE cc.id = c.id
  );
  ```

- [ ] **Task 1.2.2**: Verify all guest data migrated
  ```sql
  SELECT 
      (SELECT COUNT(*) FROM guest_users) as guest_users,
      (SELECT COUNT(*) FROM chat_users WHERE user_type = 'guest') as migrated_guests;
  ```

### 1.3 Client Notification
- [ ] **Task 1.3.1**: Send email notifications to API consumers
- [ ] **Task 1.3.2**: Add banner warning in frontend UI
- [ ] **Task 1.3.3**: Update API documentation with deprecation notices

---

## Phase 2: Database Table Removal

### 2.1 Create Alembic Migration
- [ ] **Task 2.1.1**: Create migration file
  - File: `src/app/infrastructure/persistence_sqla/alembic/versions/2026_06_01_xxxx_remove_deprecated_tables.py`
  - Strategy: Move to `deprecated_backup` schema (not DROP)

### 2.2 Tables to Remove (Order Matters!)

Execute in this order to respect foreign key dependencies:

```
1. messages (depends on conversations)
2. conversations (depends on users)
3. guest_telemetry (depends on guest_users, guest_conversations)
4. guest_messages (depends on guest_conversations)
5. guest_conversations (depends on guest_users)
6. guest_users (no deps)
7. sessions (depends on users)
8. llm_conversations (no deps)
9. user_chat_preferences (no deps)
10. models (no deps)
11. settings (no deps)
```

- [ ] **Task 2.2.1**: Backup `messages` table
- [ ] **Task 2.2.2**: Backup `conversations` table
- [ ] **Task 2.2.3**: Backup `guest_*` tables (4 tables)
- [ ] **Task 2.2.4**: Backup `sessions` table
- [ ] **Task 2.2.5**: Backup unused tables (4 tables)
- [ ] **Task 2.2.6**: Move all to `deprecated_backup` schema

---

## Phase 3: API Router Removal

### 3.1 Remove Legacy Chat Router
- [ ] **Task 3.1.1**: Update `api_v1_router.py`
  ```python
  # REMOVE these lines:
  from app.presentation.http.controllers.chat.router import create_chat_router
  # Line 43
  
  # REMOVE from sub_routers:
  create_chat_router(),
  # Line 165
  ```

- [ ] **Task 3.1.2**: Create HTTP 410 Gone stub router
  ```python
  @router.api_route("/{path:path}", methods=["GET", "POST", "PATCH", "DELETE"])
  async def legacy_endpoint_gone(path: str):
      raise HTTPException(
          status_code=410,
          detail={
              "error": "Gone",
              "message": "This endpoint has been removed. Use /api/v1/conversations/* instead.",
              "documentation": "https://docs.anvil.io/migration-guide",
              "sunset_date": "2026-06-01"
          }
      )
  ```

### 3.2 Files to Delete
- [ ] **Task 3.2.1**: Delete `src/app/presentation/http/controllers/chat/router.py` (1,070 lines)
- [ ] **Task 3.2.2**: Archive file to `_deprecated/` folder first

---

## Phase 4: Code Cleanup

### 4.1 Remove Mapping Files
- [ ] **Task 4.1.1**: Delete `src/app/infrastructure/persistence_sqla/mappings/conversation.py`
- [ ] **Task 4.1.2**: Delete `src/app/infrastructure/persistence_sqla/mappings/message.py`
- [ ] **Task 4.1.3**: Delete `src/app/infrastructure/persistence_sqla/mappings/guest.py`
- [ ] **Task 4.1.4**: Delete `src/app/infrastructure/persistence_sqla/mappings/session.py`

### 4.2 Update Mapping Registry
- [ ] **Task 4.2.1**: Update `mappings/all.py` to remove deprecated imports
  ```python
  # REMOVE:
  from .conversation import map_conversation_table
  from .message import map_message_table
  from .guest import map_guest_tables
  from .session import map_sessions_table
  
  # REMOVE from register_all_mappings():
  map_conversation_table()
  map_message_table()
  map_guest_tables()
  map_sessions_table()
  ```

### 4.3 Domain Entity Cleanup
- [ ] **Task 4.3.1**: Review `src/app/domain/chat/entities/conversation.py`
  - Check if still used by new system
  - If unused, mark for removal
  
- [ ] **Task 4.3.2**: Remove legacy domain services if unused

### 4.4 Repository Cleanup
- [ ] **Task 4.4.1**: Review and remove unused repositories
- [ ] **Task 4.4.2**: Update IoC container registrations

---

## Phase 5: Testing & Verification

### 5.1 Update Test Suite
- [ ] **Task 5.1.1**: Remove tests for deprecated endpoints
  - Check `tests/integration/user/` for legacy endpoint tests
  
- [ ] **Task 5.1.2**: Ensure new system tests pass
  ```bash
  pytest tests/integration/user/context_aware/ -v
  ```

- [ ] **Task 5.1.3**: Add regression tests for 410 Gone responses
  ```python
  async def test_legacy_endpoint_returns_410():
      response = await client.get("/api/v1/user/chat/conversations")
      assert response.status_code == 410
  ```

### 5.2 Integration Verification
- [ ] **Task 5.2.1**: Verify all new endpoints work
- [ ] **Task 5.2.2**: Verify context-aware system works
- [ ] **Task 5.2.3**: Verify guest chat still works via unified system

### 5.3 Performance Verification
- [ ] **Task 5.3.1**: Compare response times before/after
- [ ] **Task 5.3.2**: Verify database query performance

---

## Phase 6: Documentation Update

### 6.1 Update Documentation
- [ ] **Task 6.1.1**: Update `README.md` to remove legacy references
- [ ] **Task 6.1.2**: Update `CLAUDE.md` to remove deprecation notice
- [ ] **Task 6.1.3**: Archive `docs/DEPRECATION_PLAN.md` as completed
- [ ] **Task 6.1.4**: Update API documentation (OpenAPI/Swagger)

### 6.2 Cleanup Notes
- [ ] **Task 6.2.1**: Create post-mortem document
- [ ] **Task 6.2.2**: Document lessons learned
- [ ] **Task 6.2.3**: Update onboarding docs

---

## Execution Checklist

### Before Starting (2026-05-31)
```bash
# 1. Verify no active usage of deprecated endpoints
grep "DEPRECATED ENDPOINT" logs/fastapi.log | tail -100

# 2. Create full database backup
pg_dump anvil_db > backup_pre_cleanup_20260531.sql

# 3. Verify all tests pass
pytest tests/ -v --tb=short
```

### During Execution (2026-06-01)
```bash
# 1. Apply Alembic migration
alembic upgrade head

# 2. Verify tables moved to backup schema
psql -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'deprecated_backup'"

# 3. Deploy code changes
git checkout deprecation-cleanup
git pull origin master
make deploy
```

### After Execution
```bash
# 1. Verify new endpoints work
curl -X GET https://api.anvil.io/api/v1/conversations -H "Authorization: Bearer $TOKEN"

# 2. Verify legacy endpoints return 410
curl -X GET https://api.anvil.io/api/v1/user/chat/conversations -H "Authorization: Bearer $TOKEN"
# Expected: 410 Gone

# 3. Run full test suite
pytest tests/ -v
```

---

## Rollback Plan

If issues occur after deployment:

```bash
# 1. Revert code changes
git revert HEAD

# 2. Restore tables from backup schema
psql -c "ALTER TABLE deprecated_backup.conversations SET SCHEMA public"
# Repeat for all tables

# 3. Redeploy
make deploy
```

---

## Success Criteria

- [ ] All deprecated endpoints return HTTP 410 Gone
- [ ] All deprecated tables moved to backup schema
- [ ] All tests pass (including new 410 tests)
- [ ] New system performance equal or better
- [ ] No errors in production logs for 24 hours
- [ ] Documentation updated
