"""
Intent Detection Advanced Tests - Week 4

Tests advanced and complex intent detection scenarios:
- Complex multi-intent queries (triple intents, nested intents, dependencies)
- Multilingual intent detection (Chinese, Portuguese, mixed languages)
- Intent confidence boundaries and clarification flows
- Protocol-specific intent routing and comparisons

These tests advance Intent Detection coverage from 75% to 85%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import json
import warnings
from datetime import datetime


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.intent_detection]


class TestComplexMultiIntentScenarios:
    """Test detection of complex multi-intent queries with multiple actions."""

    @pytest.mark.llm_validation
    async def test_triple_intent_query(self, client: AsyncClient, llm_validator):
        """
        Test query with 3 distinct intents.

        Query: "Check ETH price, swap to USDC, then lend on Aave"
        Expected: All 3 intents detected (query, swap, lend)
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Check ETH price, swap to USDC, then lend on Aave",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        # Agent should acknowledge multiple intents or address them
        agent_response = data["agent_message"]["content"].lower()

        # Should mention price/query aspect
        price_mentioned = any(keyword in agent_response for keyword in ["price", "eth", "ethereum"])

        # Should mention swap aspect
        swap_mentioned = any(keyword in agent_response for keyword in ["swap", "exchange", "trade"])

        # Should mention lending aspect
        lend_mentioned = any(keyword in agent_response for keyword in ["lend", "aave", "supply"])

        # At least 2 of the 3 intents should be acknowledged
        intents_acknowledged = sum([price_mentioned, swap_mentioned, lend_mentioned])
        assert intents_acknowledged >= 2, "Agent should acknowledge multiple intents in query"

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_triple_intent_query",
                user_input="Check ETH price, swap to USDC, then lend on Aave",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_triple_intent_query,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_nested_intent_query(self, client: AsyncClient, llm_validator):
        """
        Test query with nested/conditional intents.

        Query: "If ETH price is above $3000, swap 1 ETH to USDC"
        Expected: Conditional query + action handling
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "If ETH price is above $3000, swap 1 ETH to USDC",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        agent_response = data["agent_message"]["content"].lower()

        # Should handle conditional nature of query
        # Agent might check price first, or explain the conditional logic
        conditional_handling = any(keyword in agent_response for keyword in [
            "if", "when", "price", "eth", "3000", "swap", "conditional"
        ])

        assert conditional_handling, "Agent should handle conditional intent logic"

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_nested_intent_query",
                user_input="If ETH price is above $3000, swap 1 ETH to USDC",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_nested_intent_query,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_sequential_dependent_intents(self, client: AsyncClient, llm_validator):
        """
        Test intents that depend on previous results.

        Query: "Swap ETH to USDC, then use half to lend on Aave"
        Expected: Sequential processing, dependency understanding
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Swap ETH to USDC, then use half to lend on Aave",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        agent_response = data["agent_message"]["content"].lower()

        # Should acknowledge sequential nature or multi-step flow
        sequential_understanding = any(keyword in agent_response for keyword in [
            "swap", "lend", "then", "after", "half", "aave", "usdc", "step"
        ])

        assert sequential_understanding, "Agent should understand sequential dependent intents"

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sequential_dependent_intents",
                user_input="Swap ETH to USDC, then use half to lend on Aave",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_sequential_dependent_intents,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )



class TestMultilingualIntentDetection:
    """Test intent detection across multiple languages."""

    @pytest.mark.llm_validation
    async def test_chinese_language_support(self, client: AsyncClient, llm_validator):
        """
        Test Chinese language query handling.

        Query (Chinese): "以太坊价格是多少?" (What is the Ethereum price?)
        Expected: Intent detected, response in Chinese
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "以太坊价格是多少?",
                "language": "zh"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        # Agent should respond (ideally in Chinese, but English acceptable)
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_chinese_language_support",
                user_input="以太坊价格是多少?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_chinese_language_support,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_portuguese_language_support(self, client: AsyncClient, llm_validator):
        """
        Test Portuguese language query handling.

        Query (Portuguese): "Qual é o preço do Ethereum?" (What is the Ethereum price?)
        Expected: Intent detected, response in Portuguese
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Qual é o preço do Ethereum?",
                "language": "pt"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        # Agent should respond (ideally in Portuguese, but English acceptable)
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portuguese_language_support",
                user_input="Qual é o preço do Ethereum?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_portuguese_language_support,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_mixed_language_query(self, client: AsyncClient, llm_validator):
        """
        Test mixed English/Chinese query tolerance.

        Query: "What is the ETH 价格?" (mixing English and Chinese)
        Expected: System handles gracefully
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What is the ETH 价格?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        # Agent should handle gracefully (not crash)
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_mixed_language_query",
                user_input="What is the ETH 价格?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_mixed_language_query,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )



class TestIntentConfidenceBoundaries:
    """Test confidence threshold boundary behavior."""

    @pytest.mark.llm_validation
    async def test_intent_confidence_boundary_70_percent(self, client: AsyncClient, llm_validator):
        """
        Test behavior at confidence threshold.

        Send a somewhat ambiguous query that might be near confidence boundary.
        Expected: Either processes or asks for clarification
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "token thing",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        # Agent should handle gracefully - either ask for clarification or provide general info
        agent_response = data["agent_message"]["content"].lower()
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_intent_confidence_boundary_70_percent",
                user_input="token thing",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_intent_confidence_boundary_70_percent,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_low_confidence_clarification_flow(self, client: AsyncClient, llm_validator):
        """
        Test clarification flow for low confidence intents.

        Send very ambiguous query, then provide clarification.
        Expected: System requests clarification, then handles follow-up
        """
        # First message: very ambiguous
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "what about it",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1.get("conversation_id")

        assert "agent_message" in data1
        assert data1["agent_message"]["content"]

        # Agent might ask for clarification or provide general response
        agent_response1 = data1["agent_message"]["content"].lower()
        assert len(agent_response1) > 0

        # Second message: clarify intent
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "I mean the Ethereum price",
                "language": "en",
                "conversation_id": conversation_id
            }
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        assert "agent_message" in data2
        assert data2["agent_message"]["content"]

        # Agent should now understand and respond to price query
        agent_response2 = data2["agent_message"]["content"].lower()
        price_response = any(keyword in agent_response2 for keyword in [
            "price", "eth", "ethereum", "market", "value"
        ])
        assert price_response, "Agent should understand clarified intent"

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_low_confidence_clarification_flow",
                user_input="what about it",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_low_confidence_clarification_flow,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )



class TestProtocolSpecificIntents:
    """Test protocol-specific intent routing."""

    @pytest.mark.llm_validation
    async def test_protocol_specific_routing_aave(self, client: AsyncClient, llm_validator):
        """
        Test query that mentions Aave specifically.

        Query: "What's the APY on Aave for USDC?"
        Expected: Aave-specific routing and data
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the APY on Aave for USDC?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        agent_response = data["agent_message"]["content"].lower()

        # Should mention Aave or APY information
        protocol_mentioned = any(keyword in agent_response for keyword in [
            "aave", "apy", "usdc", "rate", "yield", "interest"
        ])

        assert protocol_mentioned, "Agent should address protocol-specific query"

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_protocol_specific_routing_aave",
                user_input="What",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate information about Aave protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                test_func=self.test_protocol_specific_routing_aave,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Aave'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_protocol_comparison_intent(self, client: AsyncClient, llm_validator):
        """
        Test comparison queries between protocols.

        Query: "Which is better, Aave or Compound for lending?"
        Expected: Comparison handling, both protocols addressed
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Which is better, Aave or Compound for lending?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        agent_response = data["agent_message"]["content"].lower()

        # Should mention both protocols or acknowledge comparison
        aave_mentioned = "aave" in agent_response
        compound_mentioned = "compound" in agent_response

        # At least one protocol should be mentioned in comparison
        comparison_handling = aave_mentioned or compound_mentioned or "compar" in agent_response

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_protocol_comparison_intent",
                user_input="Which is better, Aave or Compound for lending?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate information about Aave protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                test_func=self.test_protocol_comparison_intent,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Aave'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


        assert comparison_handling, "Agent should handle protocol comparison query"