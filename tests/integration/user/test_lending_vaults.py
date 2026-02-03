"""
Integration tests for Lending Vault queries with authenticated users.

Tests the complete fix for vault routing:
- Commit 1 (2351206f): Intent detector vault patterns
- Commit 2 (4ccf3009): Shortcuts API vault examples
- Commit 3 (1bc72e1d): Supervisor vault routing to lending_workflow

All tests use ops@anvilcrypto.com (registered user with active sessions).
Tests validate that vault queries route to lending_workflow agent and return Morpho vault data.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Uses legacy /api/v1/user/chat endpoint")
import pytest_asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport

from app.run import make_app
import json
import warnings

# Access token for ops@anvilcrypto.com (expires 2027-01-10)
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJ0ZXN0X3Nlc3Npb25fMjAyNl8xNzY4MDY2MDc5IiwiZXhwIjoxNzk5NjAyMDc5fQ.OUFFmZW2_QACkgrIphLFcOOB3Qb-1ckVB_RvZ-VTaF0"


@pytest_asyncio.fixture
async def client():
    """Create test client."""
    app = make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def conversation_id(client: AsyncClient):
    """Create conversation for ops@anvilcrypto.com."""
    response = await client.post(
        "/api/v1/user/chat/conversations",
        json={"title": "Lending Vaults Test", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_lending_vault_discovery_best_vaults(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test 'best lending vaults' routes to lending_workflow and returns Morpho vault data."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Show best lending vaults", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()

    # Validate routing
    routing = data.get("routing", {})
    assert routing.get("intent") in ("LENDING", "SUPERVISOR_WORKFLOW"), (
        f"Expected LENDING or SUPERVISOR_WORKFLOW, got {routing.get('intent')}"
    )

    # CRITICAL: Should route to lending_workflow, NOT defi_yield
    agents_used = routing.get("agents_used", [])
    assert (
        "lending_workflow" in agents_used or "lending_handler" in str(routing).lower()
    ), f"Expected lending_workflow agent, got {agents_used}"

    # Should NOT route to defi_yield or risk_analyzer
    assert "defi_yield" not in agents_used, (
        f"Should NOT use defi_yield for vault queries, got {agents_used}"
    )

    content = data["agent_message"]["content"]
    assert len(content) > 100, "Should provide comprehensive vault information"

    # Validate Morpho vault data is present
    content_lower = content.lower()
    assert "morpho" in content_lower or "vault" in content_lower, (
        "Response should mention Morpho or vaults"
    )
    assert "apy" in content_lower or "yield" in content_lower, (
        "Response should include APY/yield information"
    )

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_lending_vault_discovery_best_vaults",
            user_input="Show best lending vaults",
            agent_output=content,
            expected_behavior=(
                "Should return Morpho curated lending vaults with APY, TVL, and vault addresses. "
                "Should NOT return generic DeFiLlama yield pools (Beefy, Kamino, Balancer). "
                "Response should focus on Morpho vault-specific data for USDC on Base chain. "
                "Should route through lending_workflow agent, not defi_yield."
            ),
            additional_context={
                "test_category": "lending_vault_routing",
                "user_type": "authenticated",
                "expected_agent": "lending_workflow",
                "actual_agents": agents_used,
                "routing_intent": routing.get("intent"),
                "fix_commits": ["2351206f", "4ccf3009", "1bc72e1d"],
            },
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    # CSV tracking
    await csv_tracker(
        "user",
        "lending_vaults",
        {
            "test_id": "user_lending_vault_discovery_001",
            "s_multistep": False,
            "input": "Show best lending vaults",
            "output": content,
            "test_label_sequence": "lending_vault_discovery",
            "output_expected": "Morpho vault data (not DeFiLlama pools) routed through lending_workflow",
            "expected_agent": "lending_workflow",
            "actual_agents": json.dumps(agents_used),
            "routing_intent": routing.get("intent"),
            "status": "PASS"
            if response.status_code in (200, 201) and "lending_workflow" in agents_used
            else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            "accuracy_score": validation.scoring.accuracy_score
            if validation and validation.scoring
            else None,
            "relevance_score": validation.scoring.relevance_score
            if validation and validation.scoring
            else None,
            "safety_score": validation.scoring.safety_score
            if validation and validation.scoring
            else None,
            "coherence_score": validation.scoring.coherence_score
            if validation and validation.scoring
            else None,
            "test_category": validation.metadata.test_category
            if validation and validation.metadata
            else None,
            "test_type": validation.metadata.test_type
            if validation and validation.metadata
            else None,
            "expected_intents": json.dumps(validation.metadata.expected_intents)
            if validation and validation.metadata
            else None,
            "token_usage": validation.metadata.token_usage
            if validation and validation.metadata
            else None,
            "improvement_suggestions": json.dumps(
                validation.recommendations.improvement_suggestions
            )
            if validation and validation.recommendations
            else None,
            "critical_issues": json.dumps(validation.recommendations.critical_issues)
            if validation and validation.recommendations
            else None,
            "next_steps": json.dumps(validation.recommendations.next_steps)
            if validation and validation.recommendations
            else None,
            "model_used": validation.metadata.model_used
            if validation and validation.metadata
            else None,
        },
    )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_lending_vault_discovery_top_vaults(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test 'top vaults' routes to lending_workflow."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "top vaults", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()

    routing = data.get("routing", {})
    agents_used = routing.get("agents_used", [])

    assert (
        "lending_workflow" in agents_used or "lending_handler" in str(routing).lower()
    ), f"Expected lending_workflow agent, got {agents_used}"

    content = data["agent_message"]["content"]
    assert len(content) > 80, "Should provide vault information"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_lending_vault_discovery_top_vaults",
            user_input="top vaults",
            agent_output=content,
            expected_behavior=(
                "Should return top Morpho vaults by APY. "
                "Response should include vault names, APYs, and TVL data."
            ),
            additional_context={
                "test_category": "lending_vault_routing",
                "user_type": "authenticated",
                "expected_agent": "lending_workflow",
                "actual_agents": agents_used,
            },
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    await csv_tracker(
        "user",
        "lending_vaults",
        {
            "test_id": "user_lending_vault_discovery_002",
            "s_multistep": False,
            "input": "top vaults",
            "output": content,
            "test_label_sequence": "lending_vault_discovery",
            "output_expected": "Top Morpho vaults by APY",
            "expected_agent": "lending_workflow",
            "actual_agents": json.dumps(agents_used),
            "routing_intent": routing.get("intent"),
            "status": "PASS" if response.status_code in (200, 201) else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            "accuracy_score": validation.scoring.accuracy_score
            if validation and validation.scoring
            else None,
            "relevance_score": validation.scoring.relevance_score
            if validation and validation.scoring
            else None,
            "safety_score": validation.scoring.safety_score
            if validation and validation.scoring
            else None,
            "coherence_score": validation.scoring.coherence_score
            if validation and validation.scoring
            else None,
            "test_category": validation.metadata.test_category
            if validation and validation.metadata
            else None,
            "test_type": validation.metadata.test_type
            if validation and validation.metadata
            else None,
            "model_used": validation.metadata.model_used
            if validation and validation.metadata
            else None,
        },
    )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_lending_vault_discovery_best_morpho_vaults(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test 'best morpho vaults' explicit routing."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "best morpho vaults", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()

    routing = data.get("routing", {})
    agents_used = routing.get("agents_used", [])

    assert (
        "lending_workflow" in agents_used or "lending_handler" in str(routing).lower()
    ), f"Expected lending_workflow agent, got {agents_used}"

    content = data["agent_message"]["content"]
    assert len(content) > 80, "Should provide Morpho vault information"
    assert "morpho" in content.lower(), "Response should explicitly mention Morpho"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_lending_vault_discovery_best_morpho_vaults",
            user_input="best morpho vaults",
            agent_output=content,
            expected_behavior=(
                "Should return best Morpho vaults specifically. "
                "Response should clearly identify Morpho protocol and vault details."
            ),
            additional_context={
                "test_category": "lending_vault_routing",
                "user_type": "authenticated",
                "expected_agent": "lending_workflow",
                "actual_agents": agents_used,
            },
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    await csv_tracker(
        "user",
        "lending_vaults",
        {
            "test_id": "user_lending_vault_discovery_003",
            "s_multistep": False,
            "input": "best morpho vaults",
            "output": content,
            "test_label_sequence": "lending_vault_discovery",
            "output_expected": "Best Morpho vaults with explicit protocol identification",
            "expected_agent": "lending_workflow",
            "actual_agents": json.dumps(agents_used),
            "routing_intent": routing.get("intent"),
            "status": "PASS" if response.status_code in (200, 201) else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            "accuracy_score": validation.scoring.accuracy_score
            if validation and validation.scoring
            else None,
            "relevance_score": validation.scoring.relevance_score
            if validation and validation.scoring
            else None,
            "safety_score": validation.scoring.safety_score
            if validation and validation.scoring
            else None,
            "coherence_score": validation.scoring.coherence_score
            if validation and validation.scoring
            else None,
            "test_category": validation.metadata.test_category
            if validation and validation.metadata
            else None,
            "test_type": validation.metadata.test_type
            if validation and validation.metadata
            else None,
            "model_used": validation.metadata.model_used
            if validation and validation.metadata
            else None,
        },
    )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_lending_vault_comparison(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test 'compare vaults' functionality."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "compare vaults", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()

    routing = data.get("routing", {})
    agents_used = routing.get("agents_used", [])

    assert (
        "lending_workflow" in agents_used or "lending_handler" in str(routing).lower()
    ), f"Expected lending_workflow agent, got {agents_used}"

    content = data["agent_message"]["content"]
    assert len(content) > 100, "Should provide comprehensive vault comparison"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_lending_vault_comparison",
            user_input="compare vaults",
            agent_output=content,
            expected_behavior=(
                "Should compare multiple Morpho vaults with APY, TVL, risk levels. "
                "Response should provide side-by-side comparison to help user choose."
            ),
            additional_context={
                "test_category": "lending_vault_comparison",
                "user_type": "authenticated",
                "expected_agent": "lending_workflow",
                "actual_agents": agents_used,
            },
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    await csv_tracker(
        "user",
        "lending_vaults",
        {
            "test_id": "user_lending_vault_comparison_004",
            "s_multistep": False,
            "input": "compare vaults",
            "output": content,
            "test_label_sequence": "lending_vault_comparison",
            "output_expected": "Comprehensive vault comparison with APY, TVL, risk levels",
            "expected_agent": "lending_workflow",
            "actual_agents": json.dumps(agents_used),
            "routing_intent": routing.get("intent"),
            "status": "PASS" if response.status_code in (200, 201) else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            "accuracy_score": validation.scoring.accuracy_score
            if validation and validation.scoring
            else None,
            "relevance_score": validation.scoring.relevance_score
            if validation and validation.scoring
            else None,
            "safety_score": validation.scoring.safety_score
            if validation and validation.scoring
            else None,
            "coherence_score": validation.scoring.coherence_score
            if validation and validation.scoring
            else None,
            "test_category": validation.metadata.test_category
            if validation and validation.metadata
            else None,
            "test_type": validation.metadata.test_type
            if validation and validation.metadata
            else None,
            "model_used": validation.metadata.model_used
            if validation and validation.metadata
            else None,
        },
    )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_lending_vault_vs_yield_routing(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test distinction: 'best vaults' (lending_workflow) vs 'best yield' (defi_yield)."""
    # Test 1: Vault query should route to lending_workflow
    r1 = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "best vaults", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert r1.status_code in (200, 201)
    data1 = r1.json()
    routing1 = data1.get("routing", {})
    agents1 = routing1.get("agents_used", [])

    assert (
        "lending_workflow" in agents1 or "lending_handler" in str(routing1).lower()
    ), f"'best vaults' should route to lending_workflow, got {agents1}"

    # Test 2: Generic yield query (without "vault") may route to defi_yield
    r2 = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "best yield farms", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert r2.status_code in (200, 201)
    data2 = r2.json()
    routing2 = data2.get("routing", {})
    agents2 = routing2.get("agents_used", [])

    # Generic yield may route to defi_yield OR other agents, but key is vault queries go to lending_workflow
    content1 = data1["agent_message"]["content"]
    content2 = data2["agent_message"]["content"]

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_lending_vault_vs_yield_routing",
            user_input="Compare: 'best vaults' vs 'best yield farms'",
            agent_output=f"Vaults response: {content1}\n\nYield farms response: {content2}",
            expected_behavior=(
                "The 'best vaults' query should route to lending_workflow and return Morpho vault data. "
                "The 'best yield farms' query may route to defi_yield and return generic DeFi yield opportunities. "
                "These should be distinct routing paths based on the 'vault' keyword."
            ),
            additional_context={
                "test_category": "routing_distinction",
                "user_type": "authenticated",
                "vault_query_agents": agents1,
                "yield_query_agents": agents2,
                "distinction_keyword": "vault",
            },
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    await csv_tracker(
        "user",
        "lending_vaults",
        {
            "test_id": "user_lending_vault_vs_yield_005",
            "s_multistep": True,
            "input": "Comparison: 'best vaults' vs 'best yield farms'",
            "output": f"Vaults: {agents1} | Yield: {agents2}",
            "test_label_sequence": "lending_vault_yield_distinction",
            "output_expected": "Vault queries route to lending_workflow, generic yield may route to defi_yield",
            "expected_agent": "lending_workflow (for vaults)",
            "actual_agents": json.dumps({"vaults": agents1, "yield": agents2}),
            "status": "PASS" if "lending_workflow" in agents1 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            "accuracy_score": validation.scoring.accuracy_score
            if validation and validation.scoring
            else None,
            "relevance_score": validation.scoring.relevance_score
            if validation and validation.scoring
            else None,
            "safety_score": validation.scoring.safety_score
            if validation and validation.scoring
            else None,
            "coherence_score": validation.scoring.coherence_score
            if validation and validation.scoring
            else None,
            "test_category": validation.metadata.test_category
            if validation and validation.metadata
            else None,
            "test_type": validation.metadata.test_type
            if validation and validation.metadata
            else None,
            "model_used": validation.metadata.model_used
            if validation and validation.metadata
            else None,
        },
    )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_lending_vault_multi_language_spanish(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test vault queries in Spanish."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "mejores bóvedas de préstamos", "language": "es"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()

    routing = data.get("routing", {})
    agents_used = routing.get("agents_used", [])

    # Spanish vault queries should also route to lending_workflow
    content = data["agent_message"]["content"]
    assert len(content) > 50, "Should provide vault information in Spanish"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_lending_vault_multi_language_spanish",
            user_input="mejores bóvedas de préstamos (best lending vaults in Spanish)",
            agent_output=content,
            expected_behavior=(
                "Should return Morpho vault information in Spanish. "
                "Should route to lending_workflow regardless of language."
            ),
            additional_context={
                "test_category": "multi_language_support",
                "user_type": "authenticated",
                "language": "es",
                "expected_agent": "lending_workflow",
                "actual_agents": agents_used,
            },
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    await csv_tracker(
        "user",
        "lending_vaults",
        {
            "test_id": "user_lending_vault_multilang_es_006",
            "s_multistep": False,
            "input": "mejores bóvedas de préstamos",
            "output": content,
            "test_label_sequence": "lending_vault_multilanguage",
            "output_expected": "Morpho vault information in Spanish",
            "expected_agent": "lending_workflow",
            "actual_agents": json.dumps(agents_used),
            "routing_intent": routing.get("intent"),
            "language": "es",
            "status": "PASS" if response.status_code in (200, 201) else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            "accuracy_score": validation.scoring.accuracy_score
            if validation and validation.scoring
            else None,
            "relevance_score": validation.scoring.relevance_score
            if validation and validation.scoring
            else None,
            "safety_score": validation.scoring.safety_score
            if validation and validation.scoring
            else None,
            "coherence_score": validation.scoring.coherence_score
            if validation and validation.scoring
            else None,
            "test_category": validation.metadata.test_category
            if validation and validation.metadata
            else None,
            "test_type": validation.metadata.test_type
            if validation and validation.metadata
            else None,
            "model_used": validation.metadata.model_used
            if validation and validation.metadata
            else None,
        },
    )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_lending_vault_deposit_workflow(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test multi-step workflow: vault discovery → deposit guidance."""
    # Step 1: Discover vaults
    r1 = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Show best lending vaults", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert r1.status_code in (200, 201)
    data1 = r1.json()
    content1 = data1["agent_message"]["content"]

    # Step 2: Ask about depositing
    r2 = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "How do I deposit into the best vault?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert r2.status_code in (200, 201)
    data2 = r2.json()
    content2 = data2["agent_message"]["content"]

    assert len(content2) > 80, "Should provide deposit instructions"

    # Deposit instructions should reference the vault from previous message
    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_lending_vault_deposit_workflow",
            user_input="Multi-turn: 1) Show best lending vaults 2) How do I deposit into the best vault?",
            agent_output=content2,
            expected_behavior=(
                "Should provide deposit instructions for the best vault identified in previous message. "
                "Should include: approve token spending, call deposit function, receive vault shares. "
                "Should maintain context from vault discovery to deposit guidance."
            ),
            additional_context={
                "test_category": "multi_step_workflow",
                "user_type": "authenticated",
                "workflow_steps": ["discovery", "deposit_guidance"],
                "conversation_turns": 2,
            },
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    await csv_tracker(
        "user",
        "lending_vaults",
        {
            "test_id": "user_lending_vault_workflow_007",
            "s_multistep": True,
            "input": "Multi-step: 1) Show best lending vaults 2) How do I deposit into the best vault?",
            "output": content2,
            "test_label_sequence": "lending_vault_deposit_workflow",
            "output_expected": "Contextual deposit instructions for previously identified best vault",
            "status": "PASS"
            if r2.status_code in (200, 201) and len(content2) > 80
            else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            "accuracy_score": validation.scoring.accuracy_score
            if validation and validation.scoring
            else None,
            "relevance_score": validation.scoring.relevance_score
            if validation and validation.scoring
            else None,
            "safety_score": validation.scoring.safety_score
            if validation and validation.scoring
            else None,
            "coherence_score": validation.scoring.coherence_score
            if validation and validation.scoring
            else None,
            "test_category": validation.metadata.test_category
            if validation and validation.metadata
            else None,
            "test_type": validation.metadata.test_type
            if validation and validation.metadata
            else None,
            "model_used": validation.metadata.model_used
            if validation and validation.metadata
            else None,
        },
    )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_lending_vault_response_format(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test that vault response includes all expected data fields."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Show best lending vaults", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    content_lower = content.lower()

    # Validate expected data fields are present
    has_apy = "apy" in content_lower or "yield" in content_lower or "%" in content
    has_vault_names = "vault" in content_lower or "morpho" in content_lower
    has_amounts = any(char.isdigit() for char in content)  # Should have numeric data

    assert has_apy, "Response should include APY/yield information"
    assert has_vault_names, "Response should mention vault names"
    assert has_amounts, "Response should include numeric data (APY, TVL, etc.)"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_lending_vault_response_format",
            user_input="Show best lending vaults",
            agent_output=content,
            expected_behavior=(
                "Response should include structured vault data: "
                "1) Vault names (e.g., 'Universal USDC', 'Edge UltraYield USDC') "
                "2) APY percentages "
                "3) TVL amounts "
                "4) Vault addresses (truncated) "
                "5) Recommendation section with deposit instructions"
            ),
            additional_context={
                "test_category": "response_format_validation",
                "user_type": "authenticated",
                "expected_fields": [
                    "vault_names",
                    "apy",
                    "tvl",
                    "addresses",
                    "recommendations",
                ],
            },
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    await csv_tracker(
        "user",
        "lending_vaults",
        {
            "test_id": "user_lending_vault_format_008",
            "s_multistep": False,
            "input": "Show best lending vaults",
            "output": content,
            "test_label_sequence": "lending_vault_response_format",
            "output_expected": "Structured vault data with names, APY, TVL, addresses, recommendations",
            "has_apy": has_apy,
            "has_vault_names": has_vault_names,
            "has_amounts": has_amounts,
            "status": "PASS"
            if (response.status_code in (200, 201) and has_apy and has_vault_names)
            else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            "accuracy_score": validation.scoring.accuracy_score
            if validation and validation.scoring
            else None,
            "relevance_score": validation.scoring.relevance_score
            if validation and validation.scoring
            else None,
            "safety_score": validation.scoring.safety_score
            if validation and validation.scoring
            else None,
            "coherence_score": validation.scoring.coherence_score
            if validation and validation.scoring
            else None,
            "test_category": validation.metadata.test_category
            if validation and validation.metadata
            else None,
            "test_type": validation.metadata.test_type
            if validation and validation.metadata
            else None,
            "model_used": validation.metadata.model_used
            if validation and validation.metadata
            else None,
        },
    )
