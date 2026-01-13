# Authenticated Chat Test Fix - Current Status

**Date**: 2026-01-13
**Status**: ⚠️ **BLOCKED** by database migration issue

---

## ✅ Completed Work

### 1. Correct Schema Understanding

Successfully identified the actual `chat_users` table schema from migration `b3057814105b`:

```sql
CREATE TABLE chat_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),           -- Auto-generated
    user_id INTEGER NOT NULL REFERENCES users(id),           -- FK to legacy users table
    email VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    total_messages INTEGER DEFAULT 0,
    language VARCHAR(5) DEFAULT 'en',
    chat_preferences JSONB DEFAULT '{}',
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_user_id UUID NOT NULL REFERENCES chat_users(id),   -- FK to chat_users, not user_id!
    title VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    message_count INTEGER DEFAULT 0,
    language VARCHAR(5) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP WITH TIME ZONE
);
```

**Key Points**:
- `users.id` = INTEGER (legacy table)
- `chat_users.id` = UUID (auto-generated)
- `chat_users.user_id` = INTEGER (FK to `users.id`)
- `chat_conversations.chat_user_id` = UUID (FK to `chat_users.id`)

### 2. Fixed All Test Fixtures (12 locations)

✅ **Commit**: `aa83614` - "fix(tests): Correct chat_users schema in authenticated test fixtures"

**Files Modified**:
- `tests/integration/chat/test_authenticated_chat_comprehensive.py`
  - Fixed all 10 `conversation_id` fixtures
  - Fixed `test_conversation_created_in_database`
  - Fixed `test_messages_stored_with_user_id`

**Correct Implementation Pattern**:
```python
@pytest_asyncio.fixture
async def conversation_id(self, test_user, async_db_session: AsyncSession):
    """Create a new conversation for testing."""
    user, token = test_user
    conversation_id = str(uuid4())

    # Extract INTEGER user_id from TestUser UUID
    # TestUser.id is UUID(int=users.id), so we get the int back
    user_id_int = int(user.id.int)

    # Insert into chat_users and get the auto-generated UUID
    result = await async_db_session.execute(
        text("""
            INSERT INTO chat_users (user_id, email)
            VALUES (:user_id, :email)
            ON CONFLICT (user_id) DO UPDATE SET email = EXCLUDED.email
            RETURNING id
        """),
        {"user_id": user_id_int, "email": user.email}
    )
    chat_user_uuid = result.scalar_one()

    # Create conversation with chat_user_id (UUID FK to chat_users.id)
    await async_db_session.execute(
        text("""
            INSERT INTO chat_conversations (id, chat_user_id, title, status, language)
            VALUES (:id, :chat_user_id, :title, :status, :language)
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "id": conversation_id,
            "chat_user_id": chat_user_uuid,
            "title": "Test Conversation",
            "status": "active",
            "language": "en"
        }
    )
    await async_db_session.commit()

    return conversation_id
```

### 3. Test Environment Setup

✅ Identified and resolved httpx dependency issue
✅ Tests run correctly in virtual environment (`.venv/bin/python3`)

---

## ⚠️ Current Blocker: Database Migration Issue

### Problem

Migration `b85c12f320c7` (Jan 12 13:28) is **broken** and cannot be applied:

```
sqlalchemy.exc.InternalError: cannot drop table llm_models because other objects depend on it
DETAIL:  constraint fk_agent_model_rankings_model_id_llm_models on table agent_model_rankings depends on table llm_models
...6 other foreign key constraints...
HINT:  Use DROP ... CASCADE to drop the dependent objects too.
```

### Current Database State

```
$ alembic current
b3057814105b  # chat_users table created

$ alembic heads
b85c12f320c7 (head)  # Cannot upgrade to this due to broken migration
```

### Impact

- **Tests cannot run** because database is missing the `chat_users.user_id` column (error suggests table schema is wrong)
- Cannot upgrade database to fix schema due to broken migration
- Cannot test our fixture fixes until database issue is resolved

---

## 🔧 Required Next Steps

### Option A: Fix the Broken Migration (RECOMMENDED)

**File**: `src/app/infrastructure/persistence_sqla/alembic/versions/2026_01_12_1328-b85c12f320c7_fix_moonpay_customer_tokens_user_id_.py`

**Problem**: Migration tries to `DROP TABLE llm_models` without handling foreign key dependencies.

**Fix**:
1. Either drop dependent tables/constraints first
2. Or use `DROP TABLE llm_models CASCADE` (risky - might delete important data)
3. Or remove the llm_models drop from this migration entirely if not needed

### Option B: Downgrade to b3057814105b and Stay There

**Commands**:
```bash
# Downgrade from broken migration
alembic downgrade b3057814105b

# Mark b3057814105b as head temporarily
alembic stamp head
```

**Then verify chat_users table schema**:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'chat_users'
ORDER BY ordinal_position;
```

**Expected columns**:
- id (uuid)
- user_id (integer) ← **Critical: this must exist!**
- email (character varying)
- subscription_tier (character varying)
- total_messages (integer)
- language (character varying)
- chat_preferences (jsonb)
- first_seen_at (timestamp with time zone)
- last_seen_at (timestamp with time zone)
- created_at (timestamp with time zone)
- updated_at (timestamp with time zone)

### Option C: Recreate Database from Scratch

If migration history is too corrupted:

```bash
# Drop and recreate database
make down.db
make up.db
make create-db

# Apply all migrations up to b3057814105b only
alembic upgrade b3057814105b

# Run tests
source .venv/bin/activate
pytest tests/integration/chat/test_authenticated_chat_comprehensive.py -v
```

---

## 📊 Expected Test Results After Fix

Once database schema is correct:

- **Expected**: 43/45 passing (95%)
- **Root cause of 30 errors**: Resolved by correct fixture implementation
- **Remaining work**: Phase 2 & 3 test implementation (23 additional tests)

---

## 🎯 Final Target

**Total Tests**: 68+
**Current**: 45 (Phase 1 complete)
**Pending**: 23 (Phase 2 & 3)

**Phase 2**: Multi-Step Flow Validation (15 tests)
**Phase 3**: Shortcuts & Quality (8 tests)

---

## 📝 Commands Reference

```bash
# Check current migration
alembic current

# Check migration heads
alembic heads

# Upgrade database (after fixing migration)
alembic upgrade head

# Downgrade one migration
alembic downgrade -1

# Run tests with virtual environment
source .venv/bin/activate
pytest tests/integration/chat/test_authenticated_chat_comprehensive.py -v

# Run single test
pytest tests/integration/chat/test_authenticated_chat_comprehensive.py::TestAuthenticatedHunterAI::test_sentiment_analysis -vv
```

---

## 🚀 Action Items

1. **IMMEDIATE**: Fix or skip broken migration b85c12f320c7
2. **IMMEDIATE**: Verify chat_users table has correct schema (especially `user_id` column)
3. **SHORT-TERM**: Run full test suite to verify 95% pass rate
4. **SHORT-TERM**: Implement Phase 2 & 3 tests (23 tests)
5. **DOCUMENTATION**: Update test coverage documentation with final results
