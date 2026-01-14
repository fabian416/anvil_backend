# LLM Test Validation - Quick Start

Get started with AI-powered test validation in 5 minutes.

## 1. Setup (One-time)

```bash
# Get DeepInfra API key from https://deepinfra.com/
export DEEPINFRA_API_KEY=your_api_key_here

# Enable AI validation
export ENABLE_LLM_VALIDATION=true

# Optional: Enable log analysis
export ENABLE_LOG_ANALYSIS=true
```

## 2. Write Your Test

```python
# tests/integration/chat/test_my_feature.py
import pytest
from httpx import AsyncClient

async def test_bitcoin_query(client: AsyncClient, llm_validator, csv_writer):
    """Test Bitcoin query with AI validation."""

    # 1. Make API call (unchanged)
    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": "What is Bitcoin?", "language": "en"}
    )

    # 2. Standard assertions (always required)
    assert response.status_code == 200
    data = response.json()
    agent_output = data["agent_message"]["content"]
    assert len(agent_output) > 0

    # 3. Optional AI validation (automatic if enabled)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_bitcoin_query",
            user_input="What is Bitcoin?",
            agent_output=agent_output,
            expected_behavior="Should provide accurate Bitcoin information"
        )

        # Print results
        print(f"\n🤖 AI Validation: {validation.verdict.value}")
        print(f"   Confidence: {validation.confidence:.2f}")
        print(f"   Reasoning: {validation.reasoning}")
```

## 3. Run Your Test

### Without AI (Fast)
```bash
pytest tests/integration/chat/test_my_feature.py
```

### With AI (Adds ~3 seconds)
```bash
ENABLE_LLM_VALIDATION=true DEEPINFRA_API_KEY=xxx \
    pytest tests/integration/chat/test_my_feature.py -v -s
```

## 4. See Results

```
test_bitcoin_query PASSED

🤖 AI Validation: PASS
   Confidence: 0.95
   Reasoning: Response accurately describes Bitcoin as a decentralized
              cryptocurrency with blockchain technology.
```

## Multi-Step Example

```python
async def test_swap_flow(client: AsyncClient, llm_validator):
    """Test multi-step swap flow."""

    # Execute steps
    resp1 = await client.post("/api/v1/guest/chat",
                              json={"content": "I want to swap tokens"})
    conv_id = resp1.json()["conversation_id"]

    resp2 = await client.post(f"/api/v1/guest/chat?conversation_id={conv_id}",
                              json={"content": "ETH to USDC"})

    resp3 = await client.post(f"/api/v1/guest/chat?conversation_id={conv_id}",
                              json={"content": "1 ETH"})

    # Validate flow
    if llm_validator.enabled:
        flow_validation = await llm_validator.validate_multistep_flow(
            test_name="test_swap_flow",
            steps=[
                {"user_input": "I want to swap tokens",
                 "agent_output": resp1.json()["agent_message"]["content"],
                 "expected_behavior": "Should ask for token pair"},
                {"user_input": "ETH to USDC",
                 "agent_output": resp2.json()["agent_message"]["content"],
                 "expected_behavior": "Should ask for amount"},
                {"user_input": "1 ETH",
                 "agent_output": resp3.json()["agent_message"]["content"],
                 "expected_behavior": "Should provide swap details"},
            ],
            expected_flow_behavior="Should guide user through swap process",
            conversation_id=conv_id
        )

        print(f"\n🤖 Flow Validation: {flow_validation.verdict.value}")
        print(f"   Context Consistency: {flow_validation.context_consistency_score:.2f}")
```

## Error Analysis Example

```python
async def test_with_error_analysis(client: AsyncClient, log_analyzer):
    """Test with automatic error analysis."""

    response = await client.post("/api/v1/guest/chat", json={...})
    test_passed = response.status_code == 200

    # Analyze logs on failure
    if not test_passed and log_analyzer.enabled:
        analysis = log_analyzer.analyze_error(
            test_name="test_chat",
            error_message=f"HTTP {response.status_code}",
            timestamp=datetime.utcnow()
        )

        print(f"\n🔍 Error Analysis:")
        print(f"   Root Cause: {analysis.root_cause}")
        print(f"   Suggested Fix: {analysis.suggested_fix}")
```

## That's It!

You're now using AI-powered test validation. Key points:

✅ **Backward Compatible** - Tests work with or without AI validation
✅ **Optional** - Controlled by environment variables
✅ **Fast** - Only adds ~3 seconds per test when enabled
✅ **Cheap** - $0.20/month for 281 tests (99% cheaper than OpenAI)

## Next Steps

1. **Read full guide**: `docs/testing/LLM_TEST_VALIDATION_GUIDE.md`
2. **See examples**: `tests/integration/chat/test_ai_validation_example.py`
3. **Architecture details**: `docs/planning/LLM_TEST_VALIDATION_ARCHITECTURE_PLAN.md`

## Common Issues

**"LLM validation is disabled"**
→ Set `ENABLE_LLM_VALIDATION=true` and `DEEPINFRA_API_KEY`

**"No relevant logs found"**
→ Logs only analyzed on localhost, check `logs/` directory exists

**Tests too slow**
→ Disable AI validation for local dev, enable only in CI

---

**Questions?** See `docs/testing/LLM_TEST_VALIDATION_GUIDE.md` for detailed documentation.
