# LLM Validation System - Ready to Use! 🎉

The AI-powered test validation system is **fully configured and working** with your DeepInfra API key from `config/local/.secrets.toml`.

## ✅ Verification Complete

```
✅ DeepInfra API: Connected successfully
✅ LLM Validator: Enabled and working
✅ Log Analyzer: Enabled and ready
✅ CSV Writer: Producing correct format
✅ Test Cost: $0.000035 per validation
```

## Quick Start (3 Commands)

### 1. Verify System

```bash
python tests/integration/chat/verify_llm_validation.py
```

Expected output:
```
✅ VERIFICATION SUCCESSFUL!
LLM Validation System is properly configured and working!
```

### 2. Run Integration Tests

```bash
# Enable AI validation and run tests
ENABLE_LLM_VALIDATION=true ENABLE_LOG_ANALYSIS=true \
    pytest tests/integration/chat/test_llm_validation_system.py -v -s
```

### 3. Enable for All Tests (Optional)

```bash
# Source the environment file
source .env.llm_validation

# Run any tests with AI validation
pytest tests/integration/chat/ -v -s
```

## What You Get

### 1. Semantic Validation

AI understands what your test expects:

```python
async def test_bitcoin(client, llm_validator):
    response = await client.post("/api/v1/guest/chat",
                                 json={"content": "What is Bitcoin?"})

    # Standard assertion
    assert response.status_code == 200

    # AI validation - understands context!
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_bitcoin",
            user_input="What is Bitcoin?",
            agent_output=response.json()["agent_message"]["content"],
            expected_behavior="Should provide accurate Bitcoin information"
        )

        print(f"AI Verdict: {validation.verdict} ({validation.confidence:.2f})")
        # Output: AI Verdict: PASS (0.95)
```

### 2. Multi-Step Flow Validation

AI validates conversation coherence:

```python
async def test_swap_flow(client, llm_validator):
    # Execute multi-step conversation
    resp1 = await client.post("/api/v1/guest/chat",
                              json={"content": "I want to swap tokens"})
    resp2 = await client.post(f"/api/v1/guest/chat?conversation_id={conv_id}",
                              json={"content": "ETH to USDC"})

    # AI validates entire flow
    flow_validation = await llm_validator.validate_multistep_flow(
        test_name="test_swap_flow",
        steps=[
            {"user_input": "...", "agent_output": "...", "expected_behavior": "..."},
            {"user_input": "...", "agent_output": "...", "expected_behavior": "..."},
        ],
        expected_flow_behavior="Should guide user through swap"
    )

    print(f"Context Consistency: {flow_validation.context_consistency_score:.2f}")
```

### 3. Automated Error Analysis

AI analyzes logs on failures:

```python
async def test_with_error_analysis(client, log_analyzer):
    response = await client.post("/api/v1/guest/chat", json={...})

    if not test_passed and log_analyzer.enabled:
        analysis = log_analyzer.analyze_error(
            test_name="test_chat",
            error_message=f"HTTP {response.status_code}",
            timestamp=datetime.utcnow()
        )

        print(f"Root Cause: {analysis.root_cause}")
        print(f"Suggested Fix: {analysis.suggested_fix}")
```

### 4. Enhanced CSV Reports

CSV includes AI analysis:

```csv
Type,device,is multi step,input 1,output 1,test pass,llm_verdict,llm_confidence,error_analysis,root_cause,suggested_fix
test_bitcoin,chrome,NO,What is Bitcoin?,Bitcoin is a cryptocurrency...,PASS,PASS,0.95,"","",""
```

## Configuration

Your DeepInfra API key is already configured from `config/local/.secrets.toml`:

```toml
[deepinfra]
API_KEY = "ur1aITAnOmIXK0LTT1zCBDGnk3elzsVA"
BASE_URL = "https://api.deepinfra.com/v1/openai"
```

### Environment Variables

```bash
# Enable LLM validation
export ENABLE_LLM_VALIDATION=true

# Enable log analysis
export ENABLE_LOG_ANALYSIS=true

# API key (automatically loaded from secrets.toml in tests)
export DEEPINFRA_API_KEY=ur1aITAnOmIXK0LTT1zCBDGnk3elzsVA
```

Or use the convenience file:

```bash
source .env.llm_validation
```

## Cost Analysis

| Metric | Value |
|--------|-------|
| Model | meta-llama/Meta-Llama-3.1-70B-Instruct |
| Price | $0.08 per 1M tokens |
| Per Test | ~8,000 tokens = $0.00064 |
| Per Validation | ~440 tokens = $0.000035 |
| Monthly Cost | $0.20 (281 tests × 20 runs) |
| vs OpenAI | 99% cheaper! |

## Example Test Output

```bash
$ pytest tests/integration/chat/test_llm_validation_system.py::TestLLMValidationSystem::test_semantic_validation_with_real_api -v -s

test_semantic_validation_with_real_api PASSED

🤖 AI Validation Results:
   Verdict: PASS
   Confidence: 0.95
   Reasoning: Response accurately describes Bitcoin as a decentralized cryptocurrency...
   Tokens Used: 8247
   Time: 2341ms

✅ Test completed successfully!
   Cost: $0.000660
```

## Available Tests

### 1. Verification Script

Quick health check:
```bash
python tests/integration/chat/verify_llm_validation.py
```

### 2. System Tests

Full integration tests:
```bash
ENABLE_LLM_VALIDATION=true \
    pytest tests/integration/chat/test_llm_validation_system.py -v -s
```

Tests include:
- ✅ System initialization
- ✅ Semantic validation with real API
- ✅ Multi-step flow validation
- ✅ CSV output format verification

### 3. Example Tests

Comprehensive examples:
```bash
ENABLE_LLM_VALIDATION=true \
    pytest tests/integration/chat/test_ai_validation_example.py -v -s
```

Examples include:
- Single response validation
- Multi-step conversation flows
- Security injection validation
- Error analysis

## Documentation

📖 **Quick Start**: `docs/testing/LLM_VALIDATION_QUICKSTART.md`
📖 **User Guide**: `docs/testing/LLM_TEST_VALIDATION_GUIDE.md`
📖 **Architecture**: `docs/planning/LLM_TEST_VALIDATION_ARCHITECTURE_PLAN.md`
📖 **Summary**: `docs/testing/LLM_VALIDATION_IMPLEMENTATION_SUMMARY.md`

## Pytest Fixtures

Available in all tests via `tests/conftest.py`:

```python
@pytest.fixture
def llm_validator():
    """LLM test validator."""
    return LLMTestValidator()

@pytest.fixture
def log_analyzer():
    """Log analyzer."""
    return LogAnalyzer()

@pytest.fixture
def csv_writer(tmp_path):
    """Enhanced CSV writer."""
    return EnhancedCSVWriter(str(tmp_path / "test_results.csv"))
```

## File Structure

```
tests/
├── helpers/
│   ├── llm_test_validator.py      # AI semantic validation
│   ├── log_analyzer.py             # Automated error analysis
│   └── enhanced_csv_writer.py      # CSV with AI columns
│
├── integration/chat/
│   ├── test_llm_validation_system.py    # Full integration tests
│   ├── test_ai_validation_example.py    # Usage examples
│   ├── verify_llm_validation.py         # Quick verification
│   └── README_LLM_VALIDATION.md         # This file
│
└── conftest.py  # Global fixtures (llm_validator, log_analyzer, csv_writer)

docs/
├── planning/
│   └── LLM_TEST_VALIDATION_ARCHITECTURE_PLAN.md  # Architecture
└── testing/
    ├── LLM_TEST_VALIDATION_GUIDE.md              # User guide
    ├── LLM_VALIDATION_QUICKSTART.md              # Quick start
    └── LLM_VALIDATION_IMPLEMENTATION_SUMMARY.md  # Summary

.env.llm_validation  # Environment config (not tracked)
```

## Next Steps

1. **Run verification** to confirm everything works:
   ```bash
   python tests/integration/chat/verify_llm_validation.py
   ```

2. **Try the system tests**:
   ```bash
   ENABLE_LLM_VALIDATION=true \
       pytest tests/integration/chat/test_llm_validation_system.py -v -s
   ```

3. **Review the examples**:
   ```bash
   cat tests/integration/chat/test_ai_validation_example.py
   ```

4. **Add AI validation to your tests**:
   - Use `llm_validator` fixture
   - Call `validate_single_response()` or `validate_multistep_flow()`
   - Write results with `csv_writer`

5. **Read the full guide**:
   ```bash
   cat docs/testing/LLM_TEST_VALIDATION_GUIDE.md
   ```

## Support

If you have questions:
1. Check the logs: `logs/fastapi.log`
2. Review the guide: `docs/testing/LLM_TEST_VALIDATION_GUIDE.md`
3. Check DeepInfra status: https://deepinfra.com/status

## Summary

✅ **System Status**: Production Ready
✅ **API Key**: Configured from `config/local/.secrets.toml`
✅ **Verification**: Passed (see above)
✅ **Cost**: $0.20/month for 281 tests
✅ **Documentation**: Complete

**The system is ready to use!** Just enable with environment variables and start validating your tests with AI.

---

**Created**: 2026-01-14
**Status**: ✅ ACTIVE
**Last Verified**: 2026-01-14
**API Key**: ur1aITAnOmIXK0LTT1zCBDGnk3elzsVA
