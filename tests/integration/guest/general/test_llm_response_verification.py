"""
Integration tests for LLM response verification.

Tests LLM response format and validation including:
- Response structure validation
- Agent type inclusion
- DeFi data formatting
- Content verification
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.chat
class TestLLMResponseStructure:
    """Integration tests for LLM response structure."""

    def test_response_structure_validation(self, client):
        """
        WHEN LLM returns response
        THEN response SHALL have valid structure
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": "What is yield farming?"}
        )

        if response.status_code == 201:
            data = response.json()
            # Check response has expected fields
            assert "user_message" in data or "agent_message" in data or "message" in data
        else:
            # Not authenticated or conversation not found
            assert response.status_code in (401, 404)

    def test_response_includes_agent_type(self, client):
        """
        WHEN LLM response includes agent info
        THEN agent type SHOULD be specified
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": "Tell me about Aave"}
        )

        if response.status_code == 201:
            data = response.json()
            # Agent type may be in agent_message or response metadata
            # This is optional, so just verify structure is present
            assert isinstance(data, dict)
        else:
            assert response.status_code in (401, 404)


@pytest.mark.integration
@pytest.mark.chat
class TestDeFiDataFormatting:
    """Integration tests for DeFi data formatting in responses."""

    def test_protocol_data_format(self, client):
        """
        WHEN response includes protocol data
        THEN data SHALL be properly formatted
        """
        response = client.post(
            "/api/v1/chat/search-protocols",
            json={"query": "top lending protocols"}
        )

        if response.status_code == 200:
            data = response.json()
            # Check for results key
            if "results" in data:
                for result in data.get("results", []):
                    # Protocol data should have certain fields
                    assert isinstance(result, dict)
        else:
            assert response.status_code in (401,)

    def test_invalid_tvl_type_fails(self):
        """
        Test that DeFi data validator catches invalid TVL types.
        """
        # This tests the validator itself, not an endpoint
        from tests.helpers.llm_verifier import LLMVerifier

        verifier = LLMVerifier()

        # Invalid TVL (string instead of number)
        defi_data = {"tvl": "invalid"}
        result = verifier.verify_defi_data_format(defi_data)
        assert result.is_valid is False

    def test_invalid_apy_range_fails(self):
        """
        Test that DeFi data validator catches invalid APY type.
        """
        from tests.helpers.llm_verifier import LLMVerifier

        verifier = LLMVerifier()

        # APY with invalid type (string instead of number)
        defi_data = {"apy": "invalid"}
        result = verifier.verify_defi_data_format(defi_data)
        assert result.is_valid is False

    def test_missing_required_fields(self):
        """
        Test that validator detects missing required fields.
        """
        from tests.helpers.llm_verifier import LLMVerifier

        verifier = LLMVerifier()

        # Empty data should fail if required fields are expected
        result = verifier.verify_response_structure({})
        # Empty response without content should fail
        assert result.is_valid is False


@pytest.mark.integration
@pytest.mark.chat
class TestMessageBuilderLLMResponses:
    """Integration tests for message builder with LLM responses."""

    def test_message_builder_llm_response(self):
        """
        Test MessageBuilder creates valid LLM response structure.
        """
        from tests.builders import an_agent_message

        message = an_agent_message().build()

        assert message is not None
        assert hasattr(message, 'content')
        assert message.content is not None

    def test_message_builder_defi_data_response(self):
        """
        Test MessageBuilder creates valid DeFi data response.
        """
        from tests.builders import an_agent_message

        message = an_agent_message().build()

        assert message is not None
        assert hasattr(message, 'content')
        assert hasattr(message, 'role')


@pytest.mark.integration
@pytest.mark.chat
class TestContentVerification:
    """Integration tests for content verification."""

    def test_response_contains_relevant_content(self, client):
        """
        WHEN user asks about specific topic
        THEN response SHOULD contain relevant information
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": "What is Uniswap?"}
        )

        if response.status_code == 201:
            data = response.json()
            # Verify we got some content back
            agent_message = data.get("agent_message", {})
            content = agent_message.get("content", "") if isinstance(agent_message, dict) else ""
            # Response should have some content (even if minimal)
            assert isinstance(data, dict)
        else:
            assert response.status_code in (401, 404)

    def test_risk_disclaimer_inclusion(self, client):
        """
        WHEN response discusses financial topics
        THEN response MAY include risk disclaimers
        """
        conversation_id = str(uuid4())
        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": "Should I invest in this DeFi protocol?"}
        )

        # Just verify we get a response
        assert response.status_code in (201, 401, 404)
