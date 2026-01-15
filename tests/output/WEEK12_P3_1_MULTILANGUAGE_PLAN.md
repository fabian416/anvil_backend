# Week 12: P3-1 Multi-Language Expansion - Planning Document

**Date**: 2026-01-15
**Priority**: P3-1 (Optional Enhancement)
**Goal**: Expand multi-language testing to 30-40 comprehensive tests
**Status**: 🎯 PLANNING

---

## Executive Summary

**Mission**: Create comprehensive multi-language testing suite covering French (new), Spanish, Portuguese, Chinese, and multi-language context switching.

**Scope**:
- Add French language support (currently unsupported)
- Expand test coverage for existing languages (es, pt, zh)
- Test multi-language context switching
- Language validation and edge cases
- Target: 30-40 comprehensive tests

**Why P3**: Optional enhancement to improve international user experience and language coverage confidence.

---

## Current State Analysis

### Supported Languages (4 languages)

**Currently Active**:
1. **en** - English (primary)
2. **es** - Spanish (supported)
3. **pt** - Portuguese (supported)
4. **zh** - Chinese (supported)

**Source**: `docs/GUEST_CHAT_SYSTEM.md` line 13

### Unsupported Languages

**Currently Rejected (422 errors)**:
- **fr** - French (P3-1 target to add)
- **de** - German
- **ja** - Japanese
- **ko** - Korean
- **ar** - Arabic
- **hi** - Hindi

**Source**: `tests/integration/chat/test_intent_all_languages.py`

### Existing Language Tests

**File**: `tests/integration/chat/test_intent_all_languages.py`

**Coverage** (6 tests):
1. Spanish full flow ✅
2. Portuguese full flow ✅
3. Chinese full flow ✅
4. Unsupported French (422) ✅
5. Unsupported Japanese (422) ✅
6. Language validation (invalid code) ✅

**Other Tests**:
- `test_guest_receive_flow.py`: French receive test (expects 422)
- `test_guest_balance_flow.py`: French balance test (expects 422)
- `test_shortcuts_edge_cases.py`: Mentions fr in supported list
- `test_all_shortcuts_examples.py`: Lists fr in languages array

**Total Current Coverage**: ~8-10 language-related tests

---

## P3-1 Implementation Plan

### Phase 1: Add French Language Support (Backend)

**1.1 Update Language Validation Schema** (30 min)
- **File**: `src/app/presentation/http/schemas/chat.py` (or similar)
- **Change**: Add "fr" to allowed language values
- **Validation**: Pydantic schema with Literal["en", "es", "pt", "zh", "fr"]

**1.2 Update Language Constants** (15 min)
- **Search for**: Language enums, constants, or config
- **Update**: Add French to supported language lists
- **Files to check**:
  - `src/app/domain/chat/value_objects/`
  - `src/app/application/chat/`
  - Configuration files

**1.3 Update Documentation** (15 min)
- **File**: `docs/GUEST_CHAT_SYSTEM.md`
- **Change**: Update line 13 from "(en, es, pt, zh)" to "(en, es, pt, zh, fr)"

**Total Phase 1**: 1 hour

---

### Phase 2: Implement Comprehensive Multi-Language Tests (30-40 tests)

#### Test Suite Structure

**File**: `tests/integration/chat/test_multilanguage_comprehensive.py` (NEW)

**Target**: 35 tests total

---

#### Test Class 1: TestFrenchLanguageSupport (10 tests)

**French Full Flow Tests** (5 tests):
1. `test_french_001_price_query` - "Quel est le prix du Bitcoin?"
2. `test_french_002_sentiment_analysis` - "Quel est le sentiment pour ETH?"
3. `test_french_003_balance_check` - "Vérifier mon solde"
4. `test_french_004_portfolio_view` - "Afficher mon portefeuille"
5. `test_french_005_help_request` - "Aide-moi avec les transactions"

**French Shortcut Tests** (5 tests):
6. `test_french_006_swap_intent` - "Échanger 100 USDC contre ETH"
7. `test_french_007_send_intent` - "Envoyer 50 USDC à..."
8. `test_french_008_receive_intent` - "Recevoir des tokens"
9. `test_french_009_lending_intent` - "Prêter 1000 USDC sur Aave"
10. `test_french_010_buy_intent` - "Acheter 0.1 ETH"

---

#### Test Class 2: TestSpanishComprehensive (8 tests)

**Expanded Spanish Coverage** (8 tests):
11. `test_spanish_001_trading_signals` - "Señales de trading para BTC"
12. `test_spanish_002_price_prediction` - "Predicción de precio para SOL"
13. `test_spanish_003_wallet_operations` - "Operaciones de billetera"
14. `test_spanish_004_defi_protocols` - "Protocolos DeFi disponibles"
15. `test_spanish_005_swap_operation` - "Intercambiar tokens en Uniswap"
16. `test_spanish_006_lending_borrowing` - "Prestar y pedir prestado en Aave"
17. `test_spanish_007_nft_query` - "Mostrar mis NFTs"
18. `test_spanish_008_gas_estimation` - "¿Cuánto gas costará esta transacción?"

---

#### Test Class 3: TestPortugueseComprehensive (8 tests)

**Expanded Portuguese Coverage** (8 tests):
19. `test_portuguese_001_market_analysis` - "Análise de mercado para BTC"
20. `test_portuguese_002_portfolio_tracking` - "Rastrear minha carteira"
21. `test_portuguese_003_token_swap` - "Trocar 200 USDC por BTC"
22. `test_portuguese_004_staking_info` - "Informações sobre staking"
23. `test_portuguese_005_yield_farming` - "Yield farming em Curve"
24. `test_portuguese_006_risk_assessment` - "Avaliação de risco do meu portfólio"
25. `test_portuguese_007_transaction_history` - "Histórico de transações"
26. `test_portuguese_008_security_check` - "Verificação de segurança da carteira"

---

#### Test Class 4: TestChineseComprehensive (6 tests)

**Expanded Chinese Coverage** (6 tests):
27. `test_chinese_001_market_overview` - "市场概览"
28. `test_chinese_002_trading_strategy` - "交易策略建议"
29. `test_chinese_003_token_analysis` - "代币分析"
30. `test_chinese_004_defi_yield` - "DeFi 收益率"
31. `test_chinese_005_wallet_security` - "钱包安全检查"
32. `test_chinese_006_gas_optimization` - "Gas 优化建议"

---

#### Test Class 5: TestMultiLanguageContextSwitching (10 tests)

**Context Switching Tests** (5 tests):
33. `test_context_switch_001_english_to_french` - Switch mid-conversation
34. `test_context_switch_002_spanish_to_english` - Reverse switch
35. `test_context_switch_003_chinese_to_portuguese` - Cross-language switch
36. `test_context_switch_004_maintain_context` - Context preserved after switch
37. `test_context_switch_005_multi_conversation_languages` - Different conversations, different languages

**Edge Case Tests** (5 tests):
38. `test_edge_case_001_mixed_language_content` - "Swap 100 USDC à ETH" (mixed en/fr)
39. `test_edge_case_002_language_detection` - Auto-detect language from content
40. `test_edge_case_003_fallback_to_english` - Unknown language defaults to en
41. `test_edge_case_004_language_preference_persistence` - Language saved per user
42. `test_edge_case_005_invalid_language_code` - Graceful handling of "xyz"

**Total Tests**: 42 tests (exceeds 30-40 target by 5%)

---

## Technical Implementation Details

### Backend Changes Required

**1. Language Validation Schema**

**File**: Search for Pydantic schemas with language field

**Before**:
```python
class ChatMessageRequest(BaseModel):
    content: str
    language: Literal["en", "es", "pt", "zh"] = "en"
```

**After**:
```python
class ChatMessageRequest(BaseModel):
    content: str
    language: Literal["en", "es", "pt", "zh", "fr"] = "en"
```

**2. Language Constants**

**File**: Check for language enums or constants

**Potential files**:
- `src/app/domain/chat/value_objects/context.py`
- `src/app/application/chat/handlers/`
- Configuration files

**Add French Support**:
```python
SUPPORTED_LANGUAGES = ["en", "es", "pt", "zh", "fr"]
```

**3. Hunter AI Translation**

**Assumption**: Hunter AI already supports French via LLM translation

**No changes needed** if using LLM for responses (auto-translates)

**If using templates**: Add French templates for common responses

---

### Test Structure

**File**: `tests/integration/chat/test_multilanguage_comprehensive.py`

**Fixtures**:
```python
@pytest_asyncio.fixture
async def multilang_client(authenticated_client: AsyncClient) -> AsyncClient:
    """Provide client for multi-language tests."""
    return authenticated_client

@pytest_asyncio.fixture
async def french_conversation(multilang_client, test_user, auth_headers):
    """Create conversation with French language."""
    response = await multilang_client.post(
        "/api/v1/conversations",
        headers=auth_headers,
        json={"language": "fr"}
    )
    return response.json()["id"]
```

**Test Template**:
```python
@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.multilanguage
class TestFrenchLanguageSupport:
    """Comprehensive French language support tests."""

    async def test_french_001_price_query(
        self,
        multilang_client: AsyncClient,
        auth_headers: dict,
        french_conversation: str,
    ):
        """
        GIVEN a French-language conversation
        WHEN sending price query in French
        THEN response should be in French with correct data
        """
        response = await multilang_client.post(
            f"/api/v1/conversations/{french_conversation}/messages",
            headers=auth_headers,
            json={
                "content": "Quel est le prix du Bitcoin?",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "agent_message" in data
        assert data["routing"]["language"] == "fr"

        # Validate substantive response
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50

        # Validate French keywords (basic check)
        french_keywords = ["bitcoin", "prix", "btc"]
        assert any(keyword in agent_response.lower() for keyword in french_keywords)
```

---

## Success Criteria

### Coverage Goals

- **Target**: 30-40 tests
- **Actual Plan**: 42 tests (105% of target)
- **Coverage**:
  - French: 10 tests (new language)
  - Spanish: 8 additional tests
  - Portuguese: 8 additional tests
  - Chinese: 6 additional tests
  - Context switching: 10 tests

### Quality Goals

- **All tests passing**: 100% pass rate
- **Real API integration**: Tests hit actual endpoints
- **Clear failure messages**: Debugging is easy
- **Realistic test data**: Uses real crypto tokens and scenarios

### Integration Goals

- **Added to test runner**: Integrated into comprehensive runner
- **Documentation complete**: Planning and summary docs created
- **Backend changes minimal**: Only add "fr" to validation, no breaking changes

### Value Goals

- **International users**: Validated French support
- **Language confidence**: Comprehensive multi-language testing
- **Context switching**: Tested mid-conversation language changes
- **Edge cases**: Handled gracefully

---

## Implementation Timeline

### Phase 1: Backend Changes (1 hour)
1. Find and update language validation schema (30 min)
2. Update language constants (15 min)
3. Update documentation (15 min)

### Phase 2: Test Implementation (4-5 hours)
1. Create test file structure (30 min)
2. Implement French tests (10 tests, 1.5 hours)
3. Implement Spanish expanded tests (8 tests, 1 hour)
4. Implement Portuguese expanded tests (8 tests, 1 hour)
5. Implement Chinese expanded tests (6 tests, 45 min)
6. Implement context switching tests (10 tests, 1.5 hours)

### Phase 3: Validation (1 hour)
1. Run all 42 tests (30 min)
2. Fix any failures (30 min buffer)
3. Verify test runner integration

### Phase 4: Documentation (1 hour)
1. Update planning document with results
2. Create completion summary
3. Update comprehensive test count

**Total Time**: 7-8 hours (1 full work day)

---

## Risk Assessment

### Low Risks ✅

**Backend Changes**:
- Minimal changes (add "fr" to validation)
- No breaking changes
- No database migrations

**Test Implementation**:
- Standard integration test patterns
- Existing fixtures reusable
- Clear test structure

### Medium Risks ⚠️

**LLM Translation Quality**:
- Hunter AI may not translate perfectly to French
- Mitigation: Test substantive responses (length > 50 chars), not exact translations

**Test Execution Time**:
- 42 tests may take 5-10 minutes to run
- Mitigation: Async execution, parallel when possible

### Mitigation Strategies

1. **Translation Quality**: Test for response presence and length, not exact content
2. **Execution Time**: Mark as P3 tests, run separately from core suite
3. **Maintenance**: Document test expectations clearly

---

## Dependencies

### Backend Components

**Language Validation**:
- Pydantic schema with language field
- Must find and update Literal type

**Hunter AI**:
- Should already support French via LLM
- No changes needed (auto-translates)

**API Endpoints**:
- `/api/v1/guest/chat` (guest endpoint)
- `/api/v1/conversations/{id}/messages` (authenticated endpoint)

### Test Infrastructure

**Existing Fixtures**:
- `authenticated_client` ✅
- `test_user` ✅
- `auth_headers` ✅
- `conversation_id` ✅

**New Fixtures Needed**:
- `french_conversation` (specific language conversation)
- `multilang_client` (convenience wrapper)

---

## Expected Test Structure

### File Organization

```
tests/integration/chat/test_multilanguage_comprehensive.py (NEW)
├── TestFrenchLanguageSupport (10 tests)
│   ├── test_french_001_price_query
│   ├── test_french_002_sentiment_analysis
│   └── ... (8 more)
├── TestSpanishComprehensive (8 tests)
│   ├── test_spanish_001_trading_signals
│   └── ... (7 more)
├── TestPortugueseComprehensive (8 tests)
│   ├── test_portuguese_001_market_analysis
│   └── ... (7 more)
├── TestChineseComprehensive (6 tests)
│   ├── test_chinese_001_market_overview
│   └── ... (5 more)
└── TestMultiLanguageContextSwitching (10 tests)
    ├── test_context_switch_001_english_to_french
    ├── test_edge_case_001_mixed_language_content
    └── ... (8 more)
```

**Total**: 42 tests, ~800-1000 lines of code

---

## Validation Strategy

### Test Execution

**Run French tests only**:
```bash
pytest tests/integration/chat/test_multilanguage_comprehensive.py::TestFrenchLanguageSupport -v
```

**Run all multi-language tests**:
```bash
pytest tests/integration/chat/test_multilanguage_comprehensive.py -v
```

**Run with comprehensive runner**:
```bash
python scripts/run_comprehensive_integration_tests.py --mode advanced
```

### Pass Criteria

**Per Test**:
- Status code 200 (or expected error code)
- Response contains agent_message
- Response length > 50 characters
- Correct language in routing metadata

**Overall**:
- 100% tests passing
- No flaky tests
- Execution time < 10 minutes

---

## Integration with Test Runner

### Update Required

**File**: `scripts/run_comprehensive_integration_tests.py`

**Change**: Add "multilanguage" to advanced test mode

```python
"advanced": {
    "agent_squad": "tests/integration/chat/test_agent_squad_ultra_hunter_full.py",
    "cross_chain": "tests/integration/chat/test_cross_chain_comprehensive.py",
    "multilanguage": "tests/integration/chat/test_multilanguage_comprehensive.py",  # NEW
    "knowledge_injection": "tests/integration/chat/test_knowledge_injection.py",
    # ... rest
},
```

**New Advanced Test Count**: 10 files (was 9)

---

## Success Metrics

### Test Coverage Growth

**Before P3-1**:
- Total tests: 315+
- Multi-language tests: ~10 tests
- Supported languages: 4 (en, es, pt, zh)
- French support: ❌ (returns 422)

**After P3-1**:
- **Total tests: 357+** (+42 tests, +13% growth)
- **Multi-language tests: 52 tests** (+420% growth)
- **Supported languages: 5** (en, es, pt, zh, fr)
- **French support: ✅** (full coverage)

### Coverage Breakdown

| Language | Before | After | Growth |
|----------|--------|-------|--------|
| English (en) | Implicit | Implicit | - |
| Spanish (es) | 1 test | 9 tests | +800% |
| Portuguese (pt) | 1 test | 9 tests | +800% |
| Chinese (zh) | 1 test | 7 tests | +600% |
| **French (fr)** | **0 tests (422)** | **10 tests** | **NEW** |
| Context switching | 0 tests | 10 tests | NEW |
| Edge cases | ~5 tests | ~10 tests | +100% |

**Total**: 52 comprehensive multi-language tests

---

## Documentation Deliverables

### Planning Documents

1. **WEEK12_P3_1_MULTILANGUAGE_PLAN.md** (this document)
   - Comprehensive planning and strategy
   - Test breakdown and structure
   - Implementation timeline

### Completion Documents

2. **WEEK12_P3_1_MULTILANGUAGE_SUMMARY.md** (after completion)
   - Implementation results
   - Test pass rates
   - Coverage analysis
   - Lessons learned

3. **Update**: `tests/output/P2_PRIORITIES_COMPLETION_SUMMARY.md`
   - Add P3-1 completion status
   - Update total test count

---

## Next Steps (After Approval)

1. **Find language validation schema** (30 min)
2. **Add "fr" to supported languages** (15 min)
3. **Update documentation** (15 min)
4. **Implement test file** (4-5 hours)
5. **Run validation tests** (1 hour)
6. **Commit and push** (15 min)
7. **Create completion summary** (1 hour)

**Total**: 7-8 hours (1 work day)

---

## References

- **Current Language Tests**: `tests/integration/chat/test_intent_all_languages.py`
- **Guest Chat Docs**: `docs/GUEST_CHAT_SYSTEM.md`
- **P2 Completion Summary**: `tests/output/P2_PRIORITIES_COMPLETION_SUMMARY.md`
- **Test Runner**: `scripts/run_comprehensive_integration_tests.py`

---

**Status**: 🎯 PLANNING COMPLETE
**Next**: Awaiting approval to begin implementation
**Estimated Effort**: 7-8 hours (1 work day)
**Priority**: P3-1 (Optional Enhancement)

**Created by**: Claude Code
**Date**: 2026-01-15
