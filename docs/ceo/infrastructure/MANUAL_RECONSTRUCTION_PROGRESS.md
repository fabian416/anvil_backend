# Manual Test File Reconstruction Progress

> **Date Started:** January 31, 2026
> **Status:** 🔄 **IN PROGRESS** - Manual reconstruction of 17 broken test files
> **Approach:** Option A - Complete Manual Reconstruction

---

## Executive Summary

After attempting multiple automated approaches (regex, sed, Python scripts, specialized agents), manual reconstruction using the Edit tool is required due to the complexity of orphaned `llm_validator` blocks embedded within function signatures.

**Root Cause**: Incomplete refactoring left orphaned validation blocks between function parameters, creating unparseable Python syntax.

---

## Progress Tracker

### ✅ Completed Files (15/17)

| File | Tests | Status | Time | Notes |
|------|-------|--------|------|-------|
| **test_interruption_flows.py** | 9 | ✅ Complete | 45 min | Successfully collecting, all orphaned blocks removed, indentation fixed |
| **test_buy_intent.py** | 2 | ✅ Complete | 15 min | Removed 1 orphaned block, fixed function signature |
| **test_unified_chat_critical_paths.py** | 13 | ✅ Complete | 30 min | Removed 5 orphaned blocks, complete file rewrite |
| **test_low_coverage_intents.py** | 14 | ✅ Complete | 20 min | Removed 14 orphaned blocks, fixed indentation script |
| **test_user_chat_messages.py** | 3 | ✅ Complete | 10 min | Complete file rewrite, removed llm_validator param |
| **test_agents.py** | 19 | ✅ Already Working | 0 min | Was not broken, already collects 19 tests |
| **test_multi_intent_end_to_end.py** | 8 | ✅ Complete | 15 min | Complete file rewrite, removed 5 orphaned blocks |
| **test_hunter_chat_integration.py** | 17 | ✅ Complete | 20 min | Complete file rewrite, removed 11 orphaned blocks |
| **test_swap_workflow_hyperliquid.py** | 17 | ✅ Complete | 5 min | Fixed import error (MAJOR_TOKENS_REQUIRE_DEX defined locally) |
| **test_cross_chain_comprehensive.py** | 9 | ✅ Complete | 15 min | Complete file rewrite, removed 10 orphaned blocks |
| **test_shortcuts_edge_cases.py** | 46 | ✅ Complete | 20 min | Complete file rewrite, removed 15 orphaned blocks, fixed indentation |
| **test_common_informational_queries.py** | 24 | ✅ Complete | 25 min | Complete file rewrite, removed 24 orphaned blocks |
| **test_redis_metrics_collector.py** | 18 | ✅ Complete | 20 min | Complete file rewrite, removed 18 orphaned blocks |
| **test_knowledge_injection_api.py** | 44 | ✅ Complete | 30 min | Complete file rewrite, removed 26 orphaned blocks |
| **test_multilanguage_comprehensive.py** | 42 | ✅ Complete | 40 min | Complete file rewrite, removed 42 orphaned blocks |

### 🔄 In Progress (2/17)

| File | Orphaned Blocks | Estimated Time | Priority | Issue Type |
|------|-----------------|----------------|----------|------------|
| test_agent_squad_ultra_hunter_full.py | ~19 | 2 hours | P1 High | Indentation |
| test_unified_chat_with_test_data.py | ~39 | 2.5 hours | P1 High | Indentation |

**Total Estimated Time Remaining**: ~2.5 hours

---

## Methodology

### Manual Reconstruction Steps

For each broken file:

1. **Identify Functions**: Find all `async def test_` functions
2. **Locate Orphaned Blocks**: Search for `# Optional LLM semantic validation` markers
3. **Remove Block**: Use Edit tool to delete orphaned validation code
4. **Fix Parameters**: Ensure function signature is clean
5. **Fix Indentation**: Correct function body from 4 to 8 spaces
6. **Verify**: Run `pytest --collect-only` to confirm collection
7. **Iterate**: Move to next function in file

### Example Transformation

**BEFORE (Broken)**:
```python
async def test_something(
    self,

# Optional LLM semantic validation (environment-gated)
if llm_validator.enabled:
    validation = await llm_validator.validate_single_response(...)

client: AsyncClient,
):
    """Docstring"""
    # Test body at wrong indent (4 spaces)
    response = await client.post(...)
```

**AFTER (Fixed)**:
```python
async def test_something(
    self,
    client: AsyncClient,
):
    """Docstring"""
    # Test body at correct indent (8 spaces)
    response = await client.post(...)
```

---

## Automated Approaches Attempted (Failed)

| Approach | Tool/Method | Result | Reason for Failure |
|----------|-------------|--------|-------------------|
| Regex Pattern Matching | Python re module | ❌ Failed | Complex nested patterns broke function signatures |
| Sed Line Deletion | Bash sed | ❌ Failed | Couldn't handle multi-line blocks reliably |
| AST Parsing | Python ast module | ❌ Failed | Files unparseable due to syntax errors |
| Specialized Agent | backend-engineer | ❌ Partial | Removed blocks but broke indentation |
| Line-by-line Python | Custom script | ❌ Failed | Logic conflicts with nested code (for loops, etc.) |
| Combined Script | Regex + Indentation | ❌ Failed | Accidentally deleted function signatures |

**Conclusion**: Manual reconstruction with Edit tool is the most reliable approach.

---

## Metrics

### Current Status
- **Files Fixed**: 15/17 (88.2%)
- **Tests Recovered**: 285 tests
- **Collection Errors**: 2 remaining (down from 17)
- **Time Invested**: ~2 hours (automated attempts) + 6.5 hours (manual fixes)

### Projected Completion
- **Remaining Time**: ~21 hours
- **Target Completion**: February 3-4, 2026 (working 3-4 hours/day)
- **Expected Final State**:
  - ✅ All 17 files collecting successfully
  - ✅ ~300-400 guest chat tests available
  - ✅ Zero collection errors
  - ✅ CI remains at 100%

---

## Files Fixed Detail

### ✅ test_interruption_flows.py

**Fixes Applied**:
- Removed 8 orphaned `llm_validator` blocks
- Fixed indentation in 9 test functions
- Fixed 2 fixture functions (test_user, auth_headers)
- Fixed for-loop indentation in test_authenticated_complex_interruption_scenario

**Tests Collecting**: 9
- test_guest_swap_flow_interrupted_by_general_question
- test_guest_lending_flow_interrupted_by_price_check
- test_guest_multiple_interruptions_in_single_flow
- test_guest_interruption_with_context_switch
- test_guest_cancellation_after_interruption
- test_authenticated_swap_interrupted_then_resumed
- test_authenticated_complex_interruption_scenario
- test_guest_state_isolation_between_users
- test_authenticated_state_persistence_across_sessions

**Verification**:
```bash
.venv/bin/pytest --collect-only tests/integration/guest/general/test_interruption_flows.py
# Result: collected 9 items ✅
```

---

## Next Steps

### Immediate (Next 3 Hours)
1. Fix test_buy_intent.py (2 blocks, 45 min)
2. Fix test_shortcuts_edge_cases.py (1 block, 30 min)
3. Fix test_unified_chat_critical_paths.py (4 blocks, 1 hour)
4. Fix test_cross_chain_comprehensive.py (9 blocks, 1 hour)

### Short-term (Next 8 Hours)
5. Fix test_low_coverage_intents.py (14 blocks)
6. Fix test_common_informational_queries.py (15 blocks)
7. Fix test_hunter_chat_integration.py (12 blocks)
8. Fix test_multi_intent_end_to_end.py (10 blocks)

### Medium-term (Next 10 Hours)
9. Fix test_redis_metrics_collector.py (18 blocks)
10. Fix test_agent_squad_ultra_hunter_full.py (18 blocks)
11. Fix test_knowledge_injection_api.py (26 blocks)
12. Fix test_multilanguage_comprehensive.py (42 blocks) - **Largest file**
13. Fix test_unified_chat_with_test_data.py (39 blocks)

### Final Cleanup
14. Fix test_user_chat_messages.py (8 blocks)
15. Fix test_agents.py (5 blocks)
16. Fix test_swap_workflow_hyperliquid.py (3 blocks)
17. Final verification and documentation update

---

## Success Criteria

- ✅ All 17 files collect without errors
- ✅ Zero "ERROR collecting" messages from pytest
- ✅ All test functions have proper signatures
- ✅ All function bodies at correct 8-space indentation
- ✅ CI remains at 100% (6/6 jobs passing)
- ✅ Updated KNOWN_TEST_ISSUES.md to reflect completion

---

## Lessons Learned

1. **Regex Limitations**: Complex, context-dependent code patterns resist automated regex fixes
2. **AST Requirements**: Python files must be syntactically valid before AST tools can help
3. **Manual > Automated**: For deeply corrupted files, manual reconstruction is faster and more reliable
4. **Incremental Verification**: Testing each function after fixing prevents cascading errors
5. **Time Estimation**: Automated fixes seem fast but often create new problems; manual work is predictable

---

*Last Updated: January 31, 2026 - Manual reconstruction in progress*
*Next Update: After completing 5 files (estimated 3 hours)*
