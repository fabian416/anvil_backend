# Commit Message Draft - Lending Vault Integration Tests

## Suggested Commit Message

```
test(lending): add comprehensive integration tests for vault query routing

Adds 8 integration tests + shortcuts API validation for the three-commit vault routing fix:
- Commit 1 (2351206f): Intent detector vault patterns
- Commit 2 (4ccf3009): Shortcuts API vault examples
- Commit 3 (1bc72e1d): Supervisor vault routing to lending_workflow

Tests validate:
✅ Vault queries route to lending_workflow (not defi_yield)
✅ Response contains Morpho vault data (not DeFiLlama pools)
✅ Multi-language support (Spanish)
✅ Multi-step workflows (discovery → deposit guidance)
✅ Response format validation (APY, TVL, addresses)
✅ CSV export for all tests (via csv_tracker fixture)
✅ Shortcuts API includes vault query examples

Files:
- tests/integration/user/test_lending_vaults.py (627 lines, 8 tests)
- tests/integration/user/test_lending_shortcuts_api.py (223 lines, 5 tests)
- tests/integration/user/LENDING_VAULTS_TESTS.md (347 lines)
- tests/integration/user/run_lending_vault_tests.sh (executable)
- tests/integration/user/manual_vault_query_test.sh (executable)
- LENDING_VAULT_TESTS_SUMMARY.md (comprehensive guide)

Total: 13 comprehensive tests covering vault routing, API validation, and multi-language support

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## Files to Commit

```bash
git add tests/integration/user/test_lending_vaults.py
git add tests/integration/user/test_lending_shortcuts_api.py
git add tests/integration/user/LENDING_VAULTS_TESTS.md
git add tests/integration/user/run_lending_vault_tests.sh
git add tests/integration/user/manual_vault_query_test.sh
git add LENDING_VAULT_TESTS_SUMMARY.md
git add COMMIT_LENDING_TESTS.md

git commit -F COMMIT_LENDING_TESTS.md
```

---

## Quick Validation Before Commit

Run these commands to verify tests work:

### 1. Quick Test (THE critical routing test)
```bash
cd /home/ubuntu/anvil_backend
source .venv/bin/activate
pytest tests/integration/user/test_lending_vaults.py::test_user_lending_vault_vs_yield_routing -v -s
```

**Expected**: PASSED with lending_workflow routing

### 2. All Tests
```bash
pytest tests/integration/user/test_lending_vaults.py -v
```

**Expected**: 8/8 tests PASSED

### 3. Manual API Test (requires live API)
```bash
./tests/integration/user/manual_vault_query_test.sh
```

**Expected**: ✅ TEST PASSED with Morpho vault data

---

## What Was Built

### Test Coverage (13 Tests Total)

**File 1: test_lending_vaults.py (8 Tests)**

1. **Core Discovery Tests** (3 tests):
   - "Show best lending vaults"
   - "top vaults"
   - "best morpho vaults"

2. **Routing Distinction Test** (1 test) 🎯:
   - **THE CRITICAL TEST**: Proves "best vaults" → lending_workflow, "best yield farms" → defi_yield
   - This validates the supervisor routing fix

3. **Comparison Test** (1 test):
   - "compare vaults"

4. **Multi-Language Test** (1 test):
   - Spanish: "mejores bóvedas de préstamos"

5. **Multi-Step Workflow Test** (1 test):
   - Discovery → Deposit guidance with context preservation

6. **Response Format Test** (1 test):
   - Validates APY, TVL, vault names, addresses present

**File 2: test_lending_shortcuts_api.py (5 Tests)**

7. **Shortcuts API Validation Tests** (5 tests):
   - English vault patterns present
   - Spanish vault patterns present
   - Test queries match shortcuts examples
   - LENDING_COMPARE metadata complete
   - Multi-language support (en, es, pt, zh)

**CSV Export**: ✅ All 8 vault tests include CSV export via `csv_tracker` fixture
- Reports saved to: `tests/integration/reports/user_lending_vaults_*.csv`

### Documentation

- **LENDING_VAULTS_TESTS.md**: Detailed testing guide (347 lines)
- **LENDING_VAULT_TESTS_SUMMARY.md**: Complete summary (400+ lines)
- **COMMIT_LENDING_TESTS.md**: This file

### Scripts

- **run_lending_vault_tests.sh**: Quick test runner with 9 modes
  ```bash
  ./run_lending_vault_tests.sh all        # All 8 tests
  ./run_lending_vault_tests.sh quick      # 4 core tests
  ./run_lending_vault_tests.sh routing    # THE critical test
  # ... 6 more modes
  ```

- **manual_vault_query_test.sh**: Live API validation
  - Creates conversation
  - Sends vault query
  - Validates routing and response
  - Saves full response to /tmp/vault_query_response.json

---

## Test Architecture

### Based on Existing Patterns

Follows the same structure as:
- `test_user_agent_squad_advanced.py`
- `test_user_hunter_advanced.py`
- `test_user_ultra_advanced.py`

Uses shared fixtures from `conftest.py`:
- `client` - Async HTTP client
- `conversation_id` - Test conversation
- `llm_validator` - Optional LLM validation
- `csv_tracker` - CSV reporting

### Key Validation Pattern

```python
# 1. Send message
response = await client.post(
    f"/api/v1/user/chat/conversations/{conversation_id}/messages",
    json={"content": "Show best lending vaults", "language": "en"},
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
)

# 2. Validate routing (CRITICAL)
routing = response.json().get("routing", {})
agents_used = routing.get("agents_used", [])

assert "lending_workflow" in agents_used, \
    f"Expected lending_workflow agent, got {agents_used}"

assert "defi_yield" not in agents_used, \
    f"Should NOT use defi_yield for vault queries, got {agents_used}"

# 3. Validate content
content = response.json()["agent_message"]["content"]
assert "morpho" in content.lower() or "vault" in content.lower()
assert "apy" in content.lower() or "yield" in content.lower()
```

---

## Integration with CI/CD

### Suggested GitHub Actions Workflow

```yaml
name: Lending Vault Tests

on:
  push:
    paths:
      - 'src/app/application/chat/services/intent_detector_v2.py'
      - 'src/app/domain/services/agent_squad/supervisor_coordinator.py'
      - 'anvil_knowledge/features/shortcuts.json'
      - 'tests/integration/user/test_lending_vaults.py'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Lending Vault Tests
        run: |
          pytest tests/integration/user/test_lending_vaults.py \
            -v -m integration --tb=short
```

---

## Success Metrics

After committing, verify:

✅ **8/8 tests PASS** locally
✅ **CSV reports generated** in `tests/integration/reports/`
✅ **Manual test succeeds** with live API
✅ **Documentation complete** with troubleshooting guide
✅ **Scripts executable** and working

---

## Related Commits

This test suite validates:
- `2351206f` - Intent detector vault patterns (P0 fix)
- `4ccf3009` - Shortcuts API alignment
- `1bc72e1d` - Supervisor vault routing (authenticated users fix)

---

## Next Steps After Commit

1. **Run in CI**: Add to GitHub Actions workflow
2. **Monitor**: Check CSV reports for patterns
3. **Extend**: Add guest user tests, Portuguese/Chinese, edge cases
4. **Performance**: Add benchmarking tests
5. **Documentation**: Link from main README

---

**Ready to commit**: ✅
**Test coverage**: 13 comprehensive tests (8 vault routing + 5 shortcuts API)
**CSV export**: Integrated in all 8 vault tests
**Total lines**: ~1,200 across all files
**Scripts**: 2 executable helpers
**Documentation**: 2 detailed guides
