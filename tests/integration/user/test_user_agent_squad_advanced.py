"""
Integration tests for advanced Agent Squad features with authenticated users.

All tests use ops@anvilcrypto.com (registered user with active sessions).
Tests mirror guest Agent Squad tests but validate user-specific features.
"""

import pytest
import pytest_asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport

from app.run import make_app

# Access token for ops@anvilcrypto.com (expires 2027-01-10)
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
        json={"title": "Agent Squad Advanced Test", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_agent_squad_context_preservation_multi_turn(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Agent Squad context preservation across multiple turns for authenticated user."""
    # Turn 1: Initial question
    r1 = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Tell me about Aave lending protocol", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert r1.status_code in (200, 201)

    # Turn 2: Follow-up referring to previous context
    r2 = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "What are its main risks?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert r2.status_code in (200, 201)

    # Turn 3: Comparison requiring full context
    r3 = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Compare it to Compound", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert r3.status_code in (200, 201)

    data = r3.json()
    content = data["agent_message"]["content"]

    assert len(content) > 80, "Should provide contextual comparison"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_agent_squad_context_preservation_multi_turn",
            user_input="Compare it to Compound (referring to Aave from previous messages)",
            agent_output=content,
            expected_behavior=(
                "Should compare Aave and Compound based on conversation history. "
                "Response should demonstrate context awareness by referencing previous discussion "
                "about Aave and its risks when making the comparison. Should not ask 'what protocol?'"
            ),
            additional_context={
                'test_category': 'context_preservation',
                'user_type': 'authenticated',
                'turns': 3,
                'conversation_flow': 'Aave -> Risks -> Compare to Compound'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "agent_squad", {
        "test_id": "user_agent_squad_context_preservation_001",
        "s_multistep": True,
        "input": "Multi-turn: 1) Tell me about Aave 2) What are its main risks? 3) Compare it to Compound",
        "output": content,
        "test_label_sequence": "agent_squad_context_preservation",
        "output_expected": "Contextual comparison of Aave and Compound based on conversation history",
        "status": "PASS" if r3.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_agent_squad_handoff_transition_smoothness(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Agent Squad smooth handoff transitions for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={
            "content": "What's the current ETH price and should I buy or provide liquidity?",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 100, "Should provide comprehensive response"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_agent_squad_handoff_transition_smoothness",
            user_input="What's the current ETH price and should I buy or provide liquidity?",
            agent_output=content,
            expected_behavior=(
                "Should handle handoff between Hunter AI (price info) and ULTRA (strategy advice). "
                "Response should flow naturally without explicitly mentioning agent switching. "
                "Should integrate price data with actionable strategy recommendations."
            ),
            additional_context={
                'test_category': 'agent_handoff',
                'user_type': 'authenticated',
                'agents_involved': ['hunter', 'ultra']
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "agent_squad", {
        "test_id": "user_agent_squad_handoff_transition_002",
        "s_multistep": False,
        "input": "What's the current ETH price and should I buy or provide liquidity?",
        "output": content,
        "test_label_sequence": "agent_squad_handoff_transition",
        "output_expected": "Smooth handoff between Hunter AI price data and ULTRA strategy recommendations",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_agent_squad_parallel_agent_coordination(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Agent Squad parallel coordination for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={
            "content": "Analyze Bitcoin from technical, fundamental, and sentiment perspectives",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 150, "Should provide multi-dimensional analysis"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_agent_squad_parallel_agent_coordination",
            user_input="Analyze Bitcoin from technical, fundamental, and sentiment perspectives",
            agent_output=content,
            expected_behavior=(
                "Should coordinate multiple analysis dimensions (technical, fundamental, sentiment). "
                "Response should integrate insights from different analytical perspectives. "
                "Should provide holistic view without obvious agent separation."
            ),
            additional_context={
                'test_category': 'parallel_coordination',
                'user_type': 'authenticated',
                'analysis_types': ['technical', 'fundamental', 'sentiment']
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "agent_squad", {
        "test_id": "user_agent_squad_parallel_coordination_003",
        "s_multistep": False,
        "input": "Analyze Bitcoin from technical, fundamental, and sentiment perspectives",
        "output": content,
        "test_label_sequence": "agent_squad_parallel_coordination",
        "output_expected": "Multi-dimensional Bitcoin analysis integrating technical, fundamental, and sentiment insights",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_agent_squad_specialization_routing_accuracy(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Agent Squad routing accuracy for complex queries for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={
            "content": "I want to explore DeFi yields but I'm worried about smart contract risks. "
                      "What should I consider for Curve vs Convex?",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 100, "Should provide specialized analysis"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_agent_squad_specialization_routing_accuracy",
            user_input="I want to explore DeFi yields but I'm worried about smart contract risks. "
                      "What should I consider for Curve vs Convex?",
            agent_output=content,
            expected_behavior=(
                "Should route to appropriate specialist agents (yield analysis + risk assessment). "
                "Response should address both yield opportunities and security concerns. "
                "Should compare Curve vs Convex with balanced perspective."
            ),
            additional_context={
                'test_category': 'specialization_routing',
                'user_type': 'authenticated',
                'query_complexity': 'high',
                'domains': ['yield_farming', 'security', 'protocol_comparison']
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "agent_squad", {
        "test_id": "user_agent_squad_specialization_routing_004",
        "s_multistep": False,
        "input": "I want to explore DeFi yields but I'm worried about smart contract risks. What should I consider for Curve vs Convex?",
        "output": content,
        "test_label_sequence": "agent_squad_specialization_routing",
        "output_expected": "Specialized analysis routing to yield and risk agents with Curve vs Convex comparison",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_agent_squad_fallback_agent_quality(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Agent Squad fallback handling for ambiguous intents for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={
            "content": "What's happening with crypto today?",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 80, "Should provide useful response"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_agent_squad_fallback_agent_quality",
            user_input="What's happening with crypto today?",
            agent_output=content,
            expected_behavior=(
                "Should handle ambiguous query gracefully. Response should provide relevant "
                "crypto market overview (prices, news, trends) without asking for clarification. "
                "Fallback agent should provide value even with vague query."
            ),
            additional_context={
                'test_category': 'fallback_handling',
                'user_type': 'authenticated',
                'query_ambiguity': 'high'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "agent_squad", {
        "test_id": "user_agent_squad_fallback_quality_005",
        "s_multistep": False,
        "input": "What's happening with crypto today?",
        "output": content,
        "test_label_sequence": "agent_squad_fallback_handling",
        "output_expected": "Graceful handling of ambiguous query with relevant crypto market overview",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_agent_squad_memory_utilization_long_context(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Agent Squad memory utilization in long conversations for authenticated user."""
    # Simulate a 9-turn conversation building context
    topics = [
        "Tell me about Uniswap V3",
        "How does concentrated liquidity work?",
        "What are the fee tiers?",
        "Compare it to V2",
        "What about capital efficiency?",
        "Explain position management",
        "What are the risks?",
        "How do I provide liquidity?",
        "Based on everything we discussed, should a beginner start with V2 or V3?"
    ]

    responses = []
    for topic in topics:
        r = await client.post(
            f"/api/v1/user/chat/conversations/{conversation_id}/messages",
            json={"content": topic, "language": "en"},
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        )
        assert r.status_code in (200, 201)
        responses.append(r.json())

    # Validate final response that should synthesize the entire conversation
    final_content = responses[-1]["agent_message"]["content"]
    assert len(final_content) > 100, "Should provide comprehensive recommendation"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_agent_squad_memory_utilization_long_context",
            user_input="Based on everything we discussed, should a beginner start with V2 or V3?",
            agent_output=final_content,
            expected_behavior=(
                "Should synthesize insights from entire 9-turn conversation about Uniswap V2 vs V3. "
                "Response should reference key points discussed (concentrated liquidity, fee tiers, "
                "capital efficiency, risks) and provide informed recommendation for beginners. "
                "Should demonstrate long-context memory retention."
            ),
            additional_context={
                'test_category': 'long_context_memory',
                'user_type': 'authenticated',
                'conversation_turns': 9,
                'topic': 'uniswap_v2_vs_v3'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "agent_squad", {
        "test_id": "user_agent_squad_memory_utilization_006",
        "s_multistep": True,
        "input": "9-turn conversation: Uniswap V3 -> concentrated liquidity -> fee tiers -> V2 comparison -> capital efficiency -> position management -> risks -> providing liquidity -> beginner recommendation",
        "output": final_content,
        "test_label_sequence": "agent_squad_long_context_memory",
        "output_expected": "Synthesized recommendation for beginners based on entire conversation context",
        "status": "PASS" if responses[-1] and len(final_content) > 100 else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })
