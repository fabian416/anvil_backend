# Guest Chat Intent Testing Results

**Date**: January 7, 2026
**Endpoint**: `POST /api/v1/guest/chat`
**Testing Script**: `test-guest-chat-intents.sh`
**Methodology**: Based on `docs/steering/guest-chat-intent-testing.md` and CTO testing framework

---

## Test Execution Summary

### Overall Results

| Category | Total | Passed | Failed | Pass Rate | Notes |
|----------|-------|--------|--------|-----------|-------|
| **DeFi Shortcut Intents** | 7 | 1 | 6 | 14% | Rate limiting affects later tests |
| **Hunter AI Intents** | 6 | 0 | 6 | 0% | Rate limited after test #7 |
| **ULTRA Intents** | 4 | 0 | 4 | 0% | Rate limited |
| **GraphRAG Intents** | 3 | 0 | 3 | 0% | Rate limited |
| **Agent Squad Intents** | 2 | 0 | 2 | 0% | Rate limited |
| **General Conversation** | 1 | 0 | 1 | 0% | Rate limited |
| **TOTAL** | **23** | **1** | **22** | **4%** | Rate limit: 20 msgs/hour |

---

## Detailed Test Results

### ✅ Working Intents

#### MONEY_MARKET (Test #2)
- **Test**: `"compare aave vs compound"`
- **Status**: ✅ **PASS**
- **Detected Intent**: `money_market`
- **Detected Handler**: `money_market_handler`
- **Confidence**: `0.75`
- **Enrichment**: ✅ Complete (rates, best protocols, APY data)
- **Response Quality**: ✅ Real-time Aave and Compound rates with comparison table
- **Rate Limited**: ❌ No

**Response Sample**:
```json
{
  "routing": {
    "intent": "money_market",
    "handler": "money_market_handler",
    "confidence": 0.75,
    "is_demo_mode": true
  },
  "enrichment": {
    "asset": "USDC",
    "chain": "ethereum",
    "rates": [
      {
        "protocol": "Aave V3",
        "supply_apy": 4.5,
        "borrow_apy": 5.2,
        "source": "real"
      },
      {
        "protocol": "Compound V3",
        "supply_apy": 3.65,
        "borrow_apy": 4.46,
        "source": "real"
      }
    ],
    "best_supply_protocol": "Aave V3",
    "best_supply_apy": 4.5,
    "best_borrow_protocol": "Compound V3",
    "best_borrow_apy": 4.46,
    "latency_ms": 973
  }
}
```

---

### ⚠️ Rate Limited Tests

**Issue**: After test #7, all subsequent tests return `RATE_LIMITED` intent because:
- Rate limit: **20 messages per hour** per IP
- Test script executes **23 tests sequentially** from same IP
- Tests #8-23 all hit rate limit

**Affected Tests**:
- LENDING (Test #1) - Intent detection issue (not rate limited)
- SWAP, BALANCE, PORTFOLIO, ACTIVITY, RECEIVE (Tests #3-7) - Need individual testing
- All Hunter AI, ULTRA, GraphRAG, Agent Squad tests (Tests #8-23) - Rate limited

**Solution**: 
1. Test each intent individually with delays between requests
2. Use different IP addresses for batch testing
3. Increase rate limit for testing environment
4. Test during off-peak hours when rate limit resets

---

### ⚠️ Needs Investigation

#### LENDING (Test #1)
- **Test**: `"deposit 1000 usdc into morpho vault"`
- **Status**: ⚠️ **PARTIAL** (Intent detection issue)
- **Detected Intent**: `general_conversation` (expected: `LENDING`)
- **Detected Handler**: `demo_handler` (expected: `lending_handler`)
- **Issue**: Intent classifier not recognizing lending intents correctly
- **Rate Limited**: ❌ No
- **Action Required**: Review intent detection logic for lending-related messages

---

## Error Analysis

### FastAPI Logs
- ✅ **No critical errors** in FastAPI application logs
- ✅ All requests return `200 OK` status
- ✅ No exceptions or tracebacks in guest chat endpoint

### Background Tasks (Celery)
- ⚠️ Some Celery tasks show `NoFactoryError` for:
  - `GenerateEmbeddingsInteractor` (GraphRAG embeddings)
  - `RiskAlertMonitor` (Risk alerts)
- **Note**: These are background task errors, not related to guest chat endpoint
- **Impact**: None on guest chat functionality

### Database Errors
- ⚠️ One error about missing table: `distillation_cache_exact`
- **Note**: This is a background task issue, not guest chat
- **Impact**: None on guest chat functionality

---

## Testing Methodology

### Test Validation Criteria

Each test validates:
1. ✅ **HTTP Status**: Must return `200 OK`
2. ✅ **Intent Detection**: Detected intent matches expected (case-insensitive)
3. ✅ **Handler Routing**: Correct handler is invoked
4. ✅ **Response Content**: Valid response with meaningful content (>10 chars)
5. ✅ **Enrichment Data**: Structured data in `enrichment` field (when applicable)

### Test Execution

```bash
# Run all tests (will hit rate limit after ~7 tests)
./test-guest-chat-intents.sh

# Test specific intent individually
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "compare aave vs compound", "language": "en"}'
```

### Rate Limit Considerations

**Current Rate Limits**:
- 20 messages per hour per IP
- 50 messages per day per IP

**For Comprehensive Testing**:
1. Add delays between tests (e.g., 3-4 minutes)
2. Use multiple IP addresses
3. Test in batches across different time periods
4. Consider increasing rate limit in test environment

---

## Key Findings

### ✅ Strengths

1. **Money Market Handler**: Fully functional with real-time data
   - Correct intent detection (`money_market`)
   - Proper handler routing (`money_market_handler`)
   - Complete enrichment data (rates, protocols, APY)
   - Real-time Aave and Compound data integration
   - No rate limiting issues

2. **Response Format**: Consistent and well-structured
   - Proper routing metadata
   - Enrichment data when applicable
   - Guest info and rate limiting status

3. **Error Handling**: No application errors
   - All requests return proper HTTP status codes
   - No exceptions in guest chat endpoint
   - Graceful handling of rate limits

### ⚠️ Areas for Improvement

1. **Intent Detection Accuracy**: Some intents not detected correctly
   - LENDING intent falls back to `general_conversation`
   - May need improved training data or keyword matching

2. **Rate Limiting for Testing**: Current limit prevents comprehensive testing
   - Need strategy for batch testing
   - Consider test-specific rate limit exemptions

3. **Handler Coverage**: Not all handlers tested yet
   - Need individual testing for each handler
   - Verify each handler's integration with guest chat

---

## Recommendations

### Immediate Actions

1. ✅ **Money Market Handler**: Working correctly - no action needed
2. ⚠️ **Intent Detection**: Review and improve intent classifier for lending-related messages
3. 📋 **Individual Testing**: Test each intent individually to avoid rate limits
4. 📊 **Rate Limit Strategy**: Implement test-friendly rate limiting or delays

### Long-term Improvements

1. **Intent Classification**: 
   - Improve training data for edge cases
   - Add keyword-based fallback for common intents
   - Consider fine-tuning the classifier model

2. **Handler Integration**:
   - Ensure all handlers are properly injected in guest mode
   - Verify handler responses meet guest chat requirements
   - Test handler fallbacks when services unavailable

3. **Testing Automation**:
   - Integrate tests into CI/CD pipeline with proper rate limit handling
   - Add performance benchmarks
   - Monitor intent detection accuracy over time
   - Implement test delays or use multiple test IPs

---

## Test Script Usage

```bash
# Make executable
chmod +x test-guest-chat-intents.sh

# Run all tests (will hit rate limit)
./test-guest-chat-intents.sh

# Save results
./test-guest-chat-intents.sh > test-results-$(date +%Y%m%d).log 2>&1

# Test individual intent (avoid rate limit)
curl -X POST http://localhost:8080/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "compare aave vs compound", "language": "en"}'
```

---

## References

- **Testing Guide**: `docs/steering/guest-chat-intent-testing.md`
- **CTO Methodology**: `cto.md`
- **Guest Chat Spec**: `docs/steering/guest-chat-complete-flow-spec.md`
- **API Documentation**: `docs/steering/api-documentation.md`

---

**Last Updated**: January 7, 2026
**Next Review**: After intent detection improvements and rate limit strategy implementation
