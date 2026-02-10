# Etherscan Celery Architecture: Scalability to 1,000+ Users

**Document type:** CTO methodology analysis (Problem Decomposition → Solution Generation → Risk Assessment)  
**Scope:** Etherscan-backed Celery tasks (sync_transactions, sync_balances, sync_all_tokens, sync_single_wallet)  
**Goal:** Assess whether the current architecture can support 1,000+ users and document options.

---

## 1. Problem Decomposition & Root Cause Analysis

### 1.1 Actual requirement

- **Requirement:** Support **1,000+ users** (wallets) with Etherscan-based:
  - Transaction status sync (pending → confirmed)
  - Balance sync (on-chain verification)
  - Token balance sync (ETH, USDC, WETH per chain)
  - On-demand single-wallet checks (e.g. pre-tx validation)

### 1.2 Hard constraints (external)

| Constraint | Source | Value |
|------------|--------|--------|
| **Etherscan API rate (per key)** | [Etherscan rate limits](https://docs.etherscan.io/resources/rate-limits) | **Free:** 3–5 calls/sec, 100,000 calls/day. **Standard:** 10/sec, 200k/day. **Advanced:** 20/sec, 500k/day. **Professional:** 30/sec, 1M/day. **Pro Plus:** 30/sec, 1.5M/day. |
| **Chain coverage** | Free tier | Selected chains only; Base/Optimism etc. require Lite/paid. |
| **Celery rate limit** | Per-worker | `rate_limit` is **per worker**, not global. Global cap requires single queue or external coordinator. |

### 1.3 Current architecture (as-built)

| Component | Location | Behavior |
|-----------|----------|----------|
| **Tasks** | `etherscan_balance_tasks.py` | `sync_transactions`, `sync_balances`, `sync_all_tokens`, `sync_single_wallet`, `verify_test_wallet` |
| **Queue** | All Etherscan tasks | `maintenance` |
| **Rate limiting** | In-task | `EtherscanClient` token bucket: **3 calls/sec** (configurable), exponential backoff on 429. |
| **Batch sizes** | Config / code | `sync_transactions`: 50 wallets, 1 txlist per chain per wallet. `sync_balances`: **20 wallets** per run (`max_wallets_per_batch`), ~4–6 API calls per wallet (deposit chain + LiFi chains). `sync_all_tokens`: 50 wallets, 3 chains × 3 tokens = **9 calls per wallet** per run. |
| **Schedules** | `celery/app.py` beat | `sync_transactions`: 300s. `sync_balances`: 300s. `sync_all_tokens`: **30s**. |

### 1.4 API call volume (back-of-envelope)

Assume **1,000 wallets**, 3 chains (e.g. ethereum, arbitrum, base with paid tier), and current logic:

| Task | Calls per run | Runs per day | Calls per day |
|------|----------------|--------------|----------------|
| **sync_transactions** | 1,000 × 3 = 3,000 (if we processed all) | Current: 50 wallets/run → 20 runs to cover 1k → 20 × (50 × 3) = **3,000** per full cycle. At 5 min/cycle: 288 cycles/day × (50×3) = **43,200** (if we scaled to 50 per run only). | If we process 1,000 users in batches of 50: 20 batches × 50 × 3 = **3,000** per cycle; 288 cycles/day = **864,000** (unbounded growth with users). |
| **sync_balances** | 20 × ~5 = **100** per run | 288 runs/day | **28,800** |
| **sync_all_tokens** | 50 × 3 × 3 = **450** per run | 2,880 runs/day (every 30s) | **1,296,000** |

So with **current design** (no cap on “eligible” wallets and sync_all_tokens every 30s):

- **sync_balances** at 20 wallets/run: to cover 1,000 users we need 50 runs per cycle; at 5 min that’s 50 × 100 = 5,000 calls per cycle → **1.44M calls/day** for balance alone.
- **sync_all_tokens** at 50 wallets/run every 30s already yields **~1.3M calls/day** for 50 wallets only; scaling to 1,000 would multiply further.

**Conclusion (first principles):** The current architecture **does not** support 1,000+ users on a **single Etherscan Free** key (100k calls/day). It can support a small cohort (tens of wallets) within 100k/day if schedules and batch sizes are tuned. For 1,000+ users, we must either **reduce calls per user per day**, **increase the daily cap** (paid tier), or **coordinate multiple keys** (if allowed by Etherscan ToS).

---

## 2. Solution Generation & Trade-off Analysis

### 2.1 Solution A: Stay on Free tier – reduce coverage and frequency

**Idea:** Keep one key, stay under 100k calls/day by processing a **subset** of users per day and reducing frequency/calls per user.

- **Measures:**  
  - Lower `sync_all_tokens` frequency (e.g. 300s instead of 30s).  
  - Cap “eligible” wallets per run (e.g. round-robin or priority so each wallet is refreshed every N hours).  
  - Reduce chains or tokens (e.g. only 1 chain, or only USDC).
- **Rough capacity:** 100,000 / (calls_per_user_per_day). If we target e.g. 50 calls/user/day → **2,000 users** in theory, but with 5-min balance and 5-min token sync and 3 chains × 3 tokens + txlist, calls per user per day can be 20–50+; so **~1,500–2,000 users** is an upper bound with aggressive tuning.
- **Trade-offs:**  
  - ✅ No cost.  
  - ❌ Not all users refreshed every 5 min; some may see stale data.  
  - ❌ Tighter coupling of schedule to a single global cap.

### 2.2 Solution B: Etherscan paid tier (recommended for 1,000+ users)

**Idea:** Upgrade to a tier that raises the **daily cap** so that 1,000+ users fit within one key.

| Tier | Rate | Daily cap | Approx. headroom for 1k users |
|------|------|-----------|--------------------------------|
| Standard | 10/s | 200k | Tight (same order as current design at 1k users). |
| Advanced | 20/s | 500k | Comfortable with tuned batching. |
| Professional | 30/s | **1M** | Comfortable; allows growth. |
| Pro Plus | 30/s | 1.5M | Headroom for 1.5–2k+ users. |

**Design:**  
- Keep **single queue** (`maintenance`) and **single worker pool** for Etherscan tasks so that the in-process token bucket (3–5/s) is the only producer of Etherscan traffic (no multi-worker race).  
- Optionally increase `max_calls_per_second` in config to match tier (e.g. 10 or 20).  
- Keep or slightly increase `max_wallets_per_batch` and add a **global cap** on “wallets processed per run” so daily calls stay under the chosen tier.

**Trade-offs:**  
- ✅ Predictable capacity; fits 1,000+ users.  
- ✅ Same codebase; config + tier selection.  
- ❌ Recurring cost (see Etherscan pricing).

### 2.3 Solution C: Task dispatcher / DB-backed job queue (global rate cap)

**Idea:** Decouple “who needs a sync” from “when we call Etherscan.” A **dispatcher** (periodic task or scheduler) selects N wallets **under a global daily/minute budget** and enqueues **one task per wallet** (or per wallet+chain). Workers pull from queue; a **shared rate limiter** (e.g. Redis token bucket or DB counter) ensures **global** Etherscan call count stays under the cap.

- **Mechanics:**  
  - Table or queue: `etherscan_sync_queue(wallet_id, chain, task_type, created_at, dispatched_at)`.  
  - Dispatcher runs every 1–5 min, counts “calls in last 1 min” (or “calls today”), selects up to M rows such that M × calls_per_task ≤ remaining budget, marks them “dispatched,” and calls `sync_single_wallet.apply_async(...)` or a small batch task.  
  - Workers execute only what’s dispatched; no per-task “process 20 wallets” that could be run by multiple workers in parallel.
- **Trade-offs:**  
  - ✅ True global rate limit; safe with multiple workers and 1,000+ users.  
  - ✅ Can prioritize (e.g. high-value, or “never synced” first).  
  - ❌ More moving parts (dispatcher, state, monitoring).  
  - ❌ Requires refactor of current “batch in one task” design.

### 2.4 Solution D: Multiple API keys (shard by user or queue)

**Idea:** Use several Etherscan keys and shard traffic (e.g. by `user_id % N` or by dedicated queues with one worker per key).

- **Trade-offs:**  
  - ✅ Higher aggregate daily cap (N × 100k for N keys).  
  - ❌ Etherscan ToS may restrict multi-key use for a single product; must verify.  
  - ❌ Operational and security overhead (key rotation, per-key monitoring).

---

## 3. Multi-dimensional comparison

| Criterion | A: Free + reduce | B: Paid tier | C: Dispatcher | D: Multi-key |
|-----------|------------------|-------------|---------------|--------------|
| Supports 1,000+ users | Partial (stale data) | Yes | Yes | Yes (if ToS OK) |
| Implementation cost | Low (config + caps) | Low (config + tier) | High (new pipeline) | Medium (routing + ops) |
| Operational complexity | Low | Low | Medium–High | Medium |
| Predictability | Medium (tight budget) | High | High | Medium |
| Staleness vs. freshness | Worse | Same as now | Tunable | Same as now |

---

## 4. Risk Assessment & Validation

### 4.1 Assumptions

- Etherscan daily cap is enforced per key and is the **binding** limit at scale (vs. 3–5/s which we already throttle).  
- “1,000 users” means 1,000 active wallets that need balance/tx sync; not all will have activity every minute.  
- We keep a **single** Etherscan key for all Celery Etherscan tasks (no sharding) unless we adopt Solution D and confirm ToS.

### 4.2 Risks

- **Celery `rate_limit` is per worker:** With multiple workers on `maintenance`, aggregate Etherscan calls can exceed 3–5/s unless we either (1) use a **single worker** for Etherscan tasks, or (2) implement a **global** limiter (e.g. Redis) inside the task or in a wrapper.  
- **sync_all_tokens at 30s:** At 50 wallets × 9 calls = 450 calls/run, 2,880 runs/day → **~1.3M calls/day**; already over 100k. So current default schedule is **not** compatible with Free tier at 50 wallets; must reduce frequency or batch size.  
- **Growth:** If we add more chains or tokens, calls per user grow; any budget (100k, 200k, 1M) should be modeled with “calls per user per day” and a safety margin.

### 4.3 Validation approach

- **Metering:** Log or export **Etherscan API call count per task type** (and optionally per chain) in the existing `EtherscanClient` metrics; aggregate in monitoring (e.g. Prometheus/Flower).  
- **Alerts:** Alert when “calls in last 24h” > 80% of tier cap.  
- **Load test:** Run a synthetic load with 1,000 wallet IDs (or a subset) and measure actual calls/day and latency; compare to tier limits.

---

## 5. Recommendations (CTO view)

1. **Short term (current architecture, &lt; ~100–200 users):**  
   - **Cap daily Etherscan usage** so we stay under 100k/day:  
     - Reduce **sync_all_tokens** to every **5 minutes** (or 10) instead of 30s.  
     - Keep **sync_balances** at 20 wallets/run and 5 min; ensure total runs per day × 100 &lt; 100,000.  
   - **Single worker** for the `maintenance` queue (or a dedicated Etherscan queue with concurrency 1) so the in-task token bucket is the only throttle and we don’t exceed 3–5/s.

2. **Medium term (target 1,000+ users):**  
   - **Upgrade to Etherscan Professional (or equivalent)** for 1M calls/day (Solution B).  
   - Keep **one** Etherscan key and **one** logical producer of Etherscan traffic (one queue + rate-limited client).  
   - Set **max_wallets_per_batch** and “max wallets per run” for sync_transactions/sync_all_tokens so that at 1,000 users we stay under 1M/day with a margin (e.g. target 700–800k/day).  
   - Optionally increase `max_calls_per_second` in config to match the tier (e.g. 10 or 20).

3. **Long term (10k+ users or multiple products):**  
   - Consider **Solution C** (dispatcher + DB-backed queue and global rate limiter) for strict caps and prioritization.  
   - Re-evaluate **Solution D** only after confirming Etherscan’s terms for multiple keys.

---

## 6. References

- **Etherscan rate limits (official):**  
  - [Rate Limits – Etherscan API](https://docs.etherscan.io/resources/rate-limits)  
  - [Etherscan V2 rate limits](https://docs.etherscan.io/etherscan-v2/rate-limits)  
  - Free: 3–5 calls/sec, 100,000 calls/day; Lite/Standard/Advanced/Pro/Pro Plus tiers.
- **Celery rate limiting:**  
  - [Celery Tasks – rate_limit](https://docs.celeryq.dev/en/stable/userguide/tasks.html): per-worker; for global limit, restrict to one queue or use external coordinator.  
  - [Task rate limiting with Celery (Moldstud)](https://moldstud.com/articles/p-mastering-task-rate-limiting-with-celery-essential-insights-for-developers): token bucket, Redis, multi-worker coordination.  
  - [Celery #5732 – rate limit multiple workers](https://github.com/celery/celery/issues/5732): global limit requires external mechanism (e.g. Redis lock or token queue).
- **Internal:**  
  - `cto.md` – CTO methodology (problem decomposition, solution generation, risk assessment).  
  - `src/app/infrastructure/celery/tasks/etherscan_balance_tasks.py` – Etherscan client and task implementation.  
  - `src/app/setup/config/etherscan.py` – `EtherscanSettings` (max_calls_per_second, max_wallets_per_batch, etc.).  
  - `src/app/infrastructure/celery/app.py` – Beat schedule and task routes.

---

*Summary: The current Etherscan Celery design can support a small number of users on the Free tier (100k calls/day) if schedules and batch sizes are tuned; it **cannot** support 1,000+ users on Free without significant staleness or redesign. For 1,000+ users, upgrading to an Etherscan paid tier (e.g. Professional, 1M/day) and keeping a single-queue, single-key, rate-limited design is the most straightforward and maintainable path.*
