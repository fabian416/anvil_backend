# Money Market Transaction Tracking — Implementation Plan

## Problem

The **Money Market Workflow** (Aave V3 + Compound V3) currently only compares rates and builds `execute_data` for the frontend. It has **no transaction tracking** and **no position recovery**:

- If `/execute` fails or the user signs a tx but the backend never records it, the position is lost.
- No Celery task fetches Aave/Compound positions from on-chain.
- The `earn_positions` table exists but is only populated by the Etherscan balance scanner for Morpho deposits.

The **Lending Workflow** (Morpho) is fully working with:
- `lending_transactions` — tracks supply/withdraw/borrow/repay with tx_hash, status, health_factor
- `lending_positions` — tracks active positions with amount, APY, status
- Celery tasks: `refresh_lending_positions` (hourly), `monitor_lending_health_factors` (15min), `confirm_withdraw_transaction`
- Etherscan balance task classifies on-chain txs and upserts both tables

## Goal

Bring Money Market to parity with Lending using the **same naming convention** (`earn_*`) and the same architectural patterns.

---

## Phase 1: Database — `earn_transactions` Table

### New Table: `earn_transactions`

Mirrors `lending_transactions` but for Aave V3 / Compound V3 supply/withdraw operations.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` |
| `user_id` | UUID FK → `chat_users.id` | ON DELETE CASCADE |
| `protocol` | ENUM(`aave`, `compound`) | Reuse `protocol_enum` (add `compound` value) |
| `chain` | VARCHAR(20) | `base`, `ethereum`, etc. |
| `action_type` | ENUM(`supply`, `withdraw`) | New `earn_action_enum` |
| `asset_address` | VARCHAR(42) | Token contract address |
| `asset_symbol` | VARCHAR(20) | e.g. `USDC`, `ETH` |
| `amount` | NUMERIC(78,18) | Amount in token units |
| `amount_usd` | NUMERIC(18,2) | USD value at time of tx |
| `apy_at_time` | NUMERIC(6,2) | APY when tx was made |
| `transaction_hash` | VARCHAR(66) UNIQUE | On-chain tx hash |
| `status` | ENUM(`pending`, `confirmed`, `failed`) | Reuse `transaction_status_enum` |
| `wallet_address` | VARCHAR(42) | User wallet |
| `pool_address` | VARCHAR(42) | Aave pool / Compound comet address |
| `metadata` | JSONB | Extra data (vault_address, rate_data, etc.) |
| `created_at` | TIMESTAMPTZ | `CURRENT_TIMESTAMP` |
| `confirmed_at` | TIMESTAMPTZ | When tx confirmed on-chain |

### Indexes

- `idx_earn_transactions_user_id` → `user_id`
- `idx_earn_transactions_tx_hash` → `transaction_hash`
- `idx_earn_transactions_status` → `status`
- `idx_earn_transactions_user_protocol_action` → `(user_id, protocol, action_type)`
- `idx_earn_transactions_wallet` → `wallet_address`

### Files Created/Modified

1. **New mapping**: `src/app/infrastructure/persistence_sqla/mappings/earn_transaction_mapping.py` ✅
2. **Updated**: `src/app/infrastructure/persistence_sqla/mappings/all.py` — registered new mapping ✅
3. **Updated**: `src/app/infrastructure/persistence_sqla/mappings/defi_operations.py` — added `pool_address`, `wallet_address`, `last_synced_at` to `earn_positions` ✅
4. **Updated**: `docs/guides/development/04_earn_and_save.py` — added `EarnTransaction` model ✅
5. **Note**: Alembic migrations are for production only. Dev uses SQLAlchemy mappings directly.

---

## Phase 2: Reuse `earn_positions` Table for Aave/Compound

The existing `earn_positions` table already has `protocol`, `chain`, `asset`, `amount_deposited`, `current_value`, `apy`, `status`. It's currently only used for Morpho deposits from the Etherscan scanner.

**Action**: Reuse as-is. Aave/Compound positions will be inserted with `protocol='aave'` or `protocol='compound'`.

### Minor Schema Additions (via migration)

| Column | Type | Notes |
|---|---|---|
| `supply_apy` | NUMERIC(8,4) | Current supply APY (rename/alias of `apy`) |
| `pool_address` | VARCHAR(42) | Aave pool or Compound comet address |
| `last_synced_at` | TIMESTAMPTZ | When position was last refreshed from on-chain |

---

## Phase 3: Celery Tasks — Position Recovery & Tx Confirmation

### Task 1: `refresh_earn_positions` (Hourly)

Fetches current Aave V3 and Compound V3 positions for all users with active `earn_positions`.

**Flow:**
1. Query `earn_positions WHERE status = 'active' AND protocol IN ('aave', 'compound')`
2. Group by `(wallet_address, protocol, chain)`
3. For each group:
   - **Aave**: Call `AaveGateway.get_user_position(address, chain)` → get supplies
   - **Compound**: Call `CompoundGateway.get_user_position(address, asset, chain)` → get balance
4. Upsert `earn_positions` with fresh `current_value`, `current_apy`, `last_synced_at`
5. Close positions where on-chain balance is 0

**File**: `src/app/infrastructure/celery/tasks/earn_position_tasks.py`

### Task 2: `confirm_earn_transaction` (On-demand, after user signs)

Mirrors `confirm_withdraw_transaction` from lending.

**Flow:**
1. Triggered after `execute_data` is sent to frontend
2. Poll tx_hash for confirmation (via Web3 provider or Etherscan)
3. Update `earn_transactions.status` → `confirmed` or `failed`
4. Upsert `earn_positions` based on confirmed tx
5. If supply: create/increment position
6. If withdraw: decrement/close position

**File**: `src/app/infrastructure/celery/tasks/earn_position_tasks.py`

### Task 3: `reconcile_earn_transactions` (Every 6 hours)

Handles the gap when frontend signs tx but backend doesn't record it.

**Flow:**
1. Query all users with active `earn_positions`
2. For each user+protocol+chain:
   - Fetch on-chain position via gateway
   - Compare with DB `earn_positions.current_value`
   - If mismatch > threshold: fetch recent txs from Etherscan/subgraph
   - Insert missing `earn_transactions`
   - Update `earn_positions`
3. Also check `earn_transactions WHERE status = 'pending' AND created_at < 30min ago`
   - Poll tx_hash → update to `confirmed` or `failed`

**File**: `src/app/infrastructure/celery/tasks/earn_position_tasks.py`

### Beat Schedule Additions

```python
# In celery app.py beat_schedule:
"refresh-earn-positions": {
    "task": "earn_positions.refresh",
    "schedule": crontab(minute=30),  # Every hour at :30
    "options": {"queue": "maintenance"},
},
"reconcile-earn-transactions": {
    "task": "earn_transactions.reconcile",
    "schedule": crontab(hour="*/6", minute=15),  # Every 6 hours
    "options": {"queue": "maintenance"},
},
```

---

## Phase 4: Money Market Workflow — Record Transactions

### Update `_handle_execute` in `money_market_workflow_agent.py`

After building `execute_data`, insert a `pending` row into `earn_transactions`:

```python
# After state.execute_data = self._build_deposit_execute_data(...)
await self._record_earn_transaction(
    user_id=user_context.user_id,
    protocol=selected_protocol,
    chain=chain,
    action_type="supply",
    asset_symbol=asset,
    amount=amount,
    apy=selected_rate.get("supply_apy"),
    wallet_address=user_context.wallet_address,
    pool_address=selected_rate.get("pool_address"),
)
```

### Update `_handle_positions_request` — Withdraw Flow

When user confirms withdraw and `execute_data` is built, insert a `pending` withdraw transaction.

### Trigger `confirm_earn_transaction` Celery Task

After `execute_data` is returned to frontend, schedule the confirmation task:

```python
from app.infrastructure.celery.tasks.earn_position_tasks import confirm_earn_transaction
confirm_earn_transaction.apply_async(
    kwargs={
        "transaction_hash": tx_hash,  # from frontend callback
        "user_id": str(user_context.user_id),
        "protocol": selected_protocol,
        "chain": chain,
        "amount": str(amount),
        "action_type": "supply",
    },
    countdown=15,  # Wait 15s for tx to propagate
)
```

---

## Phase 5: Etherscan Balance Task — Classify Aave/Compound Txs

The existing `etherscan_balance_tasks.py` already classifies Morpho txs into `lending_transactions` and `earn_positions`. Extend it to also classify Aave and Compound txs into `earn_transactions`.

### Add Aave/Compound Contract Addresses

Add Aave V3 Pool and Compound V3 Comet addresses to `_LENDING_CONTRACTS` set.

### Classification Logic

When a tx interacts with Aave Pool or Compound Comet:
- Decode function selector → `supply()`, `withdraw()`, `deposit()`, etc.
- Insert into `earn_transactions` with `protocol='aave'` or `protocol='compound'`
- Upsert `earn_positions`

---

## Implementation Order

| Step | Description | Priority | Files |
|---|---|---|---|
| 1 | ✅ SQLAlchemy mapping: `earn_transaction_mapping.py` + `earn_positions` additions | HIGH | `mappings/` |
| 2 | ✅ Register in `all.py` + update dev guide `04_earn_and_save.py` | HIGH | `mappings/all.py`, `docs/guides/` |
| 3 | Celery task: `refresh_earn_positions` | HIGH | `tasks/earn_position_tasks.py` |
| 4 | Celery task: `confirm_earn_transaction` | HIGH | `tasks/earn_position_tasks.py` |
| 5 | Update `money_market_workflow_agent.py` — record txs | HIGH | `workflows/` |
| 6 | Celery task: `reconcile_earn_transactions` | MEDIUM | `tasks/earn_position_tasks.py` |
| 7 | Beat schedule: register new tasks | HIGH | `celery/app.py` |
| 8 | Etherscan scanner: classify Aave/Compound txs | MEDIUM | `etherscan_balance_tasks.py` |
| 9 | Register in `tasks/__init__.py` and IoC | HIGH | `tasks/__init__.py`, `setup/ioc/` |

---

## Data Flow Diagram

```
User says "deposit 100 USDC on Aave"
    │
    ▼
MoneyMarketWorkflow._handle_execute()
    │
    ├── 1. Build execute_data (Aave supply tx)
    ├── 2. INSERT earn_transactions (status=pending)
    └── 3. Return execute_data to frontend
            │
            ▼
    Frontend signs tx via Privy SDK
            │
            ├── Success: POST /execute with tx_hash
            │       │
            │       ▼
            │   confirm_earn_transaction.delay(tx_hash, ...)
            │       │
            │       ├── Poll tx confirmation
            │       ├── UPDATE earn_transactions SET status=confirmed
            │       └── UPSERT earn_positions (increment balance)
            │
            └── Failure / Never calls backend
                    │
                    ▼
            reconcile_earn_transactions (every 6h)
                    │
                    ├── Fetch on-chain position via AaveGateway
                    ├── Compare with earn_positions
                    ├── Insert missing earn_transactions
                    └── Update earn_positions

User refreshes page / re-opens app
    │
    ▼
POST /privy-login
    │
    ├── 1. Normal auth flow (upsert user, issue JWT)
    ├── 2. CHECK Redis key: "earn_recovery:{user_id}"
    │       │
    │       ├── Key EXISTS (TTL not expired) → skip recovery
    │       └── Key MISSING → trigger recovery:
    │               │
    │               ├── SET Redis "earn_recovery:{user_id}" EX 300 (5 min)
    │               └── recover_earn_positions.delay(user_id, wallet_address)
    │                       │
    │                       ├── AaveGateway.get_user_position(wallet, chain)
    │                       ├── CompoundGateway.get_user_position(wallet, asset, chain)
    │                       ├── Upsert earn_positions
    │                       └── Reconcile earn_transactions
    └── 3. Return JWT tokens
```

---

## Phase 6: Login-Triggered Recovery with Redis Cooldown ✅

### Why

When a user logs in (or refreshes the page, which calls `/privy-login` again), we should
recover their Aave/Compound positions immediately — not wait for the 6-hour reconciliation.
However, if the user refreshes multiple times in quick succession, we must not spam the
on-chain APIs. A **5-minute Redis cooldown** per user prevents this.

**Status**: ✅ Implemented in `privy_login.py` with `_trigger_earn_recovery()` helper.

### Redis Key Pattern

```
Key:    earn_recovery:{user_id}
Value:  "1"
TTL:    300 seconds (5 minutes)
```

### Implementation

**File**: `src/app/presentation/http/controllers/account/privy_login.py`

After the existing `sync_single_user.delay(response.user_id)` call, add:

```python
# Trigger earn position recovery (Aave/Compound) with 5-min cooldown
if response.user_id and request_body.wallet_address:
    try:
        from redis.asyncio import Redis as AsyncRedis
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/3")
        redis = AsyncRedis.from_url(redis_url, decode_responses=True)
        cooldown_key = f"earn_recovery:{response.user_id}"

        # Only trigger if cooldown has expired
        already_running = await redis.get(cooldown_key)
        if not already_running:
            await redis.setex(cooldown_key, 300, "1")  # 5 min TTL

            from app.infrastructure.celery.tasks.earn_position_tasks import (
                recover_earn_positions,
            )
            recover_earn_positions.delay(
                user_id=response.user_id,
                wallet_address=request_body.wallet_address,
            )
        await redis.aclose()
    except Exception:
        pass  # Non-critical: periodic reconciliation will catch up
```

### Celery Task: `recover_earn_positions`

**File**: `src/app/infrastructure/celery/tasks/earn_position_tasks.py`

```python
@celery_app.task(
    name="earn_positions.recover",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def recover_earn_positions(self, user_id: int, wallet_address: str):
    """
    Recover Aave V3 + Compound V3 positions for a single user.

    Triggered on login with 5-min Redis cooldown.
    Fetches on-chain positions and reconciles with earn_positions table.
    """
    async def runner(container):
        from app.domain.ports.aave_gateway import AaveGateway
        from app.domain.ports.compound_gateway import CompoundGateway

        aave = await container.get(AaveGateway)
        compound = await container.get(CompoundGateway)

        recovered = {"aave": 0, "compound": 0, "errors": []}

        # 1. Recover Aave positions (Base chain)
        try:
            position = await aave.get_user_position(
                address=wallet_address, chain="base"
            )
            if position and position.supplies:
                # Upsert earn_positions for each supply
                for supply in position.supplies:
                    await _upsert_earn_position(
                        session, user_id, wallet_address,
                        protocol="aave", chain="base",
                        asset=supply.symbol, amount=supply.amount,
                        apy=supply.apy,
                    )
                    recovered["aave"] += 1
        except Exception as e:
            recovered["errors"].append(f"aave: {e}")

        # 2. Recover Compound positions (Base chain, USDC)
        try:
            for asset in ("USDC", "ETH"):
                comp_pos = await compound.get_user_position(
                    user_address=wallet_address,
                    asset=asset, chain="base",
                )
                if comp_pos and comp_pos.supply_balance > 0:
                    await _upsert_earn_position(
                        session, user_id, wallet_address,
                        protocol="compound", chain="base",
                        asset=asset, amount=comp_pos.supply_balance,
                        apy=comp_pos.supply_apy,
                    )
                    recovered["compound"] += 1
        except Exception as e:
            recovered["errors"].append(f"compound: {e}")

        return recovered

    return asyncio.run(_run_task(runner))
```

### Why Not Just Use the 6-Hour Reconciliation?

| Scenario | Without login trigger | With login trigger |
|---|---|---|
| User deposits on Aave, refreshes page | Position invisible for up to 6h | Position visible in ~5s |
| User deposits, closes browser, comes back next day | Position invisible until next reconciliation | Position recovered on login |
| User rapidly refreshes (panic) | N/A | Redis cooldown prevents API spam |

### Updated Implementation Order

| Step | Description | Priority | Files |
|---|---|---|---|
| 1 | ✅ SQLAlchemy mapping: `earn_transaction_mapping.py` + `earn_positions` additions | HIGH | `mappings/` |
| 2 | ✅ Register in `all.py` + update dev guide `04_earn_and_save.py` | HIGH | `mappings/all.py`, `docs/guides/` |
| 3 | ✅ Celery task: `refresh_earn_positions` (hourly) | HIGH | `tasks/earn_position_tasks.py` |
| 4 | ✅ Celery task: `confirm_earn_transaction` (on-demand) | HIGH | `tasks/earn_position_tasks.py` |
| 5 | ✅ Celery task: `recover_earn_positions` (login-triggered) | HIGH | `tasks/earn_position_tasks.py` |
| 6 | ✅ **Login trigger + Redis cooldown** in `/privy-login` | HIGH | `controllers/account/privy_login.py` |
| 7 | ✅ Record txs in `/execute` endpoint (conversations_router.py) | HIGH | `controllers/chat/` |
| 8 | ✅ Celery task: `reconcile_earn_transactions` (6-hourly fallback) | MEDIUM | `tasks/earn_position_tasks.py` |
| 9 | ✅ Beat schedule: register new tasks | HIGH | `celery/app.py` |
| 10 | ✅ Etherscan scanner: classify Aave/Compound txs | MEDIUM | `etherscan_balance_tasks.py` |
| 11 | ✅ Register in `tasks/__init__.py` | HIGH | `tasks/__init__.py` |
