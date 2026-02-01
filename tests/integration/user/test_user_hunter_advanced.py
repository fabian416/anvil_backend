"""
Integration tests for advanced Hunter AI features with authenticated users.

All tests use ops@anvilcrypto.com (registered user with active sessions).
Tests mirror guest Hunter tests but validate user-specific features.
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def conversation_id(client: AsyncClient):
    """Create conversation for ops@anvilcrypto.com."""
    response = await client.post(
        "/api/v1/user/chat/conversations",
        json={"title": "Hunter AI Advanced Test", "language": "en"},
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
    csv_tracker,
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

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_hunter_cross_chain_analysis",
            user_input="Find arbitrage opportunities between Ethereum and Polygon for USDC",
            agent_output=agent_response,
            expected_behavior=(
                "Should identify cross-chain arbitrage opportunities for authenticated user. "
                "Response should mention specific protocols, price differences, gas costs, profit margins. "
                "May include personalized recommendations based on user's wallet/portfolio if available."
            ),
            test_func=self.test_user_hunter_cross_chain_analysis,  # PHASE 3: Custom prompt generation
            additional_context={
                'test_category': 'cross_chain_analysis',
                'user_type': 'authenticated',
                'chains': ['ethereum', 'polygon'],
                'token': 'USDC'
            }
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    # CSV tracking
    await csv_tracker("user", "hunter", {
        "test_id": "user_hunter_cross_chain_001",
        "s_multistep": False,
        "input": "Find arbitrage opportunities between Ethereum and Polygon for USDC",
        "output": content,
        "test_label_sequence": "hunter_cross_chain",
        "output_expected": "Cross-chain arbitrage opportunities with personalized recommendations",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    # Enhanced validation fields (PHASE 3)
    "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
    "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
    "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
    "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
    "test_category": validation.metadata.test_category if validation and validation.metadata else None,
    "test_type": validation.metadata.test_type if validation and validation.metadata else None,
    "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
    "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
    "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
    "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
    "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
    "model_used": validation.metadata.model_used if validation and validation.metadata else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_hunter_sentiment_aggregation_sources(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Hunter AI multi-source sentiment aggregation for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "What's the overall sentiment about Solana across news, Reddit, and Twitter?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 100, "Should provide comprehensive sentiment analysis"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_hunter_sentiment_aggregation_sources",
            user_input="What's the overall sentiment about Solana across news, Reddit, and Twitter?",
            agent_output=agent_response,
            expected_behavior=(
                "Should aggregate sentiment from multiple sources (news, social media). "
                "Response should synthesize different perspectives and provide balanced sentiment analysis. "
                "Should mention specific sources or data points when possible."
            ),
            test_func=self.test_user_hunter_sentiment_aggregation_sources,  # PHASE 3: Custom prompt generation
            additional_context={
                'test_category': 'sentiment_analysis',
                'user_type': 'authenticated',
                'sources': ['news', 'reddit', 'twitter'],
                'asset': 'SOL'
            }
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    # CSV tracking
    await csv_tracker("user", "hunter", {
        "test_id": "user_hunter_sentiment_002",
        "s_multistep": False,
        "input": "What's the overall sentiment about Solana across news, Reddit, and Twitter?",
        "output": content,
        "test_label_sequence": "hunter_sentiment_analysis",
        "output_expected": "Multi-source sentiment analysis with synthesized perspectives",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    # Enhanced validation fields (PHASE 3)
    "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
    "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
    "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
    "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
    "test_category": validation.metadata.test_category if validation and validation.metadata else None,
    "test_type": validation.metadata.test_type if validation and validation.metadata else None,
    "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
    "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
    "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
    "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
    "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
    "model_used": validation.metadata.model_used if validation and validation.metadata else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_hunter_historical_pattern_recognition(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Hunter AI historical pattern analysis for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Show me Bitcoin's price patterns during the last 3 bull markets", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 150, "Should provide detailed historical analysis"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_hunter_historical_pattern_recognition",
            user_input="Show me Bitcoin's price patterns during the last 3 bull markets",
            agent_output=agent_response,
            expected_behavior=(
                "Should analyze historical BTC price patterns across multiple bull markets. "
                "Response should identify recurring patterns, timeframes, percentage gains/losses. "
                "Should provide actionable insights based on historical data."
            ),
            test_func=self.test_user_hunter_historical_pattern_recognition,  # PHASE 3: Custom prompt generation
            additional_context={
                'test_category': 'historical_analysis',
                'user_type': 'authenticated',
                'asset': 'BTC',
                'timeframe': 'multi_cycle'
            }
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    # CSV tracking
    await csv_tracker("user", "hunter", {
        "test_id": "user_hunter_historical_003",
        "s_multistep": False,
        "input": "Show me Bitcoin's price patterns during the last 3 bull markets",
        "output": content,
        "test_label_sequence": "hunter_historical_analysis",
        "output_expected": "Historical BTC patterns with recurring trends and actionable insights",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    # Enhanced validation fields (PHASE 3)
    "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
    "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
    "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
    "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
    "test_category": validation.metadata.test_category if validation and validation.metadata else None,
    "test_type": validation.metadata.test_type if validation and validation.metadata else None,
    "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
    "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
    "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
    "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
    "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
    "model_used": validation.metadata.model_used if validation and validation.metadata else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_hunter_risk_adjusted_recommendations(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Hunter AI risk-adjusted yield recommendations for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Suggest low-risk DeFi yield opportunities with 5%+ APY", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 100, "Should provide risk-adjusted recommendations"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_hunter_risk_adjusted_recommendations",
            user_input="Suggest low-risk DeFi yield opportunities with 5%+ APY",
            agent_output=agent_response,
            expected_behavior=(
                "Should recommend DeFi yield opportunities filtered by risk level (low risk). "
                "Response should mention specific protocols, APY rates, risk factors. "
                "Should balance yield potential with risk considerations."
            ),
            test_func=self.test_user_hunter_risk_adjusted_recommendations,  # PHASE 3: Custom prompt generation
            additional_context={
                'test_category': 'yield_recommendations',
                'user_type': 'authenticated',
                'risk_level': 'low',
                'min_apy': '5%'
            }
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    # CSV tracking
    await csv_tracker("user", "hunter", {
        "test_id": "user_hunter_risk_adjusted_004",
        "s_multistep": False,
        "input": "Suggest low-risk DeFi yield opportunities with 5%+ APY",
        "output": content,
        "test_label_sequence": "hunter_yield_recommendations",
        "output_expected": "Risk-adjusted DeFi yield opportunities with protocols and APY rates",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    # Enhanced validation fields (PHASE 3)
    "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
    "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
    "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
    "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
    "test_category": validation.metadata.test_category if validation and validation.metadata else None,
    "test_type": validation.metadata.test_type if validation and validation.metadata else None,
    "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
    "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
    "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
    "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
    "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
    "model_used": validation.metadata.model_used if validation and validation.metadata else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_hunter_portfolio_rebalancing_suggestions(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Hunter AI portfolio rebalancing suggestions for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "I have 70% ETH and 30% BTC. Should I rebalance?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 80, "Should provide rebalancing analysis"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_hunter_portfolio_rebalancing_suggestions",
            user_input="I have 70% ETH and 30% BTC. Should I rebalance?",
            agent_output=agent_response,
            expected_behavior=(
                "Should analyze current portfolio allocation (70% ETH, 30% BTC) and provide rebalancing advice. "
                "Response should consider market conditions, correlation, risk diversification. "
                "Should provide specific rebalancing suggestions if appropriate."
            ),
            test_func=self.test_user_hunter_portfolio_rebalancing_suggestions,  # PHASE 3: Custom prompt generation
            additional_context={
                'test_category': 'portfolio_rebalancing',
                'user_type': 'authenticated',
                'current_allocation': {'ETH': 70, 'BTC': 30}
            }
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    # CSV tracking
    await csv_tracker("user", "hunter", {
        "test_id": "user_hunter_portfolio_005",
        "s_multistep": False,
        "input": "I have 70% ETH and 30% BTC. Should I rebalance?",
        "output": content,
        "test_label_sequence": "hunter_portfolio_rebalancing",
        "output_expected": "Portfolio allocation analysis with rebalancing advice based on market conditions",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    # Enhanced validation fields (PHASE 3)
    "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
    "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
    "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
    "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
    "test_category": validation.metadata.test_category if validation and validation.metadata else None,
    "test_type": validation.metadata.test_type if validation and validation.metadata else None,
    "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
    "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
    "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
    "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
    "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
    "model_used": validation.metadata.model_used if validation and validation.metadata else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_hunter_gas_optimization_strategies(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Hunter AI gas optimization recommendations for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "When is the best time to execute Ethereum transactions to save on gas?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 80, "Should provide gas optimization strategies"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_hunter_gas_optimization_strategies",
            user_input="When is the best time to execute Ethereum transactions to save on gas?",
            agent_output=agent_response,
            expected_behavior=(
                "Should provide gas optimization strategies for Ethereum transactions. "
                "Response should mention optimal timing (weekends, off-peak hours), current gas prices, "
                "historical patterns, and practical tips for minimizing gas costs."
            ),
            test_func=self.test_user_hunter_gas_optimization_strategies,  # PHASE 3: Custom prompt generation
            additional_context={
                'test_category': 'gas_optimization',
                'user_type': 'authenticated',
                'chain': 'ethereum'
            }
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    # CSV tracking
    await csv_tracker("user", "hunter", {
        "test_id": "user_hunter_gas_optimization_006",
        "s_multistep": False,
        "input": "When is the best time to execute Ethereum transactions to save on gas?",
        "output": content,
        "test_label_sequence": "hunter_gas_optimization",
        "output_expected": "Gas optimization strategies with timing recommendations and cost-saving tips",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    # Enhanced validation fields (PHASE 3)
    "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
    "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
    "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
    "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
    "test_category": validation.metadata.test_category if validation and validation.metadata else None,
    "test_type": validation.metadata.test_type if validation and validation.metadata else None,
    "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
    "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
    "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
    "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
    "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
    "model_used": validation.metadata.model_used if validation and validation.metadata else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_hunter_market_regime_detection(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Hunter AI market regime detection for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "Are we in a bull market or bear market right now?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 80, "Should provide market regime analysis"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_hunter_market_regime_detection",
            user_input="Are we in a bull market or bear market right now?",
            agent_output=agent_response,
            expected_behavior=(
                "Should identify current market regime (bull/bear/sideways) with supporting evidence. "
                "Response should mention price trends, volume, sentiment indicators, and provide "
                "context for the market phase assessment."
            ),
            test_func=self.test_user_hunter_market_regime_detection,  # PHASE 3: Custom prompt generation
            additional_context={
                'test_category': 'market_regime',
                'user_type': 'authenticated',
                'analysis_type': 'current_market_phase'
            }
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    # CSV tracking
    await csv_tracker("user", "hunter", {
        "test_id": "user_hunter_market_regime_007",
        "s_multistep": False,
        "input": "Are we in a bull market or bear market right now?",
        "output": content,
        "test_label_sequence": "hunter_market_regime",
        "output_expected": "Market regime identification with supporting evidence and context",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    # Enhanced validation fields (PHASE 3)
    "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
    "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
    "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
    "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
    "test_category": validation.metadata.test_category if validation and validation.metadata else None,
    "test_type": validation.metadata.test_type if validation and validation.metadata else None,
    "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
    "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
    "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
    "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
    "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
    "model_used": validation.metadata.model_used if validation and validation.metadata else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_hunter_correlation_analysis_assets(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Hunter AI asset correlation analysis for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "How correlated are BTC, ETH, and SOL price movements?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 80, "Should provide correlation analysis"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_hunter_correlation_analysis_assets",
            user_input="How correlated are BTC, ETH, and SOL price movements?",
            agent_output=agent_response,
            expected_behavior=(
                "Should analyze price correlation between BTC, ETH, and SOL. "
                "Response should explain correlation strength, provide insights about "
                "diversification benefits or concentration risks, and mention timeframes."
            ),
            test_func=self.test_user_hunter_correlation_analysis_assets,  # PHASE 3: Custom prompt generation
            additional_context={
                'test_category': 'correlation_analysis',
                'user_type': 'authenticated',
                'assets': ['BTC', 'ETH', 'SOL']
            }
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    # CSV tracking
    await csv_tracker("user", "hunter", {
        "test_id": "user_hunter_correlation_008",
        "s_multistep": False,
        "input": "How correlated are BTC, ETH, and SOL price movements?",
        "output": content,
        "test_label_sequence": "hunter_correlation_analysis",
        "output_expected": "Asset correlation analysis with diversification insights and timeframes",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    # Enhanced validation fields (PHASE 3)
    "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
    "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
    "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
    "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
    "test_category": validation.metadata.test_category if validation and validation.metadata else None,
    "test_type": validation.metadata.test_type if validation and validation.metadata else None,
    "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
    "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
    "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
    "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
    "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
    "model_used": validation.metadata.model_used if validation and validation.metadata else None,
    })


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_hunter_liquidity_depth_assessment(
    client: AsyncClient,
    conversation_id: str,
    llm_validator,
    csv_tracker,
):
    """Test Hunter AI liquidity depth analysis for authenticated user."""
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
        json={"content": "What's the liquidity depth for AAVE/ETH on Uniswap?", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    content = data["agent_message"]["content"]

    assert len(content) > 50, "Should provide liquidity assessment"

    validation = None
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_user_hunter_liquidity_depth_assessment",
            user_input="What's the liquidity depth for AAVE/ETH on Uniswap?",
            agent_output=agent_response,
            expected_behavior=(
                "Should assess liquidity depth for AAVE/ETH pair on Uniswap. "
                "Response should mention TVL, trading volume, slippage implications, "
                "and provide context about whether liquidity is sufficient for trading."
            ),
            test_func=self.test_user_hunter_liquidity_depth_assessment,  # PHASE 3: Custom prompt generation
            additional_context={
                'test_category': 'liquidity_analysis',
                'user_type': 'authenticated',
                'pair': 'AAVE/ETH',
                'dex': 'Uniswap'
            }
        )
        if validation.verdict != "PASS":
            warnings.warn(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            )

    # CSV tracking
    await csv_tracker("user", "hunter", {
        "test_id": "user_hunter_liquidity_009",
        "s_multistep": False,
        "input": "What's the liquidity depth for AAVE/ETH on Uniswap?",
        "output": content,
        "test_label_sequence": "hunter_liquidity_analysis",
        "output_expected": "Liquidity depth assessment with TVL, volume, and slippage implications",
        "status": "PASS" if response.status_code in (200, 201) else "FAIL",
        "date": datetime.utcnow().isoformat(),
        "quality": validation.confidence if validation else None,
        "qa_status": validation.verdict if validation else "SKIPPED",
        "qa_output": validation.reasoning if validation else None,
    # Enhanced validation fields (PHASE 3)
    "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
    "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
    "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
    "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
    "test_category": validation.metadata.test_category if validation and validation.metadata else None,
    "test_type": validation.metadata.test_type if validation and validation.metadata else None,
    "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
    "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
    "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
    "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
    "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
    "model_used": validation.metadata.model_used if validation and validation.metadata else None,
    })
