# CSV Tracking Integration Pattern
## Step-by-Step Guide for Adding CSV Tracking to Tests

**Date**: 2026-01-16
**Status**: Pilot batch complete (2 tests) | 157 tests remaining

---

## Pattern Overview

This document provides the exact pattern for adding CSV tracking to existing tests that have LLM validation.

### Pilot Batch Examples

✅ **Complete**: 2 hunter tests in `tests/integration/guest/test_guest_chat_hunter_real.py`
- test_hunter_cross_chain_analysis
- test_hunter_sentiment_aggregation_sources

---

## Step 1: Add Import

Add datetime import at the top of the file (if not already present):

```python
import pytest
from datetime import datetime  # ADD THIS LINE
from httpx import AsyncClient, ASGITransport
```

---

## Step 2: Add csv_tracker Parameter

Add `csv_tracker` to the test function parameters:

**Before**:
```python
async def test_hunter_cross_chain_analysis(self, test_app, llm_validator):
```

**After**:
```python
async def test_hunter_cross_chain_analysis(self, test_app, llm_validator, csv_tracker):
```

---

## Step 3: Capture Validation Result

Change the LLM validation section to capture the result as a variable:

**Before**:
```python
# Optional LLM semantic validation (environment-gated)
if llm_validator.enabled:
    validation = await llm_validator.validate_single_response(...)
    if validation.verdict != "PASS":
        pytest.warn(...)
```

**After**:
```python
# Optional LLM semantic validation (environment-gated)
validation = None  # ADD THIS LINE
if llm_validator.enabled:
    validation = await llm_validator.validate_single_response(...)
    if validation.verdict != "PASS":
        pytest.warn(...)
```

---

## Step 4: Add CSV Tracking Call

Add CSV tracking call immediately after LLM validation section:

```python
# CSV tracking
await csv_tracker("guest", "hunter", {
    "test_id": "guest_hunter_cross_chain_001",
    "s_multistep": False,
    "input": "Find arbitrage opportunities between Ethereum and Polygon for USDC",
    "output": content,
    "test_label_sequence": "hunter_cross_chain",
    "output_expected": "Cross-chain arbitrage opportunities with protocols and profit margins",
    "status": "PASS" if response.status_code == 200 else "FAIL",
    "date": datetime.utcnow().isoformat(),
    "quality": validation.confidence if validation else None,
    "qa_status": validation.verdict if validation else "SKIPPED",
    "qa_output": validation.reasoning if validation else None,
})
```

---

## Complete Example

### Before Adding CSV Tracking

```python
@pytest.mark.asyncio
@pytest.mark.llm_validation
async def test_hunter_cross_chain_analysis(self, test_app, llm_validator):
    """Test Hunter AI cross-chain arbitrage opportunity analysis."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/guest/chat",
            json={"content": "Find arbitrage opportunities between Ethereum and Polygon for USDC", "language": "en"},
            headers={"X-Forwarded-For": "127.0.0.500"},
        )

    assert response.status_code == 200
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 100, "Should provide detailed cross-chain analysis"

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_hunter_cross_chain_analysis",
            user_input="Find arbitrage opportunities between Ethereum and Polygon for USDC",
            agent_output=content,
            expected_behavior=(
                "Should identify cross-chain arbitrage opportunities for USDC. "
                "Response should mention specific protocols on both chains, price differences, "
                "gas cost considerations for cross-chain transfers, and potential profit margins."
            ),
            additional_context={
                'test_category': 'cross_chain_analysis',
                'chains': ['ethereum', 'polygon'],
                'token': 'USDC'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))
```

### After Adding CSV Tracking

```python
@pytest.mark.asyncio
@pytest.mark.llm_validation
async def test_hunter_cross_chain_analysis(self, test_app, llm_validator, csv_tracker):  # ADDED csv_tracker
    """Test Hunter AI cross-chain arbitrage opportunity analysis."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/guest/chat",
            json={"content": "Find arbitrage opportunities between Ethereum and Polygon for USDC", "language": "en"},
            headers={"X-Forwarded-For": "127.0.0.500"},
        )

    assert response.status_code == 200
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 100, "Should provide detailed cross-chain analysis"

    # Optional LLM semantic validation (environment-gated)
    validation = None  # ADDED
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_hunter_cross_chain_analysis",
            user_input="Find arbitrage opportunities between Ethereum and Polygon for USDC",
            agent_output=content,
            expected_behavior=(
                "Should identify cross-chain arbitrage opportunities for USDC. "
                "Response should mention specific protocols on both chains, price differences, "
                "gas cost considerations for cross-chain transfers, and potential profit margins."
            ),
            additional_context={
                'test_category': 'cross_chain_analysis',
                'chains': ['ethereum', 'polygon'],
                'token': 'USDC'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking - ADDED ENTIRE SECTION
    await csv_tracker("guest", "hunter", {
        "test_id": "guest_hunter_cross_chain_001",
        "s_multistep": False,
        "input": "Find arbitrage opportunities between Ethereum and Polygon for USDC",
        "output": content,
        "test_label_sequence": "hunter_cross_chain",
        "output_expected": "Cross-chain arbitrage opportunities with protocols and profit margins",
        "status": "PASS" if response.status_code == 200 else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })
```

---

## CSV Tracking Field Guidelines

### test_id Format

Pattern: `{user_type}_{category}_{specific}_{number}`

Examples:
- `"guest_hunter_cross_chain_001"`
- `"guest_hunter_sentiment_agg_002"`
- `"guest_ultra_arbitrage_001"`
- `"user_hunter_advanced_001"`

### s_multistep

- `False` - Single query/response
- `True` - Multi-turn conversation or multi-step shortcut

### test_label_sequence

Describes the agent flow or steps:

**Single Agent**:
- `"hunter_cross_chain"`
- `"hunter_sentiment_aggregation"`
- `"ultra_arbitrage"`
- `"agent_squad"`

**Agent Handoffs** (use `→`):
- `"hunter→ultra"`
- `"research→hunter→ultra"`

**Multi-Step Flows** (use `->`):
- `"shortcut_swap_step1->step2->step3"`
- `"shortcut_send_step1->step2"`

### User Type & Category

**Guest Tests**:
- user_type: `"guest"`
- category options: `"hunter"`, `"ultra"`, `"agent_squad"`, `"knowledge"`, `"shortcuts"`, `"flows"`, `"graphrag"`, `"errors"`, `"general"`

**User Tests**:
- user_type: `"user"`
- category options: `"hunter"`, `"ultra"`, `"agent_squad"`, `"shortcuts"`, `"errors"`, `"workflows"`, `"authenticated"`, `"general"`

---

## File-by-File Guide

### Phase 5 Files (Already have LLM validation)

These files need CSV tracking added following the pattern above:

**Guest Tests** (40 tests across 6 files):
1. `tests/integration/guest/test_guest_chat_hunter_real.py` (9 tests)
   - ✅ 2 done (test_hunter_cross_chain_analysis, test_hunter_sentiment_aggregation_sources)
   - ⏳ 7 remaining
   - Category: `"hunter"`

2. `tests/integration/guest/test_guest_chat_ultra_real.py` (8 tests)
   - Category: `"ultra"`

3. `tests/integration/guest/test_guest_chat_agent_squad_real.py` (6 tests)
   - Category: `"agent_squad"`

4. `tests/integration/guest/test_guest_chat_knowledge_research.py` (6 tests)
   - Category: `"knowledge"`

5. `tests/integration/guest/test_guest_chat_shortcuts.py` (7 tests)
   - Category: `"shortcuts"`

6. `tests/integration/guest/errors/test_guest_error_handling.py` (5 tests)
   - Category: `"errors"`

**User Tests** (26 tests across 5 files):

7. `tests/integration/user/test_user_hunter_advanced.py` (9 tests)
   - Category: `"hunter"`

8. `tests/integration/user/test_user_ultra_advanced.py` (8 tests)
   - Category: `"ultra"`

9. `tests/integration/user/test_user_agent_squad_advanced.py` (6 tests)
   - Category: `"agent_squad"`

10. `tests/integration/user/errors/test_user_error_handling.py` (3 tests)
    - Category: `"errors"`

11. `tests/integration/workflows/test_cancellation_flows.py` (6 tests) - moved to user/workflows
    - Category: `"workflows"`

### Other Files (3 tests)

12. `tests/integration/user/test_user_shortcuts_examples.py` (3 tests)
    - Category: `"shortcuts"`

---

## Remaining Work

### Summary

- ✅ **Complete**: 2 tests (test_guest_chat_hunter_real.py)
- ⏳ **Remaining**: 157 tests across 11 files

### Priority Order

1. **High Priority**: Finish Phase 5 guest tests (38 remaining)
   - hunter_real.py (7 tests)
   - ultra_real.py (8 tests)
   - agent_squad_real.py (6 tests)
   - knowledge_research.py (6 tests)
   - shortcuts.py (7 tests)
   - errors/test_guest_error_handling.py (5 tests)

2. **Medium Priority**: Phase 5 user tests (26 tests)
   - user_hunter_advanced.py (9 tests)
   - user_ultra_advanced.py (8 tests)
   - user_agent_squad_advanced.py (6 tests)
   - user/errors/test_user_error_handling.py (3 tests)

3. **Lower Priority**: Other files (91 reorganized tests without LLM validation yet)
   - These need both LLM validation AND CSV tracking added

---

## Verification Steps

After adding CSV tracking to each file:

1. **Compile check**:
   ```bash
   python3 -m py_compile tests/integration/guest/test_guest_chat_hunter_real.py
   ```

2. **Run test** (optional - if services available):
   ```bash
   pytest tests/integration/guest/test_guest_chat_hunter_real.py::TestGuestChatHunterReal::test_hunter_cross_chain_analysis -v
   ```

3. **Check CSV created**:
   ```bash
   ls -la tests/output/guest/hunter.csv
   head -20 tests/output/guest/hunter.csv
   ```

---

## Automation Considerations

While manual implementation ensures correctness, a script could help:

```python
# Pseudo-code for automation
for test_file in phase5_files:
    1. Read file
    2. Find all @pytest.mark.llm_validation functions
    3. For each function:
       - Add csv_tracker parameter
       - Wrap validation in `validation = None` + if block
       - Add CSV tracking call after validation
    4. Compile and verify
```

**Pros**: Faster, consistent
**Cons**: Risk of errors, harder to debug, less control

---

## Tips for Efficient Manual Work

1. **Work in batches**: Update 5-10 tests, then compile and commit
2. **Use search/replace**: IDE find/replace can help with repetitive patterns
3. **Copy template**: Keep a template CSV tracking block to copy/paste
4. **Test frequently**: Compile after each file
5. **Commit often**: Don't lose work - commit every 5-10 tests

---

**End of CSV Integration Pattern Guide**
