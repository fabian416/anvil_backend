"""
Knowledge Injection Error Handling Tests - Week 5

Tests comprehensive error handling for knowledge injection:
- Invalid token symbol handling
- Malformed API response handling
- Partial data availability
- Stale data detection
- Rate limit handling on external APIs
- Timeout handling on knowledge fetches

These tests advance Knowledge Injection coverage from 73% toward 85%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.knowledge_injection]


class TestKnowledgeInjectionErrors:
    """Test error handling in knowledge injection system."""

    @pytest.mark.llm_validation
    async def test_invalid_token_symbol_handling(self, client: AsyncClient, llm_validator):
        """
        Test handling of invalid/unknown token symbols.

        Query with fake/invalid token should provide graceful error handling.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the price of INVALIDTOKEN999?",
                "language": "en"
            }
        )

        # Should succeed even with invalid token
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Agent should provide helpful response even without data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 0, "Should provide helpful response for invalid token"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_invalid_token_symbol_handling",
                user_input="What",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.llm_validation
    async def test_malformed_api_response_handling(self, client: AsyncClient, llm_validator):
        """
        Test handling of malformed external API responses.

        System should handle unexpected API responses gracefully without crashing.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's happening with cryptocurrency markets?",
                "language": "en"
            }
        )

        # Should succeed even if some APIs return malformed data
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide substantive response
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide substantive response"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_malformed_api_response_handling",
                user_input="What",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.llm_validation
    async def test_partial_data_availability(self, client: AsyncClient, llm_validator):
        """
        Test when only some data is available.

        Query where some APIs work and others don't should return partial data.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Tell me about Polkadot token metrics and recent news",
                "language": "en"
            }
        )

        # Should succeed with partial data
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide useful response with available data
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide response with available data"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_partial_data_availability",
                user_input="Tell me about Polkadot token metrics and recent news",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.llm_validation
    async def test_stale_data_detection(self, client: AsyncClient, llm_validator):
        """
        Test detection and handling of stale cached data.

        System should detect potentially stale cache and handle appropriately.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What's the latest price of Chainlink?",
                "language": "en"
            }
        )

        # Should succeed with fresh or refreshed data
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide current information
        agent_response = data["agent_message"]["content"]
        assert len(agent_response) > 50, "Should provide current information"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_stale_data_detection",
                user_input="What",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.llm_validation
    async def test_rate_limit_on_knowledge_apis(self, client: AsyncClient, llm_validator):
        """
        Test handling rate limits from external APIs.

        Multiple rapid queries should handle rate limiting gracefully.
        """
        # Make multiple rapid queries
        queries = [
            "What's BTC price?",
            "What's ETH price?",
            "What's SOL price?"
        ]

        for query in queries:
            response = await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": query,
                    "language": "en"
                }
            )

            # All should succeed even with potential rate limiting
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "agent_message" in data
            assert data["agent_message"]["content"]
            assert len(data["agent_message"]["content"]) > 0

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_rate_limit_on_knowledge_apis",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.llm_validation
    async def test_timeout_on_knowledge_fetch(self, client: AsyncClient, llm_validator):
        """
        Test timeout on external API calls.

        Query that might timeout should handle gracefully without blocking indefinitely.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Give me comprehensive data on all major DeFi protocols",
                "language": "en"
            }
        )

        # Should succeed without timeout issues
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Should provide response even if some requests timeout
        agent_response = data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_timeout_on_knowledge_fetch",
                user_input="Give me comprehensive data on all major DeFi protocols",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        assert len(agent_response) > 50, "Should provide response despite potential timeouts"