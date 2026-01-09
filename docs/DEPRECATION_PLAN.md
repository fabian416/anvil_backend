# Legacy Conversation System Deprecation Plan

**Status**: 🟡 Deprecated (Active Migration Period)
**Sunset Date**: 2026-06-01
**Current Date**: 2026-01-09

---

## ⚠️ Executive Summary

The legacy conversation system (`conversations` table + `users` table) is being deprecated in favor of the new unified chat system (`chat_conversations` + `chat_users`).

**Action Required**: All API consumers must migrate to the new endpoints by **June 1, 2026**.

---

## 📊 System Comparison

### Legacy System (DEPRECATED)

**Router**: `src/app/presentation/http/controllers/chat/router.py`
**Base Path**: `/api/v1/user/chat/*`
**Database Tables**: `conversations`, `users`, `messages`

| Feature | Support |
|---------|---------|
| Guest Users | ❌ No |
| Authenticated Users | ✅ Yes (INTEGER user_id) |
| Privy Wallet Integration | ❌ No |
| Multi-language | ❌ No |
| Rate Limiting | ❌ No |
| Metadata (JSONB) | ❌ No |
| Status Tracking | ❌ No |
| Intent Routing | ⚠️ Limited |

### New System (ACTIVE)

**Router**: `src/app/presentation/http/controllers/chat/conversations_router.py`
**Base Path**: `/api/v1/conversations/*`
**Database Tables**: `chat_conversations`, `chat_users`, `chat_messages`

| Feature | Support |
|---------|---------|
| Guest Users | ✅ Yes (IP-based) |
| Authenticated Users | ✅ Yes (UUID user_id) |
| Privy Wallet Integration | ✅ Yes |
| Multi-language | ✅ Yes (en/es/pt/zh) |
| Rate Limiting | ✅ Yes (20/hour for guests) |
| Metadata (JSONB) | ✅ Yes |
| Status Tracking | ✅ Yes (active/archived/deleted) |
| Intent Routing | ✅ Full (6 intent types) |

---

## 🔄 Migration Mappings

### Endpoint Mappings

| Legacy Endpoint (DEPRECATED) | New Endpoint (USE THIS) | Status |
|------------------------------|-------------------------|--------|
| `POST /user/chat/conversations` | `POST /conversations` | ⚠️ Deprecated |
| `GET /user/chat/conversations` | `GET /conversations` | ⚠️ Deprecated |
| `GET /user/chat/conversations/{id}` | `GET /conversations/{id}` | ⚠️ Deprecated |
| `PATCH /user/chat/conversations/{id}` | `PATCH /conversations/{id}` | ⚠️ Deprecated |
| `DELETE /user/chat/conversations/{id}` | `DELETE /conversations/{id}` | ⚠️ Deprecated |
| `POST /user/chat/conversations/{id}/messages` | `POST /conversations/{id}/messages` | ⚠️ Deprecated |
| `GET /user/chat/conversations/{id}/messages` | `GET /conversations/{id}/messages` | ⚠️ Deprecated |

### Data Migration

All data from `conversations` table has been migrated to `chat_conversations`:
- ✅ 62 conversations migrated
- ✅ User mappings preserved via `chat_users.identifier`
- ✅ 0 conversations pending migration

**Migration Query**:
```sql
-- Executed on 2026-01-09
INSERT INTO chat_conversations (id, user_id, title, status, created_at, updated_at, last_message_at, message_count, language)
SELECT
    c.id,
    cu.id as user_id,
    COALESCE(c.title, 'New Chat') as title,
    'active' as status,
    c.created_at,
    c.updated_at,
    c.created_at as last_message_at,
    0 as message_count,
    'en' as language
FROM conversations c
INNER JOIN chat_users cu ON cu.identifier = c.user_id::text
    AND cu.user_type = 'authenticated';
```

---

## 📅 Deprecation Timeline

### Phase 1: Deprecation Notice (Current - 2026-01-09)
**Status**: ✅ Complete

- [x] Add deprecation warnings to all legacy endpoints
- [x] Update OpenAPI docs with deprecation notices
- [x] Add logging for deprecated endpoint usage
- [x] Migrate all existing data to new system
- [x] Create DEPRECATION_PLAN.md
- [x] Update CLAUDE.md with migration instructions

### Phase 2: Migration Period (2026-01-09 → 2026-05-01)
**Duration**: 4 months
**Status**: 🟡 In Progress

**Action Items**:
- [ ] Monitor deprecated endpoint usage metrics
- [ ] Send email notifications to API consumers
- [ ] Create migration scripts for common use cases
- [ ] Provide support for migration questions
- [ ] Add banner warnings in frontend UI

**Monitoring**:
```bash
# Check deprecated endpoint usage
grep "DEPRECATED ENDPOINT USED" logs/fastapi.log | wc -l

# View by endpoint
grep "DEPRECATED ENDPOINT USED" logs/fastapi.log | cut -d: -f2 | sort | uniq -c
```

### Phase 3: Final Warning (2026-05-01 → 2026-05-31)
**Duration**: 1 month
**Status**: 📅 Scheduled

**Action Items**:
- [ ] Send final migration deadline reminders (weekly)
- [ ] Add HTTP 410 Gone warnings (headers only, still functional)
- [ ] Dashboard alerts for clients still using legacy endpoints
- [ ] Offer assisted migration for enterprise clients

### Phase 4: Sunset (2026-06-01)
**Status**: 📅 Scheduled

**Action Items**:
- [ ] Remove legacy router from API (return HTTP 410 Gone)
- [ ] Archive `conversations` table (read-only backup)
- [ ] Remove deprecated code from codebase
- [ ] Update all documentation
- [ ] Celebrate successful migration 🎉

---

## 🚀 Quick Migration Guide

### For Frontend Developers

**Before (DEPRECATED)**:
```typescript
// ❌ Old way - STOP using this
const response = await fetch('/api/v1/user/chat/conversations', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ title: 'New Chat' })
});
```

**After (NEW)**:
```typescript
// ✅ New way - Use this instead
const response = await fetch('/api/v1/conversations', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'New Chat',
    language: 'en'  // Optional: en, es, pt, zh
  })
});
```

### For API Consumers

**Key Differences**:

1. **Base Path Changed**:
   - Old: `/api/v1/user/chat/*`
   - New: `/api/v1/conversations/*`

2. **Response Format Enhanced**:
```json
{
  "id": "uuid",
  "title": "My Chat",
  "status": "active",         // NEW: active/archived/deleted
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "last_message_at": "ISO timestamp",  // NEW
  "message_count": 5,                  // NEW
  "language": "en"                     // NEW
}
```

3. **Guest Support**:
```bash
# New system supports guest chat (no auth required)
curl -X POST https://api.anvil.io/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "What is ETH sentiment?", "language": "en"}'
```

---

## 🔧 Testing Your Migration

### 1. Local Development

Update your `.env`:
```bash
# Force new endpoints only (optional - for testing)
ENABLE_LEGACY_CHAT_ENDPOINTS=false
```

### 2. API Testing

```bash
# Test new conversation creation
curl -X POST https://testanvilcrypto.ddnsking.com/api/v1/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Migration Test", "language": "en"}'

# Test message sending
curl -X POST https://testanvilcrypto.ddnsking.com/api/v1/conversations/{id}/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello from new system!", "language": "en"}'
```

### 3. Verify Data Migration

```sql
-- Check your conversations migrated correctly
SELECT
    cc.id,
    cc.title,
    cc.status,
    cu.identifier as old_user_id,
    cu.email
FROM chat_conversations cc
JOIN chat_users cu ON cu.id = cc.user_id
WHERE cu.user_type = 'authenticated'
ORDER BY cc.created_at DESC;
```

---

## 📞 Support & Help

### Need Assistance?

**Documentation**:
- [Unified Chat Routing Proposal](./UNIFIED_CHAT_ROUTING_PROPOSAL.md)
- [Guest Chat System](./GUEST_CHAT_SYSTEM.md)
- [Chat Endpoints Explained](./CHAT_ENDPOINTS_EXPLAINED.md)

**Contact**:
- Email: ops@anvilcrypto.com
- Slack: #api-migration-support
- GitHub Issues: [anvil_backend/issues](https://github.com/anvilcrypto/anvil_backend/issues)

**Migration Scripts**:
- Available in `scripts/migration/` directory
- Run `python scripts/migration/migrate_to_new_chat.py --help`

---

## ❓ FAQ

### Q: Why is the system being deprecated?

**A**: The new system provides:
- Guest user support (critical for user acquisition)
- Multi-language support (global expansion)
- Better architecture (hexagonal design)
- Intent-based routing (smarter responses)
- Privy wallet integration (Web3 features)
- Extensible metadata (future features)

### Q: Will my existing conversations be lost?

**A**: No! All conversations have been migrated to the new system. Your data is safe and accessible via the new endpoints.

### Q: What happens if I don't migrate by June 1?

**A**: On June 1, 2026:
- Legacy endpoints will return HTTP 410 Gone
- Your application will stop working
- No data will be lost, but you'll need to migrate to access it

### Q: Can I migrate gradually?

**A**: Yes! Both systems are running in parallel until June 1. You can:
1. Test new endpoints in staging
2. Gradually roll out to production
3. Keep legacy as fallback during transition

### Q: Do I need to change my database?

**A**: No! If you're an API consumer, you don't touch the database. Just update your API calls.

### Q: What about my JWT tokens?

**A**: Same authentication system. Your existing tokens work with new endpoints.

---

## 📈 Deprecation Metrics

Track migration progress:

```bash
# View deprecation dashboard
make logs-fastapi | grep "DEPRECATED ENDPOINT"

# Get weekly usage stats
./scripts/monitoring/deprecated_endpoints_report.sh --week
```

**Current Status**:
- Legacy endpoints usage: Monitoring started 2026-01-09
- Data migration: 100% complete (62/62 conversations)
- Client migration: 0% complete (monitoring phase)

---

## ✅ Checklist for Migration

### For Frontend Teams
- [ ] Update all API calls to use `/api/v1/conversations/*`
- [ ] Test conversation creation
- [ ] Test message sending
- [ ] Test conversation listing
- [ ] Test conversation update/delete
- [ ] Handle new fields (status, language, message_count)
- [ ] Test guest chat (if applicable)
- [ ] Deploy to staging
- [ ] Test in staging
- [ ] Deploy to production
- [ ] Monitor for errors
- [ ] Remove legacy code references

### For Backend Teams
- [x] Migrate all conversation data
- [x] Create user mappings in chat_users
- [x] Add deprecation warnings
- [x] Create migration documentation
- [ ] Monitor legacy endpoint usage
- [ ] Send notifications to API consumers
- [ ] Provide migration support
- [ ] Remove legacy code on sunset date

### For DevOps/SRE
- [ ] Set up monitoring for deprecated endpoints
- [ ] Create alerts for high legacy usage
- [ ] Dashboard for migration progress
- [ ] Backup legacy data before removal
- [ ] Plan deployment for sunset date

---

## 🎯 Success Criteria

Migration is considered successful when:

1. ✅ All data migrated (100%)
2. ⏳ All API consumers migrated (0%)
3. ⏳ Legacy endpoint usage < 5% of total
4. ⏳ Zero production errors from new system
5. ⏳ Performance parity or better
6. ⏳ All clients notified and supported
7. ⏳ Documentation complete
8. ⏳ Legacy code removed on schedule

---

**Last Updated**: 2026-01-09
**Owner**: Platform Team
**Reviewers**: Frontend Team, API Consumers, DevOps Team

For questions or concerns, contact ops@anvilcrypto.com
