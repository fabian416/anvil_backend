# CSV Tracking Guide
## Test Execution Tracking with LLM Validation

**Date**: 2026-01-16
**Purpose**: Track test execution history with quality metrics

---

## Overview

The CSV tracking system records every test execution to organized CSV files:
```
tests/output/
├── guest/
│   ├── hunter.csv
│   ├── ultra.csv
│   ├── agent_squad.csv
│   ├── knowledge.csv
│   ├── shortcuts.csv
│   ├── flows.csv
│   ├── graphrag.csv
│   ├── errors.csv
│   └── general.csv
└── user/
    ├── hunter.csv
    ├── ultra.csv
    ├── agent_squad.csv
    ├── shortcuts.csv
    ├── errors.csv
    ├── workflows.csv
    ├── authenticated.csv
    └── general.csv
```

---

## CSV Format

Each CSV file contains these columns:

| Column              | Type    | Description                                    |
|---------------------|---------|------------------------------------------------|
| test_id             | string  | Unique test identifier                         |
| s_multistep         | boolean | Is this a multi-turn conversation              |
| input               | string  | User query/input (truncated to 200 chars)     |
| output              | string  | Agent response (truncated to 200 chars)        |
| test_label_sequence | string  | Agent flow (e.g., "hunter→ultra")              |
| output_expected     | string  | Expected behavior description                  |
| status              | string  | PASS/FAIL                                      |
| date                | string  | ISO timestamp                                  |
| quality             | float   | LLM confidence score (0.0-1.0)                 |
| qa_status           | string  | LLM verdict (PASS/FAIL/WARN/SKIPPED)           |
| qa_output           | string  | LLM reasoning (truncated to 200 chars)         |

---

## Usage Examples

### Example 1: Guest Test with Single Query

```python
@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_guest_hunter_basic(client: AsyncClient, llm_validator, csv_tracker):
    """Test guest Hunter AI basic functionality."""
    # Make request
    response = await client.post(
        "/api/guest/chat",
        json={"message": "Find Bitcoin opportunities"},
        headers={"X-Forwarded-For": "203.0.113.1"},
    )

    assert response.status_code == 200
    data = response.json()
    content = data["response"]

    # LLM validation
    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_guest_hunter_basic",
            user_input="Find Bitcoin opportunities",
            agent_output=content,
            expected_behavior="Should provide crypto opportunities with risk analysis",
            additional_context={'test_category': 'hunter_ai'}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(f"LLM concern: {validation.reasoning}"))

    # Track execution
    await csv_tracker("guest", "hunter", {
        "test_id": "guest_hunter_basic_001",
        "s_multistep": False,
        "input": "Find Bitcoin opportunities",
        "output": content,
        "test_label_sequence": "hunter_ai",
        "output_expected": "Crypto opportunities with risk analysis",
        "status": "PASS" if response.status_code == 200 else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })
```

### Example 2: User Test with Conversation Context

```python
@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_ultra_arbitrage(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker
):
    """Test user ULTRA arbitrage discovery."""
    # Make request
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Find ETH arbitrage on Polygon", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    # LLM validation
    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_ultra_arbitrage",
            user_input="Find ETH arbitrage on Polygon",
            agent_output=content,
            expected_behavior="Should discover cross-chain arbitrage with profit margins",
            additional_context={'test_category': 'ultra', 'user_type': 'authenticated'}
        )

    # Track execution
    await csv_tracker("user", "ultra", {
        "test_id": "user_ultra_arbitrage_001",
        "s_multistep": False,
        "input": "Find ETH arbitrage on Polygon",
        "output": content,
        "test_label_sequence": "ultra_arbitrage",
        "output_expected": "Cross-chain arbitrage with profit margins",
        "status": "PASS",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })
```

### Example 3: Multi-Turn Conversation

```python
@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_agent_squad_context(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker
):
    """Test Agent Squad context preservation."""
    # Turn 1
    r1 = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Tell me about Aave", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    # Turn 2
    r2 = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Compare it to Compound", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert r2.status_code in (200, 201)
    content = r2.json()["agent_message"]["content"]

    # Validate final turn
    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_agent_squad_context",
            user_input="Compare it to Compound (referring to Aave)",
            agent_output=content,
            expected_behavior="Should compare Aave and Compound with context awareness",
            additional_context={'test_category': 'context_preservation', 'turns': 2}
        )

    # Track multi-turn conversation
    await csv_tracker("user", "agent_squad", {
        "test_id": "user_agent_squad_context_001",
        "s_multistep": True,  # Multi-turn conversation
        "input": "Tell me about Aave -> Compare it to Compound",
        "output": content,
        "test_label_sequence": "agent_squad_context_preservation",
        "output_expected": "Contextual comparison of Aave and Compound",
        "status": "PASS",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })
```

### Example 4: Shortcut Multi-Step Flow

```python
@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_guest_shortcut_swap_flow(client: AsyncClient, llm_validator, csv_tracker):
    """Test guest shortcut swap multi-step flow."""
    response = await client.post(
        "/api/guest/chat",
        json={"message": "/swap ETH 100 USDC"},
        headers={"X-Forwarded-For": "203.0.113.2"},
    )

    assert response.status_code == 200
    content = response.json()["response"]

    # Validation
    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_guest_shortcut_swap_flow",
            user_input="/swap ETH 100 USDC",
            agent_output=content,
            expected_behavior="Should provide swap preview with rates and fees",
            additional_context={'test_category': 'shortcuts', 'shortcut': 'swap'}
        )

    # Track with sequence
    await csv_tracker("guest", "shortcuts", {
        "test_id": "guest_shortcut_swap_001",
        "s_multistep": True,  # Shortcut is multi-step
        "input": "/swap ETH 100 USDC",
        "output": content,
        "test_label_sequence": "shortcut_swap_step1->step2->step3",  # Track shortcut flow
        "output_expected": "Swap preview with rates, fees, and confirmation prompt",
        "status": "PASS",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })
```

---

## Test Label Sequence Examples

The `test_label_sequence` column tracks the agent/flow sequence:

### Single Agent
- `"hunter_ai"` - Hunter AI only
- `"ultra_arbitrage"` - ULTRA arbitrage tool
- `"agent_squad"` - Agent Squad orchestration

### Agent Handoffs
- `"hunter→ultra"` - Hunter AI hands off to ULTRA
- `"research→hunter→ultra"` - Research agent → Hunter → ULTRA
- `"agent_squad→hunter→ultra"` - Squad orchestrates Hunter and ULTRA

### Shortcut Flows
- `"shortcut_swap_step1->step2->step3"` - Swap shortcut 3-step flow
- `"shortcut_send_step1->step2"` - Send shortcut 2-step flow
- `"shortcut_buy_step1->step2->step3->step4"` - Buy shortcut 4-step flow

### Context Operations
- `"agent_squad_context_preservation"` - Context preservation test
- `"agent_squad_handoff"` - Agent handoff test
- `"knowledge_enrichment"` - Knowledge injection test

---

## Category Mapping

Map test file locations to CSV categories:

| Test Location                        | Category        |
|--------------------------------------|-----------------|
| `guest/hunter/`                      | hunter          |
| `guest/ultra/`                       | ultra           |
| `guest/agent_squad/`                 | agent_squad     |
| `guest/knowledge/`                   | knowledge       |
| `guest/shortcuts/`                   | shortcuts       |
| `guest/flows/`                       | flows           |
| `guest/graphrag/`                    | graphrag        |
| `guest/errors/`                      | errors          |
| `guest/general/`                     | general         |
| `user/hunter/`                       | hunter          |
| `user/ultra/`                        | ultra           |
| `user/agent_squad/`                  | agent_squad     |
| `user/shortcuts/`                    | shortcuts       |
| `user/errors/`                       | errors          |
| `user/workflows/`                    | workflows       |
| `user/authenticated/`                | authenticated   |
| `user/general/`                      | general         |

---

## Best Practices

1. **Always track after validation**: Call `csv_tracker` after LLM validation completes
2. **Use descriptive test_ids**: Format: `{user_type}_{category}_{specific}_###`
3. **Mark multi-step correctly**: Set `s_multistep=True` for multi-turn conversations or shortcuts
4. **Track agent flows**: Use `→` for handoffs, `->` for sequential steps
5. **Truncate long outputs**: The tracker auto-truncates to 200 chars
6. **Handle validation**: Check `llm_validator.enabled` before accessing validation results

---

## Viewing Results

### Load CSV in Python

```python
import pandas as pd

# Load guest hunter results
df = pd.read_csv("tests/output/guest/hunter.csv")

# Filter by status
failed = df[df["status"] == "FAIL"]

# Filter by quality
low_quality = df[df["quality"] < 0.8]

# Group by test_label_sequence
by_flow = df.groupby("test_label_sequence").agg({
    "status": "count",
    "quality": "mean"
})
```

### View in Excel/Sheets

Open CSV files directly in Excel or Google Sheets for analysis.

---

## Integration with CI/CD

CSV files track historical execution:
- Monitor quality trends over time
- Identify regression patterns
- Track LLM validation consistency
- Analyze agent flow performance

CSV files should be committed to git to maintain history.

---

**End of CSV Tracking Guide**
