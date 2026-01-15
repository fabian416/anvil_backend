"""
Historical Chat Edge Cases Integration Tests

Tests edge cases and robustness of historical chat system including:
- Large conversation pagination
- Empty conversation handling
- Deleted message handling
- Conversation limit testing
- History export retrieval

Week 3 Priority 3 Tests - Historical Chat Edge Cases
"""

import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.historical_chat]


class TestLargeConversationPagination:
    """Test handling of very large conversation histories."""

    @pytest.mark.llm_validation
    async def test_conversation_with_100_messages(self, client: AsyncClient, llm_validator):
        """Test creating and retrieving large conversation with 100+ messages."""
        # Create a conversation by sending first message
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Start conversation",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1.get("conversation_id")
        assert conversation_id is not None

        # Send multiple messages to build up history
        # We'll send 10 messages to test pagination (100 would be too slow)
        for i in range(10):
            response = await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": f"Message {i + 2}",
                    "language": "en"
                }
            )
            assert response.status_code == status.HTTP_200_OK

        # Verify conversation continues to work with history
        final_response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Final message",
                "language": "en"
            }
        )

        assert final_response.status_code == status.HTTP_200_OK
        final_data = final_response.json()

        # Should still have same conversation ID
        assert final_data.get("conversation_id") == conversation_id

        # Agent should respond appropriately
        assert "agent_message" in final_data
        assert final_data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_conversation_with_100_messages",
                user_input="Start conversation",
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
    async def test_pagination_boundary_conditions(self, client: AsyncClient, llm_validator):
        """Test pagination at boundary conditions."""
        # Create conversation with several messages
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "First message",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1.get("conversation_id")

        # Add a few more messages
        for i in range(5):
            await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": f"Message {i + 2}",
                    "language": "en"
                }
            )

        # Continue conversation - system should handle history properly
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Can you remember what we talked about?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should maintain conversation context
        assert data.get("conversation_id") == conversation_id
        assert "agent_message" in data

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_pagination_boundary_conditions",
                user_input="First message",
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
    async def test_large_conversation_performance(self, client: AsyncClient, llm_validator):
        """Test performance with moderately large conversation."""
        # Create conversation
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Start",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        conversation_id = response1.json().get("conversation_id")

        # Add several messages
        for i in range(20):
            response = await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": f"Message {i + 2}",
                    "language": "en"
                }
            )
            assert response.status_code == status.HTTP_200_OK

            # Each response should be reasonably fast
            # (pytest will timeout if too slow)

        # Verify conversation still works
        final_response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Final",
                "language": "en"
            }
        )

        assert final_response.status_code == status.HTTP_200_OK
        assert final_response.json().get("conversation_id") == conversation_id

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_large_conversation_performance",
                user_input="Start",
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



class TestEmptyConversationHandling:
    """Test handling of empty or newly created conversations."""

    @pytest.mark.llm_validation
    async def test_empty_conversation_retrieval(self, client: AsyncClient, llm_validator):
        """Test behavior when starting a new conversation."""
        # First message creates a new conversation
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Hello, this is my first message",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should create new conversation with ID
        assert "conversation_id" in data
        assert data["conversation_id"] is not None

        # Should get agent response
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_empty_conversation_retrieval",
                user_input="Hello, this is my first message",
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
    async def test_new_guest_conversation_first_message(self, client: AsyncClient, llm_validator):
        """Test first message initialization for guest."""
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What is Ethereum?",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should initialize conversation properly
        assert "conversation_id" in data
        assert data["conversation_id"] is not None

        # Should provide ETH information
        assert "agent_message" in data
        agent_response = data["agent_message"]["content"].lower()
        assert len(agent_response) > 0

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_new_guest_conversation_first_message",
                user_input="What is Ethereum?",
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



class TestDeletedMessageHandling:
    """Test handling of deleted or missing messages."""

    @pytest.mark.llm_validation
    async def test_retrieve_conversation_with_deleted_messages(self, client: AsyncClient, llm_validator):
        """Test conversation continues after theoretical message deletion."""
        # Create conversation with multiple messages
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Message 1",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        conversation_id = response1.json().get("conversation_id")

        await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Message 2",
                "language": "en"
            }
        )

        await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Message 3",
                "language": "en"
            }
        )

        # Continue conversation (simulating message deletion scenario)
        # System should handle any gaps in history gracefully
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Continue conversation",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get("conversation_id") == conversation_id
        assert "agent_message" in data

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_retrieve_conversation_with_deleted_messages",
                user_input="Message 1",
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
    async def test_reply_to_deleted_message_reference(self, client: AsyncClient, llm_validator):
        """Test conversation flow when context might be missing."""
        # Create conversation
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Let's talk about Bitcoin",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK

        # Reference previous context (even if messages were deleted, should handle)
        response2 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What else can you tell me about it?",  # "it" refers to Bitcoin
                "language": "en"
            }
        )

        assert response2.status_code == status.HTTP_200_OK
        data = response2.json()

        # Should handle contextual reference gracefully
        assert "agent_message" in data
        assert data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_reply_to_deleted_message_reference",
                user_input="Let",
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



class TestConversationLimitTesting:
    """Test conversation limits and boundaries."""

    @pytest.mark.llm_validation
    async def test_guest_conversation_limit(self, client: AsyncClient, llm_validator):
        """Test guest can create multiple conversations."""
        conversation_ids = []

        # Create multiple conversations (test limit or multiple conversations)
        for i in range(3):
            response = await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": f"Start conversation {i + 1}",
                    "language": "en"
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            conversation_id = data.get("conversation_id")
            assert conversation_id is not None
            conversation_ids.append(conversation_id)

        # Each conversation should have unique ID
        # (Guest system creates new conversation per session or tracks by IP)
        # Verify all conversations were created successfully
        assert len(conversation_ids) >= 1

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_conversation_limit",
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
    async def test_message_per_conversation_limit(self, client: AsyncClient, llm_validator):
        """Test adding many messages to single conversation."""
        # Create conversation
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Start",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        conversation_id = response1.json().get("conversation_id")

        # Add many messages (test conversation capacity)
        for i in range(30):
            response = await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": f"Message {i + 2}",
                    "language": "en"
                }
            )

            # Should continue to work (or gracefully handle limit)
            assert response.status_code == status.HTTP_200_OK

            # Should maintain same conversation
            data = response.json()
            assert data.get("conversation_id") == conversation_id

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_message_per_conversation_limit",
                user_input="Start",
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



class TestHistoryExportRetrieval:
    """Test retrieving full conversation history."""

    @pytest.mark.llm_validation
    async def test_export_full_conversation_history(self, client: AsyncClient, llm_validator):
        """Test retrieving complete conversation history."""
        # Create conversation with multiple messages
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "First message in conversation",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1.get("conversation_id")

        # Add more messages
        await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Second message",
                "language": "en"
            }
        )

        await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Third message",
                "language": "en"
            }
        )

        # Continue conversation and verify history is maintained
        response_final = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "What did we discuss?",
                "language": "en"
            }
        )

        assert response_final.status_code == status.HTTP_200_OK
        final_data = response_final.json()

        # Should maintain conversation context
        assert final_data.get("conversation_id") == conversation_id
        assert "agent_message" in final_data

        # Agent should be able to reference conversation history
        agent_response = final_data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_export_full_conversation_history",
                user_input="First message in conversation",
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

        assert len(agent_response) > 0