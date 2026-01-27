# Lending Vaults Integration Tests

## Overview

Integration tests validating the complete fix for vault query routing implemented in three commits:

- **Commit 1 (2351206f)**: Intent detector vault patterns - routes guest users to LENDING intent
- **Commit 2 (4ccf3009)**: Shortcuts API vault examples - advertises vault queries in API
- **Commit 3 (1bc72e1d)**: Supervisor vault routing - routes authenticated users to lending_workflow

## Test File

`tests/integration/user/test_lending_vaults.py` - 8 comprehensive test cases

## Test Coverage

### 1. Core Vault Discovery Tests

**test_user_lending_vault_discovery_best_vaults** (001)
- Query: "Show best lending vaults"
- **Critical Validation**: Routes to `lending_workflow` (NOT `defi_yield`)
- Validates response contains Morpho vault data (not DeFiLlama pools)
- Expected agents: `["lending_workflow"]` or `["lending_handler"]`

**test_user_lending_vault_discovery_top_vaults** (002)
- Query: "top vaults"
- Validates shorter query variant routes correctly
- Expected response: Top Morpho vaults by APY

**test_user_lending_vault_discovery_best_morpho_vaults** (003)
- Query: "best morpho vaults"
- Validates explicit Morpho protocol mention
- Expected response: Morpho-specific vault data

**test_user_lending_vault_comparison** (004)
- Query: "compare vaults"
- Validates vault comparison functionality
- Expected response: Side-by-side comparison with APY, TVL, risk levels

### 2. Routing Distinction Test

**test_user_lending_vault_vs_yield_routing** (005)
- **Multi-step test**:
  - Query 1: "best vaults" → should route to `lending_workflow`
  - Query 2: "best yield farms" → may route to `defi_yield`
- **Key validation**: Proves the fix correctly distinguishes vault queries from generic yield queries
- This is the MOST CRITICAL test that validates the supervisor routing fix

### 3. Multi-Language Support

**test_user_lending_vault_multi_language_spanish** (006)
- Query: "mejores bóvedas de préstamos" (Spanish)
- Validates multi-language routing works correctly
- Supported languages: en, es, pt, zh

### 4. Multi-Step Workflow

**test_user_lending_vault_deposit_workflow** (007)
- **Multi-step test**:
  - Step 1: "Show best lending vaults" → Discovery
  - Step 2: "How do I deposit into the best vault?" → Deposit guidance
- Validates context preservation across conversation turns
- Expected: Deposit instructions reference the vault from previous message

### 5. Response Format Validation

**test_user_lending_vault_response_format** (008)
- Validates response includes all expected data fields:
  - ✅ Vault names (e.g., "Universal USDC", "Edge UltraYield USDC")
  - ✅ APY percentages
  - ✅ TVL amounts
  - ✅ Vault addresses (truncated)
  - ✅ Recommendation section with deposit instructions

## Running the Tests

### Run All Lending Vault Tests

```bash
pytest tests/integration/user/test_lending_vaults.py -v
```

### Run Specific Test

```bash
pytest tests/integration/user/test_lending_vaults.py::test_user_lending_vault_discovery_best_vaults -v
```

### Run with LLM Validation

```bash
pytest tests/integration/user/test_lending_vaults.py -m llm_validation -v
```

### Run Only Integration Tests

```bash
pytest tests/integration/user/test_lending_vaults.py -m integration -v
```

### Generate CSV Report

Tests automatically generate CSV reports via the `csv_tracker` fixture.

Reports location: `tests/integration/reports/user_lending_vaults_{timestamp}.csv`

## Expected Results

### ✅ PASS Criteria

1. **Routing Validation**:
   - `routing.intent` = `"LENDING"` OR `"SUPERVISOR_WORKFLOW"`
   - `routing.agents_used` includes `"lending_workflow"` OR `"lending_handler"`
   - `routing.agents_used` does NOT include `"defi_yield"` for vault queries

2. **Response Content**:
   - Contains "morpho" or "vault" keywords
   - Includes APY/yield information
   - Has numeric data (APY percentages, TVL amounts)
   - Length > 80 characters (comprehensive response)

3. **Multi-Language**:
   - Spanish queries route to lending_workflow
   - Response in requested language

4. **Multi-Step Context**:
   - Deposit instructions reference vault from previous message
   - Context preservation across turns

### ❌ FAIL Scenarios

1. **Incorrect Routing** (the bug we fixed):
   ```json
   {
     "routing": {
       "intent": "SUPERVISOR_WORKFLOW",
       "agents_used": ["defi_yield", "risk_analyzer"]  // ❌ WRONG
     }
   }
   ```
   **Expected**:
   ```json
   {
     "routing": {
       "intent": "SUPERVISOR_WORKFLOW",
       "agents_used": ["lending_workflow"]  // ✅ CORRECT
     }
   }
   ```

2. **Wrong Data Source**:
   - Response contains DeFiLlama generic pools (Beefy, Kamino, Balancer) ❌
   - Should contain Morpho vault data (Universal USDC, Edge UltraYield USDC) ✅

3. **Missing Data Fields**:
   - No APY information ❌
   - No vault names ❌
   - No numeric data ❌

## Test Authentication

All tests use the `ops@anvilcrypto.com` test account with pre-generated JWT token:

```python
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJ0ZXN0X3Nlc3Npb25fMjAyNl8xNzY4MDY2MDc5IiwiZXhwIjoxNzk5NjAyMDc5fQ.OUFFmZW2_QACkgrIphLFcOOB3Qb-1ckVB_RvZ-VTaF0"
```

Token expires: 2027-01-10

## CSV Report Fields

Each test generates CSV rows with the following fields:

- `test_id`: Unique test identifier (e.g., "user_lending_vault_discovery_001")
- `category`: "lending_vaults"
- `input`: User query
- `output`: Agent response content
- `expected_agent`: "lending_workflow"
- `actual_agents`: JSON array of agents used
- `routing_intent`: LENDING or SUPERVISOR_WORKFLOW
- `status`: PASS/FAIL
- `quality`: LLM validation confidence (0.0-1.0)
- `qa_status`: PASS/FAIL/SKIPPED (LLM validation)
- `qa_output`: LLM validation reasoning
- `accuracy_score`: 0-10 (LLM validation)
- `relevance_score`: 0-10 (LLM validation)
- `safety_score`: 0-10 (LLM validation)
- `coherence_score`: 0-10 (LLM validation)

## Dependencies

Tests require:

- `pytest>=7.0.0`
- `pytest-asyncio>=0.21.0`
- `httpx>=0.24.0`
- FastAPI application running with:
  - PostgreSQL database
  - Morpho GraphQL API access
  - Vertex AI credentials (for LLM validation)

## Related Documentation

- **Fix Documentation**: `/home/ubuntu/anvil_backend/VAULT_QUERY_FIX_COMPLETE.md`
- **Lending Knowledge Base**: `docs/ceo/agents/lending/knowledge_base.md`
- **Shortcuts Update**: `docs/ceo/agents/lending/shortcuts_update.md`
- **Money Market Distinction**: `docs/shortcuts/money_market.md`

## Troubleshooting

### Test Fails: Wrong Agent Routing

**Symptom**: `actual_agents` contains `["defi_yield"]` instead of `["lending_workflow"]`

**Cause**: Supervisor routing not updated or reverted

**Fix**: Check `src/app/domain/services/agent_squad/supervisor_coordinator.py` lines 699-703, 744-752, 788-794

Ensure supervisor instructions include:
```python
"vault", "vaults", "morpho vault", "lending vault", "best vaults"
→ ALWAYS use "lending_workflow" (Morpho curated vaults)
```

### Test Fails: DeFiLlama Data in Response

**Symptom**: Response contains "Beefy", "Kamino", "Balancer" instead of Morpho vaults

**Cause**: Query routed to `defi_yield` agent

**Fix**: Same as above - verify supervisor routing instructions

### Test Fails: Intent Detection

**Symptom**: Guest users fail vault queries (if testing guest flow)

**Cause**: Intent detector patterns not updated

**Fix**: Check `src/app/application/chat/services/intent_detector_v2.py` lines 1412-1435

Ensure vault_patterns are present and route to `ChatIntentV2.LENDING`

### LLM Validation Disabled

**Symptom**: All tests show `qa_status: "SKIPPED"`

**Cause**: `llm_validator.enabled = False` (expected in CI/local development)

**Action**: This is normal. LLM validation is optional and only runs when explicitly enabled.

## Success Metrics

**All 8 tests should PASS** with the following routing validation:

| Test ID | Query | Expected Agent | Critical Check |
|---------|-------|----------------|----------------|
| 001 | "Show best lending vaults" | lending_workflow | NOT defi_yield |
| 002 | "top vaults" | lending_workflow | - |
| 003 | "best morpho vaults" | lending_workflow | - |
| 004 | "compare vaults" | lending_workflow | - |
| 005 | "best vaults" vs "best yield farms" | lending_workflow vs (defi_yield OR other) | Distinction proof |
| 006 | "mejores bóvedas de préstamos" (es) | lending_workflow | Multi-language |
| 007 | Multi-step: discovery → deposit | lending_workflow (both steps) | Context preservation |
| 008 | "Show best lending vaults" | lending_workflow | Format validation |

## Continuous Integration

Add to CI pipeline:

```yaml
- name: Run Lending Vault Integration Tests
  run: |
    pytest tests/integration/user/test_lending_vaults.py \
      -v \
      -m integration \
      --tb=short \
      --junit-xml=reports/lending_vaults.xml
```

## Next Steps

1. **Add Guest User Tests**: Create equivalent tests for `/api/v1/guest/chat` endpoint
2. **Add Performance Tests**: Measure response times for vault queries
3. **Add Error Handling Tests**: Test behavior when Morpho API is unavailable
4. **Add Edge Case Tests**: Empty results, single vault, filtered queries
