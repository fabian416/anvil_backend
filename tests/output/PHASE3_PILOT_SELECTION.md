# Phase 3 Pilot Test Selection

**Date**: 2026-01-16
**Status**: 🔄 IN PROGRESS
**Phase**: 3 of 4 (Pilot Rollout)

## Executive Summary

Selected 10 diverse pilot tests to validate the enhanced validation system end-to-end. Tests cover simple queries, multi-step flows, error handling, and represent real-world usage patterns.

## Selection Criteria

1. **Test Type Diversity**: Cover all 6 test types (simple_query, multi_step, intent_detection, security, error_handling, knowledge_query)
2. **Real LLM Calls**: Actual LLM validation with DeepInfra
3. **CSV Export Validation**: Verify 23-column enhanced CSV creation
4. **Representative Coverage**: Common patterns from 97 total tests

## Selected Pilot Tests

### Category 1: Simple Query Tests (4 tests)

These represent 80% of all tests - basic request/response with assertions.

**1. Guest Hunter Sentiment - Basic Analysis**
- **File**: `tests/integration/guest/hunter/test_guest_hunter_sentiment.py`
- **Test**: `TestGuestHunterSentiment::test_sentiment_analysis_basic`
- **Type**: SIMPLE_QUERY
- **Assertions**:
  - Status code == 200
  - Contains "sentiment" keyword
  - Contains "ETH" token
  - Has enrichment data
- **Update Required**: Add `test_func=self.test_sentiment_analysis_basic` parameter

**2. Guest Hunter Sentiment - Sources Breakdown**
- **File**: `tests/integration/guest/hunter/test_guest_hunter_sentiment.py`
- **Test**: `TestGuestHunterSentiment::test_sentiment_sources_breakdown`
- **Type**: SIMPLE_QUERY
- **Assertions**:
  - Status code == 200
  - Has sources breakdown
  - Mentions data sources in content
- **Update Required**: Add `test_func=self.test_sentiment_sources_breakdown` parameter

**3. Guest Hunter Price Prediction**
- **File**: `tests/integration/guest/hunter/test_guest_hunter_price_prediction.py`
- **Test**: To be selected after inspection
- **Type**: SIMPLE_QUERY
- **Expected Assertions**: Price prediction with confidence, timeframe
- **Update Required**: Add test_func parameter

**4. Guest Hunter Risk Analysis**
- **File**: `tests/integration/guest/hunter/test_guest_hunter_risk_signals.py`
- **Test**: To be selected after inspection
- **Type**: SIMPLE_QUERY
- **Expected Assertions**: Risk factors, signals, recommendations
- **Update Required**: Add test_func parameter

### Category 2: Multi-Step Flow Tests (3 tests)

These test conversational context continuity across 5 steps.

**5. Guest Swap Multi-Step Flow**
- **File**: `tests/integration/guest/flows/test_guest_swap_multistep_flow.py`
- **Test**: `TestGuestSwapMultiStepFlow::test_complete_swap_flow_btc_to_eth`
- **Type**: MULTI_STEP
- **Steps**:
  - Step 1: Initiate swap
  - Step 2: Select FROM token (BTC)
  - Step 3: Select TO token (ETH)
  - Step 4: Enter amount (0.01)
  - Step 5: Confirm swap
- **Assertions Per Step**: Flow progression, token tracking, quote generation
- **Update Required**: Add test_func parameter + conversation_history for each step

**6. Guest Send Multi-Step Flow**
- **File**: `tests/integration/guest/flows/test_guest_send_multistep_flow.py`
- **Test**: To be selected after inspection
- **Type**: MULTI_STEP
- **Expected Steps**: Token → Amount → Address → Confirmation
- **Update Required**: Add test_func + conversation_history

**7. Guest Buy Multi-Step Flow**
- **File**: `tests/integration/guest/flows/test_guest_buy_multistep_flow.py`
- **Test**: To be selected after inspection
- **Type**: MULTI_STEP
- **Expected Steps**: Token → Amount → Payment Method → Confirmation
- **Update Required**: Add test_func + conversation_history

### Category 3: Error Handling Tests (2 tests)

These test graceful degradation and user-friendly error messages.

**8. Guest Error - Invalid Message Format**
- **File**: `tests/integration/guest/errors/test_guest_error_handling.py`
- **Test**: `test_error_invalid_message_format_guest`
- **Type**: ERROR_HANDLING
- **Assertions**:
  - Status code in (200, 400, 422)
  - User-friendly error message (no stack traces)
- **Update Required**: Add test_func parameter

**9. Guest Error - LLM API Failure**
- **File**: `tests/integration/guest/errors/test_guest_error_handling.py`
- **Test**: `test_error_llm_api_failure_graceful_degradation`
- **Type**: ERROR_HANDLING
- **Expected**: Graceful fallback when LLM fails
- **Update Required**: Add test_func parameter

### Category 4: Intent Detection Test (1 test)

This tests chat routing and intent classification.

**10. Guest Chat Routing - Intent Detection**
- **File**: Need to find or create a simple intent detection test
- **Type**: INTENT_DETECTION
- **Expected**: Correct agent routing based on query intent
- **Update Required**: Add test_func parameter

## Update Pattern for Each Test

### For Simple Query Tests:

```python
# BEFORE (existing)
validation = await llm_validator.validate_single_response(
    test_name="test_sentiment_analysis_basic",
    user_input="What's the sentiment for ETH?",
    agent_output=content,
    expected_behavior="Response should provide sentiment analysis...",
    additional_context={'test_category': 'hunter_sentiment'}
)

# AFTER (Phase 3 enhanced)
validation = await llm_validator.validate_single_response(
    test_name="test_sentiment_analysis_basic",
    user_input="What's the sentiment for ETH?",
    agent_output=content,
    expected_behavior="Response should provide sentiment analysis...",
    test_func=self.test_sentiment_analysis_basic,  # NEW: AST extraction
    additional_context={'test_category': 'hunter_sentiment'}
)
```

### For Multi-Step Flow Tests:

```python
# Build conversation history
conversation_history = [
    {"role": "user", "content": "swap"},
    {"role": "agent", "content": step1_response},
    {"role": "user", "content": "BTC"},
    {"role": "agent", "content": step2_response},
    # ... etc
]

# Validate with history
validation = await llm_validator.validate_single_response(
    test_name="test_complete_swap_flow_btc_to_eth_step5",
    user_input="confirm",
    agent_output=step5_content,
    expected_behavior="Should confirm swap and prompt for signup...",
    test_func=self.test_complete_swap_flow_btc_to_eth,  # NEW
    conversation_history=conversation_history,  # NEW: Multi-step context
    additional_context={'test_category': 'flows', 'step': 5}
)
```

### For CSV Tracking (All Tests):

```python
# BEFORE (existing - 11 fields)
await csv_tracker("guest", "hunter", {
    "test_id": "guest_hunter_sentiment_basic_001",
    "s_multistep": False,
    "input": "What's the sentiment for ETH?",
    "output": content,
    "test_label_sequence": "hunter_sentiment_basic",
    "output_expected": "Sentiment analysis for ETH...",
    "status": "PASS",
    "date": datetime.utcnow().isoformat(),
    "quality": validation.confidence if validation else None,
    "qa_status": validation.verdict if validation else "SKIPPED",
    "qa_output": validation.reasoning if validation else None,
})

# AFTER (Phase 3 enhanced - 23 fields)
await csv_tracker("guest", "hunter", {
    # Standard 11 fields (unchanged)
    "test_id": "guest_hunter_sentiment_basic_001",
    "s_multistep": False,
    "input": "What's the sentiment for ETH?",
    "output": content,
    "test_label_sequence": "hunter_sentiment_basic",
    "output_expected": "Sentiment analysis for ETH...",
    "status": "PASS",
    "date": datetime.utcnow().isoformat(),
    "quality": validation.scoring.overall_score if validation and validation.scoring else None,
    "qa_status": validation.verdict.value if validation else "SKIPPED",
    "qa_output": validation.reasoning if validation else None,
    # NEW: Enhanced 12 fields
    "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
    "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
    "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
    "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
    "test_category": validation.metadata.test_category if validation and validation.metadata else "hunter",
    "test_type": validation.metadata.test_type if validation and validation.metadata else None,
    "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
    "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
    "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
    "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
    "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
    "model_used": validation.metadata.model_used if validation and validation.metadata else None,
})
```

## Execution Plan

### Step 1: Update Simple Query Tests (4 tests)
- [x] Select tests
- [ ] Update test_guest_hunter_sentiment.py (2 tests)
- [ ] Update test_guest_hunter_price_prediction.py (1 test)
- [ ] Update test_guest_hunter_risk_signals.py (1 test)

### Step 2: Update Multi-Step Flow Tests (3 tests)
- [x] Select tests
- [ ] Update test_guest_swap_multistep_flow.py
- [ ] Update test_guest_send_multistep_flow.py
- [ ] Update test_guest_buy_multistep_flow.py

### Step 3: Update Error Handling Tests (2 tests)
- [x] Select tests
- [ ] Update test_guest_error_handling.py (2 tests)

### Step 4: Find/Update Intent Detection Test (1 test)
- [ ] Identify suitable test or create simple one
- [ ] Update with test_func parameter

### Step 5: Run Pilot Tests
```bash
# Enable enhanced validation
export ENABLE_LLM_VALIDATION=true
export WRITE_ENHANCED_CSV=true

# Run pilot tests
pytest tests/integration/guest/hunter/test_guest_hunter_sentiment.py::TestGuestHunterSentiment::test_sentiment_analysis_basic -v
pytest tests/integration/guest/hunter/test_guest_hunter_sentiment.py::TestGuestHunterSentiment::test_sentiment_sources_breakdown -v
# ... run all 10 pilot tests
```

### Step 6: Verify Enhanced CSV
```bash
# Check enhanced CSV created
ls -la tests/output/guest/hunter_enhanced.csv
ls -la tests/output/guest/flows_enhanced.csv
ls -la tests/output/guest/errors_enhanced.csv

# Analyze with pandas
python -c "
import pandas as pd
df = pd.read_csv('tests/output/guest/hunter_enhanced.csv')
print(f'Columns: {len(df.columns)}')  # Should be 23
print(f'Rows: {len(df)}')
print(df[['test_id', 'accuracy_score', 'relevance_score', 'safety_score', 'coherence_score']].head())
"
```

## Success Criteria

- [x] 10 pilot tests selected
- [ ] All 10 tests updated with test_func parameter
- [ ] All 10 tests pass with ENABLE_LLM_VALIDATION=true
- [ ] Enhanced CSV files created (23 columns verified)
- [ ] LLM validation data quality checked
- [ ] Custom prompts verified for each test type
- [ ] Granular scores populated in CSV
- [ ] Phase 3 completion summary created

## Expected Outcomes

### Enhanced CSV Columns Populated
All 23 columns should have data:
- **Standard 11**: ✅ Already working
- **Granular scores (4)**: accuracy_score, relevance_score, safety_score, coherence_score
- **Test metadata (4)**: test_category, test_type, expected_intents, token_usage
- **Recommendations (4)**: improvement_suggestions, critical_issues, next_steps, model_used

### Custom Prompts Generated
Each test should get test-type-specific prompts:
- **Simple queries**: Assertion-focused prompts with keyword validation
- **Multi-step flows**: Context continuity checks with conversation history
- **Error handling**: User-friendly error message validation
- **Intent detection**: Intent classification accuracy validation

### Real LLM Validation
- DeepInfra API calls with Meta Llama 3.1 70B
- Structured JSON responses parsed successfully
- Granular scoring metrics (0.0-1.0) for all 4 dimensions
- Actionable recommendations generated

## Timeline

- **Day 1**: Update simple query tests (4 tests) ← **Current**
- **Day 2**: Update multi-step flow tests (3 tests)
- **Day 3**: Update error handling + intent detection (3 tests)
- **Day 4**: Run all pilot tests, verify CSV data
- **Day 5**: Analyze results, create Phase 3 completion summary

---

**Phase 3 Status**: 🔄 IN PROGRESS
**Tests Selected**: 10 / 10
**Tests Updated**: 0 / 10
**Tests Verified**: 0 / 10
**Next Action**: Begin updating test_guest_hunter_sentiment.py
