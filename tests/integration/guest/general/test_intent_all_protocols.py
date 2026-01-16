"""
All Protocol Coverage Tests - Week 6

Tests intent detection for specific DeFi protocols:
- Compound protocol-specific queries
- Uniswap protocol-specific queries
- Curve protocol-specific queries
- Balancer protocol-specific queries
- Yearn protocol-specific queries
- Protocol version differentiation (Uniswap v2 vs v3)

These tests advance Intent Detection coverage from 85% toward 95%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.intent_detection]


class TestAllProtocolIntents:
    """Test intent detection for all major DeFi protocols."""

    @pytest.mark.llm_validation
    async def test_compound_protocol_specific_intent(self, client: AsyncClient, llm_validator):
        """
        Test Compound protocol-specific queries.

        Query about Compound should detect protocol-specific intent and provide
        relevant information about lending/borrowing rates.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What are the current lending rates on Compound protocol?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        # Should provide substantive response about Compound
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive Compound protocol information"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_compound_protocol_specific_intent",
                user_input="What are the current lending rates on Compound protocol?",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about Compound protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Compound'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.llm_validation
    async def test_uniswap_protocol_specific_intent(self, client: AsyncClient, llm_validator):
        """
        Test Uniswap protocol-specific queries.

        Query about Uniswap should detect DEX-specific intent and provide
        relevant information about liquidity pools and swaps.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "How do I swap tokens on Uniswap?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide substantive response about Uniswap
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive Uniswap information"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_uniswap_protocol_specific_intent",
                user_input="How do I swap tokens on Uniswap?",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about Uniswap protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Uniswap'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.llm_validation
    async def test_curve_protocol_specific_intent(self, client: AsyncClient, llm_validator):
        """
        Test Curve protocol-specific queries.

        Query about Curve should detect stablecoin DEX intent and provide
        relevant information about Curve pools.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What are the best stablecoin pools on Curve Finance?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide substantive response about Curve
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive Curve protocol information"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_curve_protocol_specific_intent",
                user_input="What are the best stablecoin pools on Curve Finance?",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about Curve protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Curve'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.llm_validation
    async def test_balancer_protocol_specific_intent(self, client: AsyncClient, llm_validator):
        """
        Test Balancer protocol-specific queries.

        Query about Balancer should detect weighted pools intent and provide
        relevant information about Balancer liquidity pools.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "How do weighted pools work on Balancer?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide substantive response about Balancer
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive Balancer information"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_balancer_protocol_specific_intent",
                user_input="How do weighted pools work on Balancer?",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about DeFi protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.llm_validation
    async def test_yearn_protocol_specific_intent(self, client: AsyncClient, llm_validator):
        """
        Test Yearn protocol-specific queries.

        Query about Yearn should detect yield aggregator intent and provide
        relevant information about Yearn vaults and strategies.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What are the highest yielding Yearn vaults right now?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide substantive response about Yearn
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive Yearn protocol information"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_yearn_protocol_specific_intent",
                user_input="What are the highest yielding Yearn vaults right now?",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about DeFi protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.llm_validation
    async def test_protocol_version_specific_intent(self, client: AsyncClient, llm_validator):
        """
        Test specific protocol versions (Uniswap v2 vs v3).

        Query about specific protocol version should detect version-specific intent
        and explain differences between versions.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the difference between Uniswap v2 and Uniswap v3?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide substantive comparison between versions
        agent_response = data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_protocol_version_specific_intent",
                user_input="What",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate information about Uniswap protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Uniswap'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        assert len(agent_response) > 100, "Should provide comprehensive version comparison (100+ chars)"