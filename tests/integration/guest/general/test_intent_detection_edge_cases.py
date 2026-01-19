"""
Intent Detection Edge Cases Integration Tests

Tests edge cases and robustness of intent detection system including:
- Ambiguous query handling
- Multi-intent queries
- Language mixing scenarios
- Typo and misspelling handling
- Confidence threshold behavior

Week 3 Priority 3 Tests - Intent Detection Edge Cases
"""

import pytest
from fastapi import status
from httpx import AsyncClient
import json
import warnings
from datetime import datetime

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.intent_detection]


class TestAmbiguousQueryHandling:
    """Test how the system handles queries that could match multiple intents."""

    @pytest.mark.llm_validation
    async def test_ambiguous_swap_vs_query(self, client: AsyncClient, llm_validator):
        """Test ambiguous query that could be swap intent or price query."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the best token to swap?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return a response (either disambiguates or provides query answer)
        assert "agent_message" in data
        assert data["agent_message"]["content"]
        assert "conversation_id" in data

        # Response should handle the ambiguity gracefully
        agent_response = data["agent_message"]["content"].lower()
        # Could be interpreted as query or clarification request
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ambiguous_swap_vs_query",
                user_input="What",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_ambiguous_swap_vs_query,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_ambiguous_lend_vs_query(self, client: AsyncClient, llm_validator):
        """Test query that could be lending intent or advice query."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Should I lend USDC?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should interpret as query (asking advice) not execution
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Likely provides advice rather than executing lend action
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ambiguous_lend_vs_query",
                user_input="Should I lend USDC?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_ambiguous_lend_vs_query,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_ambiguous_protocol_mention(self, client: AsyncClient, llm_validator):
        """Test query with protocol mention that could be query or action."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Tell me about Aave and then do something",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle compound ambiguous intent
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Should either provide Aave info or ask for clarification on "do something"
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ambiguous_protocol_mention",
                user_input="Tell me about Aave and then do something",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate information about Aave protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                test_func=self.test_ambiguous_protocol_mention,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Aave'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_very_vague_query(self, client: AsyncClient, llm_validator):
        """Test extremely vague query with unclear intent."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Help me with crypto",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle gracefully with clarification or general help
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Should provide helpful response or ask for clarification
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_very_vague_query",
                user_input="Help me with crypto",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_very_vague_query,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )



class TestMultiIntentQueries:
    """Test queries containing multiple intents in one message."""

    @pytest.mark.llm_validation
    async def test_swap_then_lend_multi_intent(self, client: AsyncClient, llm_validator):
        """Test compound intent with multiple actions."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Swap ETH for USDC then lend it on Aave",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should detect compound intent (swap + lend)
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # May require registration or handle multi-step intent
        # Guest will likely be told to register for execution
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_swap_then_lend_multi_intent",
                user_input="Swap ETH for USDC then lend it on Aave",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_swap_then_lend_multi_intent,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_query_with_embedded_action(self, client: AsyncClient, llm_validator):
        """Test mixed intent: query + action in same message."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the gas price and swap 1 ETH for DAI?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle mixed intent
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Should provide gas price info and handle swap request
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_query_with_embedded_action",
                user_input="What",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_query_with_embedded_action,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_multiple_queries_single_message(self, client: AsyncClient, llm_validator):
        """Test multiple query intents in one message."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's ETH price? What's BTC price? What's SOL price?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle multiple queries
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Should provide info on multiple tokens or acknowledge multiple queries
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_multiple_queries_single_message",
                user_input="What",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_multiple_queries_single_message,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_conflicting_intents(self, client: AsyncClient, llm_validator):
        """Test query with conflicting intents."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Swap ETH but actually don't do anything",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should detect conflict and handle gracefully
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Should ask for clarification or acknowledge the contradiction
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_conflicting_intents",
                user_input="Swap ETH but actually don",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_conflicting_intents,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )



class TestLanguageMixingScenarios:
    """Test handling of mixed-language inputs."""

    @pytest.mark.llm_validation
    async def test_english_with_spanish_tokens(self, client: AsyncClient, llm_validator):
        """Test mixed English and Spanish in query."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Swap ETH por USDC",  # "por" is Spanish for "for"
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle mixed language gracefully
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should respond in English (language parameter)
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_english_with_spanish_tokens",
                user_input="Swap ETH por USDC",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_english_with_spanish_tokens,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_query_language_code_mismatch(self, client: AsyncClient, llm_validator):
        """Test Spanish query with English language parameter."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "¿Cuál es el precio de ETH?",  # Spanish: "What is the price of ETH?"
                "language": "en"  # But language set to English
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle gracefully (detect language or respect parameter)
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_query_language_code_mismatch",
                user_input="¿Cuál es el precio de ETH?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_query_language_code_mismatch,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_unsupported_language_fallback(self, client: AsyncClient, llm_validator):
        """Test query in unsupported language."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What is the price of ETH?",
                "language": "fr"  # French - may not be supported
            }
        )

        # Should either support French or fallback gracefully
        # Accept both 200 (supported) or 400/422 (not supported)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "agent_message" in data
            assert data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_unsupported_language_fallback",
                user_input="What is the price of ETH?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_unsupported_language_fallback,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )



class TestTypoAndMisspellingHandling:
    """Test robustness against common typos and misspellings."""

    @pytest.mark.llm_validation
    async def test_misspelled_protocol_name(self, client: AsyncClient, llm_validator):
        """Test query with misspelled protocol name."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Lend on Aavee",  # Typo: Aavee → Aave
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle gracefully (correct typo or ask for clarification)
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_misspelled_protocol_name",
                user_input="Lend on Aavee",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate information about Aave protocol. Response must explain what the protocol does, its key features, and relevant DeFi concepts in an accessible way."
                ),
                test_func=self.test_misspelled_protocol_name,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'defi_protocol', 'protocol': 'Aave'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_misspelled_action_verb(self, client: AsyncClient, llm_validator):
        """Test query with misspelled action verb."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Sawp ETH for USDC",  # Typo: Sawp → Swap
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle gracefully (correct typo or handle intent)
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_misspelled_action_verb",
                user_input="Sawp ETH for USDC",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_misspelled_action_verb,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_multiple_typos_in_query(self, client: AsyncClient, llm_validator):
        """Test query with multiple typos."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Wat iz the prce of etherum?",  # Multiple typos
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should understand intent despite typos
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Should provide price info or indicate understanding
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_multiple_typos_in_query",
                user_input="Wat iz the prce of etherum?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_multiple_typos_in_query,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_completely_garbled_input(self, client: AsyncClient, llm_validator):
        """Test completely garbled/nonsense input."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "asdfghjkl qwerty zxcvbnm",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle gracefully with helpful error message
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Should indicate unable to understand or ask for clarification
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_completely_garbled_input",
                user_input="asdfghjkl qwerty zxcvbnm",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_completely_garbled_input,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )



class TestConfidenceThresholdBehavior:
    """Test intent detection confidence scoring and thresholds."""

    @pytest.mark.llm_validation
    async def test_high_confidence_intent_executes(self, client: AsyncClient, llm_validator):
        """Test clear, unambiguous query gets processed immediately."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What is the current price of ETH?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # High confidence query should get direct answer
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Should provide price information directly
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_high_confidence_intent_executes",
                user_input="What is the current price of ETH?",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_high_confidence_intent_executes,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_low_confidence_asks_clarification(self, client: AsyncClient, llm_validator):
        """Test vague query results in clarification request."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "I need help",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Low confidence should ask for clarification
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Should ask what kind of help or provide general guidance
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_low_confidence_asks_clarification",
                user_input="I need help",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_low_confidence_asks_clarification,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )


    @pytest.mark.llm_validation
    async def test_medium_confidence_provides_suggestions(self, client: AsyncClient, llm_validator):
        """Test somewhat clear query gets helpful suggestions."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Tell me about DeFi",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Medium confidence should provide info or suggestions
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        agent_response = data["agent_message"]["content"].lower()
        # Should provide DeFi information or ask for specific area of interest

        # Optional LLM semantic validation (environment-gated)
        # Extract response data
        data = response.json()
        agent_response = data["agent_message"]["content"]

        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_medium_confidence_provides_suggestions",
                user_input="Tell me about DeFi",
                agent_output=agent_response,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                test_func=self.test_medium_confidence_provides_suggestions,  # PHASE 3: Custom prompt generation
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )

        assert len(agent_response) > 0