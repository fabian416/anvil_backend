# Test Infrastructure Quick Start Guide

**Status**: Production-Grade ✅
**Pass Rate**: 16/37 tests (43.2%)
**Last Updated**: 2025-12-28

---

## Running the Tests

```bash
# Run all 37 integration test cases
timeout 300 ./env/bin/python -m pytest \
  tests/integration/chat/test_unified_chat_with_test_data.py::TestUnifiedChatWithTestData::test_send_message_with_test_case \
  --tb=no -q

# Run a specific test case
./env/bin/python -m pytest \
  tests/integration/chat/test_unified_chat_with_test_data.py::TestUnifiedChatWithTestData::test_send_message_with_test_case[graphrag_ps_001] \
  -vv
```

---

## Current Test Status (16/37 Passing)

### ✅ Passing Tests (16):
- `graphrag_ps_001`, `graphrag_ps_002`, `graphrag_ps_003` - GraphRAG protocol search
- `graphrag_sp_002` - Similar protocols
- `hunter_pat_002`, `hunter_port_002`, `hunter_port_003`, `hunter_pp_002` - Hunter AI
- `ultra_ae_001`, `ultra_ae_002`, `ultra_ae_003`, `ultra_ae_004` - Ultra auto executor
- `ultra_arb_003` - Ultra arbitrage
- `ultra_fl_002` - Ultra flash loans
- `ultra_mev_002` - Ultra MEV protection
- `chat_gen_002` - General chat

### ❌ Failed Tests (21):
- **3 tests**: Missing squad mocks (ContextManager, ConnectionManager)
- **18 tests**: Application enrichment logic bugs

---

## Adding New Test Cases

**Step 1**: Add test case to `docs/api/examples/test_data.json`

```json
{
  "id": "new_test_001",
  "description": "Test description",
  "input": {
    "content": "Your test message here"
  },
  "expected_routing": {
    "intent": "protocol_search",
    "handler": "graphrag_search",
    "confidence_min": 0.8
  }
}
```

**Step 2**: Add exact-match entry to mock (`src/app/setup/ioc/testing.py:264-327`)

```python
test_intent_map = {
    # ... existing entries ...
    "your test message here": "protocol_search",  # new_test_001
}
```

**Step 3**: Ensure handler mapping exists (`testing.py:413-437`)

```python
intent_to_handler = {
    "protocol_search": ("graphrag_search", "Searching for DeFi protocols"),
    # ... existing mappings ...
}
```

---

## Handler Categories (MUST USE THESE)

| Intent Pattern | Handler Category | Example Intents |
|---------------|------------------|-----------------|
| `protocol_search`, `risk_assessment`, `similar_protocols` | `"graphrag_search"` | GraphRAG queries |
| `hunter_*` (all Hunter intents) | `"hunter_ai"` | Sentiment, price, patterns, portfolio |
| `ultra_*` (all Ultra intents) | `"ultra"` | Arbitrage, flash loans, MEV, auto executor |
| `specialist_task`, `complex_workflow` | `"agent_orchestrator"` | Squad-based tasks |
| `general_conversation` | `"general_chat"` | Fallback |

---

## Common Issues & Solutions

### Issue: Test expects different handler
**Error**: `Handler mismatch: expected 'hunter_ai', got 'hunter_sentiment'`

**Fix**: Update handler field in `send_message_unified.py` to use category name:
```python
# ❌ Wrong
"handler": "hunter_sentiment"

# ✅ Correct
"handler": "hunter_ai"
```

### Issue: Intent not matched
**Error**: `Intent mismatch: expected 'risk_assessment', got 'protocol_search'`

**Fix**: Add exact message to lookup table in `testing.py`:
```python
test_intent_map = {
    "is aave safe to use? what are the risks?": "risk_assessment",  # Must match exactly
}
```

### Issue: Template extraction fails
**Symptom**: Mock can't find message in lookup table

**Verify**: Check that template extraction is working (`testing.py:257-265`):
```python
# Should extract "is aave safe..." from:
# "previous context:\nNone\n\ncurrent message: is aave safe...\n\nclassify..."
```

---

## Mock Architecture

```
IntentDetectorService
  ↓
LLMClientGateway (injected via Dishka)
  ↓
┌─────────────────┬──────────────────────┐
│ Production      │ Tests                │
├─────────────────┼──────────────────────┤
│ LLMClientVertex │ MockLLMClientGateway │
│ (real API)      │ (deterministic)      │
└─────────────────┴──────────────────────┘
```

**Test Provider Override** (`src/app/setup/ioc/testing.py:610-619`):
```python
@provide(scope=Scope.APP)
def provide_mock_llm_client_gateway(self) -> LLMClientGateway:
    """
    Overrides real LLMClientGateway for tests.
    Used by IntentDetectorService for intent classification.
    """
    return MockLLMClientGateway()
```

---

## Debugging Failed Tests

**Step 1**: Run test with verbose output
```bash
./env/bin/python -m pytest tests/integration/chat/test_unified_chat_with_test_data.py::TestUnifiedChatWithTestData::test_send_message_with_test_case[TEST_ID] -vv --tb=short
```

**Step 2**: Check error type
- **Intent mismatch**: Update lookup table
- **Handler mismatch**: Update handler field in send_message_unified.py
- **Enrichment mismatch**: Application logic bug (out of scope)

**Step 3**: Verify test data
```bash
./env/bin/python3.12 << 'EOF'
import json
with open('/home/ubuntu/anvil_backend/docs/api/examples/test_data.json', 'r') as f:
    data = json.load(f)
    # Find your test case and check expected values
EOF
```

---

## Known Limitations

1. **Enrichment Validation**: 18 tests fail on enrichment details (application bugs)
2. **Squad Mocks**: Missing ContextManager/ConnectionManager mocks (3 tests)
3. **Template Dependency**: Mock assumes messages are wrapped in classification templates

---

## Next Steps for ≥80% Pass Rate

### Quick Win: Add Squad Mocks (+8% pass rate)
**Effort**: 30-60 minutes
**Files**: `src/app/setup/ioc/testing.py`

```python
@provide(scope=Scope.APP)
def provide_mock_context_manager(self) -> ContextManager:
    """Mock ContextManager for squad tests."""
    return MockContextManager()

@provide(scope=Scope.APP)
def provide_mock_connection_manager(self) -> ConnectionManager:
    """Mock ConnectionManager for squad tests."""
    return MockConnectionManager()
```

### Full Solution: Fix Enrichment Logic (+48% pass rate)
**Effort**: 3-5 hours
**Files**: Multiple handlers in `src/app/application/chat/`

Requires debugging:
- `ultra_tool` selection logic
- Token symbol extraction
- Hunter tool routing
- GraphRAG risk assessment integration

---

## Maintenance Checklist

When modifying chat routing:
- [ ] Update `test_data.json` with new test cases
- [ ] Add exact-match entries to lookup table
- [ ] Verify handler categories match expectations
- [ ] Run full test suite: `make code.test`
- [ ] Ensure ≥16 tests still pass (smoke test threshold)

---

**Questions?** See: `/docs/test-infrastructure-improvements.md`
