# Test Suite Reorganization Plan
## CTO Methodology Framework Applied

**Date**: 2026-01-16
**Goal**: Reorganize tests into clean guest/user structure + add CSV tracking

---

## Phase 1: Problem Decomposition & Root Cause Analysis

### Current Problems
1. **Scattered Test Files**: 17 `test_guest_*.py` files in root `/tests/integration/`
2. **Mixed Folders**: `chat/`, `hunter/`, `ultra/`, `agent_squad_tests/` contain both guest AND user tests
3. **No Tracking**: Zero historical execution data or quality metrics
4. **No Organization**: Hard to find specific test categories

### Root Causes
- **Historical Growth**: Tests added organically without structure
- **No Enforcement**: No guidelines for where new tests should go
- **Missing Tooling**: No CSV tracking system existed

---

## Phase 2: Solution Generation & Trade-off Analysis

### Proposed Structure

```
tests/integration/
├── guest/
│   ├── hunter/
│   │   ├── test_guest_hunter_basic.py
│   │   ├── test_guest_hunter_advanced.py (from Phase 5)
│   │   ├── test_guest_hunter_patterns.py (moved from root)
│   │   ├── test_guest_hunter_portfolio_optimization.py (moved)
│   │   ├── test_guest_hunter_price_prediction.py (moved)
│   │   ├── test_guest_hunter_risk_signals.py (moved)
│   │   ├── test_guest_hunter_sentiment.py (moved)
│   │   └── test_guest_hunter_trading_signals.py (moved)
│   ├── ultra/
│   │   ├── test_guest_ultra_basic.py
│   │   ├── test_guest_ultra_advanced.py (from Phase 5)
│   │   ├── test_arbitrage_discovery.py (moved from ultra/)
│   │   ├── test_flash_loans.py (moved)
│   │   ├── test_mev_execution.py (moved)
│   │   └── test_auto_executor_risk.py (moved)
│   ├── agent_squad/
│   │   ├── test_guest_agent_squad_basic.py
│   │   ├── test_guest_agent_squad_advanced.py (from Phase 5)
│   │   ├── test_orchestration.py (moved from agent_squad_tests/)
│   │   ├── test_context_preservation.py (moved)
│   │   └── test_agents.py (moved)
│   ├── knowledge/
│   │   ├── test_guest_knowledge_research.py (from Phase 5)
│   │   ├── test_knowledge_context_enrichment.py (moved from chat/)
│   │   ├── test_knowledge_compression.py (moved)
│   │   └── test_knowledge_quality_assurance.py (moved)
│   ├── shortcuts/
│   │   ├── test_guest_shortcuts.py (from Phase 5)
│   │   ├── test_shortcuts_edge_cases.py (moved from chat/)
│   │   └── test_shortcuts_edge_cases_comprehensive.py (moved)
│   ├── flows/
│   │   ├── test_guest_activity_flow.py (moved from root)
│   │   ├── test_guest_balance_flow.py (moved)
│   │   ├── test_guest_portfolio_flow.py (moved)
│   │   ├── test_guest_receive_flow.py (moved)
│   │   ├── test_guest_buy_multistep_flow.py (moved)
│   │   ├── test_guest_swap_multistep_flow.py (moved)
│   │   ├── test_guest_send_multistep_flow.py (moved)
│   │   └── test_guest_lending_multistep_flow.py (moved)
│   ├── graphrag/
│   │   ├── test_guest_graphrag_protocol_search.py (moved from root)
│   │   ├── test_guest_graphrag_risk_assessment.py (moved)
│   │   └── test_guest_graphrag_similar_protocols.py (moved)
│   ├── errors/
│   │   └── test_guest_error_handling.py (split from errors/)
│   ├── general/
│   │   ├── test_guest_chat_comprehensive.py (moved from chat/)
│   │   ├── test_guest_chat_parity.py (moved)
│   │   ├── test_common_informational_queries.py (moved)
│   │   ├── test_intent_detection_advanced.py (moved)
│   │   ├── test_intent_edge_cases.py (moved)
│   │   ├── test_rate_limiting_comprehensive.py (moved)
│   │   └── test_security_malicious_inputs.py (moved)
│   └── ... (many more from chat/)
│
├── user/
│   ├── hunter/
│   │   ├── test_user_hunter_advanced.py (from Phase 5)
│   │   └── test_hunter_chat_integration.py (moved from chat/)
│   ├── ultra/
│   │   ├── test_user_ultra_advanced.py (from Phase 5)
│   │   └── test_ultra_chat_integration.py (moved from ultra/)
│   ├── agent_squad/
│   │   ├── test_user_agent_squad_advanced.py (from Phase 5)
│   │   ├── test_agent_squad_gateway.py (moved from agent_squad_tests/)
│   │   └── test_agent_squad_ultra_hunter_full.py (moved from chat/)
│   ├── shortcuts/
│   │   └── test_user_shortcuts_examples.py (from Phase 5)
│   ├── errors/
│   │   └── test_user_error_handling.py (split from errors/)
│   ├── workflows/
│   │   ├── test_user_cancellation_flows.py (from workflows/)
│   │   ├── test_multistep_flow_cancellation.py (moved from chat/)
│   │   ├── test_multistep_flow_error_recovery.py (moved)
│   │   └── test_multistep_flow_orchestration.py (moved)
│   ├── authenticated/
│   │   ├── test_authenticated_chat_comprehensive.py (moved from chat/)
│   │   ├── test_authenticated_chat_integration.py (moved from tests/integration/chat/)
│   │   ├── test_conversation_lifecycle.py (moved)
│   │   ├── test_archive_conversation.py (moved)
│   │   └── test_historical_chat_advanced.py (moved)
│   └── general/
│       ├── test_cross_chain_comprehensive.py (moved from chat/)
│       ├── test_multilanguage_comprehensive.py (moved)
│       └── test_security_advanced_xss_prevention.py (moved)
│
└── output/
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

### Files to Move Summary

**From Root** (17 files → guest/):
- 6 test_guest_hunter_*.py → guest/hunter/
- 3 test_guest_graphrag_*.py → guest/graphrag/
- 8 test_guest_*_flow.py → guest/flows/

**From chat/** (~60 files):
- Guest tests → guest/general/
- User tests → user/authenticated/ or user/general/
- Intent/knowledge tests → guest/knowledge/ or guest/general/

**From hunter/** (needs analysis):
- Guest hunter tests → guest/hunter/
- User hunter tests → user/hunter/

**From ultra/** (needs analysis):
- Guest ultra tests → guest/ultra/
- User ultra tests → user/ultra/

**From agent_squad_tests/** (4 files):
- Split between guest/agent_squad/ and user/agent_squad/

**From errors/** (1 file):
- Split into guest/errors/ and user/errors/

**From workflows/** (1 file):
- Move to user/workflows/

---

## Phase 3: Risk Assessment & Validation Design

### Risks Identified

1. **Import Path Breakage** 🔴 HIGH RISK
   - Moving files changes import paths
   - Other files may import moved tests
   - **Mitigation**: Search for cross-imports before moving

2. **pytest Discovery** 🟡 MEDIUM RISK
   - pytest may not find tests in new locations
   - **Mitigation**: Verify conftest.py, __init__.py in all folders

3. **CI/CD Pipeline** 🟡 MEDIUM RISK
   - CI may have hardcoded test paths
   - **Mitigation**: Update CI configuration after move

4. **File Duplication** 🟢 LOW RISK
   - Option 3 requires splitting mixed tests
   - **Mitigation**: Careful analysis before split

### Validation Strategy

1. **Pre-Move Verification**:
   ```bash
   # Check for import dependencies
   grep -r "from tests.integration.test_guest" tests/
   grep -r "import test_guest" tests/
   ```

2. **Post-Move Verification**:
   ```bash
   # Verify all tests discoverable
   pytest --collect-only tests/integration/guest/
   pytest --collect-only tests/integration/user/

   # Compile all test files
   python3 -m py_compile tests/integration/guest/**/*.py
   python3 -m py_compile tests/integration/user/**/*.py
   ```

3. **CSV Tracking Validation**:
   ```bash
   # Run sample test and verify CSV created
   pytest tests/integration/guest/hunter/test_guest_hunter_basic.py -v
   ls tests/output/guest/hunter.csv
   ```

---

## Phase 4: Implementation Plan

### Step 1: Create Folder Structure
```bash
mkdir -p tests/integration/guest/{hunter,ultra,agent_squad,knowledge,shortcuts,flows,graphrag,errors,general}
mkdir -p tests/integration/user/{hunter,ultra,agent_squad,shortcuts,errors,workflows,authenticated,general}
mkdir -p tests/output/guest tests/output/user
```

### Step 2: Move Files (Batch Operations)

**Batch 1: Simple Moves (guest root files)**
```bash
# Hunter tests
mv tests/integration/test_guest_hunter_*.py tests/integration/guest/hunter/

# GraphRAG tests
mv tests/integration/test_guest_graphrag_*.py tests/integration/guest/graphrag/

# Flow tests
mv tests/integration/test_guest_*_flow.py tests/integration/guest/flows/
```

**Batch 2: Analyze & Split (mixed files)**
- errors/test_error_handling_comprehensive.py → Split into guest/user
- workflows/test_cancellation_flows.py → Move to user/workflows/
- chat/* files → Analyze individually (60+ files)

**Batch 3: Folder Relocations**
- hunter/* → Analyze and split guest/user
- ultra/* → Analyze and split guest/user
- agent_squad_tests/* → Analyze and split guest/user

### Step 3: Create CSV Tracking System

**Create fixture** `tests/conftest.py`:
```python
import csv
import os
from datetime import datetime
from pathlib import Path

@pytest.fixture
def csv_tracker():
    """Track test execution to CSV files."""
    def track(user_type: str, category: str, test_data: dict):
        # Ensure output directory exists
        output_dir = Path(f"tests/output/{user_type}")
        output_dir.mkdir(parents=True, exist_ok=True)

        csv_path = output_dir / f"{category}.csv"

        # CSV columns
        fieldnames = [
            'test_id', 's_multistep', 'input', 'output',
            'test_label_sequence', 'output_expected', 'status',
            'date', 'quality', 'qa_status', 'qa_output'
        ]

        # Check if file exists
        file_exists = csv_path.exists()

        # Append row
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(test_data)

    return track
```

### Step 4: Add CSV Tracking to Tests

Example modification:
```python
@pytest.mark.asyncio
@pytest.mark.llm_validation
async def test_guest_hunter_cross_chain(client, llm_validator, csv_tracker):
    # ... existing test logic ...

    # Track execution (add at end of test)
    await csv_tracker("guest", "hunter", {
        "test_id": "guest_hunter_cross_chain_001",
        "s_multistep": False,
        "input": "Find arbitrage opportunities between Ethereum and Polygon",
        "output": content[:200],  # Truncate for CSV
        "test_label_sequence": "hunter_ai",
        "output_expected": "Cross-chain arbitrage analysis with protocols and margins",
        "status": "PASS" if response.status_code == 200 else "FAIL",
        "date": datetime.now().isoformat(),
        "quality": validation.confidence if llm_validator.enabled else None,
        "qa_status": validation.verdict if llm_validator.enabled else "SKIPPED",
        "qa_output": validation.reasoning[:200] if llm_validator.enabled else None
    })
```

### Step 5: Update All Tests
- Add `csv_tracker` parameter to all test functions
- Add tracking call at end of each test
- Ensure proper category mapping (hunter, ultra, agent_squad, etc.)

---

## Timeline Estimate

**Total Effort**: 6-8 hours

- **Hour 1-2**: Create folder structure, move simple files
- **Hour 3-4**: Analyze and split mixed test files
- **Hour 5**: Create CSV tracking system
- **Hour 6-7**: Add tracking to all tests (76 Phase 5 tests + moved tests)
- **Hour 8**: Verification, compilation, commit

---

## Success Criteria

✅ All tests organized in guest/ or user/ structure
✅ All tests compile successfully
✅ CSV tracking active on all tests
✅ CSV files populate correctly on test runs
✅ No broken imports
✅ pytest discovery works for all tests
✅ Git history preserved (use `git mv` not `mv`)

---

## Next Steps

1. **User Approval**: Confirm this plan before proceeding
2. **Backup**: Create git branch for reorganization
3. **Execute**: Follow implementation plan step-by-step
4. **Verify**: Run full test suite after each batch
5. **Commit**: Incremental commits per batch

---

**Awaiting confirmation to proceed with implementation.**
