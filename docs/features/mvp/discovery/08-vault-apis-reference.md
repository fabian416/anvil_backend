# Discovery Module — Vault APIs Reference

APIs used to **recommend vaults** in the Discovery module (vault cards, sorted by APY/TVL/risk).

---

## Summary

| API | Role | Auth | Used in |
|-----|------|------|--------|
| **DeFiLlama** | Primary vault/yield data | None (free) | Celery `collect_vault_snapshots`, `GetVaultsQuery` (via cached DB) |
| **Vaults.fyi** | Broader protocol coverage | API key (free tier) | Optional/secondary in adapters |

---

## 1. DeFiLlama (Primary)

**Base URL:** `https://yields.llama.fi`

| Item | Detail |
|------|--------|
| **Endpoint** | `GET /pools` |
| **Auth** | None |
| **Rate** | Free, no key required |
| **Docs** | [DeFiLlama Yields](https://docs.llama.fi/) |

**Discovery usage (from spec):**

- **Celery task:** `collect_vault_snapshots` (every 5 min).
- **Filters (in adapter):**
  - `protocol ∈ {morpho, aave-v3, compound-v3}`
  - `chain ∈ {Base, Ethereum}`
  - `tvl_usd ≥ 100,000`
- **Sort:** Total APY desc, keep **top 50**.
- **Risk:** APY > 100% or TVL < $500K → classified as high risk.

**Adapter:** `infrastructure/adapters/discovery/defillama_adapter.py` (implements `VaultFetcherPort`).

---

## 2. Vaults.fyi (Secondary / Broader Coverage)

**Base URL:** `https://api.vaults.fyi`

| Item | Detail |
|------|--------|
| **Endpoint** | `GET /v2/vaults` (and `GET /v2/vaults/{id}`) |
| **Auth** | API key (free tier) |
| **Coverage** | Morpho, Aave, 75+ protocols |
| **Env** | `VAULTSFYI_KEY` (see `07-celery-pipeline.md`) |

**Discovery usage:**

- Implemented by **VaultsFyiAdapter** (implements `VaultFetcherPort`).
- Used for broader protocol coverage alongside DeFiLlama.
- Same `RawVault` / `VaultSnapshot` shape as DeFiLlama for recommendation and display.

**Adapter:** `infrastructure/adapters/discovery/vaultsfyi_adapter.py`.

---

## 3. Pipeline Flow (How vaults become recommendations)

1. **Celery Beat** (every 5 min) runs `collect_vault_snapshots`.
2. **CollectVaultsCommand** (or equivalent in task):
   - Fetches from **DeFiLlama** (and optionally **Vaults.fyi**).
   - Filters by protocol, chain, min TVL.
   - **Deactivates** old snapshots (`is_active = false` where `snapshot_at` &lt; 1h ago).
   - **Inserts** new `VaultSnapshot` rows (`is_active = true`).
   - Invalidates cache `discovery:vaults:*`.
3. **GET /discovery/vaults** (user endpoint):
   - **GetVaultsQuery** reads from DB (and cache `discovery:vaults:{sort}:{chain}` TTL 60s).
   - Returns sorted vault cards (apy_desc | tvl_desc | risk_asc), with CTA and `intent_trigger: "lending_deposit"`.

So **recommendations** are driven by data **collected** from DeFiLlama (+ optionally Vaults.fyi), not by calling those APIs on each user request.

---

## 4. References in this repo

- **Architecture / integrations:** `01-architecture-spec.md` (§4 External System Integrations).
- **Services / adapters:** `04-services-layer.md` (PART C: DeFiLlamaAdapter, VaultsFyiAdapter, VaultFetcherPort, CollectVaultsCommand, GetVaultsQuery).
- **Celery:** `07-celery-pipeline.md` (§6 collect_vault_snapshots, §10 env vars).
- **Provider list (high level):** `api.md` (Primary Vaults table and `VAULT_PROVIDERS`).
