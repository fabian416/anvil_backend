# LLM Test Validation System - User Guide

## Overview

The **LLM Test Validation System** provides AI-powered semantic validation and automated error analysis for integration tests. It uses DeepInfra (Meta Llama 3.1 70B) to validate test responses beyond traditional assertion-based testing.

### Key Features

✅ **Semantic Validation** - Understands context and intent, not just syntax
✅ **Multi-Step Flow Validation** - Validates conversation coherence across multiple steps
✅ **Automated Log Analysis** - Analyzes FastAPI/Celery/MCP logs to identify root causes
✅ **Enhanced CSV Reporting** - Adds AI analysis columns to test reports
✅ **Feature Flags** - Fully optional, backward compatible
✅ **Cost-Effective** - $0.08/1M tokens via DeepInfra (99% cheaper than OpenAI)

### When to Use

Use LLM validation when:
- Testing conversational AI responses
- Validating multi-step conversation flows
- Ensuring semantic correctness beyond assertions
- Debugging complex test failures
- Generating detailed test reports for QA teams

## Architecture

### Components

```
tests/helpers/
├── llm_test_validator.py    # Semantic validation with LLM
├── log_analyzer.py           # Automated log analysis
└── enhanced_csv_writer.py    # CSV writer with AI columns
```

### Flow Diagram

```
┌─────────────────┐
│  Integration    │
│     Test        │
└────────┬────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│   Standard      │   │   LLM Test      │
│  Assertions     │   │   Validator     │
│   (Required)    │   │   (Optional)    │
└─────────────────┘   └────────┬────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │  Validation     │
                      │   Result        │
                      └────────┬────────┘
                               │
                   ┌───────────┴────────────┐
                   │                        │
                   ▼                        ▼
         ┌─────────────────┐      ┌─────────────────┐
         │  Test Passed?   │      │   Log Analyzer  │
         │   NO → Analyze  │      │   (On Failure)  │
         │      Logs        │      │                 │
         └─────────────────┘      └────────┬────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ Error Analysis  │
                                   │   Result        │
                                   └────────┬────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │   Enhanced      │
                                   │   CSV Writer    │
                                   └─────────────────┘
```

## Setup

### 1. Environment Variables

```bash
# Enable LLM validation (default: false)
export ENABLE_LLM_VALIDATION=true

# Enable log analysis (default: false)
export ENABLE_LOG_ANALYSIS=true

# DeepInfra API key (required if validation enabled)
export DEEPINFRA_API_KEY=your_api_key_here

# Optional: Logs directory (default: ./logs)
export LOGS_DIR=/home/ubuntu/anvil_backend/logs
```

### 2. Get DeepInfra API Key

1. Sign up at [DeepInfra](https://deepinfra.com/)
2. Navigate to API Keys section
3. Create a new API key
4. Add to environment or `.env` file

### 3. Install Dependencies

No additional dependencies required! Uses existing project packages:
- `openai` (for DeepInfra API client)
- `httpx` (for tests)
- `pytest` (for test framework)

## Usage

### Basic Example

```python
import pytest
from httpx import AsyncClient
from tests.helpers.llm_test_validator import LLMTestValidator
from tests.helpers.enhanced_csv_writer import EnhancedCSVWriter, EnhancedTestResult

@pytest.fixture
def llm_validator():
    return LLMTestValidator()

@pytest.fixture
def csv_writer(tmp_path):
    return EnhancedCSVWriter(str(tmp_path / "results.csv"))

async def test_with_ai_validation(client: AsyncClient, llm_validator, csv_writer):
    # Step 1: Make API call
    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": "What is Bitcoin?", "language": "en"}
    )

    # Step 2: Standard assertions (always required)
    assert response.status_code == 200
    data = response.json()
    agent_output = data["agent_message"]["content"]
    assert len(agent_output) > 0

    # Step 3: Optional AI validation
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_bitcoin_query",
            user_input="What is Bitcoin?",
            agent_output=agent_output,
            expected_behavior="Should provide accurate Bitcoin information"
        )
        print(f"AI Validation: {validation.verdict} ({validation.confidence:.2f})")

    # Step 4: Write to CSV
    result = EnhancedTestResult(
        test_type="test_bitcoin_query",
        device="chrome",
        is_multi_step=False,
        inputs=["What is Bitcoin?"],
        outputs=[agent_output],
        test_pass=True,
        llm_verdict=validation.verdict.value if llm_validator.enabled else None,
        llm_confidence=validation.confidence if llm_validator.enabled else None,
    )
    csv_writer.write_single_result(result)
```

### Multi-Step Validation

```python
async def test_multistep_flow(client: AsyncClient, llm_validator):
    # Execute multi-step conversation
    steps_data = []

    # Step 1
    resp1 = await client.post("/api/v1/guest/chat",
                               json={"content": "I want to swap tokens"})
    steps_data.append({
        "user_input": "I want to swap tokens",
        "agent_output": resp1.json()["agent_message"]["content"],
        "expected_behavior": "Should ask for token pair"
    })

    # Step 2
    resp2 = await client.post(f"/api/v1/guest/chat?conversation_id={conv_id}",
                               json={"content": "ETH to USDC"})
    steps_data.append({
        "user_input": "ETH to USDC",
        "agent_output": resp2.json()["agent_message"]["content"],
        "expected_behavior": "Should ask for amount"
    })

    # Validate entire flow
    if llm_validator.enabled:
        flow_validation = await llm_validator.validate_multistep_flow(
            test_name="test_swap_flow",
            steps=steps_data,
            expected_flow_behavior="Should guide user through swap process",
            conversation_id=conv_id
        )

        print(f"Flow Validation: {flow_validation.verdict}")
        print(f"Context Consistency: {flow_validation.context_consistency_score:.2f}")
```

### Error Analysis

```python
from tests.helpers.log_analyzer import LogAnalyzer
from datetime import datetime

async def test_with_error_analysis(client: AsyncClient, log_analyzer):
    response = await client.post("/api/v1/guest/chat", json={...})

    test_passed = response.status_code == 200

    if not test_passed and log_analyzer.enabled:
        # Analyze logs to find root cause
        error_analysis = log_analyzer.analyze_error(
            test_name="test_chat_failure",
            error_message=f"HTTP {response.status_code}: {response.text}",
            timestamp=datetime.utcnow(),
            time_window_seconds=60  # Check logs ±30s around error
        )

        print(f"Root Cause: {error_analysis.root_cause}")
        print(f"Error Type: {error_analysis.error_type}")
        print(f"Suggested Fix: {error_analysis.suggested_fix}")
        print(f"Confidence: {error_analysis.confidence:.2f}")

        # Relevant logs
        for log in error_analysis.relevant_logs[:5]:
            print(f"  [{log.timestamp}] {log.source}: {log.message}")
```

## Running Tests

### Without AI Validation (Fast)

```bash
# Standard pytest run - no AI validation
pytest tests/integration/chat/test_ai_validation_example.py
```

**Result**: Tests run normally, AI validation skipped

### With AI Validation (Slower)

```bash
# Enable AI validation
export ENABLE_LLM_VALIDATION=true
export DEEPINFRA_API_KEY=your_key

pytest tests/integration/chat/test_ai_validation_example.py -v
```

**Result**: Tests run with AI validation, extra output shows validation results

### With Full Analysis (Slowest)

```bash
# Enable both validation and log analysis
export ENABLE_LLM_VALIDATION=true
export ENABLE_LOG_ANALYSIS=true
export DEEPINFRA_API_KEY=your_key

pytest tests/integration/chat/test_ai_validation_example.py -v -s
```

**Result**: Tests run with full AI analysis, detailed output on failures

## CSV Output Format

### Standard Format (Original)

```csv
Type,device,is multi step,input 1,output 1,input 2,output 2,input 3,output 3,input 4,output 4,test pass
test_bitcoin,chrome,NO,What is Bitcoin?,Bitcoin is a cryptocurrency...,,,,,,,PASS
```

### Enhanced Format (With AI Columns)

```csv
Type,device,is multi step,input 1,output 1,input 2,output 2,input 3,output 3,input 4,output 4,test pass,llm_verdict,llm_confidence,error_analysis,root_cause,suggested_fix
test_bitcoin,chrome,NO,What is Bitcoin?,Bitcoin is a cryptocurrency...,,,,,,,PASS,PASS,0.95,"","",""
test_xss,chrome,NO,<script>alert()</script>,"Bitcoin price is...",,,,,,PASS,WARNING,0.82,"Response doesn't acknowledge security handling","",""
test_failed,chrome,NO,Show price,Error occurred,,,,,,,FAIL,FAIL,0.90,"API timeout detected","FastAPI timeout after 30s","Increase timeout or optimize query"
```

### New Columns Explained

| Column | Type | Description |
|--------|------|-------------|
| `llm_verdict` | PASS/FAIL/WARNING/SKIP | AI validation verdict |
| `llm_confidence` | 0.0-1.0 | AI confidence in verdict |
| `error_analysis` | Text | Summary of semantic issues found |
| `root_cause` | Text | Root cause identified from logs |
| `suggested_fix` | Text | AI-suggested fix for the issue |

## Performance Impact

### Metrics

- **LLM Validation**: +2-3 seconds per test
- **Log Analysis**: +1-2 seconds per failure
- **Total Impact**: ~25% increase in test execution time

### Cost

- **Model**: `meta-llama/Meta-Llama-3.1-70B-Instruct`
- **Price**: $0.08 per 1M tokens (DeepInfra)
- **Per Test**: ~8,000 tokens = $0.00064 per test
- **Monthly**: 281 tests × 20 runs = $0.20/month

**Comparison**: OpenAI GPT-4 would cost $30/1M tokens = 375x more expensive!

## Best Practices

### 1. Feature Flags

Always use feature flags - never force AI validation:

```python
# ✅ GOOD - Optional validation
if llm_validator.enabled:
    validation = await llm_validator.validate_single_response(...)

# ❌ BAD - Forced validation
validation = await llm_validator.validate_single_response(...)  # Fails if disabled
```

### 2. Keep Standard Assertions

AI validation supplements, not replaces assertions:

```python
# ✅ GOOD - Both assertions and AI validation
assert response.status_code == 200  # Always runs
if llm_validator.enabled:
    validation = await llm_validator.validate_single_response(...)

# ❌ BAD - AI validation only
if llm_validator.enabled:
    validation = await llm_validator.validate_single_response(...)
    assert validation.verdict == ValidationVerdict.PASS  # Test fails if disabled!
```

### 3. Use Clear Expected Behaviors

Be specific about what you expect:

```python
# ✅ GOOD - Clear expectation
expected_behavior="Should provide Bitcoin price in USD with timestamp"

# ❌ BAD - Vague expectation
expected_behavior="Should work correctly"
```

### 4. Analyze Logs Only on Failure

Don't waste API calls on passing tests:

```python
# ✅ GOOD - Conditional analysis
if not test_passed and log_analyzer.enabled:
    error_analysis = log_analyzer.analyze_error(...)

# ❌ BAD - Always analyze
error_analysis = log_analyzer.analyze_error(...)  # Wastes API calls
```

## Troubleshooting

### Issue: "LLM validation is disabled"

**Cause**: `ENABLE_LLM_VALIDATION` not set or `DEEPINFRA_API_KEY` missing

**Fix**:
```bash
export ENABLE_LLM_VALIDATION=true
export DEEPINFRA_API_KEY=your_key_here
```

### Issue: "Log analysis is only available on localhost"

**Cause**: Running tests in production/staging environment

**Fix**: Log analysis only works on localhost for security. This is expected behavior.

### Issue: "No relevant logs found"

**Cause**: Logs directory not found or logs not being written

**Fix**:
1. Check logs directory: `ls -la logs/`
2. Verify FastAPI is logging: `tail -f logs/fastapi.log`
3. Set correct logs directory: `export LOGS_DIR=/path/to/logs`

### Issue: High API costs

**Cause**: Running validation too frequently

**Fix**:
1. Use validation selectively (e.g., only on CI)
2. Disable for local development
3. Use smaller model for simple tests

## Advanced Usage

### Custom Validation Logic

```python
from tests.helpers.llm_test_validator import ValidationVerdict

async def test_with_custom_validation(client, llm_validator):
    response = await client.post(...)
    agent_output = response.json()["agent_message"]["content"]

    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(...)

        # Custom logic based on validation
        if validation.verdict == ValidationVerdict.FAIL:
            pytest.fail(f"AI validation failed: {validation.reasoning}")
        elif validation.verdict == ValidationVerdict.WARNING:
            print(f"⚠️  Warning: {validation.reasoning}")

        # Require high confidence for critical tests
        if validation.confidence < 0.9:
            pytest.skip(f"Low confidence validation: {validation.confidence:.2f}")
```

### Batch CSV Writing

```python
from tests.helpers.enhanced_csv_writer import EnhancedCSVWriter

writer = EnhancedCSVWriter("tests/output/batch_results.csv")

results = []
for test_case in test_cases:
    # Run test
    result = run_test(test_case)
    results.append(result)

# Write all at once
writer.write_results(results)
```

### Integration with Existing Tests

Update existing test files gradually:

```python
# 1. Add fixtures to conftest.py
@pytest.fixture
def llm_validator():
    return LLMTestValidator()

# 2. Add validation to existing tests (optional parameter)
async def test_existing(client: AsyncClient, llm_validator=None):
    response = await client.post(...)
    assert response.status_code == 200

    # Optional validation - doesn't break if fixture missing
    if llm_validator and llm_validator.enabled:
        validation = await llm_validator.validate_single_response(...)
        print(f"AI: {validation.verdict}")
```

## Examples

See complete examples in:
- `tests/integration/chat/test_ai_validation_example.py` - Comprehensive examples
- `docs/planning/LLM_TEST_VALIDATION_ARCHITECTURE_PLAN.md` - Architecture details

## Support

For issues or questions:
1. Check logs: `logs/fastapi.log`, `logs/celery/*.log`, `logs/mcp/*.log`
2. Review architecture plan: `docs/planning/LLM_TEST_VALIDATION_ARCHITECTURE_PLAN.md`
3. Check DeepInfra status: https://deepinfra.com/status
4. Review test examples: `tests/integration/chat/test_ai_validation_example.py`

## Cost Optimization Tips

1. **Use validation selectively**: Enable only for critical test suites
2. **Batch validation**: Validate in CI pipeline, not on every local run
3. **Lower temperature**: Use `temperature=0.1` for consistent, cheaper results
4. **Reduce max_tokens**: Limit to 500 tokens for simple validations
5. **Cache results**: Store validation results to avoid re-validation

---

**Created**: 2026-01-14
**Version**: 1.0.0
**Status**: ✅ Production Ready
