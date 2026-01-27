# Lending Vault Integration Tests - Complete Summary

**Date**: 2026-01-27
**Related Fix**: VAULT_QUERY_FIX_COMPLETE.md
**Test Coverage**: 13 comprehensive integration tests (8 vault routing + 5 shortcuts API)

---

## What Was Built

Comprehensive integration test suite validating the three-commit fix for vault query routing:

- **Commit 1 (2351206f)**: Intent detector vault patterns for guest users
- **Commit 2 (4ccf3009)**: Shortcuts API vault examples
- **Commit 3 (1bc72e1d)**: Supervisor vault routing for authenticated users

---

## Files Created

### 1. Main Test Files

**`tests/integration/user/test_lending_vaults.py`** (627 lines)

8 comprehensive test cases:
- ✅ `test_user_lending_vault_discovery_best_vaults` (001) - Core vault discovery
- ✅ `test_user_lending_vault_discovery_top_vaults` (002) - Short query variant
- ✅ `test_user_lending_vault_discovery_best_morpho_vaults` (003) - Explicit Morpho
- ✅ `test_user_lending_vault_comparison` (004) - Vault comparison
- ✅ `test_user_lending_vault_vs_yield_routing` (005) - **THE CRITICAL TEST** 🎯
- ✅ `test_user_lending_vault_multi_language_spanish` (006) - Spanish support
- ✅ `test_user_lending_vault_deposit_workflow` (007) - Multi-step workflow
- ✅ `test_user_lending_vault_response_format` (008) - Format validation

**`tests/integration/user/test_lending_shortcuts_api.py`** (223 lines)

5 shortcuts API validation tests:
- ✅ `test_shortcuts_api_includes_vault_patterns_english` - Validates vault patterns in API (English)
- ✅ `test_shortcuts_api_includes_vault_patterns_spanish` - Validates vault patterns in API (Spanish)
- ✅ `test_shortcuts_api_vault_patterns_match_test_queries` - Ensures test queries match API examples
- ✅ `test_shortcuts_api_lending_compare_metadata` - Validates LENDING_COMPARE metadata
- ✅ `test_shortcuts_api_multi_language_support` - Multi-language support (en, es, pt, zh)

**Total Test Coverage**: 13 comprehensive tests (8 vault routing + 5 shortcuts API)

**CSV Export**: ✅ All 8 vault tests include CSV export via `csv_tracker` fixture
- Reports location: `tests/integration/reports/user_lending_vaults_*.csv`

### 2. Documentation
**`tests/integration/user/LENDING_VAULTS_TESTS.md`** (347 lines)

Complete testing guide covering:
- Test coverage overview
- Running instructions
- Pass/fail criteria
- Troubleshooting guide
- Success metrics

### 3. Test Runner Script
**`tests/integration/user/run_lending_vault_tests.sh`** (executable)

Quick test execution modes:
```bash
./run_lending_vault_tests.sh all        # Run all 8 tests
./run_lending_vault_tests.sh quick      # Run 4 core tests
./run_lending_vault_tests.sh routing    # Run THE critical test
./run_lending_vault_tests.sh discovery  # Discovery tests only
./run_lending_vault_tests.sh workflow   # Multi-step workflow
./run_lending_vault_tests.sh multilang  # Spanish language test
./run_lending_vault_tests.sh format     # Format validation
./run_lending_vault_tests.sh comparison # Vault comparison
./run_lending_vault_tests.sh llm        # With LLM validation
```

### 4. Manual API Test Script
**`tests/integration/user/manual_vault_query_test.sh`** (executable)

Quick API validation:
```bash
./manual_vault_query_test.sh
```

Validates:
- ✅ Routes to `lending_workflow` (not `defi_yield`)
- ✅ Returns Morpho vault data (not DeFiLlama pools)
- ✅ Includes APY/yield information
- ✅ No DeFiLlama pool names (Beefy, Kamino, Balancer)

---

## Quick Start

### 1. Run All Tests

```bash
cd /home/ubuntu/anvil_backend
source .venv/bin/activate
pytest tests/integration/user/test_lending_vaults.py -v
```

### 2. Run THE Critical Test (Routing Distinction)

This is **THE MOST IMPORTANT TEST** that validates the supervisor routing fix:

```bash
pytest tests/integration/user/test_lending_vaults.py::test_user_lending_vault_vs_yield_routing -v -s
```

**What it validates**:
- Query 1: "best vaults" → routes to `lending_workflow` ✅
- Query 2: "best yield farms" → may route to `defi_yield` ✅
- Proves the fix correctly distinguishes vault queries from generic yield queries

### 3. Run Quick Validation (4 Core Tests)

```bash
./tests/integration/user/run_lending_vault_tests.sh quick
```

### 4. Manual API Test (Live Endpoint)

```bash
./tests/integration/user/manual_vault_query_test.sh
```

---

## Test Architecture

### Fixtures Used (from conftest.py)

- **`client`**: Async HTTP client
- **`conversation_id`**: Test conversation for ops@anvilcrypto.com
- **`llm_validator`**: Optional LLM-based validation
- **`csv_tracker`**: CSV report generation

### Authentication

All tests use pre-generated JWT for `ops@anvilcrypto.com`:
```python
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJ0ZXN0X3Nlc3Npb25fMjAyNl8xNzY4MDY2MDc5IiwiZXhwIjoxNzk5NjAyMDc5fQ.OUFFmZW2_QACkgrIphLFcOOB3Qb-1ckVB_RvZ-VTaF0"
```
**Expires**: 2027-01-10

### Test Pattern

Each test follows this structure:
1. Send message to conversation endpoint
2. Validate HTTP status code (200 or 201)
3. **Critical validation**: Check `routing.agents_used` contains `lending_workflow`
4. **Critical validation**: Ensure `defi_yield` NOT in agents_used
5. Validate response content (Morpho vaults, APY, TVL)
6. Optional LLM validation
7. CSV tracking for reporting

---

## Key Validation Criteria

### ✅ PASS Criteria

**Routing**:
```json
{
  "routing": {
    "intent": "SUPERVISOR_WORKFLOW",
    "agents_used": ["lending_workflow"]  // ✅ CORRECT
  }
}
```

**Response Content**:
- Contains "morpho" or "vault" keywords
- Includes APY/yield percentages
- Has vault names (e.g., "Universal USDC", "Edge UltraYield USDC")
- Has TVL amounts
- Has vault addresses (truncated)
- Length > 80 characters

### ❌ FAIL Scenarios (The Bug We Fixed)

**Wrong Routing**:
```json
{
  "routing": {
    "intent": "SUPERVISOR_WORKFLOW",
    "agents_used": ["defi_yield", "risk_analyzer"]  // ❌ WRONG
  }
}
```

**Wrong Data Source**:
- Response contains: "Beefy", "Kamino", "Balancer", "Convex" ❌
- These are DeFiLlama generic yield pools, NOT Morpho vaults

**Missing Data**:
- No APY information ❌
- No vault names ❌
- No numeric data ❌

---

## Test Coverage Summary

| Test ID | Category | Query | Expected Agent | Critical |
|---------|----------|-------|----------------|----------|
| 001 | Discovery | "Show best lending vaults" | lending_workflow | ✅ Core |
| 002 | Discovery | "top vaults" | lending_workflow | ✅ Core |
| 003 | Discovery | "best morpho vaults" | lending_workflow | ✅ Core |
| 004 | Comparison | "compare vaults" | lending_workflow | - |
| **005** | **Routing Distinction** | **"best vaults" vs "best yield farms"** | **lending_workflow vs defi_yield** | **🎯 CRITICAL** |
| 006 | Multi-Language | "mejores bóvedas de préstamos" (es) | lending_workflow | - |
| 007 | Multi-Step | Discovery → Deposit guidance | lending_workflow | - |
| 008 | Format | "Show best lending vaults" | lending_workflow | - |

---

## Expected Results

### All Tests PASS

```
tests/integration/user/test_lending_vaults.py::test_user_lending_vault_discovery_best_vaults PASSED
tests/integration/user/test_lending_vaults.py::test_user_lending_vault_discovery_top_vaults PASSED
tests/integration/user/test_lending_vaults.py::test_user_lending_vault_discovery_best_morpho_vaults PASSED
tests/integration/user/test_lending_vaults.py::test_user_lending_vault_comparison PASSED
tests/integration/user/test_lending_vaults.py::test_user_lending_vault_vs_yield_routing PASSED
tests/integration/user/test_lending_vaults.py::test_user_lending_vault_multi_language_spanish PASSED
tests/integration/user/test_lending_vaults.py::test_user_lending_vault_deposit_workflow PASSED
tests/integration/user/test_lending_vaults.py::test_user_lending_vault_response_format PASSED

======================== 8 passed in X.XXs ========================
```

### CSV Reports Generated

Location: `tests/integration/reports/user_lending_vaults_*.csv`

Fields include:
- `test_id`, `input`, `output`
- `expected_agent`, `actual_agents`
- `routing_intent`
- `status`, `quality`, `qa_status`
- `accuracy_score`, `relevance_score`, `safety_score`, `coherence_score`

---

## Troubleshooting

### Test Fails: Wrong Agent Routing

**Symptom**:
```python
AssertionError: Expected lending_workflow agent, got ['defi_yield', 'risk_analyzer']
```

**Cause**: Supervisor routing not updated or reverted

**Fix**: Check `supervisor_coordinator.py` lines 699-703, 744-752, 788-794

Ensure instructions include:
```python
"vault", "vaults", "morpho vault", "lending vault", "best vaults"
→ ALWAYS use "lending_workflow" (Morpho curated vaults)
```

### Test Fails: DeFiLlama Data in Response

**Symptom**: Response contains "Beefy", "Kamino", "Balancer"

**Cause**: Query routed to `defi_yield` agent

**Fix**: Same as above - verify supervisor routing

### All Tests Pass But Response Seems Wrong

Run manual test to see actual response:
```bash
./tests/integration/user/manual_vault_query_test.sh
cat /tmp/vault_query_response.json | jq '.agent_message.content'
```

---

## Integration with Existing Tests

### Test File Structure

```
tests/integration/user/
├── conftest.py                          # Shared fixtures
├── test_lending_vaults.py              # NEW: Lending vault tests
├── test_user_agent_squad_advanced.py
├── test_user_hunter_advanced.py
├── test_user_ultra_advanced.py
├── test_profile_management.py
├── test_user_shortcuts_examples.py
├── LENDING_VAULTS_TESTS.md             # NEW: Documentation
├── run_lending_vault_tests.sh          # NEW: Test runner
└── manual_vault_query_test.sh          # NEW: Manual API test
```

### Running All Integration Tests

```bash
pytest tests/integration/user/ -v -m integration
```

---

## CI/CD Integration

### Add to GitHub Actions

```yaml
name: Lending Vault Integration Tests

on:
  push:
    branches: [master, develop]
  pull_request:
    branches: [master]

jobs:
  test-lending-vaults:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e '.[test]'

      - name: Run Lending Vault Tests
        run: |
          pytest tests/integration/user/test_lending_vaults.py \
            -v \
            -m integration \
            --tb=short \
            --junit-xml=reports/lending_vaults.xml

      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: lending-vault-test-results
          path: reports/lending_vaults.xml
```

---

## Performance Benchmarks

Expected response times (with live API):
- Simple queries ("top vaults"): 2-5 seconds
- Complex queries ("compare vaults"): 5-10 seconds
- Multi-step workflows: 5-15 seconds total

---

## Next Steps

### Immediate
- [x] Create test file with 8 comprehensive tests
- [x] Create documentation
- [x] Create test runner script
- [x] Create manual API test script

### Future Enhancements
- [ ] Add guest user tests (via `/api/v1/guest/chat`)
- [ ] Add performance benchmarking tests
- [ ] Add error handling tests (Morpho API unavailable)
- [ ] Add edge case tests (empty results, single vault, filtered queries)
- [ ] Add Portuguese language tests (pt)
- [ ] Add Chinese language tests (zh)
- [ ] Add WebSocket real-time update tests
- [ ] Add load testing for high-traffic scenarios

---

## Related Documentation

1. **Fix Documentation**: `/home/ubuntu/anvil_backend/VAULT_QUERY_FIX_COMPLETE.md`
   - Complete fix details with before/after flow
   - Testing instructions
   - Expected response format

2. **Test Documentation**: `tests/integration/user/LENDING_VAULTS_TESTS.md`
   - Detailed test coverage
   - Running instructions
   - Troubleshooting guide

3. **Lending Knowledge Base**: `docs/ceo/agents/lending/knowledge_base.md`
   - Section 6.5: Vault query patterns

4. **Shortcuts Update**: `docs/ceo/agents/lending/shortcuts_update.md`
   - Section 5.5: Vault discovery flow

5. **Money Market Distinction**: `docs/shortcuts/money_market.md`
   - MONEY_MARKET vs LENDING distinction

---

## Success Confirmation

Run this command to verify everything is working:

```bash
cd /home/ubuntu/anvil_backend
source .venv/bin/activate

# Quick validation (THE critical test)
pytest tests/integration/user/test_lending_vaults.py::test_user_lending_vault_vs_yield_routing -v -s

# If that passes, run all tests
pytest tests/integration/user/test_lending_vaults.py -v

# Verify with live API
./tests/integration/user/manual_vault_query_test.sh
```

**Expected outcome**: All tests PASS, manual test shows ✅ with Morpho vault data.

---

## Contact & Support

For issues or questions:
1. Check `LENDING_VAULTS_TESTS.md` troubleshooting section
2. Review `VAULT_QUERY_FIX_COMPLETE.md` for fix details
3. Examine `/tmp/vault_query_response.json` for actual API responses
4. Check git commits: 2351206f, 4ccf3009, 1bc72e1d

---

**Status**: ✅ Complete
**Test Suite**: 8 comprehensive tests
**Scripts**: 2 executable helper scripts
**Documentation**: 2 detailed guides
**Lines of Code**: ~1,000 lines across all files
