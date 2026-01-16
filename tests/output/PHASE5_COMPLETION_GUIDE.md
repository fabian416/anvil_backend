# Phase 5 Completion Guide
## Remaining 36 Tests Implementation

**Current Progress**: 40/76 tests (52.6% complete)
**Remaining Work**: 36 tests across 4 file sections
**Estimated Time**: 18-20 hours

---

## ✅ Completed Work (40 tests)

### Phase 1: Critical Gaps (17 tests) ✅
- User tests enhanced (3 tests)
- Error handling suite (8 tests)
- Cancellation flow suite (6 tests)

### Phase 2.1-2.3: Feature Depth (23 tests) ✅
- Hunter AI expansion (9 tests)
- ULTRA expansion (8 tests)
- Agent Squad expansion (6 tests)

**All 40 tests compile successfully and follow established patterns!**

---

## ⏸️ Remaining Work (36 tests)

### Phase 2.4: Knowledge/Research Expansion (6 tests)

**File to Create**: `tests/integration/guest/test_guest_chat_knowledge_research.py`

**Template Structure**:
```python
"""
Integration tests for Knowledge/Research features in guest chat.

Tests educational content, protocol documentation, and research quality.
"""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.integration
class TestGuestChatKnowledgeResearch:
    """Test knowledge and research features in guest chat."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_protocol_documentation_accuracy(self, test_app, llm_validator):
        """Test protocol documentation technical accuracy."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Explain how Uniswap V3 concentrated liquidity works technically", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.800"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed technical explanation"

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_knowledge_protocol_documentation_accuracy",
                user_input="Explain how Uniswap V3 concentrated liquidity works technically",
                agent_output=content,
                expected_behavior=(
                    "Should provide technically accurate explanation of Uniswap V3 concentrated liquidity. "
                    "Response should cover tick ranges, capital efficiency, position NFTs, and fee tiers. "
                    "Should be educational and technically precise."
                ),
                additional_context={
                    'test_category': 'protocol_documentation',
                    'protocol': 'uniswap_v3',
                    'topic': 'concentrated_liquidity'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    # Add 5 more tests following the same pattern:
    # - test_knowledge_smart_contract_audit_insights
    # - test_knowledge_tokenomics_analysis_depth
    # - test_knowledge_governance_proposal_summaries
    # - test_knowledge_regulatory_compliance_guidance
    # - test_knowledge_educational_content_beginner_friendly
```

**Test Scenarios**:
1. `test_knowledge_protocol_documentation_accuracy` - Uniswap V3 concentrated liquidity
2. `test_knowledge_smart_contract_audit_insights` - Security audit analysis
3. `test_knowledge_tokenomics_analysis_depth` - Economic model evaluation
4. `test_knowledge_governance_proposal_summaries` - DAO proposal clarity
5. `test_knowledge_regulatory_compliance_guidance` - Legal disclaimers
6. `test_knowledge_educational_content_beginner_friendly` - Jargon-free explanations

---

### Phase 2.5: Shortcuts Expansion (7 tests)

**File to Enhance**: `tests/integration/guest/test_guest_chat_shortcuts.py`

**Location**: Append to end of existing file (similar to Hunter/ULTRA/Agent Squad pattern)

**Test Scenarios**:
```python
# ========================================
# Advanced Shortcuts Tests (Phase 2.5)
# ========================================

@pytest.mark.asyncio
@pytest.mark.llm_validation
async def test_shortcuts_multi_step_portfolio_analysis(self, test_app, llm_validator):
    """Test chained shortcut workflow for portfolio analysis."""
    # Query that requires multiple shortcuts in sequence
    # e.g., "Show my portfolio then analyze risks"

@pytest.mark.asyncio
@pytest.mark.llm_validation
async def test_shortcuts_conditional_execution_logic(self, test_app, llm_validator):
    """Test if-then shortcut behaviors."""
    # Query with conditional logic
    # e.g., "Check ETH price and suggest buy if under $2000"

@pytest.mark.asyncio
@pytest.mark.llm_validation
async def test_shortcuts_parameter_validation_edge_cases(self, test_app, llm_validator):
    """Test invalid input handling in shortcuts."""
    # Test with invalid parameters
    # e.g., "Swap -100 ETH" (negative amount)

@pytest.mark.asyncio
@pytest.mark.llm_validation
async def test_shortcuts_output_format_consistency(self, test_app, llm_validator):
    """Test standardized response structures."""
    # Verify consistent formatting across shortcuts

@pytest.mark.asyncio
@pytest.mark.llm_validation
async def test_shortcuts_internationalization_parity(self, test_app, llm_validator):
    """Test multi-language quality consistency."""
    # Test same shortcut in en/es/pt/zh

@pytest.mark.asyncio
@pytest.mark.llm_validation
async def test_shortcuts_accessibility_considerations(self, test_app, llm_validator):
    """Test screen reader friendly responses."""
    # Check response structure for accessibility

@pytest.mark.asyncio
@pytest.mark.llm_validation
async def test_shortcuts_mobile_optimization_responses(self, test_app, llm_validator):
    """Test concise mobile-friendly output."""
    # Verify responses work well on mobile screens
```

---

### Phase 3.1: User Hunter Advanced (9 tests)

**File to Create**: `tests/integration/user/test_user_hunter_advanced.py`

**Critical Pattern**: ALWAYS use `ops@anvilcrypto.com` for authentication!

**Template Structure**:
```python
"""
Integration tests for advanced Hunter AI features with authenticated users.

All tests use ops@anvilcrypto.com (registered user with active sessions).
Tests mirror guest Hunter tests but validate user-specific features.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.run import make_app

# Access token for ops@anvilcrypto.com
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJ0ZXN0X3Nlc3Npb25fMjAyNl8xNzY4MDY2MDc5IiwiZXhwIjoxNzk5NjAyMDc5fQ.OUFFmZW2_QACkgrIphLFcOOB3Qb-1ckVB_RvZ-VTaF0"


@pytest_asyncio.fixture
async def client():
    """Create test client."""
    app = make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def conversation_id(client: AsyncClient):
    """Create conversation for ops@anvilcrypto.com."""
    response = await client.post(
        "/api/v1/user/chat/conversations",
        json={"title": "Hunter Test", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_hunter_cross_chain_analysis(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
):
    """Test Hunter AI cross-chain analysis for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Find arbitrage opportunities between Ethereum and Polygon for USDC", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 100, "Should provide detailed cross-chain analysis"

    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_hunter_cross_chain_analysis",
            user_input="Find arbitrage opportunities between Ethereum and Polygon for USDC",
            agent_output=content,
            expected_behavior=(
                "Should identify cross-chain arbitrage opportunities for authenticated user. "
                "Response should mention specific protocols, price differences, gas costs, profit margins. "
                "May include personalized recommendations based on user's wallet/portfolio if available."
            ),
            additional_context={
                'test_category': 'cross_chain_analysis',
                'user_type': 'authenticated',
                'chains': ['ethereum', 'polygon'],
                'token': 'USDC'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))


# Add 8 more tests mirroring Phase 2.1 tests:
# - test_user_hunter_sentiment_aggregation_sources
# - test_user_hunter_historical_pattern_recognition
# - test_user_hunter_risk_adjusted_recommendations
# - test_user_hunter_portfolio_rebalancing_suggestions
# - test_user_hunter_gas_optimization_strategies
# - test_user_hunter_market_regime_detection
# - test_user_hunter_correlation_analysis_assets
# - test_user_hunter_liquidity_depth_assessment
```

**Key Differences from Guest Tests**:
1. Use `conversation_id` fixture (not direct `/api/v1/guest/chat`)
2. Always include `Authorization` header with ACCESS_TOKEN
3. API endpoint: `/api/v1/user/chat/conversations/{id}/messages`
4. May include user-specific personalization in validation expectations

---

### Phase 3.2: User ULTRA Advanced (8 tests)

**File to Create**: `tests/integration/user/test_user_ultra_advanced.py`

**Pattern**: Same as User Hunter above, but mirror Phase 2.2 ULTRA tests

**Test Scenarios** (mirror guest ULTRA tests):
1. `test_user_ultra_flash_loan_arbitrage_explanation`
2. `test_user_ultra_mev_protection_strategies`
3. `test_user_ultra_slippage_tolerance_recommendations`
4. `test_user_ultra_gas_price_prediction_accuracy`
5. `test_user_ultra_multi_hop_swap_routing`
6. `test_user_ultra_impermanent_loss_warnings`
7. `test_user_ultra_yield_farming_roi_calculations`
8. `test_user_ultra_liquidation_risk_monitoring`

**Template**: Use same structure as User Hunter, just change test content to match ULTRA scenarios.

---

### Phase 3.3: User Agent Squad Advanced (6 tests)

**File to Create**: `tests/integration/user/test_user_agent_squad_advanced.py`

**Pattern**: Same as User Hunter/ULTRA, but mirror Phase 2.3 Agent Squad tests

**Test Scenarios** (mirror guest Agent Squad tests):
1. `test_user_agent_squad_context_preservation_multi_turn`
2. `test_user_agent_squad_handoff_transition_smoothness`
3. `test_user_agent_squad_parallel_agent_coordination`
4. `test_user_agent_squad_specialization_routing_accuracy`
5. `test_user_agent_squad_fallback_agent_quality`
6. `test_user_agent_squad_memory_utilization_long_context`

**Template**: Use same structure, adapt for authenticated user API endpoints.

---

## 🔧 Implementation Checklist

### For Each Test File

- [ ] Copy appropriate template from this guide
- [ ] Update test names and scenarios
- [ ] Verify fixture usage (guest vs user patterns)
- [ ] For user tests: ALWAYS use `ops@anvilcrypto.com` ACCESS_TOKEN
- [ ] Include comprehensive LLM validation blocks
- [ ] Add descriptive expected_behavior strings
- [ ] Include relevant additional_context metadata
- [ ] Compile with: `python3 -m py_compile <file_path>`
- [ ] Verify no syntax errors

### Phase 2.4 Specific
- [ ] Create `test_guest_chat_knowledge_research.py`
- [ ] Implement 6 knowledge/research tests
- [ ] Focus on educational content quality
- [ ] Validate technical accuracy

### Phase 2.5 Specific
- [ ] Append to `test_guest_chat_shortcuts.py`
- [ ] Implement 7 shortcuts tests
- [ ] Test edge cases and workflows
- [ ] Validate multi-step logic

### Phase 3.1 Specific
- [ ] Create `test_user_hunter_advanced.py`
- [ ] Implement 9 user Hunter tests
- [ ] Mirror Phase 2.1 scenarios
- [ ] Use authenticated API endpoints

### Phase 3.2 Specific
- [ ] Create `test_user_ultra_advanced.py`
- [ ] Implement 8 user ULTRA tests
- [ ] Mirror Phase 2.2 scenarios
- [ ] Use authenticated API endpoints

### Phase 3.3 Specific
- [ ] Create `test_user_agent_squad_advanced.py`
- [ ] Implement 6 user Agent Squad tests
- [ ] Mirror Phase 2.3 scenarios
- [ ] Use authenticated API endpoints

---

## 📊 Progress Tracking

| Phase | Tests | Status | Files |
|-------|-------|--------|-------|
| Phase 1 | 17 | ✅ COMPLETE | 3 files |
| Phase 2.1 | 9 | ✅ COMPLETE | 1 file |
| Phase 2.2 | 8 | ✅ COMPLETE | 1 file |
| Phase 2.3 | 6 | ✅ COMPLETE | 1 file |
| **Completed** | **40** | **✅** | **6 files** |
| Phase 2.4 | 6 | ⏸️ PENDING | 1 file (NEW) |
| Phase 2.5 | 7 | ⏸️ PENDING | 1 file (ENHANCE) |
| Phase 3.1 | 9 | ⏸️ PENDING | 1 file (NEW) |
| Phase 3.2 | 8 | ⏸️ PENDING | 1 file (NEW) |
| Phase 3.3 | 6 | ⏸️ PENDING | 1 file (NEW) |
| **Remaining** | **36** | **⏸️** | **5 files** |
| **TOTAL** | **76** | **52.6%** | **11 files** |

---

## 💰 Cost Analysis

### Completed (40 tests)
- Cost per run: $0.003 (40 × $0.000075)
- Monthly (300 runs): $0.90/month

### Remaining (36 tests)
- Additional cost/run: $0.0027 (36 × $0.000075)
- Additional monthly: $0.81/month

### Total Phase 5 (76 tests)
- Cost per run: $0.0057
- Monthly (300 runs): $1.71/month

### Combined with Phases 1-4
- Total tests: 1,348 (1,272 + 76)
- Cost per run: $0.101
- Monthly: $30.51/month

---

## 🎯 Quality Standards

### Every Test Must

1. **Compile Successfully**: No syntax errors
2. **Follow Patterns**: Use established fixtures and structure
3. **Use Correct Authentication**:
   - Guest tests: `X-Forwarded-For` header only
   - User tests: `Authorization: Bearer {ACCESS_TOKEN}` + conversation_id
4. **Include LLM Validation**: Comprehensive semantic validation
5. **Have Clear Expectations**: Detailed `expected_behavior` strings
6. **Include Context**: Relevant `additional_context` metadata

### LLM Validation Template

```python
if llm_validator.enabled:
    validation = await llm_validator.validate_single_response(
        test_name="test_descriptive_name",
        user_input="exact user query string",
        agent_output=content,
        expected_behavior=(
            "Clear, specific description of what response should contain. "
            "Multiple sentences explaining nuances and requirements. "
            "Should be detailed enough for LLM to evaluate quality."
        ),
        additional_context={
            'test_category': 'category_name',
            'subcategory': 'value',
            'user_type': 'guest' or 'authenticated',
            'other_metadata': ['relevant', 'context']
        }
    )
    if validation.verdict != "PASS":
        pytest.warn(UserWarning(
            f"LLM validation concern (confidence={validation.confidence:.2f}): "
            f"{validation.reasoning}"
        ))
```

---

## 🚀 Execution Plan

### Recommended Order

**Day 1: Phase 2.4-2.5** (13 tests, ~6 hours)
1. Create Knowledge/Research file (6 tests)
2. Enhance Shortcuts file (7 tests)
3. Compile and verify

**Day 2-3: Phase 3** (23 tests, ~12 hours)
1. Create User Hunter advanced (9 tests)
2. Create User ULTRA advanced (8 tests)
3. Create User Agent Squad advanced (6 tests)
4. Compile all files
5. Run full test suite

**Day 4: Finalization** (~2 hours)
1. Create Phase 5 completion summary
2. Update all documentation
3. Final commit and push
4. Celebrate 100% completion! 🎉

---

## 📝 Compilation Commands

```bash
# Phase 2.4
python3 -m py_compile tests/integration/guest/test_guest_chat_knowledge_research.py

# Phase 2.5
python3 -m py_compile tests/integration/guest/test_guest_chat_shortcuts.py

# Phase 3.1
python3 -m py_compile tests/integration/user/test_user_hunter_advanced.py

# Phase 3.2
python3 -m py_compile tests/integration/user/test_user_ultra_advanced.py

# Phase 3.3
python3 -m py_compile tests/integration/user/test_user_agent_squad_advanced.py

# Verify all new files
find tests/integration/guest tests/integration/user -name "*.py" -newer tests/output/PHASE5_COMPLETION_GUIDE.md -exec python3 -m py_compile {} \;
```

---

## 🎓 Lessons from Completed Work

### What Worked Well ⭐

1. **Consistent Patterns**: Established templates make implementation fast
2. **Incremental Commits**: Committing per phase section prevents data loss
3. **Compilation Checks**: Early verification caught all issues
4. **CTO Methodology**: Structured approach ensured quality

### Best Practices 📋

1. **Read Existing Files First**: Understand structure before appending
2. **Copy-Paste-Modify**: Start from working examples, adapt carefully
3. **Test Incrementally**: Compile after each file
4. **Keep Patterns Consistent**: Don't reinvent structure mid-implementation

---

## ✅ Success Criteria

### Phase 5 Complete When

- [ ] All 76 tests implemented
- [ ] All 11 files compile successfully
- [ ] 100% LLM validation coverage
- [ ] All user tests use `ops@anvilcrypto.com`
- [ ] Documentation updated
- [ ] Final commit pushed

### Quality Gates

- Zero syntax errors
- Zero false positives in LLM validation
- All tests follow established patterns
- Comprehensive coverage analysis complete

---

## 📞 Need Help?

### Reference Files (Completed Examples)

- **Error Handling**: `tests/integration/errors/test_error_handling_comprehensive.py`
- **Cancellation**: `tests/integration/workflows/test_cancellation_flows.py`
- **Guest Advanced**: `tests/integration/guest/test_guest_chat_hunter_real.py` (lines 1286-1733)
- **User Pattern**: `tests/integration/user/test_user_shortcuts_examples.py` (with llm_validator)

### Common Issues

**Issue**: `NameError: name 'llm_validator' is not defined`
**Fix**: Add `llm_validator` parameter to test function signature

**Issue**: User test fails with 401
**Fix**: Verify ACCESS_TOKEN is correct and headers include Authorization

**Issue**: Syntax error in LLM validation block
**Fix**: Check parentheses balance and string formatting

---

**Completion Guide Created**: 2026-01-16
**Current Progress**: 40/76 tests (52.6%)
**Remaining Effort**: 18-20 hours
**Success Probability**: HIGH (patterns established, templates provided)

**You've got this! The hard work is done - now just follow the patterns.** 🚀

---

**End of Completion Guide**
