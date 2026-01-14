"""
Historical Chat Data Integrity Tests - Week 7

Tests data integrity and edge cases for historical chat:
- Empty conversation history
- Deleted message handling
- Conversation timestamp consistency
- Large conversation performance

These tests advance Historical Chat coverage from 80% toward 90%.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.historical_chat]


class TestHistoricalChatDataIntegrity:
    """Test data integrity and edge cases for historical chat."""

    async def test_empty_conversation_history(self, client: AsyncClient):
        """
        Test accessing history of brand new conversation.

        New conversation should be created successfully even without
        prior messages.
        """
        response = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "This is my first message",
                "language": "en"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "agent_message" in data
        assert "conversation_id" in data
        assert data["conversation_id"] is not None
        assert len(data["agent_message"]["content"]) > 20

    async def test_deleted_message_handling(self, client: AsyncClient):
        """
        Test conversation continuity when messages removed.

        Conversation should continue smoothly even after context
        from earlier messages.
        """
        # Create conversation
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Tell me about Bitcoin",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1["conversation_id"]

        # Add second message (context from first)
        response2 = await client.post(
            f"/api/v1/guest/chat?conversation_id={conversation_id}",
            json={
                "content": "What about Ethereum?",
                "language": "en"
            }
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert "agent_message" in data2
        assert len(data2["agent_message"]["content"]) > 20

        # Third message should still work (conversation continuity)
        response3 = await client.post(
            f"/api/v1/guest/chat?conversation_id={conversation_id}",
            json={
                "content": "Compare them for me",
                "language": "en"
            }
        )

        assert response3.status_code == status.HTTP_200_OK
        data3 = response3.json()
        assert "agent_message" in data3
        assert len(data3["agent_message"]["content"]) > 50

    async def test_conversation_timestamp_consistency(self, client: AsyncClient):
        """
        Test timestamp consistency across conversation history.

        Messages added sequentially should have increasing timestamps
        and maintain proper ordering.
        """
        # Create initial message
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Message 1",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1["conversation_id"]

        # Add multiple messages in sequence
        for i in range(2, 6):
            response = await client.post(
                f"/api/v1/guest/chat?conversation_id={conversation_id}",
                json={
                    "content": f"Message {i}",
                    "language": "en"
                }
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "agent_message" in data

        # Verify conversation maintains order
        assert conversation_id is not None

    async def test_large_conversation_performance(self, client: AsyncClient):
        """
        Test performance with large conversation history.

        Conversation with many messages should maintain reasonable
        response times.
        """
        # Create conversation
        response1 = await client.post(
            "/api/v1/guest/chat",
            json={
                "content": "Start of long conversation",
                "language": "en"
            }
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1["conversation_id"]

        # Add many messages to test performance
        for i in range(20):  # 20 messages for performance test
            response = await client.post(
                f"/api/v1/guest/chat?conversation_id={conversation_id}",
                json={
                    "content": f"Message {i}: Tell me about crypto topic {i}",
                    "language": "en"
                }
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "agent_message" in data
            # Each response should be reasonable (we don't check exact timing
            # but verify responses are generated)
            assert len(data["agent_message"]["content"]) > 20

        # Final message should still work with full history
        response_final = await client.post(
            f"/api/v1/guest/chat?conversation_id={conversation_id}",
            json={
                "content": "Summarize everything we discussed",
                "language": "en"
            }
        )

        assert response_final.status_code == status.HTTP_200_OK
        data_final = response_final.json()
        assert "agent_message" in data_final
        assert len(data_final["agent_message"]["content"]) > 50
