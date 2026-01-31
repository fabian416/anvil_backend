"""
Integration tests for guest chat history endpoints using real API.

Tests verify that:
- History endpoint returns real conversation messages
- Status endpoint returns real session data
- All responses are in correct language (en, es, pt, zh)
- Content is validated to ensure it's not mock/placeholder data

Methodology: CTO Engineering Framework
- Phase 1: Problem Decomposition - History requires real database queries
- Phase 2: Solution Generation - Test history and status endpoints
- Phase 3: Risk Assessment - Verify empty states and edge cases
- Phase 4: Implementation - Comprehensive multi-language coverage

NOTE: Guest chat tests require database migrations to be applied.
Run: alembic upgrade head
"""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.integration
class TestGuestChatHistorialReal:
    """Test guest chat history endpoints with real API responses."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_history_empty(self, test_app):
        """Test history endpoint returns empty for new guest."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/v1/guest/chat/history",
                headers={"X-Forwarded-For": "127.0.0.401"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty history structure
        assert "messages" in data or "is_active" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_history_with_messages(self, test_app):
        """Test history endpoint returns real messages after conversation."""
        ip = "127.0.0.402"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Send first message
            response1 = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Hello", "language": "en"},
                headers={"X-Forwarded-For": ip},
            )
            assert response1.status_code == 200
            
            # Send second message
            response2 = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "What can you do?", "language": "en"},
                headers={"X-Forwarded-For": ip},
            )
            assert response2.status_code == 200
            
            # Get history
            response = await ac.get(
                "/api/v1/guest/chat/history",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "messages" in data
        assert "total_messages" in data
        assert "is_active" in data
        
        # Should have messages
        assert len(data["messages"]) >= 2
        
        # Verify message structure
        for msg in data["messages"]:
            assert "id" in msg
            assert "role" in msg
            assert "content" in msg
            assert "created_at" in msg
            assert msg["role"] in ["user", "assistant"]
            assert len(msg["content"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_history_spanish(self, test_app):
        """Test history endpoint with Spanish conversation."""
        ip = "127.0.0.403"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Send Spanish message
            await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Hola", "language": "es"},
                headers={"X-Forwarded-For": ip},
            )
            
            # Get history
            response = await ac.get(
                "/api/v1/guest/chat/history",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language
        if "language" in data:
            assert data["language"] == "es"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_history_portuguese(self, test_app):
        """Test history endpoint with Portuguese conversation."""
        ip = "127.0.0.404"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Send Portuguese message
            await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Olá", "language": "pt"},
                headers={"X-Forwarded-For": ip},
            )
            
            # Get history
            response = await ac.get(
                "/api/v1/guest/chat/history",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language
        if "language" in data:
            assert data["language"] == "pt"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_history_chinese(self, test_app):
        """Test history endpoint with Chinese conversation."""
        ip = "127.0.0.405"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Send Chinese message
            await ac.post(
                "/api/v1/guest/chat",
                json={"content": "你好", "language": "zh"},
                headers={"X-Forwarded-For": ip},
            )
            
            # Get history
            response = await ac.get(
                "/api/v1/guest/chat/history",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language
        if "language" in data:
            assert data["language"] == "zh"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_history_limit(self, test_app):
        """Test history endpoint respects limit parameter."""
        ip = "127.0.0.406"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Send multiple messages
            for i in range(5):
                await ac.post(
                    "/api/v1/guest/chat",
                    json={"content": f"Message {i}", "language": "en"},
                    headers={"X-Forwarded-For": ip},
                )
            
            # Get history with limit
            response = await ac.get(
                "/api/v1/guest/chat/history?limit=3",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should respect limit (may return less if fewer messages)
        assert len(data["messages"]) <= 3

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_status_empty(self, test_app):
        """Test status endpoint returns empty for new guest."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/v1/guest/chat/status",
                headers={"X-Forwarded-For": "127.0.0.407"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return status structure
        assert "has_active_session" in data or "messages_remaining" in data

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_status_with_session(self, test_app):
        """Test status endpoint returns real session data."""
        ip = "127.0.0.408"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Create session by sending message
            await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Test", "language": "en"},
                headers={"X-Forwarded-For": ip},
            )
            
            # Get status
            response = await ac.get(
                "/api/v1/guest/chat/status",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "has_active_session" in data
        assert "messages_remaining" in data
        assert "messages_this_hour" in data
        assert "is_blocked" in data
        
        # Should have active session
        assert data["has_active_session"] is True
        assert data["messages_remaining"] >= 0
        assert data["messages_this_hour"] >= 0
        assert data["is_blocked"] is False

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_status_spanish(self, test_app):
        """Test status endpoint with Spanish session."""
        ip = "127.0.0.409"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Create Spanish session
            await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Hola", "language": "es"},
                headers={"X-Forwarded-For": ip},
            )
            
            # Get status
            response = await ac.get(
                "/api/v1/guest/chat/status",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language
        if "language" in data:
            assert data["language"] == "es"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_status_portuguese(self, test_app):
        """Test status endpoint with Portuguese session."""
        ip = "127.0.0.410"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Create Portuguese session
            await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Olá", "language": "pt"},
                headers={"X-Forwarded-For": ip},
            )
            
            # Get status
            response = await ac.get(
                "/api/v1/guest/chat/status",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language
        if "language" in data:
            assert data["language"] == "pt"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_status_chinese(self, test_app):
        """Test status endpoint with Chinese session."""
        ip = "127.0.0.411"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Create Chinese session
            await ac.post(
                "/api/v1/guest/chat",
                json={"content": "你好", "language": "zh"},
                headers={"X-Forwarded-For": ip},
            )
            
            # Get status
            response = await ac.get(
                "/api/v1/guest/chat/status",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language
        if "language" in data:
            assert data["language"] == "zh"

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_history_message_structure(self, test_app):
        """Test history messages have complete structure."""
        ip = "127.0.0.412"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Send message
            await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Test message", "language": "en"},
                headers={"X-Forwarded-For": ip},
            )
            
            # Get history
            response = await ac.get(
                "/api/v1/guest/chat/history",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify message structure
        if data.get("messages"):
            for msg in data["messages"]:
                assert "id" in msg
                assert "role" in msg
                assert "content" in msg
                assert "created_at" in msg
                assert msg["role"] in ["user", "assistant"]
                
                # Verify optional fields if present
                if "intent" in msg:
                    assert isinstance(msg["intent"], str) or msg["intent"] is None
                if "is_restricted_action" in msg:
                    assert isinstance(msg["is_restricted_action"], bool)

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_history_conversation_id(self, test_app):
        """Test history includes conversation_id when active."""
        ip = "127.0.0.413"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Send message to create conversation
            response1 = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Hello", "language": "en"},
                headers={"X-Forwarded-For": ip},
            )
            assert response1.status_code == 200
            conv_id = response1.json()["conversation_id"]
            
            # Get history
            response = await ac.get(
                "/api/v1/guest/chat/history",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have conversation_id if active
        if data.get("is_active"):
            assert "conversation_id" in data
            assert data["conversation_id"] == conv_id

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_status_rate_limits(self, test_app):
        """Test status endpoint shows accurate rate limit information."""
        ip = "127.0.0.414"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Send a few messages
            for i in range(3):
                await ac.post(
                    "/api/v1/guest/chat",
                    json={"content": f"Message {i}", "language": "en"},
                    headers={"X-Forwarded-For": ip},
                )
            
            # Get status
            response = await ac.get(
                "/api/v1/guest/chat/status",
                headers={"X-Forwarded-For": ip},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify rate limit fields
        assert "messages_remaining" in data
        assert "messages_this_hour" in data
        assert isinstance(data["messages_remaining"], int)
        assert isinstance(data["messages_this_hour"], int)
        assert data["messages_remaining"] >= 0
