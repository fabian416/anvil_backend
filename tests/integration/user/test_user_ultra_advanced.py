"""
Integration tests for advanced ULTRA features with authenticated users.

All tests use ops@anvilcrypto.com (registered user with active sessions).
Tests mirror guest ULTRA tests but validate user-specific features.
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
        json={"title": "ULTRA Advanced Test", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_ultra_flash_loan_arbitrage_explanation(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test ULTRA flash loan arbitrage explanation for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Explain how flash loan arbitrage works and the risks involved", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 150, "Should provide detailed flash loan explanation"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_ultra_flash_loan_arbitrage_explanation",
            user_input="Explain how flash loan arbitrage works and the risks involved",
            agent_output=content,
            expected_behavior=(
                "Should explain flash loan mechanics, arbitrage opportunities, and associated risks. "
                "Response should cover uncollateralized loans, same-transaction execution, "
                "profit potential, and failure risks. Should be technically accurate."
            ),
            additional_context={
                'test_category': 'flash_loan_education',
                'user_type': 'authenticated',
                'topic': 'arbitrage'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "ultra", {
        "test_id": "user_ultra_flash_loan_001",
        "s_multistep": False,
        "input": "Explain how flash loan arbitrage works and the risks involved",
        "output": content,
        "test_label_sequence": "ultra_flash_loan",
        "output_expected": "Flash loan mechanics with arbitrage opportunities and risk analysis",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_ultra_mev_protection_strategies(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test ULTRA MEV protection strategies for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "How can I protect my transactions from MEV bots using Flashbots?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 100, "Should provide MEV protection strategies"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_ultra_mev_protection_strategies",
            user_input="How can I protect my transactions from MEV bots using Flashbots?",
            agent_output=content,
            expected_behavior=(
                "Should explain MEV (Maximum Extractable Value) and protection strategies. "
                "Response should cover Flashbots, private transactions, RPC endpoints, "
                "and practical steps for MEV protection."
            ),
            additional_context={
                'test_category': 'mev_protection',
                'user_type': 'authenticated',
                'tool': 'flashbots'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "ultra", {
        "test_id": "user_ultra_mev_protection_002",
        "s_multistep": False,
        "input": "How can I protect my transactions from MEV bots using Flashbots?",
        "output": content,
        "test_label_sequence": "ultra_mev_protection",
        "output_expected": "MEV protection strategies with Flashbots, private transactions, and RPC endpoints",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_ultra_slippage_tolerance_recommendations(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test ULTRA slippage tolerance recommendations for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "What slippage tolerance should I set for a $10,000 ETH swap on Uniswap?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 80, "Should provide slippage recommendations"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_ultra_slippage_tolerance_recommendations",
            user_input="What slippage tolerance should I set for a $10,000 ETH swap on Uniswap?",
            agent_output=content,
            expected_behavior=(
                "Should provide slippage tolerance recommendations for large swap ($10k). "
                "Response should consider liquidity depth, market conditions, typical slippage rates, "
                "and provide specific percentage recommendations (e.g., 0.5%-2%)."
            ),
            additional_context={
                'test_category': 'slippage_recommendation',
                'user_type': 'authenticated',
                'swap_size': '$10000',
                'asset': 'ETH'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "ultra", {
        "test_id": "user_ultra_slippage_tolerance_003",
        "s_multistep": False,
        "input": "What slippage tolerance should I set for a $10,000 ETH swap on Uniswap?",
        "output": content,
        "test_label_sequence": "ultra_slippage_tolerance",
        "output_expected": "Slippage tolerance recommendations considering liquidity depth and market conditions",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_ultra_gas_price_prediction_accuracy(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test ULTRA gas price prediction for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Estimate gas costs for swapping tokens on Ethereum right now", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 50, "Should provide gas estimation"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_ultra_gas_price_prediction_accuracy",
            user_input="Estimate gas costs for swapping tokens on Ethereum right now",
            agent_output=content,
            expected_behavior=(
                "Should provide current gas price estimates for Ethereum token swaps. "
                "Response should mention gas price in gwei, estimated USD cost, "
                "and context about whether gas is currently high/normal/low."
            ),
            additional_context={
                'test_category': 'gas_estimation',
                'user_type': 'authenticated',
                'chain': 'ethereum',
                'operation': 'token_swap'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "ultra", {
        "test_id": "user_ultra_gas_price_prediction_004",
        "s_multistep": False,
        "input": "Estimate gas costs for swapping tokens on Ethereum right now",
        "output": content,
        "test_label_sequence": "ultra_gas_estimation",
        "output_expected": "Current gas price estimates with gwei and USD cost for token swaps",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_ultra_multi_hop_swap_routing(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test ULTRA multi-hop swap routing optimization for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "What's the best route to swap LINK to MATIC with minimal slippage?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 80, "Should provide routing analysis"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_ultra_multi_hop_swap_routing",
            user_input="What's the best route to swap LINK to MATIC with minimal slippage?",
            agent_output=content,
            expected_behavior=(
                "Should analyze optimal routing for LINK to MATIC swap. "
                "Response should mention potential intermediate tokens (e.g., LINK->ETH->MATIC), "
                "compare direct vs multi-hop routes, and explain trade-offs."
            ),
            additional_context={
                'test_category': 'swap_routing',
                'user_type': 'authenticated',
                'from_token': 'LINK',
                'to_token': 'MATIC'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "ultra", {
        "test_id": "user_ultra_multi_hop_swap_routing_005",
        "s_multistep": False,
        "input": "What's the best route to swap LINK to MATIC with minimal slippage?",
        "output": content,
        "test_label_sequence": "ultra_swap_routing",
        "output_expected": "Optimal routing analysis for LINK to MATIC swap with intermediate tokens and trade-offs",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_ultra_impermanent_loss_warnings(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test ULTRA impermanent loss risk disclosure for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Explain impermanent loss risk for providing ETH/USDC liquidity", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 100, "Should provide IL explanation"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_ultra_impermanent_loss_warnings",
            user_input="Explain impermanent loss risk for providing ETH/USDC liquidity",
            agent_output=content,
            expected_behavior=(
                "Should explain impermanent loss (IL) concept for ETH/USDC pair. "
                "Response should cover how IL occurs with price divergence, "
                "magnitude of losses at different price changes, and risk mitigation strategies."
            ),
            additional_context={
                'test_category': 'impermanent_loss',
                'user_type': 'authenticated',
                'pair': 'ETH/USDC'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "ultra", {
        "test_id": "user_ultra_impermanent_loss_006",
        "s_multistep": False,
        "input": "Explain impermanent loss risk for providing ETH/USDC liquidity",
        "output": content,
        "test_label_sequence": "ultra_impermanent_loss",
        "output_expected": "Impermanent loss explanation for ETH/USDC pair with price divergence and risk mitigation",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_ultra_yield_farming_roi_calculations(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test ULTRA yield farming ROI transparency for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Calculate real APY for Curve 3pool considering all fees and IL", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 80, "Should provide ROI calculation"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_ultra_yield_farming_roi_calculations",
            user_input="Calculate real APY for Curve 3pool considering all fees and IL",
            agent_output=content,
            expected_behavior=(
                "Should analyze Curve 3pool yield with comprehensive ROI calculation. "
                "Response should consider trading fees, CRV rewards, gas costs, and IL risks. "
                "Should provide realistic APY estimates, not just headline rates."
            ),
            additional_context={
                'test_category': 'yield_calculation',
                'user_type': 'authenticated',
                'protocol': 'curve',
                'pool': '3pool'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "ultra", {
        "test_id": "user_ultra_yield_farming_roi_007",
        "s_multistep": False,
        "input": "Calculate real APY for Curve 3pool considering all fees and IL",
        "output": content,
        "test_label_sequence": "ultra_yield_calculation",
        "output_expected": "Comprehensive ROI calculation for Curve 3pool with trading fees, CRV rewards, and gas costs",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_ultra_liquidation_risk_monitoring(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test ULTRA liquidation risk monitoring for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "How can I monitor my Aave position to avoid liquidation?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 100, "Should provide liquidation monitoring guidance"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_ultra_liquidation_risk_monitoring",
            user_input="How can I monitor my Aave position to avoid liquidation?",
            agent_output=content,
            expected_behavior=(
                "Should explain liquidation risk monitoring for Aave leveraged positions. "
                "Response should cover health factor monitoring, price alerts, "
                "liquidation thresholds, and preventive actions. Should be practical and actionable."
            ),
            additional_context={
                'test_category': 'liquidation_monitoring',
                'user_type': 'authenticated',
                'protocol': 'aave'
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))

    # CSV tracking
    await csv_tracker("user", "ultra", {
        "test_id": "user_ultra_liquidation_risk_monitoring_008",
        "s_multistep": False,
        "input": "How can I monitor my Aave position to avoid liquidation?",
        "output": content,
        "test_label_sequence": "ultra_liquidation_monitoring",
        "output_expected": "Liquidation risk monitoring guidance with health factor, price alerts, and preventive actions",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    })
